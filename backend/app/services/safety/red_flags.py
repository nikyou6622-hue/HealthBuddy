"""Hard-coded red-flag safety rules for HealthBuddy v3.0.

Safety rules always run first and override any ML risk output.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.core.constants import EMERGENCY_NUMBERS


class RedFlagInput(BaseModel):
    chest_pain_or_pressure: bool = False
    pain_spreading_arm_or_jaw: bool = False
    severe_breathlessness_at_rest: bool = False
    fainting: bool = False
    face_drooping: bool = False
    arm_weakness: bool = False
    speech_difficulty: bool = False
    sudden_confusion: bool = False
    altered_consciousness: bool = False
    vomiting_blood: bool = False
    black_stools: bool = False
    severe_abdominal_swelling: bool = False
    glucose_mg_dl: Optional[float] = Field(default=None, ge=0, le=2000)
    persistent_vomiting: bool = False
    fruity_breath: bool = False


def evaluate_red_flags(payload: RedFlagInput) -> Dict[str, Any]:
    """Evaluate deterministic red-flag emergency rules.

    Returns emergency=True if any red-flag rule fires.
    """
    triggered: List[str] = []

    if payload.chest_pain_or_pressure:
        triggered.append("Chest pain or pressure")
    if payload.pain_spreading_arm_or_jaw:
        triggered.append("Pain spreading to arm or jaw")
    if payload.severe_breathlessness_at_rest:
        triggered.append("Severe breathlessness at rest")
    if payload.fainting:
        triggered.append("Fainting / syncope")

    # Stroke signs
    if payload.face_drooping:
        triggered.append("Stroke warning sign: face drooping")
    if payload.arm_weakness:
        triggered.append("Stroke warning sign: arm weakness")
    if payload.speech_difficulty:
        triggered.append("Stroke warning sign: speech difficulty")
    if payload.sudden_confusion:
        triggered.append("Sudden confusion")

    # Severe GI / Neurological signs
    if payload.altered_consciousness:
        triggered.append("Altered consciousness")
    if payload.vomiting_blood:
        triggered.append("Vomiting blood (hematemesis)")
    if payload.black_stools:
        triggered.append("Black tarry stools (melena)")
    if payload.severe_abdominal_swelling:
        triggered.append("Severe abdominal swelling")

    # Hyperglycemic crisis
    if payload.glucose_mg_dl is not None and payload.glucose_mg_dl > 300:
        if payload.sudden_confusion or payload.persistent_vomiting or payload.fruity_breath:
            triggered.append("Very high glucose (>300 mg/dL) with confusion, persistent vomiting, or fruity breath")

    is_emergency = len(triggered) > 0
    return {
        "emergency": is_emergency,
        "triggered_rules": triggered,
        "action": (
            "SEEK IMMEDIATE EMERGENCY MEDICAL CARE. Call your local emergency number now and go to the nearest emergency-capable hospital."
            if is_emergency
            else "No immediate emergency red flags detected. You may proceed to clinical risk screening."
        ),
        "emergency_numbers": EMERGENCY_NUMBERS,
        "override_ml": is_emergency,
    }

