"""Shared patient, item, and pair interaction feature builders for ML #3."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.metrics.pairwise import paired_cosine_distances
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from backend.ml.reco.label_rules import CARE_RULES, EXERCISE_RULES, FOOD_RULES, TIER_ORD

PATIENT_NUMERIC_COLS = [
    "age", "bmi", "waist_cm", "systolic_bp", "diastolic_bp",
    "fpg", "hba1c", "total_cholesterol", "ldl", "hdl",
    "triglycerides", "serum_creatinine", "egfr", "urine_acr",
    "alcohol_drinks_per_week",
]

PATIENT_ORDINAL_COLS = [
    "sex_male", "smoker_flag", "activity_ord", "fam_diab_ord",
    "heart_tier_ord", "diabetes_tier_ord", "bp_tier_ord",
    "obesity_tier_ord", "metabolic_tier_ord", "kidney_tier_ord",
]

CAT_INDEX = {"foods": 0, "exercises": 1, "hospitals": 2, "specialties": 3, "care": 4}
ACT_MAP = {"vigorous": 0.0, "moderate": 1.0, "mild": 2.0, "sedentary": 3.0}
FAM_MAP = {"none": 0.0, "one_parent": 1.0, "both": 2.0}

ITEM_STRUCT_NAMES = [
    "cat_idx", "high_sugar", "high_sodium", "high_fiber", "high_sat_fat",
    "high_potassium", "high_protein", "ex_intensity", "ex_clearance",
    "hosp_emergency", "hosp_teleconsult", "hosp_govt",
]

INTERACTION_NAMES = [
    "condition_match", "food_status_ord", "nutrient_conflict",
    "clearance_conflict", "same_city", "specialty_match",
    "emergency_fit", "tfidf_cosine",
]


def patient_to_row(p: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a patient dict into a flat row for the ColumnTransformer."""
    tiers = p.get("tiers", {})
    row: Dict[str, Any] = {
        "age": p.get("age"),
        "bmi": p.get("bmi"),
        "waist_cm": p.get("waist_cm"),
        "systolic_bp": p.get("systolic_bp"),
        "diastolic_bp": p.get("diastolic_bp"),
        "fpg": p.get("fpg"),
        "hba1c": p.get("hba1c"),
        "total_cholesterol": p.get("total_cholesterol"),
        "ldl": p.get("ldl"),
        "hdl": p.get("hdl"),
        "triglycerides": p.get("triglycerides"),
        "serum_creatinine": p.get("serum_creatinine"),
        "egfr": p.get("egfr"),
        "urine_acr": p.get("urine_acr"),
        "alcohol_drinks_per_week": p.get("alcohol_drinks_per_week", 0.0),
        "sex_male": 1.0 if str(p.get("sex", "")).lower() in ("male", "m", "1") else 0.0,
        "smoker_flag": 1.0 if p.get("smoker") else 0.0,
        "activity_ord": ACT_MAP.get(str(p.get("physical_activity", "moderate")).lower(), 1.0),
        "fam_diab_ord": FAM_MAP.get(str(p.get("family_diabetes", "none")).lower(), 0.0),
        "heart_tier_ord": float(TIER_ORD.get(tiers.get("heart"), 1)),
        "diabetes_tier_ord": float(TIER_ORD.get(tiers.get("diabetes"), 1)),
        "bp_tier_ord": float(TIER_ORD.get(tiers.get("hypertension"), 1)),
        "obesity_tier_ord": float(TIER_ORD.get(tiers.get("obesity"), 1)),
        "metabolic_tier_ord": float(TIER_ORD.get(tiers.get("metabolic"), 1)),
        "kidney_tier_ord": float(TIER_ORD.get(tiers.get("kidney"), 1)),
    }
    return row


def build_patient_preprocessor() -> ColumnTransformer:
    """Create ColumnTransformer with median SimpleImputer(add_indicator=True) + StandardScaler."""
    num_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
        ("scaler", StandardScaler()),
    ])
    ord_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
    ])
    return ColumnTransformer(
        transformers=[
            ("num", num_pipe, PATIENT_NUMERIC_COLS),
            ("ord", ord_pipe, PATIENT_ORDINAL_COLS),
        ],
        remainder="drop",
    )


