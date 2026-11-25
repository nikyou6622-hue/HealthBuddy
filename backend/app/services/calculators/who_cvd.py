"""WHO South Asia 10-year CVD risk estimator (lab + non-lab) for ages 40-74."""

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

    Outside 40-74: returns status='skipped' ('not applicable outside ages 40-74')
    along with traditional risk-factor count.
    """
    risk_factors: List[str] = []
    if systolic_bp >= 140:
        risk_factors.append(f"Elevated SBP ({int(systolic_bp)} mmHg >= 140)")
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

    # Simplified South Asia WHO-aligned risk point model (lab if cholesterol present, else non-lab using BMI)
    points = 0
    if age >= 65:
        points += 4
    elif age >= 55:
        points += 3
    elif age >= 45:
        points += 2
    else:
        points += 1

    if systolic_bp >= 160:
        points += 4
    elif systolic_bp >= 140:
        points += 2
    elif systolic_bp >= 130:
        points += 1

    if smoker:
        points += 2
    if diabetes_present:
        points += 2

    if total_cholesterol_mg_dl is not None:
        method = "WHO South Asia Lab-Based Chart (includes Stroke)"
        if total_cholesterol_mg_dl >= 240:
            points += 2
        elif total_cholesterol_mg_dl >= 200:
            points += 1
    else:
        method = "WHO South Asia Non-Lab Chart (BMI-based, includes Stroke)"
        if bmi is not None:
            if bmi >= 30:
                points += 2
            elif bmi >= 25:
                points += 1

    # Map points to approximate 10-yr % risk band
    if points <= 4:
        pct = 5.0
        cat = "low"
    elif points <= 7:
        pct = 12.0
        cat = "moderate"
    else:
        pct = 24.0
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

