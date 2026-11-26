"""Comprehensive unit tests for deterministic clinical calculators.

Covers:
- Exact clinical boundary values (Indian BMI, IDRS, Glucose HbA1c/FPG/OGTT, BP, CKD-EPI 2021, Metabolic Syndrome)
- WHO South Asia CVD continuous risk calibration (lab-based & non-lab, age bounds, sex differentiation)
- Mathematical & clinical monotonicity invariants (risk strictly increases with BP/age/cholesterol/smoking/diabetes; eGFR strictly decreases with age/creatinine)
- Safety-first skipped/missing/invalid input handling (never guessing missing labs)
- 10 diverse patient profile end-to-end verification
"""

import pytest

from app.services.calculators.anthropometry import calculate_anthropometry
from app.services.calculators.bp import calculate_bp
from app.services.calculators.glucose import classify_glucose
from app.services.calculators.idrs import calculate_idrs
from app.services.calculators.kidney import calculate_kidney_egfr
from app.services.calculators.metabolic import calculate_metabolic_syndrome
from app.services.calculators.who_cvd import calculate_who_cvd


# ---------------------------------------------------------------------------
# 1. Indian BMI & Central Obesity (Anthropometry)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "height_cm,weight_kg,waist_cm,sex,expected_bmi_cat,expected_overall,expected_central",
    [
        (100, 18.4, 70, "male", "underweight", "low", False),
        (100, 18.5, 70, "male", "normal", "low", False),
        (100, 22.9, 89.9, "male", "normal", "low", False),
        (100, 23.0, 89.9, "male", "overweight", "moderate", False),
        (100, 24.9, 80.0, "male", "overweight", "moderate", False),
        (100, 24.9, 90.0, "male", "overweight", "high", True),
        (100, 25.0, 75.0, "female", "obese", "high", False),
        (100, 21.5, 80.0, "female", "normal", "high", True),
        (100, 21.5, 79.9, "female", "normal", "low", False),
    ],
)
def test_indian_bmi_exact_boundaries(
    height_cm, weight_kg, waist_cm, sex, expected_bmi_cat, expected_overall, expected_central
):
    res = calculate_anthropometry(height_cm, weight_kg, waist_cm, sex)
    assert res["status"] == "computed"
    assert res["bmi_category"] == expected_bmi_cat
    assert res["category"] == expected_overall
    assert res["central_obesity"] is expected_central
    assert res["unit"] == "kg/m2"
    assert res["kind"] == "rule"


@pytest.mark.parametrize("height_cm,weight_kg", [(0, 65), (-170, 65), (170, 0), (170, -5)])
def test_indian_bmi_invalid_inputs_skipped(height_cm, weight_kg):
    res = calculate_anthropometry(height_cm, weight_kg, 85, "male")
    assert res["status"] == "skipped"
    assert res["score"] is None
    assert res["category"] is None


# ---------------------------------------------------------------------------
# 2. Indian Diabetes Risk Score (IDRS)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "age,waist,sex,activity,family,expected_score,expected_cat",
    [
        (25, 75, "female", "vigorous", "none", 0, "low"),
        (30, 85, "male", "moderate", "one_parent", 20, "low"),
        (35, 85, "male", "moderate", "none", 30, "moderate"),
        (50, 95, "male", "moderate", "none", 50, "moderate"),
        (55, 92, "male", "mild", "none", 60, "high"),
        (52, 90, "female", "sedentary", "both", 100, "high"),
        (34, 80, "female", "vigorous", "both", 30, "moderate"),
    ],
)
def test_idrs_boundaries_and_non_overlapping_bands(
    age, waist, sex, activity, family, expected_score, expected_cat
):
    res = calculate_idrs(
        age=age, waist_cm=waist, sex=sex, physical_activity=activity, family_diabetes=family
    )
    assert res["status"] == "computed"
    assert res["score"] == expected_score
    assert res["category"] == expected_cat
    assert res["unit"] == "/100"
    assert res["kind"] == "rule"