def patient_query_text(p: Dict[str, Any]) -> str:
    """Build patient condition-context text for TF-IDF cosine similarity."""
    tiers = p.get("tiers", {})
    flagged = [f"{k} {v} risk" for k, v in tiers.items() if v in ("high", "moderate")]
    top_c = p.get("top_condition", "heart")
    specs = " ".join(CARE_RULES["condition_to_specialties"].get(top_c, []))
    svcs = " ".join(CARE_RULES["condition_to_services"].get(top_c, []))
    city = p.get("city") or ""
    return f"{top_c} {' '.join(flagged)} {specs} {svcs} {city}"


def fit_item_vectorizer(items: List[Dict[str, Any]]) -> TfidfVectorizer:
    """Fit 1-2 gram TF-IDF vectorizer over KB item EN+HI text."""
    corpus = [it.get("text", it.get("name", "")) for it in items]
    vec = TfidfVectorizer(ngram_range=(1, 2), max_features=800, sublinear_tf=True)
    vec.fit(corpus)
    return vec


def item_struct_vector(item: Dict[str, Any]) -> List[float]:
    """Extract structured numeric flags for a KB item."""
    cat = item["category"]
    flags = item.get("nutrient_flags", {})
    return [
        float(CAT_INDEX.get(cat, 0)),
        float(flags.get("high_sugar", 0)),
        float(flags.get("high_sodium", 0)),
        float(flags.get("high_fiber", 0)),
        float(flags.get("high_sat_fat", 0)),
        float(flags.get("high_potassium", 0)),
        float(flags.get("high_protein", 0)),
        float(EXERCISE_RULES["intensity_order"].get(item.get("intensity", "low"), 0)) if cat == "exercises" else 0.0,
        1.0 if item.get("medical_clearance_required") else 0.0,
        1.0 if item.get("emergency_24x7") else 0.0,
        1.0 if item.get("teleconsult") else 0.0,
        1.0 if item.get("is_govt") else 0.0,
    ]


