"""Unit tests for HealthBuddy v3.0 safety rules and care matching."""

from app.services.safety.red_flags import RedFlagInput, evaluate_red_flags
from app.services.safety.disclaimers import CARE_MATCHING_DISCLAIMER, PERSISTENT_BANNER_DISCLAIMER
from app.services.care.matcher import recommend_care
from app.db.session import SessionLocal, init_db
from app.models.tables import Hospital


def test_red_flag_chest_pain_triggers_emergency():
    res = evaluate_red_flags(RedFlagInput(chest_pain_or_pressure=True))
    assert res["emergency"] is True
    assert res["override_ml"] is True
    assert "Chest pain or pressure" in res["triggered_rules"]


def test_red_flag_hyperglycemic_crisis():
    res = evaluate_red_flags(RedFlagInput(glucose_mg_dl=340, fruity_breath=True))
    assert res["emergency"] is True
    assert res["override_ml"] is True


def test_red_flag_clear_when_no_symptoms():
    res = evaluate_red_flags(RedFlagInput())
    assert res["emergency"] is False
    assert res["triggered_rules"] == []


def test_unverified_hospitals_never_returned_and_no_best_claim():
    init_db()
    db = SessionLocal()
    try:
        res = recommend_care(db=db, disease="heart_disease", risk_level="High", city="New Delhi")
        assert res["disclaimer"] == CARE_MATCHING_DISCLAIMER
        assert "best" not in res["disclaimer"].lower()
        for h in res["matched_hospitals"]:
            assert h["verified"] is True
            assert "Unverified Sample Clinic" not in h["name"]
            assert len(h["match_reasons"]) >= 1
    finally:
        db.close()

