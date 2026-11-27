"""Data-driven relevance labeling rules and KB candidate loader for ML #3."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

RULES_DIR = Path(__file__).resolve().parent / "rules"


def _load_json(name: str) -> Dict[str, Any]:
    with open(RULES_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)


FOOD_RULES = _load_json("food_rules.json")
EXERCISE_RULES = _load_json("exercise_rules.json")
CARE_RULES = _load_json("care_rules.json")

TIER_ORD = {"low": 0, "moderate": 1, "high": 2, "skipped": 1, "not_applicable": 0, None: 1}


def infer_nutrient_flags(food: Dict[str, Any]) -> Dict[str, int]:
    """Derive structured nutrient flags from food name, group, and clinical note."""
    blob = f"{food.get('name', '')} {food.get('group', '')} {food.get('note', '')}".lower()
    flags: Dict[str, int] = {}
    for flag_name, keywords in FOOD_RULES["nutrient_keywords"].items():
        flags[flag_name] = 1 if any(kw in blob for kw in keywords) else 0
    return flags


def normalize_kb_candidates(kb: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Flatten KB records into uniform candidate items across the 5 recommendation categories."""
    items: List[Dict[str, Any]] = []

    # 1. Foods (291)
    for f in kb.get("foods", []):
        flags = infer_nutrient_flags(f)
        items.append(
            {
                "id": f["id"],
                "category": "foods",
                "name": f.get("name", ""),
                "hindi": f.get("hindi", ""),
                "group": f.get("group", ""),
                "advice": f.get("advice", "moderate"),
                "codes": f.get("codes", {}),
                "note": f.get("note", ""),
                "text": f"{f.get('name', '')} {f.get('hindi', '')} {f.get('group', '')} {f.get('advice', '')} {f.get('note', '')}",
                "nutrient_flags": flags,
            }
        )

    # 2. Exercises & yoga (55)
    for ex in kb.get("exercises", []):
        items.append(
            {
                "id": ex["id"],
                "category": "exercises",
                "name": ex.get("name", ""),
                "hindi": ex.get("hindi", ""),
                "group": ex.get("category", "aerobic"),
                "intensity": ex.get("intensity", "low"),
                "conditions_safe": ex.get("conditions_safe", []),
                "medical_clearance_required": bool(ex.get("medical_clearance_required", False)),
                "duration_or_reps": ex.get("duration_or_reps", ""),
                "benefits": ex.get("benefits", ""),
                "cautions": ex.get("cautions", ""),
                "text": f"{ex.get('name', '')} {ex.get('hindi', '')} {ex.get('category', '')} {' '.join(ex.get('conditions_safe', []))} {ex.get('benefits', '')}",
            }
        )

    # 3. Verified Hospitals (60)
    for h in kb.get("hospitals", []):
        if not h.get("verified", False):
            continue
        notes = f"{h.get('insurance_notes', '')} {h.get('name', '')}".lower()
        is_govt = any(k in notes for k in ("public", "cghs", "aiims", "pgimer", "jipmer", "safdarjung", "kem", "nims", "sskm", "rims", "skims"))
        items.append(
            {
                "id": f"hosp_{h['id']}",
                "raw_id": h["id"],
                "category": "hospitals",
                "name": h.get("name", ""),
                "hindi": h.get("name", ""),
                "city": h.get("city", ""),
                "pincode": h.get("pincode", ""),
                "address": h.get("address", ""),
                "lat": h.get("lat"),
                "lon": h.get("lon"),
                "phone": h.get("phone", ""),
                "website": h.get("website", ""),
                "insurance_notes": h.get("insurance_notes", ""),
                "emergency_24x7": bool(h.get("emergency_24x7", False)),
                "teleconsult": bool(h.get("teleconsult", False)),
                "is_govt": is_govt,
                "specialties": h.get("specialties", []),
                "facilities": h.get("facilities", []),
                "verified": True,
                "text": f"{h.get('name', '')} {h.get('city', '')} {' '.join(h.get('specialties', []))} {' '.join(h.get('facilities', []))} {h.get('insurance_notes', '')}",
            }
        )

    # 4. Doctor specialties & lab tests (18)
    for d in kb.get("doctors", []):
        items.append(
            {
                "id": f"spec_{d['id']}",
                "category": "specialties",
                "name": d.get("name", ""),
                "hindi": d.get("name", ""),
                "subspecialty": d.get("subspecialty", ""),
                "conditions_covered": d.get("conditions_covered", []),
                "available_at_hospitals": d.get("available_at_hospitals", []),
                "text": f"{d.get('name', '')} {d.get('subspecialty', '')} {' '.join(d.get('conditions_covered', []))}",
            }
        )

    # 5. Care services & follow-up routing (39)
    for c in kb.get("care", []):
        items.append(
            {
                "id": c["id"],
                "category": "care",
                "name": c.get("name", ""),
                "hindi": c.get("name", ""),
                "care_type": c.get("category", "clinical_service"),
                "urgency": c.get("urgency", ""),
                "description": c.get("description", ""),
                "available_at_hospitals": c.get("available_at_hospitals", []),
                "text": f"{c.get('name', '')} {c.get('description', '')} {' '.join(c.get('available_at_hospitals', [])[:3])}",
            }
        )

    return items


