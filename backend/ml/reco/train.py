"""Offline training script for ML #3 Personalized Recommendation Engine.

Run from repo root:
    python -m backend.ml.reco.train
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.inspection import permutation_importance
from sklearn.model_selection import GroupShuffleSplit

_REPO_ROOT = Path(__file__).resolve().parents[3]
_BACKEND_DIR = _REPO_ROOT / "backend"
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.core.config import ARTIFACTS_DIR
from app.services.kb.records import build_knowledge_base_record
from backend.ml.reco.evaluate import evaluate_rankings
from backend.ml.reco.features import (
    INTERACTION_NAMES,
    ITEM_STRUCT_NAMES,
    build_pair_matrix,
    build_patient_preprocessor,
    fit_item_vectorizer,
)
from backend.ml.reco.label_rules import normalize_kb_candidates, score_pair_by_rules
from backend.ml.reco.synth import SYNTH_SEED, generate_synthetic_patients, sample_training_pairs

RECO_MODEL_PATH = ARTIFACTS_DIR / "reco_model.joblib"
RECO_META_PATH = ARTIFACTS_DIR / "reco_meta.json"
RECO_EVAL_PATH = ARTIFACTS_DIR / "reco_eval.json"


def _kb_hash(kb: Dict[str, Any]) -> str:
    payload = json.dumps(kb.get("counts", {}), sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]


def train_reco_pipeline(n_profiles: int = 20000, seed: int = SYNTH_SEED) -> Dict[str, Any]:
    """Generate synthetic profiles, train HGBR ranker, benchmark vs baselines, and save artifacts."""
    kb = build_knowledge_base_record(save=True)
    candidates = normalize_kb_candidates(kb)

    profiles = generate_synthetic_patients(n_profiles=n_profiles, seed=seed)
    p_rows, i_rows, y_all, groups = sample_training_pairs(profiles, candidates, pairs_per_profile=12, seed=seed)

    # 80/20 Group split by patient_id (never split by pair)
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=seed)
    train_idx, test_idx = next(splitter.split(y_all, y_all, groups))

    p_train = [p_rows[i] for i in train_idx]
    i_train = [i_rows[i] for i in train_idx]
    y_train = y_all[train_idx]

    p_test = [p_rows[i] for i in test_idx]
    i_test = [i_rows[i] for i in test_idx]
    y_test = y_all[test_idx]
    g_test = groups[test_idx]

    preprocessor = build_patient_preprocessor()
    vectorizer = fit_item_vectorizer(candidates)

    X_train, _, feat_names = build_pair_matrix(p_train, i_train, preprocessor, vectorizer, fit_preprocessor=True)
    X_test, cos_test, _ = build_pair_matrix(p_test, i_test, preprocessor, vectorizer, fit_preprocessor=False)

    ranker = HistGradientBoostingRegressor(
        max_iter=140,
        max_depth=6,
        learning_rate=0.08,
        min_samples_leaf=30,
        random_state=seed,
    )
    ranker.fit(X_train, y_train)
    pred_hgbr = np.clip(ranker.predict(X_test), 0.0, 3.0)

    # Compute Baseline B (noisy rule-table baseline representing rigid rules without learned interaction smoothing)
    rule_preds = np.array([score_pair_by_rules(p, it)[0] for p, it in zip(p_test, i_test)], dtype=float)

    def _build_eval_groups(preds: np.ndarray) -> Dict[int, List[Dict[str, Any]]]:
        grouped: Dict[int, List[Dict[str, Any]]] = {}
        for pid, it, true_y, pred_y in zip(g_test, i_test, y_test, preds):
            grouped.setdefault(int(pid), []).append({
                "item_id": it["id"],
                "true_label": float(true_y),
                "pred_score": float(pred_y),
                "safety_blocked": float(true_y) == 0.0,
            })
        return grouped

    hgbr_metrics = evaluate_rankings(_build_eval_groups(pred_hgbr), len(candidates))
    cosine_metrics = evaluate_rankings(_build_eval_groups(cos_test * 3.0), len(candidates))
    rule_metrics = evaluate_rankings(_build_eval_groups(rule_preds), len(candidates))

    # Offline permutation importance on a 4,000-row sample of held-out test set
    sample_n = min(4000, len(X_test))
    perm = permutation_importance(ranker, X_test[:sample_n], y_test[:sample_n], n_repeats=3, random_state=seed, n_jobs=-1)
    feat_imp = sorted(
        [{"feature": name, "importance": round(float(imp), 5)} for name, imp in zip(feat_names, perm.importances_mean)],
        key=lambda x: x["importance"],
        reverse=True,
    )

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    model_version = f"reco-hgbr-v1.0-{datetime.now(timezone.utc).strftime('%Y%m%d')}"
    artifact_payload = {
        "model": ranker,
        "preprocessor": preprocessor,
        "vectorizer": vectorizer,
        "feature_names": feat_names,
        "model_version": model_version,
    }
    joblib.dump(artifact_payload, RECO_MODEL_PATH, compress=3)
    size_mb = round(RECO_MODEL_PATH.stat().st_size / (1024.0 * 1024.0), 3)

    eval_payload = {
        "model_version": model_version,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "n_profiles": n_profiles,
        "train_pairs": int(len(y_train)),
        "test_pairs": int(len(y_test)),
        "artifact_size_mb": size_mb,
        "models": {
            "hist_gradient_boosting": hgbr_metrics,
            "baseline_cosine_similarity": cosine_metrics,
            "baseline_rule_table": rule_metrics,
        },
        "top_permutation_importances": feat_imp[:12],
        "limitations": (
            "Labels are derived from clinical rule tables and synthetic Indian population profiles, "
            "not real longitudinal patient outcomes. The ranker smooths and generalizes those rules "
            "across missing-lab combinations and is strictly educational."
        ),
    }
    with open(RECO_EVAL_PATH, "w", encoding="utf-8") as f:
        json.dump(eval_payload, f, indent=2)

    meta_payload = {
        "model_version": model_version,
        "seed": seed,
        "kb_hash": _kb_hash(kb),
        "kb_counts": kb["counts"],
        "feature_count": len(feat_names),
        "feature_names": feat_names,
        "item_struct_names": ITEM_STRUCT_NAMES,
        "interaction_names": INTERACTION_NAMES,
        "artifact_size_mb": size_mb,
    }
    with open(RECO_META_PATH, "w", encoding="utf-8") as f:
        json.dump(meta_payload, f, indent=2)

    return eval_payload


if __name__ == "__main__":
    res = train_reco_pipeline()
    print(json.dumps({
        "model_version": res["model_version"],
        "artifact_size_mb": res["artifact_size_mb"],
        "hgbr_ndcg10": res["models"]["hist_gradient_boosting"]["ndcg_at_10"],
        "cosine_ndcg10": res["models"]["baseline_cosine_similarity"]["ndcg_at_10"],
        "rule_ndcg10": res["models"]["baseline_rule_table"]["ndcg_at_10"],
    }, indent=2))

