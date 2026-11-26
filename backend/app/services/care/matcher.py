"""Care matching, deterministic ranking, and risk-based routing for HealthBuddy v3.0.

Only verified hospitals are ever returned. Never claims any provider is the 'best'.
"""

import math
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.core.constants import DISEASE_CARE_MAPPING, RISK_ROUTING_GUIDANCE
from app.models.tables import Hospital
from app.services.safety.disclaimers import CARE_MATCHING_DISCLAIMER


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance in kilometers."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return round(2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 2)


def recommend_care(
    db: Session,
    disease: str,
    risk_level: str,
    city: Optional[str] = None,
    pincode: Optional[str] = None,
    user_lat: Optional[float] = None,
    user_lon: Optional[float] = None,
    teleconsult_only: bool = False,
    language: Optional[str] = None,
    limit: int = 5,
) -> Dict[str, Any]:
    """Match specialist types, suggested tests, urgency timeline, and verified hospitals."""
    care_cfg = DISEASE_CARE_MAPPING.get(disease, DISEASE_CARE_MAPPING["heart_disease"])
    routing_cfg = RISK_ROUTING_GUIDANCE.get(risk_level, RISK_ROUTING_GUIDANCE["Moderate"])

    required_specialists: List[str] = care_cfg["specialists"]
    required_capabilities: List[str] = care_cfg["capabilities"]

    # Strict: only verified hospitals
    verified_hospitals = db.query(Hospital).filter(Hospital.verified.is_(True)).all()

    scored: List[Dict[str, Any]] = []
    for hosp in verified_hospitals:
        if teleconsult_only and not hosp.teleconsult:
            continue

        hosp_services = {s.name.lower() for s in hosp.services}
        hosp_specs = {s.strip().lower() for s in (hosp.specialties_text or "").split(",") if s.strip()}
        hosp_langs = {l.strip().lower() for l in (hosp.languages_text or "").split(",") if l.strip()}

        spec_matches = [s for s in required_specialists if s.lower() in hosp_specs]
        cap_matches = [c for c in required_capabilities if c.lower() in hosp_services]

        if not spec_matches and not cap_matches:
            continue

        distance_km: Optional[float] = None
        if user_lat is not None and user_lon is not None and hosp.lat is not None and hosp.lon is not None:
            distance_km = haversine_km(user_lat, user_lon, hosp.lat, hosp.lon)

        city_match = bool(city and hosp.city.lower() == city.strip().lower())
        pin_match = bool(pincode and hosp.pincode.strip() == pincode.strip())
        lang_match = bool(language and language.strip().lower() in hosp_langs)

        # Deterministic ranking tuple (higher capability & location priority, lower distance)
        emergency_score = 1 if (routing_cfg["emergency_first"] and hosp.emergency_24x7) else 0
        loc_score = (2 if pin_match else 0) + (1 if city_match else 0)
        cap_score = len(cap_matches) + len(spec_matches)
        dist_penalty = distance_km if distance_km is not None else 9999.0

        reasons: List[str] = []
        if spec_matches:
            reasons.append(f"Specialist match: {', '.join(spec_matches)}")
        if cap_matches:
            reasons.append(f"Capabilities: {', '.join(cap_matches)}")
        if hosp.emergency_24x7:
            reasons.append("24x7 Emergency care available")
        if city_match or pin_match:
            reasons.append(f"Matches location ({hosp.city} {hosp.pincode})")
        if distance_km is not None:
            reasons.append(f"Approximately {distance_km} km away")
        if hosp.teleconsult:
            reasons.append("Teleconsultation available")

        scored.append(
            {
                "_rank_key": (-emergency_score, -loc_score, -cap_score, dist_penalty, hosp.id),
                "id": hosp.id,
                "name": hosp.name,
                "address": hosp.address,
                "city": hosp.city,
                "pincode": hosp.pincode,
                "lat": hosp.lat,
                "lon": hosp.lon,
                "distance_km": distance_km,
                "emergency_24x7": hosp.emergency_24x7,
                "teleconsult": hosp.teleconsult,
                "languages": [l.strip() for l in (hosp.languages_text or "").split(",") if l.strip()],
                "insurance_notes": hosp.insurance_notes,
                "phone": hosp.phone,
                "website": hosp.website,
                "verified": hosp.verified,
                "verified_at": hosp.verified_at,
                "source_url": hosp.source_url,
                "matched_capabilities": cap_matches,
                "match_reasons": reasons,
            }
        )

    scored.sort(key=lambda x: x["_rank_key"])
    matched_hospitals = [{k: v for k, v in item.items() if k != "_rank_key"} for item in scored[:limit]]

    emergency_warning = None
    if risk_level == "High" and not any(h["emergency_24x7"] for h in matched_hospitals):
        emergency_warning = (
            "No emergency-capable verified hospital found in your immediate filter. "
            "Call your national emergency number (112 / 108 in India, 911 in US) immediately if symptoms worsen."
        )

    return {
        "disease": disease,
        "risk_level": risk_level,
        "specialist_types": required_specialists,
        "suggested_tests": care_cfg["suggested_tests"],
        "urgency_timeline": routing_cfg["urgency_timeline"],
        "guidance": routing_cfg["guidance"],
        "matched_hospitals": matched_hospitals,
        "emergency_warning": emergency_warning,
        "disclaimer": CARE_MATCHING_DISCLAIMER,
    }

