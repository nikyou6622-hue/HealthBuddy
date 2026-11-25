"""Blood pressure classification calculator."""

from typing import Any, Dict, List


def calculate_bp(systolic_bp: float, diastolic_bp: float) -> Dict[str, Any]:
    """Classify blood pressure into normal, elevated, stage_1, stage_2, or crisis."""
    if systolic_bp <= 0 or diastolic_bp <= 0:
        return {
            "module": "hypertension_bp",
            "status": "skipped",
            "skip_reason": "requires positive systolic and diastolic BP",
            "score": None,
            "unit": "mmHg",
            "category": None,
            "method": "ACC/AHA & Indian Hypertension Guidelines",
            "factors": [],
            "kind": "rule",
        }

    factors: List[str] = [f"BP: {int(systolic_bp)}/{int(diastolic_bp)} mmHg"]
    if systolic_bp >= 180 or diastolic_bp >= 120:
        cat = "crisis"
        tier = "high"
        factors.append("Hypertensive crisis range (>=180 or >=120 mmHg)")
    elif systolic_bp >= 140 or diastolic_bp >= 90:
        cat = "stage_2"
        tier = "high"
        factors.append("Stage 2 hypertension range (>=140 or >=90 mmHg)")
    elif systolic_bp >= 130 or diastolic_bp >= 80:
        cat = "stage_1"
        tier = "moderate"
        factors.append("Stage 1 hypertension range (130-139 or 80-89 mmHg)")
    elif systolic_bp >= 120 and diastolic_bp < 80:
        cat = "elevated"
        tier = "moderate"
        factors.append("Elevated blood pressure (120-129 / <80 mmHg)")
    else:
        cat = "normal"
        tier = "low"
        factors.append("Normal blood pressure (<120 / <80 mmHg)")

    return {
        "module": "hypertension_bp",
        "status": "computed",
        "skip_reason": None,
        "score": round(systolic_bp, 1),
        "unit": "mmHg",
        "bp_display": f"{int(systolic_bp)}/{int(diastolic_bp)} mmHg",
        "category": tier,
        "bp_stage": cat,
        "method": "BP Staging (SBP/DBP)",
        "factors": factors,
        "kind": "rule",
    }

