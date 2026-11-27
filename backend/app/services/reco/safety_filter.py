"""Non-negotiable post-model clinical safety filter for ML #3 Personalized Recommender."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from app.services.safety.disclaimers import CARE_MATCHING_DISCLAIMER
from app.services.safety.red_flags import RedFlagInput, evaluate_red_flags

# Never output drug names or dosing instructions (allow educational terms like "insulin sensitivity/resistance")
BLOCKED_MED_PATTERNS = re.compile(
    r"\b(\d+\s*mg|\d+\s*mcg|\d+\s*iu|metformin|atorvastatin|amlodipine|lisinopril|insulin(?!\s+(?:sensitivity|resistance|level|levels|action|response|spike|index))|glimepiride|losartan|aspirin|clopidogrel|tablet|capsule|dose|dosage)\b",
    re.IGNORECASE,
)


def sanitize_clinical_text(text: str) -> str:
    """Ensure no medication names or dosing instructions ever appear in recommendation text."""
    if not text:
        return ""
    if BLOCKED_MED_PATTERNS.search(text):
        return re.sub(BLOCKED_MED_PATTERNS, "[consult physician]", text)
    return text


def check_emergency_short_circuit(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Run existing red-flag safety layer; glucose > 300 also triggers emergency path."""
    rf_raw = dict(payload.get("red_flags") or {})
    fpg = payload.get("fpg")
    if fpg is not None and float(fpg) > 300:
        rf_raw["glucose_mg_dl"] = float(fpg)
    rf_input = RedFlagInput(**rf_raw)
    res = evaluate_red_flags(rf_input)
    if fpg is not None and float(fpg) > 300 and not res.get("emergency"):
        res["emergency"] = True
        reasons = list(res.get("triggered_rules") or [])
        reasons.append("Severe hyperglycemia (fasting glucose > 300 mg/dL)")
        res["triggered_rules"] = reasons
        res["message"] = (
            "URGENT SAFETY ALERT: Fasting glucose above 300 mg/dL requires immediate medical attention. "
            "Call local emergency services (India: 112 / 108) or visit the nearest 24x7 emergency hospital."
        )
    return res


def apply_safety_filter(
    patient: Dict[str, Any],
    ranked_by_category: Dict[str, List[Dict[str, Any]]],
) -> Tuple[Dict[str, List[Dict[str, Any]]], int]:
    """Enforce clinical blocklists AFTER ML ranking. Returns (filtered_lists, blocked_count)."""
    tiers = patient.get("tiers", {})
    top_cond = patient.get("top_condition", "heart")
    egfr = patient.get("egfr")
    bp_stage = patient.get("bp_stage", "normal")
    age = int(patient.get("age", 45))
    pregnancy = bool(patient.get("pregnancy", False))
    high_risk_any = any(tiers.get(k) == "high" for k in ("heart", "hypertension", "kidney", "diabetes"))

    blocked_count = 0
    out: Dict[str, List[Dict[str, Any]]] = {
        "foods": [],
        "exercises": [],
        "hospitals": [],
        "specialties": [],
        "care": [],
    }

    # 1. Foods: hard blocklists + never put 'avoid' in Eat more / OK
    for item in ranked_by_category.get("foods", []):
        flags = item.get("nutrient_flags", {})
        codes = item.get("codes", {})
        cond_key = "diabetes" if top_cond == "metabolic" else top_cond
        cond_status = codes.get(cond_key, "watch")

        # eGFR < 30 -> block high-potassium / high-protein foods; force Ask nephrologist/dietitian
        if egfr is not None and egfr < 30:
            if flags.get("high_potassium") or flags.get("high_protein") or codes.get("kidney") == "avoid":
                blocked_count += 1
                continue
            item["status_label"] = "ask_dietitian"
            item["safety_notes"] = "eGFR < 30: Ask nephrologist/dietitian before adding to your meal plan."
        elif cond_status == "avoid":
            # Keep Avoid items out of top recommended 'Eat more / OK' list; tag explicitly if included
            item["status_label"] = "avoid"
            blocked_count += 1
            continue
        else:
            if item.get("advice") == "eat_more" and cond_status == "ok":
                item["status_label"] = "eat_more"
            else:
                item["status_label"] = cond_status

        if tiers.get("hypertension") == "high" and flags.get("high_sodium"):
            blocked_count += 1
            continue

        item["name"] = sanitize_clinical_text(item.get("name", ""))
        item["safety_notes"] = sanitize_clinical_text(item.get("safety_notes", ""))
        out["foods"].append(item)

    # 2. Exercises: BP stage 2/crisis -> light/walking only + clearance; age <18 / >75 / pregnancy -> clearance on all
    force_all_clearance = pregnancy or age < 18 or age > 75
    for item in ranked_by_category.get("exercises", []):
        intensity = item.get("intensity", "low")
        if bp_stage in ("stage_2", "crisis") and intensity in ("moderate", "vigorous"):
            blocked_count += 1
            continue
        if force_all_clearance or bp_stage in ("stage_2", "crisis") or high_risk_any:
            item["needs_medical_clearance"] = True
            if bp_stage in ("stage_2", "crisis"):
                item["safety_notes"] = "Stage 2 / Crisis BP: limit to gentle walking/breathing and get physician clearance."
            elif force_all_clearance:
                item["safety_notes"] = "Physician clearance advised for age <18, >75, or pregnancy."
        else:
            item["needs_medical_clearance"] = bool(item.get("medical_clearance_required", False))
        item["name"] = sanitize_clinical_text(item.get("name", ""))
        item["safety_notes"] = sanitize_clinical_text(item.get("safety_notes", ""))
        out["exercises"].append(item)

    # 3. Hospitals: strict verified-only + mandatory disclaimer
    for item in ranked_by_category.get("hospitals", []):
        if not item.get("verified", False):
            blocked_count += 1
            continue
        item["safety_notes"] = CARE_MATCHING_DISCLAIMER
        out["hospitals"].append(item)

    # 4. Specialties & 5. Care
    for cat in ("specialties", "care"):
        for item in ranked_by_category.get(cat, []):
            item["name"] = sanitize_clinical_text(item.get("name", ""))
            item["safety_notes"] = sanitize_clinical_text(item.get("safety_notes", ""))
            if isinstance(item.get("meta"), dict) and "description" in item["meta"]:
                item["meta"]["description"] = sanitize_clinical_text(str(item["meta"]["description"]))
            out[cat].append(item)

    return out, blocked_count
