"""Kidney function calculator: CKD-EPI 2021 (race-free) eGFR + ACR staging."""

from typing import Any, Dict, List, Optional


def calculate_kidney_egfr(
    age: int,
    sex: str,
    serum_creatinine_mg_dl: Optional[float] = None,
    urine_acr_mg_g: Optional[float] = None,
) -> Dict[str, Any]:
    """Compute CKD-EPI 2021 race-free eGFR (mL/min/1.73m²) and optional ACR stage."""
    if serum_creatinine_mg_dl is None or serum_creatinine_mg_dl <= 0:
        return {
            "module": "kidney_ckd_epi",
            "status": "skipped",
            "skip_reason": "needs serum creatinine",
            "score": None,
            "unit": "mL/min/1.73m2",
            "category": None,
            "method": "CKD-EPI 2021",
            "factors": [],
            "kind": "rule",
        }

    is_female = sex.strip().lower() in ("female", "f", "0")
    kappa = 0.7 if is_female else 0.9
    alpha = -0.241 if is_female else -0.302
    sex_factor = 1.012 if is_female else 1.0

    scr_k = serum_creatinine_mg_dl / kappa
    egfr = 142.0 * (min(scr_k, 1.0) ** alpha) * (max(scr_k, 1.0) ** -1.200) * (0.9938 ** age) * sex_factor
    egfr = round(egfr, 1)

    factors: List[str] = [f"eGFR (CKD-EPI 2021): {egfr} mL/min/1.73m²"]
    if egfr >= 90:
        g_stage = "G1"
    elif egfr >= 60:
        g_stage = "G2"
    elif egfr >= 45:
        g_stage = "G3a"
    elif egfr >= 30:
        g_stage = "G3b"
    elif egfr >= 15:
        g_stage = "G4"
    else:
        g_stage = "G5"
    factors.append(f"GFR Stage: {g_stage}")

    a_stage = None
    if urine_acr_mg_g is not None:
        if urine_acr_mg_g < 30:
            a_stage = "A1 (<30 mg/g)"
        elif urine_acr_mg_g <= 300:
            a_stage = "A2 (30–300 mg/g)"
        else:
            a_stage = "A3 (>300 mg/g)"
        factors.append(f"Albuminuria: {a_stage}")

    if egfr < 45 or (urine_acr_mg_g is not None and urine_acr_mg_g > 300):
        tier = "high"
    elif egfr < 60 or (urine_acr_mg_g is not None and urine_acr_mg_g >= 30):
        tier = "moderate"
    else:
        tier = "low"

    return {
        "module": "kidney_ckd_epi",
        "status": "computed",
        "skip_reason": None,
        "score": egfr,
        "unit": "mL/min/1.73m2",
        "category": tier,
        "g_stage": g_stage,
        "a_stage": a_stage,
        "method": "CKD-EPI 2021 (Race-Free)",
        "factors": factors,
        "kind": "rule",
    }

