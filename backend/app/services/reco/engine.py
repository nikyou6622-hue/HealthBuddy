"""Personalized Recommendation Engine service (ML #3) with ablation explainability & fallback."""

from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np

from app.core.config import ARTIFACTS_DIR
from app.services.kb.records import get_knowledge_base
from app.services.reco.safety_filter import apply_safety_filter, check_emergency_short_circuit
from app.services.safety.disclaimers import PERSISTENT_BANNER_DISCLAIMER

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    from backend.ml.reco.features import (
        INTERACTION_NAMES,
        ITEM_STRUCT_NAMES,
        PATIENT_NUMERIC_COLS,
        PATIENT_ORDINAL_COLS,
        build_pair_matrix,
    )
    from backend.ml.reco.label_rules import CARE_RULES, normalize_kb_candidates, score_pair_by_rules
    from backend.ml.reco.synth import compute_profile_tiers
except ImportError:
    from ml.reco.features import (  # type: ignore[no-redef]
        INTERACTION_NAMES,
        ITEM_STRUCT_NAMES,
        PATIENT_NUMERIC_COLS,
        PATIENT_ORDINAL_COLS,
        build_pair_matrix,
    )
    from ml.reco.label_rules import CARE_RULES, normalize_kb_candidates, score_pair_by_rules  # type: ignore[no-redef]
    from ml.reco.synth import compute_profile_tiers  # type: ignore[no-redef]

RECO_MODEL_PATH = ARTIFACTS_DIR / "reco_model.joblib"
RECO_EVAL_PATH = ARTIFACTS_DIR / "reco_eval.json"
REASON_TEMPLATES_PATH = Path(__file__).resolve().parent / "content" / "reason_templates.json"

LAB_FIELDS = [
    ("fpg", "Fasting Glucose"),
    ("hba1c", "HbA1c"),
    ("total_cholesterol", "Total Cholesterol"),
    ("ldl", "LDL Cholesterol"),
    ("hdl", "HDL Cholesterol"),
    ("triglycerides", "Triglycerides"),
    ("serum_creatinine", "Serum Creatinine"),
    ("urine_acr", "Urine ACR"),
]

TRAINED_RANGES = {
    "age": (18, 90),
    "systolic_bp": (85, 200),
    "diastolic_bp": (50, 125),
    "waist_cm": (55, 145),
}