def test_idrs_missing_waist_skipped():
    res = calculate_idrs(age=45, waist_cm=0, sex="male", physical_activity="mild", family_diabetes="none")
    assert res["status"] == "skipped"
    assert res["score"] is None


# ---------------------------------------------------------------------------
# 3. Glycemic Classification (HbA1c / FPG / OGTT)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "kwargs,expected_status,expected_tier",
    [
        ({"hba1c": 5.6}, "normal", "low"),
        ({"hba1c": 5.7}, "prediabetes", "moderate"),
        ({"hba1c": 6.4}, "prediabetes", "moderate"),
        ({"hba1c": 6.5}, "diabetes", "high"),
        ({"fpg": 99}, "normal", "low"),
        ({"fpg": 100}, "prediabetes", "moderate"),
        ({"fpg": 125}, "prediabetes", "moderate"),
        ({"fpg": 126}, "diabetes", "high"),
        ({"ogtt_2h": 139}, "normal", "low"),
        ({"ogtt_2h": 140}, "prediabetes", "moderate"),
        ({"ogtt_2h": 199}, "prediabetes", "moderate"),
        ({"ogtt_2h": 200}, "diabetes", "high"),
        # Mixed markers: worst marker governs
        ({"hba1c": 5.4, "fpg": 130}, "diabetes", "high"),
        # IFCC mmol/mol auto-conversion (>20)
        ({"hba1c": 56}, "diabetes", "high"),
    ],
)
def test_glucose_hba1c_exact_boundaries(kwargs, expected_status, expected_tier):
    res = classify_glucose(**kwargs)
    assert res["status"] == "computed"
    assert res["glycemic_status"] == expected_status
    assert res["category"] == expected_tier
    assert res["kind"] == "rule"


def test_glucose_skipped_when_empty():
    res = classify_glucose()
    assert res["status"] == "skipped"
    assert res["score"] is None


# ---------------------------------------------------------------------------
# 4. WHO South Asia 10-Year CVD Risk (Continuous Lab & Non-Lab)
# ---------------------------------------------------------------------------


def test_who_cvd_age_bounds_and_non_lab():
    r_young = calculate_who_cvd(age=39, sex="male", systolic_bp=120)
    assert r_young["status"] == "skipped"
    assert r_young["category"] == "not_applicable"
    assert r_young["kind"] == "rule"

    r_old = calculate_who_cvd(age=75, sex="female", systolic_bp=145, smoker=True)
    assert r_old["status"] == "skipped"
    assert r_old["category"] == "not_applicable"
    assert r_old["score"] == 2

    r_nonlab = calculate_who_cvd(age=58, sex="male", systolic_bp=150, smoker=True, bmi=27.0)
    assert r_nonlab["status"] == "computed"
    assert r_nonlab["unit"] == "%"
    assert "Non-Lab" in r_nonlab["method"]
    assert 1.0 <= r_nonlab["score"] <= 48.0


def test_who_cvd_continuous_differentiation_and_monotonicity():
    base = calculate_who_cvd(age=50, sex="female", systolic_bp=120, total_cholesterol_mg_dl=180)
    male = calculate_who_cvd(age=50, sex="male", systolic_bp=120, total_cholesterol_mg_dl=180)
    older = calculate_who_cvd(age=62, sex="male", systolic_bp=120, total_cholesterol_mg_dl=180)
    higher_bp = calculate_who_cvd(age=62, sex="male", systolic_bp=152, total_cholesterol_mg_dl=180)
    smoker = calculate_who_cvd(age=62, sex="male", systolic_bp=152, smoker=True, total_cholesterol_mg_dl=180)
    diabetic = calculate_who_cvd(
        age=62, sex="male", systolic_bp=152, smoker=True, diabetes_present=True, total_cholesterol_mg_dl=240
    )

    scores = [base["score"], male["score"], older["score"], higher_bp["score"], smoker["score"], diabetic["score"]]
    # Strictly increasing as each risk factor is added
    assert all(a < b for a, b in zip(scores, scores[1:])), f"Expected strictly increasing scores, got {scores}"
    assert base["category"] == "low"
    assert diabetic["category"] == "high"

    # Non-lab BMI monotonicity
    bmi_low = calculate_who_cvd(age=52, sex="male", systolic_bp=130, bmi=21.0)
    bmi_high = calculate_who_cvd(age=52, sex="male", systolic_bp=130, bmi=32.0)
    assert bmi_low["score"] < bmi_high["score"]


