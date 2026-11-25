"""Doctor-reviewed recommendation engine for HealthBuddy v3.0."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict

from app.services.safety.disclaimers import CARE_MATCHING_DISCLAIMER

CONTENT_DIR = Path(__file__).parent / "content"


def get_recommendation_plan(condition: str, tier: str) -> Dict[str, Any]:
    """Load and validate a doctor-reviewed care guidance plan for a condition and tier."""
    cond_key = condition.strip().lower()
    tier_key = tier.strip().lower()
    if tier_key not in ("low", "moderate", "high"):
        tier_key = "moderate"

    plan_file = CONTENT_DIR / f"{cond_key}.json"
    if not plan_file.exists():
        raise ValueError(f"No care guidance plan found for condition '{condition}'")

    with open(plan_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Safety rule: never release unreviewed plans to users
    if not data.get("reviewed_by"):
        raise PermissionError(f"Plan for '{condition}' has not been clinically reviewed (reviewed_by is null)")

    tier_data = data["tiers"].get(tier_key, data["tiers"]["moderate"])
    followup_days = int(tier_data.get("followup_days", 30))
    followup_due = (datetime.now(timezone.utc) + timedelta(days=followup_days)).date().isoformat()

    return {
        "condition": data["condition"],
        "title": data["title"],
        "tier": tier_key,
        "source": data["source"],
        "reviewed_by": data["reviewed_by"],
        "version": data["version"],
        "doctor_tests": tier_data["doctor_tests"],
        "exercise": tier_data["exercise"],
        "food": tier_data["food"],
        "food_to_limit": tier_data.get(
            "food_to_limit",
            ["Maida snacks (white bread, samosa pastry, biscuits)", "Deep-fried items", "Sweets and sugary drinks", "Pickles, papads, and extra table salt"],
        ),
        "hospital_guidance": tier_data["hospital_guidance"],
        "followup_days": followup_days,
        "followup_due_date": followup_due,
        "disclaimer": CARE_MATCHING_DISCLAIMER,
    }

