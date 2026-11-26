"""Assessment orchestrator: safety check -> calculators -> ML -> recommendations."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.calculators.anthropometry import calculate_anthropometry
from app.services.calculators.bp import calculate_bp
from app.services.calculators.glucose import classify_glucose
from app.services.calculators.idrs import calculate_idrs
from app.services.calculators.kidney import calculate_kidney_egfr
from app.services.calculators.metabolic import calculate_metabolic_syndrome
from app.services.calculators.who_cvd import calculate_who_cvd
from app.services.care.matcher import recommend_care
from app.services.ml.predictor import HealthBuddyPredictor
from app.services.recommend.engine import get_recommendation_plan
from app.services.safety.disclaimers import FULL_MEDICAL_DISCLAIMER, PERSISTENT_BANNER_DISCLAIMER
from app.services.safety.red_flags import RedFlagInput, evaluate_red_flags

_ml_cache: Dict[str, HealthBuddyPredictor] = {}


def _get_ml(disease: str) -> Optional[HealthBuddyPredictor]:
    try:
        if disease not in _ml_cache:
            _ml_cache[disease] = HealthBuddyPredictor(disease=disease)
        return _ml_cache[disease]
    except Exception:
        return None


def _ml_band(prob: Optional[float]) -> Dict[str, str]:
    """Map calibrated probability to configurable risk band and rounded range."""
    if prob is None:
        return {"category": "moderate", "range_label": "Estimated risk unavailable"}
    if prob < settings.ML_LOW_THRESHOLD:
        return {"category": "low", "range_label": f"Under {int(settings.ML_LOW_THRESHOLD * 100)}%"}
    if prob <= settings.ML_HIGH_THRESHOLD:
        return {
            "category": "moderate",
            "range_label": f"{int(settings.ML_LOW_THRESHOLD * 100)}–{int(settings.ML_HIGH_THRESHOLD * 100)}%",
        }
    return {"category": "high", "range_label": f"Above {int(settings.ML_HIGH_THRESHOLD * 100)}%"}


def run_full_assessment(payload: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """Orchestrate safety check -> deterministic calculators -> ML -> care & plans.

    If a red flag fires, returns ONLY { emergency: {...} } with NO scores and NO exercise advice.
    """
    # 1. Safety layer ALWAYS runs first
    rf_input = RedFlagInput(
        **(payload.get("red_flags") or {}),
        glucose_mg_dl=payload.get("fpg") or (payload.get("red_flags") or {}).get("glucose_mg_dl"),
    )
    safety = evaluate_red_flags(rf_input)
    if safety["emergency"]:
        return {
            "emergency": safety,
            "disclaimer": PERSISTENT_BANNER_DISCLAIMER,
        }

    # 2. Deterministic clinical calculators (missing labs -> status='skipped')
    age = int(payload["age"])
    sex = str(payload["sex"])
    height_cm = float(payload["height_cm"])
    weight_kg = float(payload["weight_kg"])
    waist_cm = float(payload["waist_cm"])
    sbp = float(payload["systolic_bp"])
    dbp = float(payload["diastolic_bp"])
    activity = str(payload["physical_activity"])
    fam_diab = str(payload["family_diabetes"])

    anthro = calculate_anthropometry(height_cm=height_cm, weight_kg=weight_kg, waist_cm=waist_cm, sex=sex)
    bp_res = calculate_bp(systolic_bp=sbp, diastolic_bp=dbp)
    idrs_res = calculate_idrs(age=age, waist_cm=waist_cm, sex=sex, physical_activity=activity, family_diabetes=fam_diab)
    glucose_res = classify_glucose(hba1c=payload.get("hba1c"), fpg=payload.get("fpg"), ogtt_2h=payload.get("ogtt_2h"))
    diab_present = bool(glucose_res.get("glycemic_status") == "diabetes")
    who_res = calculate_who_cvd(
        age=age,
        sex=sex,
        systolic_bp=sbp,
        smoker=bool(payload.get("smoker", False)),
        diabetes_present=diab_present,
        total_cholesterol_mg_dl=payload.get("total_cholesterol"),
        bmi=anthro.get("score"),
    )
    kidney_res = calculate_kidney_egfr(
        age=age,
        sex=sex,
        serum_creatinine_mg_dl=payload.get("serum_creatinine"),
        urine_acr_mg_g=payload.get("urine_acr"),
    )
    metabolic_res = calculate_metabolic_syndrome(
        waist_cm=waist_cm,
        sex=sex,
        systolic_bp=sbp,
        diastolic_bp=dbp,
        fpg=payload.get("fpg"),
        triglycerides_mg_dl=payload.get("triglycerides"),
        hdl_mg_dl=payload.get("hdl"),
    )

    modules: List[Dict[str, Any]] = [anthro, bp_res, idrs_res, glucose_res, who_res, kidney_res, metabolic_res]

    # 3. ML modules: run ONLY when all required training features are present; otherwise 'needs_more_info'
    ml_results: List[Dict[str, Any]] = []
    ml_reqs = {
        "parkinsons": "Requires 22 voice acoustic measurements not collected in this screening wizard.",
        "liver_disease": "Requires liver enzyme and bilirubin lab panel (AST, ALT, ALP, bilirubin, albumin) not collected in this wizard.",
    }
    provided_ml = payload.get("ml_features") or {}
    target_ml_disease = payload.get("ml_disease")

    for d_key, missing_reason in ml_reqs.items():
        if target_ml_disease == d_key and provided_ml:
            pred_engine = _get_ml(d_key)
            if pred_engine and all(f in provided_ml for f in pred_engine.feature_names):
                ml_out = pred_engine.predict(provided_ml)
                if ml_out.get("success"):
                    band = _ml_band(ml_out.get("probability"))
                    ml_results.append(
                        {
                            "module": f"ml_{d_key}",
                            "status": "computed",
                            "skip_reason": None,
                            "score": band["range_label"],
                            "unit": "estimated risk band",
                            "category": band["category"],
                            "method": "ML estimated risk band (Secondary opinion)",
                            "confidence_flag": ml_out["confidence_flag"],
                            "factors": [f["plain_explanation"] for f in ml_out.get("top_factors", [])[:3]],
                            "kind": "ml",
                            "disagreement_note": None,
                        }
                    )
                    continue
        ml_results.append(
            {
                "module": f"ml_{d_key}",
                "status": "needs_more_info",
                "skip_reason": missing_reason,
                "score": None,
                "unit": "estimated risk band",
                "category": None,
                "method": "ML estimated risk band (Secondary opinion)",
                "confidence_flag": "unavailable",
                "factors": [],
                "kind": "ml",
                "disagreement_note": None,
            }
        )

    # Optional ML for heart_disease / diabetes if ml_features provided
    if target_ml_disease in ("heart_disease", "diabetes") and provided_ml:
        pred_engine = _get_ml(target_ml_disease)
        if pred_engine and all(f in provided_ml for f in pred_engine.feature_names):
            ml_out = pred_engine.predict(provided_ml)
            if ml_out.get("success"):
                band = _ml_band(ml_out.get("probability"))
                rule_cat = who_res.get("category") if target_ml_disease == "heart_disease" else idrs_res.get("category")
                disagreement = None
                if rule_cat in ("low", "moderate", "high") and rule_cat != band["category"]:
                    disagreement = (
                        f"Rule-based score ({rule_cat}) and ML estimated risk ({band['category']}) differ. "
                        "Both are shown separately; review both with a doctor."
                    )
                ml_results.append(
                    {
                        "module": f"ml_{target_ml_disease}",
                        "status": "computed",
                        "skip_reason": None,
                        "score": band["range_label"],
                        "unit": "estimated risk band",
                        "category": band["category"],
                        "method": "ML estimated risk band (Secondary opinion)",
                        "confidence_flag": ml_out["confidence_flag"],
                        "factors": [f["plain_explanation"] for f in ml_out.get("top_factors", [])[:3]],
                        "kind": "ml",
                        "disagreement_note": disagreement,
                    }
                )

    # 4. Recommendation plans & follow-up dates (3, 6, or 12 months by tier)
    condition_tier_map = {
        "obesity": anthro.get("category") or "low",
        "hypertension": bp_res.get("category") or "low",
        "diabetes": (
            glucose_res.get("category")
            if glucose_res.get("status") == "computed"
            else (idrs_res.get("category") or "low")
        ),
        "heart": (
            who_res.get("category")
            if who_res.get("status") == "computed"
            else (bp_res.get("category") or "low")
        ),
    }
    if kidney_res.get("status") == "computed":
        condition_tier_map["kidney"] = kidney_res["category"]
    if metabolic_res.get("status") == "computed":
        condition_tier_map["metabolic"] = metabolic_res["category"]

    tier_months = {"high": 3, "moderate": 6, "low": 12}
    plans: Dict[str, Any] = {}
    followups: List[Dict[str, Any]] = []
    for cond, tier in condition_tier_map.items():
        plan = get_recommendation_plan(cond, tier)
        months = tier_months.get(tier, 6)
        due_date = (datetime.now(timezone.utc) + timedelta(days=months * 30)).date().isoformat()
        plan["followup_due_date"] = due_date
        plan["followup_months"] = months
        plans[cond] = plan
        followups.append({"condition": cond, "tier": tier, "due_date": due_date, "months": months})

    highest_tier = "High" if "high" in condition_tier_map.values() else ("Moderate" if "moderate" in condition_tier_map.values() else "Low")
    urgency = "urgent_24_72h" if highest_tier == "High" else ("within_2_weeks" if highest_tier == "Moderate" else "routine_6_12_months")

    # Max 3 "what_to_do_first" items from highest-tier conditions
    what_to_do_first: List[str] = []
    for cond, tier in sorted(condition_tier_map.items(), key=lambda kv: {"high": 0, "moderate": 1, "low": 2}.get(kv[1], 3)):
        for item in plans[cond]["doctor_tests"]:
            if item not in what_to_do_first:
                what_to_do_first.append(item)
            if len(what_to_do_first) >= 3:
                break
        if len(what_to_do_first) >= 3:
            break

    care = recommend_care(
        db=db,
        disease="heart_disease" if condition_tier_map.get("heart") == "high" else "diabetes",
        risk_level=highest_tier,
        city=payload.get("city"),
        pincode=payload.get("pincode"),
        user_lat=payload.get("lat") if payload.get("consent_location") else None,
        user_lon=payload.get("lon") if payload.get("consent_location") else None,
    )

    return {
        "emergency": None,
        "urgency": urgency,
        "what_to_do_first": what_to_do_first[:3],
        "modules": modules,
        "ml_results": ml_results,
        "plans": plans,
        "followups": followups,
        "care": care,
        "disclaimer": FULL_MEDICAL_DISCLAIMER,
    }
