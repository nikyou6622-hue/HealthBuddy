"""Deterministic synthetic patient generator (20,000 profiles) for ML #3 training."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple
import numpy as np

from app.services.calculators.anthropometry import calculate_anthropometry
from app.services.calculators.bp import calculate_bp
from app.services.calculators.idrs import calculate_idrs
from app.services.calculators.kidney import calculate_kidney_egfr
from app.services.calculators.metabolic import calculate_metabolic_syndrome
from app.services.calculators.who_cvd import calculate_who_cvd
from backend.ml.reco.label_rules import score_pair_by_rules

SYNTH_SEED = 42
CITIES = [
    "New Delhi", "Mumbai", "Bengaluru", "Chennai", "Hyderabad",
    "Kolkata", "Pune", "Jaipur", "Ahmedabad", "Lucknow", "Kochi", "Bhopal",
]
ACTIVITIES = ["vigorous", "moderate", "mild", "sedentary"]
FAM_DIAB = ["none", "one_parent", "both"]


def compute_profile_tiers(p: Dict[str, Any]) -> Dict[str, Any]:
    """Run the 6 deterministic calculators on a profile to attach exact risk tiers."""
    anthro = calculate_anthropometry(p["height_cm"], p["weight_kg"], p["waist_cm"], p["sex"])
    bp = calculate_bp(p["systolic_bp"], p["diastolic_bp"])
    idrs = calculate_idrs(p["age"], p["waist_cm"], p["sex"], p["physical_activity"], p["family_diabetes"])
    diab_present = bool((p.get("hba1c") is not None and p["hba1c"] >= 6.5) or (p.get("fpg") is not None and p["fpg"] >= 126))
    who = calculate_who_cvd(
        p["age"], p["sex"], p["systolic_bp"], p["smoker"], diab_present, p.get("total_cholesterol"), anthro.get("score")
    )
    kidney = calculate_kidney_egfr(p["age"], p["sex"], p.get("serum_creatinine"), p.get("urine_acr"))
    metab = calculate_metabolic_syndrome(
        p["waist_cm"], p["sex"], p["systolic_bp"], p["diastolic_bp"], p.get("fpg"), p.get("triglycerides"), p.get("hdl")
    )

    tiers = {
        "heart": who.get("category") if who.get("status") == "computed" else "low",
        "diabetes": "high" if diab_present else (idrs.get("category") or "low"),
        "hypertension": bp.get("category") or "low",
        "obesity": anthro.get("category") or "low",
        "metabolic": metab.get("category") if metab.get("status") == "computed" else "moderate",
        "kidney": kidney.get("category") if kidney.get("status") == "computed" else "low",
    }
    rank = {"high": 0, "moderate": 1, "low": 2}
    top_cond = min(tiers.keys(), key=lambda k: rank.get(tiers[k], 2))
    p["bmi"] = anthro.get("score")
    p["egfr"] = kidney.get("score")
    p["bp_stage"] = bp.get("bp_stage", "normal")
    p["tiers"] = tiers
    p["top_condition"] = top_cond
    return p


def generate_synthetic_patients(n_profiles: int = 20000, seed: int = SYNTH_SEED) -> List[Dict[str, Any]]:
    """Generate clinically plausible Indian patient profiles with ~40% missing labs & edge cases."""
    rng = np.random.default_rng(seed)
    profiles: List[Dict[str, Any]] = []

    for i in range(n_profiles):
        # Deliberate clinical archetypes + general population
        archetype = i % 10
        if archetype == 0:  # Young healthy
            age = int(rng.integers(20, 36))
            sbp = float(rng.integers(105, 122))
            dbp = float(rng.integers(68, 80))
            bmi_target = float(rng.uniform(19.0, 22.8))
        elif archetype == 1:  # CKD edge case
            age = int(rng.integers(52, 78))
            sbp = float(rng.integers(135, 165))
            dbp = float(rng.integers(82, 98))
            bmi_target = float(rng.uniform(22.0, 29.0))
        elif archetype == 2:  # Uncontrolled diabetes
            age = int(rng.integers(40, 70))
            sbp = float(rng.integers(126, 152))
            dbp = float(rng.integers(78, 94))
            bmi_target = float(rng.uniform(24.0, 32.0))
        elif archetype == 3:  # Hypertension Stage 2 / Crisis
            age = int(rng.integers(45, 75))
            sbp = float(rng.integers(145, 185))
            dbp = float(rng.integers(92, 112))
            bmi_target = float(rng.uniform(23.5, 31.0))
        elif archetype == 4:  # Elderly >75
            age = int(rng.integers(75, 88))
            sbp = float(rng.integers(125, 158))
            dbp = float(rng.integers(74, 92))
            bmi_target = float(rng.uniform(20.0, 28.0))
        else:
            age = int(rng.integers(24, 74))
            sbp = float(np.clip(rng.normal(128, 16), 95, 185))
            dbp = float(np.clip(rng.normal(82, 10), 60, 115))
            bmi_target = float(np.clip(rng.normal(25.2, 3.8), 17.5, 36.0))

        sex = "male" if rng.random() < 0.52 else "female"
        height_cm = float(np.clip(rng.normal(169 if sex == "male" else 157, 6.5), 145, 192))
        weight_kg = round(bmi_target * ((height_cm / 100.0) ** 2), 1)
        waist_cm = float(np.clip(bmi_target * 3.55 + rng.normal(0, 4.5), 62, 130))
        activity = str(rng.choice(ACTIVITIES, p=[0.15, 0.35, 0.30, 0.20]))
        fam_diab = str(rng.choice(FAM_DIAB, p=[0.55, 0.30, 0.15]))
        smoker = bool(rng.random() < (0.22 if sex == "male" else 0.04))
        alcohol = float(rng.choice([0.0, 2.0, 5.0, 10.0], p=[0.65, 0.20, 0.10, 0.05]))
        city = str(rng.choice(CITIES))

        # ~40% of profiles have missing lab panels
        has_labs = rng.random() >= 0.40 or archetype in (1, 2)
        fpg = hba1c = total_chol = ldl = hdl = tg = creat = acr = None
        if has_labs:
            if archetype == 2:
                fpg = float(rng.integers(145, 290))
                hba1c = round(float(rng.uniform(7.2, 10.5)), 1)
            else:
                fpg = float(np.clip(rng.normal(104, 24), 70, 260))
                hba1c = round(float(np.clip(rng.normal(5.8, 0.9), 4.5, 10.5)), 1)
            total_chol = float(np.clip(rng.normal(198, 36), 120, 320))
            ldl = float(np.clip(total_chol * 0.62 + rng.normal(0, 10), 60, 220))
            hdl = float(np.clip(rng.normal(42 if sex == "male" else 48, 8), 24, 80))
            tg = float(np.clip(rng.normal(158, 52), 60, 420))
            if archetype == 1:
                creat = round(float(rng.uniform(1.6, 3.8)), 2)
                acr = float(rng.integers(45, 420))
            else:
                creat = round(float(np.clip(rng.normal(0.92, 0.22), 0.5, 2.4)), 2)
                acr = float(np.clip(rng.exponential(20.0), 2.0, 350.0))

        profile = {
            "patient_id": i,
            "age": age,
            "sex": sex,
            "height_cm": round(height_cm, 1),
            "weight_kg": weight_kg,
            "waist_cm": round(waist_cm, 1),
            "systolic_bp": round(sbp, 0),
            "diastolic_bp": round(dbp, 0),
            "smoker": smoker,
            "alcohol_drinks_per_week": alcohol,
            "physical_activity": activity,
            "family_diabetes": fam_diab,
            "city": city,
            "fpg": fpg,
            "hba1c": hba1c,
            "total_cholesterol": total_chol,
            "ldl": ldl,
            "hdl": hdl,
            "triglycerides": tg,
            "serum_creatinine": creat,
            "urine_acr": acr,
        }
        profiles.append(compute_profile_tiers(profile))

    return profiles


def sample_training_pairs(
    profiles: List[Dict[str, Any]],
    candidates: List[Dict[str, Any]],
    pairs_per_profile: int = 12,
    seed: int = SYNTH_SEED,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], np.ndarray, np.ndarray]:
    """Sample balanced (patient, item) pairs across all 5 categories with 0-3 relevance grades."""
    rng = np.random.default_rng(seed)
    by_cat: Dict[str, List[Dict[str, Any]]] = {}
    for c in candidates:
        by_cat.setdefault(c["category"], []).append(c)

    cat_quotas = {"foods": 4, "exercises": 3, "hospitals": 2, "specialties": 2, "care": 1}
    p_rows: List[Dict[str, Any]] = []
    i_rows: List[Dict[str, Any]] = []
    labels: List[float] = []
    groups: List[int] = []

    for prof in profiles:
        pid = prof["patient_id"]
        for cat, quota in cat_quotas.items():
            pool = by_cat.get(cat, [])
            if not pool:
                continue
            idxs = rng.choice(len(pool), size=min(quota, len(pool)), replace=False)
            for idx in idxs:
                item = pool[int(idx)]
                raw_score, _ = score_pair_by_rules(prof, item)
                p_rows.append(prof)
                i_rows.append(item)
                labels.append(float(int(round(raw_score))))
                groups.append(pid)

    return p_rows, i_rows, np.array(labels, dtype=float), np.array(groups, dtype=int)

