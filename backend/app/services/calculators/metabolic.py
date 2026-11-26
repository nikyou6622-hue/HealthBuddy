"""Metabolic syndrome calculator (Harmonized South Asian criteria)."""

from typing import Any, Dict, List, Optional


def calculate_metabolic_syndrome(
    waist_cm: float,
    sex: str,
    systolic_bp: float,
    diastolic_bp: float,
    fpg: Optional[float] = None,
    triglycerides_mg_dl: Optional[float] = None,
    hdl_mg_dl: Optional[float] = None,
) -> Dict[str, Any]:
    """Evaluate metabolic syndrome (>=3 of 5 criteria). Skips if all lab markers are missing."""
    if fpg is None and triglycerides_mg_dl is None and hdl_mg_dl is None:
        return {
            "module": "metabolic_syndrome",
            "status": "skipped",
            "skip_reason": "needs fasting glucose, triglycerides, or HDL",
            "score": None,
            "unit": "/5",
            "category": None,
            "method": "IDF / Harmonized South Asian Criteria",
            "factors": [],
            "kind": "rule",
        }

    is_male = sex.strip().lower() in ("male", "m", "1")
    criteria_met = 0
    factors: List[str] = []

    waist_cut = 90.0 if is_male else 80.0
    if waist_cm >= waist_cut:
        criteria_met += 1
        factors.append(f"Elevated waist ({waist_cm} >= {waist_cut} cm)")

    if systolic_bp >= 130 or diastolic_bp >= 85:
        criteria_met += 1
        factors.append(f"Elevated BP ({int(systolic_bp)}/{int(diastolic_bp)} >= 130/85)")

    if fpg is not None and fpg >= 100:
        criteria_met += 1
        factors.append(f"Elevated fasting glucose ({fpg} >= 100 mg/dL)")

    if triglycerides_mg_dl is not None and triglycerides_mg_dl >= 150:
        criteria_met += 1
        factors.append(f"Elevated triglycerides ({triglycerides_mg_dl} >= 150 mg/dL)")

    hdl_cut = 40.0 if is_male else 50.0
    if hdl_mg_dl is not None and hdl_mg_dl < hdl_cut:
        criteria_met += 1
        factors.append(f"Low HDL ({hdl_mg_dl} < {hdl_cut} mg/dL)")

    if criteria_met >= 3:
        tier = "high"
    elif criteria_met == 2:
        tier = "moderate"
    else:
        tier = "low"

    return {
        "module": "metabolic_syndrome",
        "status": "computed",
        "skip_reason": None,
        "score": criteria_met,
        "unit": "/5",
        "category": tier,
        "method": "Harmonized South Asian Metabolic Syndrome (>=3/5 criteria)",
        "factors": factors or ["0 of 5 metabolic syndrome criteria met"],
        "kind": "rule",
    }