def score_pair_by_rules(patient: Dict[str, Any], item: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
    """Compute continuous rule score and discrete 0-3 relevance grade for a (patient, item) pair."""
    cat = item["category"]
    tiers = patient.get("tiers", {})
    top_cond = patient.get("top_condition", "heart")
    top_tier = tiers.get(top_cond, "moderate")
    bp_tier = tiers.get("hypertension", "low")
    kidney_tier = tiers.get("kidney", "low")
    diab_tier = tiers.get("diabetes", "low")
    heart_tier = tiers.get("heart", "low")
    bp_stage = patient.get("bp_stage", "normal")
    egfr = patient.get("egfr")
    age = int(patient.get("age", 45))

    if cat == "foods":
        codes = item.get("codes", {})
        cond_key = "diabetes" if top_cond == "metabolic" else top_cond
        status_str = codes.get(cond_key, "watch")
        short_code = {"ok": "o", "watch": "w", "limit": "l", "avoid": "a", "ask_dietitian": "d"}.get(status_str, "w")
        base = FOOD_RULES["code_to_grade"].get(short_code, 1.5)
        flags = item.get("nutrient_flags", {})

        # Penalize specific clinical conflicts
        conflict = 0.0
        if kidney_tier in ("moderate", "high") or (egfr is not None and egfr < 60):
            if codes.get("kidney") in ("avoid", "ask_dietitian") and (flags.get("high_potassium") or flags.get("high_protein")):
                base = min(base, 0.5)
                conflict = 1.0
        if diab_tier in ("moderate", "high") and flags.get("high_sugar"):
            base = min(base, 0.2)
            conflict = 1.0
        if bp_tier in ("moderate", "high") and flags.get("high_sodium"):
            base = min(base, 0.3)
            conflict = 1.0
        if heart_tier in ("moderate", "high") and flags.get("high_sat_fat"):
            base = min(base, 0.7)
            conflict = 1.0
        if flags.get("high_fiber") and base >= 2.0:
            base = min(3.0, base + 0.3)

        advice_adj = FOOD_RULES["advice_bonus"].get(item.get("advice", "moderate"), 0.0)
        raw = max(0.0, min(3.0, base + 0.35 * advice_adj))
        grade = float(int(round(raw)))
        return raw, {"food_status_ord": base / 3.0, "nutrient_conflict": conflict, "condition_match": 1.0 if raw >= 2.0 else 0.0}

    if cat == "exercises":
        safe_conds = set(item.get("conditions_safe", []))
        cond_key = "diabetes" if top_cond == "metabolic" else top_cond
        cond_match = 1.0 if cond_key in safe_conds else 0.0
        intensity_val = EXERCISE_RULES["intensity_order"].get(item.get("intensity", "low"), 1)
        max_safe = EXERCISE_RULES["bp_stage_max_safe_intensity"].get(bp_stage, 1)
        clearance = bool(item.get("medical_clearance_required", False))
        high_risk_any = any(tiers.get(k) == "high" for k in ("heart", "hypertension", "kidney", "diabetes"))

        conflict = 0.0
        score = 1.5 + cond_match * EXERCISE_RULES["safe_condition_bonus"]
        if intensity_val > max_safe:
            score -= 2.0
            conflict = 1.0
        if clearance and (high_risk_any or age < 18 or age > 75):
            score -= EXERCISE_RULES["high_risk_clearance_penalty"]
            conflict = 1.0
        if not clearance and intensity_val == 0 and high_risk_any:
            score += 0.6

        raw = max(0.0, min(3.0, score))
        grade = float(int(round(raw)))
        return raw, {"condition_match": cond_match, "clearance_conflict": conflict, "intensity_fit": 1.0 if intensity_val <= max_safe else 0.0}

    if cat == "hospitals":
        p_city = (patient.get("city") or "").strip().lower()
        h_city = (item.get("city") or "").strip().lower()
        same_city = 1.0 if (p_city and h_city and p_city == h_city) else 0.0
        req_specs = set(s.lower() for s in CARE_RULES["condition_to_specialties"].get(top_cond, []))
        hosp_specs = set(s.lower() for s in item.get("specialties", []))
        spec_overlap = len(req_specs & hosp_specs)
        high_risk_any = any(tiers.get(k) == "high" for k in ("heart", "hypertension", "kidney", "diabetes"))
        emerg_fit = 1.0 if (item.get("emergency_24x7") and high_risk_any) else 0.0

        score = 0.6 + same_city * 1.4 + min(1.0, spec_overlap * 0.5) + emerg_fit * 0.6
        if item.get("teleconsult"):
            score += 0.2
        raw = max(0.0, min(3.0, score))
        grade = float(int(round(raw)))
        return raw, {"same_city": same_city, "specialty_match": float(spec_overlap), "emergency_fit": emerg_fit}

    if cat == "specialties":
        req_specs = [s.lower() for s in CARE_RULES["condition_to_specialties"].get(top_cond, [])]
        name_low = item.get("name", "").lower()
        exact_match = 1.0 if name_low in req_specs else 0.0
        secondary_match = 0.0
        for c, t in tiers.items():
            if t in ("moderate", "high"):
                if name_low in [s.lower() for s in CARE_RULES["condition_to_specialties"].get(c, [])]:
                    secondary_match = 1.0
        score = 0.4 + exact_match * 2.0 + secondary_match * 0.6
        raw = max(0.0, min(3.0, score))
        return raw, {"condition_match": max(exact_match, secondary_match), "specialty_match": exact_match}

    # care services & routing
    req_svcs = [s.lower() for s in CARE_RULES["condition_to_services"].get(top_cond, [])]
    cname = item.get("name", "").lower()
    svc_match = 1.0 if cname in req_svcs else 0.0
    urgency_match = 0.0
    if item.get("care_type") == "care_routing":
        urg = item.get("urgency", "")
        if top_tier == "high" and urg == "24_72_hours":
            urgency_match = 1.0
        elif top_tier == "moderate" and urg == "within_2_weeks":
            urgency_match = 1.0
        elif top_tier == "low" and urg == "routine":
            urgency_match = 1.0
    score = 0.5 + svc_match * 1.8 + urgency_match * 2.2
    raw = max(0.0, min(3.0, score))
    return raw, {"condition_match": max(svc_match, urgency_match)}