def compute_interaction_vector(p: Dict[str, Any], item: Dict[str, Any], cosine_sim: float) -> List[float]:
    """Compute explicit domain interaction features for a (patient, item) pair."""
    cat = item["category"]
    tiers = p.get("tiers", {})
    top_cond = p.get("top_condition", "heart")
    top_tier = tiers.get(top_cond, "moderate")
    bp_stage = p.get("bp_stage", "normal")
    age = int(p.get("age", 45))
    egfr = p.get("egfr")
    high_risk_any = any(tiers.get(k) == "high" for k in ("heart", "hypertension", "kidney", "diabetes"))

    cond_match = 0.0
    food_status_ord = 0.5
    nutrient_conflict = 0.0
    clearance_conflict = 0.0
    same_city = 0.0
    spec_match = 0.0
    emerg_fit = 0.0

    if cat == "foods":
        codes = item.get("codes", {})
        cond_key = "diabetes" if top_cond == "metabolic" else top_cond
        status_str = codes.get(cond_key, "watch")
        short_code = {"ok": "o", "watch": "w", "limit": "l", "avoid": "a", "ask_dietitian": "d"}.get(status_str, "w")
        grade = FOOD_RULES["code_to_grade"].get(short_code, 1.5)
        food_status_ord = grade / 3.0
        cond_match = 1.0 if grade >= 2.0 else 0.0
        flags = item.get("nutrient_flags", {})
        if (tiers.get("kidney") in ("moderate", "high") or (egfr is not None and egfr < 60)) and (flags.get("high_potassium") or flags.get("high_protein")):
            nutrient_conflict = 1.0
        if tiers.get("diabetes") in ("moderate", "high") and flags.get("high_sugar"):
            nutrient_conflict = 1.0
        if tiers.get("hypertension") in ("moderate", "high") and flags.get("high_sodium"):
            nutrient_conflict = 1.0
        if tiers.get("heart") in ("moderate", "high") and flags.get("high_sat_fat"):
            nutrient_conflict = 1.0

    elif cat == "exercises":
        cond_key = "diabetes" if top_cond == "metabolic" else top_cond
        cond_match = 1.0 if cond_key in set(item.get("conditions_safe", [])) else 0.0
        intensity_val = EXERCISE_RULES["intensity_order"].get(item.get("intensity", "low"), 1)
        max_safe = EXERCISE_RULES["bp_stage_max_safe_intensity"].get(bp_stage, 1)
        if intensity_val > max_safe or (item.get("medical_clearance_required") and (high_risk_any or age < 18 or age > 75)):
            clearance_conflict = 1.0

    elif cat == "hospitals":
        p_city = (p.get("city") or "").strip().lower()
        h_city = (item.get("city") or "").strip().lower()
        same_city = 1.0 if (p_city and h_city and p_city == h_city) else 0.0
        req_specs = set(s.lower() for s in CARE_RULES["condition_to_specialties"].get(top_cond, []))
        hosp_specs = set(s.lower() for s in item.get("specialties", []))
        spec_match = float(len(req_specs & hosp_specs))
        emerg_fit = 1.0 if (item.get("emergency_24x7") and high_risk_any) else 0.0
        cond_match = 1.0 if (same_city or spec_match > 0) else 0.0

    elif cat == "specialties":
        req_specs = [s.lower() for s in CARE_RULES["condition_to_specialties"].get(top_cond, [])]
        is_match = item.get("name", "").lower() in req_specs
        cond_match = 1.0 if is_match else 0.0
        spec_match = 1.0 if is_match else 0.0

    else:  # care
        req_svcs = [s.lower() for s in CARE_RULES["condition_to_services"].get(top_cond, [])]
        if item.get("name", "").lower() in req_svcs:
            cond_match = 1.0
        elif item.get("care_type") == "care_routing" and (
            (top_tier == "high" and item.get("urgency") == "24_72_hours")
            or (top_tier == "moderate" and item.get("urgency") == "within_2_weeks")
            or (top_tier == "low" and item.get("urgency") == "routine")
        ):
            cond_match = 1.0

    return [
        cond_match,
        food_status_ord,
        nutrient_conflict,
        clearance_conflict,
        same_city,
        spec_match,
        emerg_fit,
        float(cosine_sim),
    ]


def build_pair_matrix(
    patients: List[Dict[str, Any]],
    items: List[Dict[str, Any]],
    preprocessor: ColumnTransformer,
    vectorizer: TfidfVectorizer,
    fit_preprocessor: bool = False,
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """Build combined [patient_features, item_features, interaction_features] matrix."""
    p_df = pd.DataFrame([patient_to_row(p) for p in patients])
    if fit_preprocessor:
        p_mat = preprocessor.fit_transform(p_df)
    else:
        p_mat = preprocessor.transform(p_df)

    p_texts = [patient_query_text(p) for p in patients]
    i_texts = [it.get("text", it.get("name", "")) for it in items]
    p_vec = vectorizer.transform(p_texts)
    i_vec = vectorizer.transform(i_texts)
    cosines = 1.0 - paired_cosine_distances(p_vec, i_vec)
    cosines = np.nan_to_num(cosines, nan=0.0)

    i_mat = np.array([item_struct_vector(it) for it in items], dtype=float)
    inter_mat = np.array(
        [compute_interaction_vector(p, it, float(c)) for p, it, c in zip(patients, items, cosines)],
        dtype=float,
    )

    X = np.hstack([p_mat, i_mat, inter_mat])

    # Build feature names for explainability / permutation importance
    num_names = list(preprocessor.named_transformers_["num"].get_feature_names_out(PATIENT_NUMERIC_COLS))
    ord_names = list(PATIENT_ORDINAL_COLS)
    feat_names = num_names + ord_names + ITEM_STRUCT_NAMES + INTERACTION_NAMES
    return X, cosines, feat_names

