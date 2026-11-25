"""Anthropometry calculator using Indian / South Asian BMI and waist cutoffs."""

from typing import Any, Dict, List


def calculate_anthropometry(height_cm: float, weight_kg: float, waist_cm: float, sex: str) -> Dict[str, Any]:
    """Compute BMI with Indian cutoffs (<18.5, 18.5-22.9, 23.0-24.9, >=25.0) and waist category."""
    if height_cm <= 0 or weight_kg <= 0:
        return {
            "module": "obesity_anthropometry",
            "status": "skipped",
            "skip_reason": "requires positive height and weight",
            "score": None,
            "unit": "kg/m2",
            "category": None,
            "method": "Indian Consensus BMI & Waist Cutoffs",
            "factors": [],
            "kind": "rule",
        }

    height_m = height_cm / 100.0
    bmi = round(weight_kg / (height_m ** 2), 2)

    if bmi < 18.5:
        bmi_cat = "underweight"
    elif bmi < 23.0:
        bmi_cat = "normal"
    elif bmi < 25.0:
        bmi_cat = "overweight"
    else:
        bmi_cat = "obese"

    is_male = sex.strip().lower() in ("male", "m", "1")
    waist_cutoff = 90.0 if is_male else 80.0
    central_obesity = waist_cm >= waist_cutoff

    factors: List[str] = [f"BMI: {bmi} kg/m² ({bmi_cat} by Indian cutoffs)"]
    if central_obesity:
        factors.append(f"Waist circumference {waist_cm} cm >= {waist_cutoff} cm (central obesity)")
    else:
        factors.append(f"Waist circumference {waist_cm} cm < {waist_cutoff} cm")

    overall_cat = "high" if (bmi_cat == "obese" or central_obesity) else ("moderate" if bmi_cat == "overweight" else "low")
    return {
        "module": "obesity_anthropometry",
        "status": "computed",
        "skip_reason": None,
        "score": bmi,
        "unit": "kg/m2",
        "category": overall_cat,
        "bmi_category": bmi_cat,
        "central_obesity": central_obesity,
        "method": "Indian Consensus BMI (>=23 overweight, >=25 obese) & Waist",
        "factors": factors,
        "kind": "rule",
    }

