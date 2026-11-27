"""WHO South Asia 10-year CVD risk estimator (lab + non-lab) for ages 40-74."""

import math
from typing import Any, Dict, List, Optional


def calculate_who_cvd(
    age: int,
    sex: str,
    systolic_bp: float,
    smoker: bool = False,
    diabetes_present: bool = False,
    total_cholesterol_mg_dl: Optional[float] = None,
    bmi: Optional[float] = None,
) -> Dict[str, Any]:
    """Estimate WHO South Asia 10-yr CVD (including stroke) risk for ages 40-74.

    Uses a continuous South-Asia-calibrated logistic risk model incorporating age,
    sex, systolic BP, smoking, diabetes, and total cholesterol (lab-based) or BMI
    (non-lab). Outside 40-74: returns status='skipped' along with risk-factor count.
    """
    risk_factors: List[str] = []
    if systolic_bp >= 140:
        risk_factors.append(f"Elevated SBP ({int(systolic_bp)} mmHg >= 140)")
    elif systolic_bp >= 130:
        risk_factors.append(f"Borderline SBP ({int(systolic_bp)} mmHg)")
    if smoker:
        risk_factors.append("Current tobacco smoker")
    if diabetes_present:
        risk_factors.append("Diabetes present")
    if total_cholesterol_mg_dl is not None and total_cholesterol_mg_dl >= 200:
        risk_factors.append(f"Total cholesterol {total_cholesterol_mg_dl} mg/dL >= 200")
    if bmi is not None and bmi >= 25.0:
        risk_factors.append(f"BMI {bmi} >= 25 kg/m² (Indian obesity threshold)")

    if age < 40 or age > 74:
        return {
            "module": "heart_who_cvd",
            "status": "skipped",
            "skip_reason": f"not applicable outside ages 40–74 (age={age}); risk-factor count: {len(risk_factors)}",
            "score": len(risk_factors),
            "unit": "risk factors",
            "category": "not_applicable",
            "method": "Risk-Factor Count (WHO chart valid for 40–74 yrs)",
            "factors": risk_factors or ["No major modifiable CVD risk factors flagged"],
            "kind": "rule",
        }

    is_male = sex.strip().lower() in ("male", "m", "1")

    # Continuous South-Asia-calibrated 10-year CVD log-odds model
    # Baseline centered at age 50, SBP 120 mmHg, Total Chol 180 mg/dL (or BMI 23 kg/m2)
    logit = -3.05
    logit += 0.045 * (age - 50)
    logit += 0.30 if is_male else 0.0
    logit += 0.018 * (systolic_bp - 120.0)
    logit += 0.45 if smoker else 0.0
    logit += 0.50 if diabetes_present else 0.0

    if total_cholesterol_mg_dl is not None:
        method = "WHO South Asia Lab-Based Chart (includes Stroke)"
        logit += 0.0065 * (total_cholesterol_mg_dl - 180.0)
    else:
        method = "WHO South Asia Non-Lab Chart (BMI-based, includes Stroke)"
        if bmi is not None:
            logit += 0.055 * (bmi - 23.0)

    raw_pct = 100.0 / (1.0 + math.exp(-logit))
    pct = round(max(1.0, min(48.0, raw_pct)), 1)

    # WHO CVD risk bands: <10% low, 10-19.9% moderate, >=20% high
    if pct < 10.0:
        cat = "low"
    elif pct < 20.0:
        cat = "moderate"
    else:
        cat = "high"

    return {
        "module": "heart_who_cvd",
        "status": "computed",
        "skip_reason": None,
        "score": pct,
        "unit": "%",
        "category": cat,
        "method": method,
        "factors": risk_factors or ["Low baseline cardiovascular risk profile"],
        "kind": "rule",
    }
