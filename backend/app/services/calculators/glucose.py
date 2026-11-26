"""Glucose classification calculator (HbA1c, FPG, OGTT) folding prediabetes into one card."""

from typing import Any, Dict, List, Optional


def classify_glucose(
    hba1c: Optional[float] = None,
    fpg: Optional[float] = None,
    ogtt_2h: Optional[float] = None,
) -> Dict[str, Any]:
    """Classify glycemic status (normal, prediabetes, diabetes) using ADA/ICMR thresholds."""
    if hba1c is None and fpg is None and ogtt_2h is None:
        return {
            "module": "glucose_classification",
            "status": "skipped",
            "skip_reason": "needs HbA1c, fasting plasma glucose (FPG), or 2h OGTT",
            "score": None,
            "unit": "%",
            "category": None,
            "method": "ADA / ICMR Glycemic Thresholds",
            "factors": [],
            "kind": "rule",
        }

    factors: List[str] = []
    status_rank = 0  # 0=normal (low), 1=prediabetes (moderate), 2=diabetes (high)
    primary_score: Optional[float] = None

    if hba1c is not None:
        hba1c_pct = hba1c
        if hba1c > 20.0:
            # Auto-convert IFCC mmol/mol (e.g. 56 mmol/mol) to NGSP %
            hba1c_pct = round((0.09148 * hba1c) + 2.152, 2)
            factors.append(f"Converted HbA1c {hba1c} mmol/mol to {hba1c_pct}%")
        primary_score = round(hba1c_pct, 2)
        if hba1c_pct >= 6.5:
            status_rank = max(status_rank, 2)
            factors.append(f"HbA1c {hba1c_pct}% >= 6.5% (diabetes range)")
        elif hba1c_pct >= 5.7:
            status_rank = max(status_rank, 1)
            factors.append(f"HbA1c {hba1c_pct}% in 5.7–6.4% (prediabetes range)")
        else:
            factors.append(f"HbA1c {hba1c_pct}% < 5.7% (normal range)")

    if fpg is not None:
        if primary_score is None:
            primary_score = round(fpg, 1)
        if fpg >= 126:
            status_rank = max(status_rank, 2)
            factors.append(f"FPG {fpg} mg/dL >= 126 mg/dL (diabetes range)")
        elif fpg >= 100:
            status_rank = max(status_rank, 1)
            factors.append(f"FPG {fpg} mg/dL in 100–125 mg/dL (prediabetes / IFG range)")
        else:
            factors.append(f"FPG {fpg} mg/dL < 100 mg/dL (normal range)")

    if ogtt_2h is not None:
        if primary_score is None:
            primary_score = round(ogtt_2h, 1)
        if ogtt_2h >= 200:
            status_rank = max(status_rank, 2)
            factors.append(f"2h OGTT {ogtt_2h} mg/dL >= 200 mg/dL (diabetes range)")
        elif ogtt_2h >= 140:
            status_rank = max(status_rank, 1)
            factors.append(f"2h OGTT {ogtt_2h} mg/dL in 140–199 mg/dL (prediabetes / IGT range)")
        else:
            factors.append(f"2h OGTT {ogtt_2h} mg/dL < 140 mg/dL (normal range)")

    tier_map = {0: "low", 1: "moderate", 2: "high"}
    label_map = {0: "normal", 1: "prediabetes", 2: "diabetes"}

    return {
        "module": "glucose_classification",
        "status": "computed",
        "skip_reason": None,
        "score": primary_score,
        "unit": "%" if hba1c is not None else "mg/dL",
        "category": tier_map[status_rank],
        "glycemic_status": label_map[status_rank],
        "method": "ADA / ICMR Glycemic Classification (HbA1c / FPG / OGTT)",
        "factors": factors,
        "kind": "rule",
    }

