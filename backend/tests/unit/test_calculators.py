"""Unit tests for deterministic clinical calculators and exact boundary values."""

from app.services.calculators.anthropometry import calculate_anthropometry
from app.services.calculators.bp import calculate_bp
from app.services.calculators.glucose import classify_glucose
from app.services.calculators.idrs import calculate_idrs
from app.services.calculators.who_cvd import calculate_who_cvd
from app.services.calculators.kidney import calculate_kidney_egfr
from app.services.calculators.metabolic import calculate_metabolic_syndrome


def test_indian_bmi_exact_boundaries():
    # 22.9 (<23 -> normal), 23.0 (>=23 -> overweight), 24.9 (<25 -> overweight), 25.0 (>=25 -> obese)
    assert calculate_anthropometry(100, 22.9, 80, "male")["bmi_category"] == "normal"
    assert calculate_anthropometry(100, 23.0, 80, "male")["bmi_category"] == "overweight"
    assert calculate_anthropometry(100, 24.9, 80, "male")["bmi_category"] == "overweight"
    r25 = calculate_anthropometry(100, 25.0, 80, "male")
    assert r25["bmi_category"] == "obese"
    assert r25["unit"] == "kg/m2"
    assert r25["kind"] == "rule"


def test_idrs_boundaries_and_non_overlapping_bands():
    # <30 -> low (20)
    r20 = calculate_idrs(age=30, waist_cm=85, sex="male", physical_activity="moderate", family_diabetes="one_parent")
    assert r20["score"] == 20
    assert r20["category"] == "low"
    assert r20["unit"] == "/100"
    assert r20["kind"] == "rule"

    # 30-59 -> moderate (30 and 50)
    r30 = calculate_idrs(age=40, waist_cm=85, sex="male", physical_activity="moderate", family_diabetes="none")
    assert r30["score"] == 30
    assert r30["category"] == "moderate"

    r50 = calculate_idrs(age=50, waist_cm=95, sex="male", physical_activity="moderate", family_diabetes="none")
    assert r50["score"] == 50
    assert r50["category"] == "moderate"

    # >=60 -> high (60)
    r60 = calculate_idrs(age=55, waist_cm=92, sex="male", physical_activity="mild", family_diabetes="none")
    assert r60["score"] == 60
    assert r60["category"] == "high"


def test_glucose_hba1c_exact_boundaries():
    assert classify_glucose(hba1c=5.6)["glycemic_status"] == "normal"
    assert classify_glucose(hba1c=5.7)["glycemic_status"] == "prediabetes"
    assert classify_glucose(hba1c=6.4)["glycemic_status"] == "prediabetes"
    r65 = classify_glucose(hba1c=6.5)
    assert r65["glycemic_status"] == "diabetes"
    assert r65["unit"] == "%"
    assert r65["kind"] == "rule"
    assert classify_glucose()["status"] == "skipped"


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


def test_kidney_ckd_epi_2021_and_missing():
    r_skip = calculate_kidney_egfr(age=45, sex="male")
    assert r_skip["status"] == "skipped"
    assert r_skip["kind"] == "rule"

    r = calculate_kidney_egfr(age=50, sex="female", serum_creatinine_mg_dl=0.9, urine_acr_mg_g=15)
    assert r["status"] == "computed"
    assert r["score"] > 60
    assert r["unit"] == "mL/min/1.73m2"
    assert r["category"] == "low"


def test_bp_and_metabolic():
    r_bp = calculate_bp(118, 76)
    assert r_bp["category"] == "low"
    assert r_bp["unit"] == "mmHg"
    assert r_bp["kind"] == "rule"
    assert calculate_bp(145, 92)["category"] == "high"

    assert calculate_metabolic_syndrome(95, "male", 135, 85)["status"] == "skipped"
    m = calculate_metabolic_syndrome(95, "male", 135, 88, fpg=110, triglycerides_mg_dl=180, hdl_mg_dl=35)
    assert m["status"] == "computed"
    assert m["score"] == 5
    assert m["unit"] == "/5"
    assert m["category"] == "high"
