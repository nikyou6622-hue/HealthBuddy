"""Indian Diabetes Risk Score (IDRS) calculator (Mohan et al., MDRF)."""

from typing import Any, Dict, List


def calculate_idrs(
    age: int,
    waist_cm: float,
    sex: str,
    physical_activity: str,
    family_diabetes: str,
) -> Dict[str, Any]:
    """Compute IDRS (0-100) with non-overlapping bands: <30 low, 30-59 moderate, >=60 high."""
    if waist_cm <= 0:
        return {
            "module": "diabetes_idrs",
            "status": "skipped",
            "skip_reason": "needs waist",
            "score": None,
            "unit": "/100",
            "category": None,
            "method": "Screening score (IDRS)",
            "factors": [],
            "kind": "rule",
        }

    score = 0
    factors: List[str] = []

    # 1. Age
    if age >= 50:
        score += 30
        factors.append("Age >= 50 years (+30)")
    elif age >= 35:
        score += 20
        factors.append("Age 35–49 years (+20)")
    else:
        factors.append("Age < 35 years (+0)")

    # 2. Abdominal obesity (waist)
    is_male = sex.strip().lower() in ("male", "m", "1")
    if is_male:
        if waist_cm >= 100:
            score += 20
            factors.append("Waist >= 100 cm in men (+20)")
        elif waist_cm >= 90:
            score += 10
            factors.append("Waist 90–99 cm in men (+10)")
        else:
            factors.append("Waist < 90 cm in men (+0)")
    else:
        if waist_cm >= 90:
            score += 20
            factors.append("Waist >= 90 cm in women (+20)")
        elif waist_cm >= 80:
            score += 10
            factors.append("Waist 80–89 cm in women (+10)")
        else:
            factors.append("Waist < 80 cm in women (+0)")

    # 3. Physical activity
    act = physical_activity.strip().lower()
    if act == "vigorous":
        factors.append("Vigorous regular exercise (+0)")
    elif act == "moderate":
        score += 10
        factors.append("Moderate physical activity (+10)")
    elif act == "mild":
        score += 20
        factors.append("Mild physical activity (+20)")
    else:
        score += 30
        factors.append("Sedentary lifestyle (+30)")

    # 4. Family history of diabetes
    fam = family_diabetes.strip().lower()
    if fam == "both":
        score += 20
        factors.append("Both parents have diabetes (+20)")
    elif fam == "one_parent":
        score += 10
        factors.append("One parent has diabetes (+10)")
    else:
        factors.append("No parental diabetes history (+0)")

    # Non-overlapping bands: <30, 30-59, >=60
    if score < 30:
        cat = "low"
    elif score < 60:
        cat = "moderate"
    else:
        cat = "high"

    return {
        "module": "diabetes_idrs",
        "status": "computed",
        "skip_reason": None,
        "score": score,
        "unit": "/100",
        "category": cat,
        "method": "Screening score (IDRS)",
        "factors": factors,
        "kind": "rule",
    }