@lru_cache(maxsize=1)
def _load_reason_templates() -> Dict[str, Dict[str, str]]:
    with open(REASON_TEMPLATES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _load_reco_artifact() -> Optional[Dict[str, Any]]:
    if not RECO_MODEL_PATH.exists():
        return None
    try:
        return joblib.load(RECO_MODEL_PATH)
    except Exception:
        return None


def get_reco_model_info() -> Dict[str, Any]:
    """Return offline evaluation metrics and limitations for /api/v1/reco/model-info."""
    if RECO_EVAL_PATH.exists():
        with open(RECO_EVAL_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "model_version": "rules-fallback",
        "trained_at": None,
        "models": {},
        "limitations": "Model artifact not found; running deterministic rule-table fallback.",
    }


@lru_cache(maxsize=1)
def _get_cached_candidates() -> List[Dict[str, Any]]:
    kb = get_knowledge_base()
    return normalize_kb_candidates(kb)


def _compute_batch_ablation_drops(
    selected_items: List[Dict[str, Any]],
    X_all: Optional[np.ndarray],
    model: Any,
    feat_names: List[str],
) -> Dict[int, List[Tuple[str, float]]]:
    """Run one batched model.predict() across all selected items and 4 feature-group ablations."""
    drops_by_idx: Dict[int, List[Tuple[str, float]]] = {}
    if model is None or X_all is None or not selected_items:
        return drops_by_idx

    groups = {
        "condition_match": [i for i, n in enumerate(feat_names) if n in ("condition_match", "food_status_ord")],
        "text_relevance": [i for i, n in enumerate(feat_names) if n == "tfidf_cosine"],
        "same_city_hospital": [i for i, n in enumerate(feat_names) if n in ("same_city", "specialty_match", "emergency_fit")],
        "high_fiber_benefit": [i for i, n in enumerate(feat_names) if n == "high_fiber"],
    }
    active_groups = [(g_key, idxs) for g_key, idxs in groups.items() if idxs]
    if not active_groups:
        return drops_by_idx

    batch_rows: List[np.ndarray] = []
    meta_pairs: List[Tuple[int, float, str]] = []
    for item in selected_items:
        idx = item["_idx"]
        base_pred = float(item["_raw_pred"])
        row = X_all[idx : idx + 1]
        for g_key, idxs in active_groups:
            abl = row.copy()
            abl[0, idxs] = 0.0
            batch_rows.append(abl)
            meta_pairs.append((idx, base_pred, g_key))

    X_batch = np.vstack(batch_rows)
    preds = model.predict(X_batch)
    for (idx, base_pred, g_key), pred_val in zip(meta_pairs, preds):
        drop = float(base_pred - float(pred_val))
        if drop > 0.01:
            drops_by_idx.setdefault(idx, []).append((g_key, drop))
    for idx in drops_by_idx:
        drops_by_idx[idx].sort(key=lambda x: x[1], reverse=True)
    return drops_by_idx


def _build_reasons_via_ablation(
    patient: Dict[str, Any],
    item: Dict[str, Any],
    group_drops: List[Tuple[str, float]],
    missing_labs_ratio: float,
) -> List[Dict[str, str]]:
    """Compute top 3 plain-language EN+HI reasons via feature-group ablation + rule context."""
    templates = _load_reason_templates()
    top_cond = patient.get("top_condition", "heart")
    top_tier = patient.get("tiers", {}).get(top_cond, "moderate")

    reason_keys: List[str] = []
    cat = item["category"]
    if cat == "foods":
        status_label = item.get("status_label", "watch")
        if status_label in ("eat_more", "ok"):
            reason_keys.append("food_status_ok")
        elif status_label == "watch":
            reason_keys.append("food_status_watch")
        else:
            reason_keys.append("food_status_limit")
        if item.get("nutrient_flags", {}).get("high_fiber"):
            reason_keys.append("high_fiber_benefit")
    elif cat == "exercises":
        if item.get("needs_medical_clearance"):
            reason_keys.append("clearance_advised")
        else:
            reason_keys.append("low_intensity_safe")
    elif cat == "hospitals":
        p_city = (patient.get("city") or "").strip().lower()
        if p_city and (item.get("city") or "").strip().lower() == p_city:
            reason_keys.append("same_city_hospital")
        if item.get("emergency_24x7") and top_tier == "high":
            reason_keys.append("emergency_capable")
    elif cat in ("specialties", "care"):
        reason_keys.append("specialty_match")

    for g_key, _ in group_drops:
        if g_key not in reason_keys:
            reason_keys.append(g_key)

    if "condition_match" not in reason_keys:
        reason_keys.append("condition_match")
    if "text_relevance" not in reason_keys:
        reason_keys.append("text_relevance")
    if missing_labs_ratio > 0.5 and "missing_labs_note" not in reason_keys:
        reason_keys.append("missing_labs_note")

    out: List[Dict[str, str]] = []
    city_lbl = patient.get("city") or item.get("city") or "your city"
    for rk in reason_keys[:3]:
        tpl = templates.get(rk, templates["text_relevance"])
        out.append({
            "en": tpl["en"].format(condition=top_cond, tier=top_tier, city=city_lbl),
            "hi": tpl["hi"].format(condition=top_cond, tier=top_tier, city=city_lbl),
        })
    return out


def generate_personalized_recommendations(
    payload: Dict[str, Any],
    lang: str = "en",
    top_k: int = 8,
    artifact_override: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Run safety check -> feature engineering -> HGBR ranker -> post-filter -> explanations."""
    # 1. Emergency red-flag short-circuit
    safety = check_emergency_short_circuit(payload)
    if safety.get("emergency"):
        return {
            "emergency": safety,
            "categories": {"foods": [], "exercises": [], "hospitals": [], "specialties": [], "care": []},
            "confidence": "high_confidence",
            "missing_inputs": [],
            "model_version": "safety-override",
            "followup_days": 0,
            "disclaimer": PERSISTENT_BANNER_DISCLAIMER,
        }

    # 2. Compute deterministic 6 risk tiers & detect missing labs / out-of-range
    patient = compute_profile_tiers(dict(payload))
    missing_inputs = [label for field, label in LAB_FIELDS if payload.get(field) is None]
    missing_labs_ratio = len(missing_inputs) / float(len(LAB_FIELDS))

    out_of_range = False
    for k, (lo, hi) in TRAINED_RANGES.items():
        val = payload.get(k)
        if val is not None and (float(val) < lo or float(val) > hi):
            out_of_range = True

    candidates = _get_cached_candidates()

    artifact = artifact_override if artifact_override is not None else _load_reco_artifact()
    use_ml = artifact is not None and "model" in artifact

    if use_ml:
        model = artifact["model"]
        preprocessor = artifact["preprocessor"]
        vectorizer = artifact["vectorizer"]
        feat_names = artifact["feature_names"]
        model_version = artifact.get("model_version", "reco-hgbr-v1.0")

        p_list = [patient] * len(candidates)
        X_all, _, _ = build_pair_matrix(p_list, candidates, preprocessor, vectorizer, fit_preprocessor=False)
        raw_preds = np.clip(model.predict(X_all), 0.0, 3.0)
    else:
        model = None
        feat_names = []
        X_all = None
        model_version = "rules-fallback"
        raw_preds = np.array([score_pair_by_rules(patient, it)[0] for it in candidates], dtype=float)

    # Group by category and sort descending by predicted score
    by_cat: Dict[str, List[Dict[str, Any]]] = {"foods": [], "exercises": [], "hospitals": [], "specialties": [], "care": []}
    for idx, (item, raw_s) in enumerate(zip(candidates, raw_preds)):
        item_copy = dict(item)
        item_copy["_score"] = round(float(raw_s) / 3.0, 4)
        item_copy["_raw_pred"] = float(raw_s)
        item_copy["_idx"] = idx
        by_cat[item["category"]].append(item_copy)

    for cat in by_cat:
        by_cat[cat].sort(key=lambda x: (-x["_score"], x["name"]))

    # 3. Apply non-negotiable safety filter AFTER model ranking
    filtered_by_cat, _ = apply_safety_filter(patient, by_cat)

    # Confidence calculation
    food_scores = [x["_score"] for x in filtered_by_cat.get("foods", [])[:2]]
    top_margin = (food_scores[0] - food_scores[1]) if len(food_scores) >= 2 else 0.1
    if not use_ml or missing_labs_ratio > 0.5 or out_of_range or top_margin < 0.05:
        confidence = "low_confidence"
    elif missing_labs_ratio > 0.0:
        confidence = "medium"
    else:
        confidence = "high"

    # 4. Format top_k per category with rank, reasons (EN + HI), confidence, and safety_notes
    selected_all = [item for items_list in filtered_by_cat.values() for item in items_list[:top_k]]
    drops_by_idx = _compute_batch_ablation_drops(selected_all, X_all, model, feat_names)

    formatted: Dict[str, List[Dict[str, Any]]] = {}
    for cat, items_list in filtered_by_cat.items():
        cat_out: List[Dict[str, Any]] = []
        for rank_idx, item in enumerate(items_list[:top_k], start=1):
            reasons = _build_reasons_via_ablation(
                patient,
                item,
                drops_by_idx.get(item["_idx"], []),
                missing_labs_ratio,
            )
            cat_out.append({
                "id": item["id"],
                "category": cat,
                "name": item.get("name", ""),
                "hindi": item.get("hindi", item.get("name", "")),
                "rank": rank_idx,
                "score": item["_score"],
                "status_label": item.get("status_label") or item.get("intensity") or item.get("city") or item.get("care_type") or "recommended",
                "needs_medical_clearance": bool(item.get("needs_medical_clearance", False)),
                "reasons": reasons,
                "confidence": confidence,
                "safety_notes": item.get("safety_notes", ""),
                "meta": {
                    k: item.get(k)
                    for k in ("group", "note", "duration_or_reps", "benefits", "cautions", "city", "pincode", "lat", "lon", "phone", "emergency_24x7", "insurance_notes", "teleconsult", "subspecialty", "conditions_covered", "available_at_hospitals", "description", "urgency")
                    if item.get(k) is not None
                },
            })
        formatted[cat] = cat_out

    top_tier = patient.get("tiers", {}).get(patient.get("top_condition", "heart"), "moderate")
    followup_days = CARE_RULES["followup_days_by_tier"].get(top_tier, 21)

    return {
        "emergency": None,
        "top_condition": patient.get("top_condition"),
        "top_tier": top_tier,
        "followup_days": followup_days,
        "categories": formatted,
        "confidence": confidence,
        "missing_inputs": missing_inputs,
        "model_version": model_version,
        "disclaimer": PERSISTENT_BANNER_DISCLAIMER,
    }