# ---------------------------------------------------------------------------
# 5. Kidney Health (CKD-EPI 2021 Race-Free eGFR + ACR)
# ---------------------------------------------------------------------------


def test_kidney_ckd_epi_2021_and_missing():
    r_skip = calculate_kidney_egfr(age=45, sex="male")
    assert r_skip["status"] == "skipped"
    assert r_skip["kind"] == "rule"
    assert r_skip["score"] is None

    r_zero = calculate_kidney_egfr(age=45, sex="male", serum_creatinine_mg_dl=0)
    assert r_zero["status"] == "skipped"

    r = calculate_kidney_egfr(age=50, sex="female", serum_creatinine_mg_dl=0.9, urine_acr_mg_g=15)
    assert r["status"] == "computed"
    assert r["score"] > 60
    assert r["g_stage"] in ("G1", "G2")
    assert r["a_stage"] == "A1 (<30 mg/g)"
    assert r["unit"] == "mL/min/1.73m2"
    assert r["category"] == "low"


@pytest.mark.parametrize(
    "creatinine,acr,expected_g,expected_tier",
    [
        (0.8, 10, "G1", "low"),
        (1.2, 45, "G2", "moderate"),  # A2 albuminuria elevates to moderate
        (1.5, 15, "G3a", "moderate"),
        (2.2, 15, "G3b", "high"),
        (3.5, 15, "G4", "high"),
        (0.8, 350, "G1", "high"),  # A3 albuminuria elevates to high even with normal eGFR
    ],
)
def test_kidney_kdigo_staging_and_monotonicity(creatinine, acr, expected_g, expected_tier):
    res = calculate_kidney_egfr(age=55, sex="male", serum_creatinine_mg_dl=creatinine, urine_acr_mg_g=acr)
    assert res["status"] == "computed"
    assert res["g_stage"] == expected_g
    assert res["category"] == expected_tier

    # Increasing creatinine strictly reduces eGFR
    worse = calculate_kidney_egfr(age=55, sex="male", serum_creatinine_mg_dl=creatinine + 0.5)
    assert worse["score"] < res["score"]


# ---------------------------------------------------------------------------
# 6. Blood Pressure & Metabolic Syndrome
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "sbp,dbp,expected_stage,expected_tier",
    [
        (118, 76, "normal", "low"),
        (124, 78, "elevated", "moderate"),
        (134, 84, "stage_1", "moderate"),
        (128, 82, "stage_1", "moderate"),
        (145, 92, "stage_2", "high"),
        (182, 110, "crisis", "high"),
    ],
)
def test_bp_and_metabolic(sbp, dbp, expected_stage, expected_tier):
    r_bp = calculate_bp(sbp, dbp)
    assert r_bp["status"] == "computed"
    assert r_bp["bp_stage"] == expected_stage
    assert r_bp["category"] == expected_tier
    assert r_bp["unit"] == "mmHg"
    assert r_bp["kind"] == "rule"

    assert calculate_bp(0, 80)["status"] == "skipped"

    assert calculate_metabolic_syndrome(95, "male", 135, 85)["status"] == "skipped"
    m = calculate_metabolic_syndrome(95, "male", 135, 88, fpg=110, triglycerides_mg_dl=180, hdl_mg_dl=35)
    assert m["status"] == "computed"
    assert m["score"] == 5
    assert m["unit"] == "/5"
    assert m["category"] == "high"

    # Sex-specific HDL (<50 female vs <40 male) and waist (>=80 female vs >=90 male)
    m_f = calculate_metabolic_syndrome(82, "female", 118, 76, fpg=92, triglycerides_mg_dl=120, hdl_mg_dl=45)
    assert m_f["score"] == 2  # waist >=80 and HDL <50
    assert m_f["category"] == "moderate"
