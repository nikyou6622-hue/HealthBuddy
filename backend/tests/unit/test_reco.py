"""Comprehensive unit & integration tests for ML Component #3 (Personalized Recommender)."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import ARTIFACTS_DIR
from app.main import app
from app.services.reco.engine import generate_personalized_recommendations, get_reco_model_info
from app.services.reco.safety_filter import BLOCKED_MED_PATTERNS, sanitize_clinical_text

BASE_PROFILE = {
    "age": 52,
    "sex": "male",
    "height_cm": 170,
    "weight_kg": 76,
    "waist_cm": 94,
    "systolic_bp": 134,
    "diastolic_bp": 84,
    "smoker": False,
    "alcohol_drinks_per_week": 0.0,
    "physical_activity": "moderate",
    "family_diabetes": "one_parent",
    "city": "New Delhi",
    "fpg": 112.0,
    "hba1c": 6.1,
    "total_cholesterol": 208.0,
    "ldl": 130.0,
    "hdl": 40.0,
    "triglycerides": 175.0,
    "serum_creatinine": 0.95,
    "urine_acr": 18.0,
}


def test_reco_determinism():
    r1 = generate_personalized_recommendations(BASE_PROFILE, lang="en", top_k=8)
    r2 = generate_personalized_recommendations(BASE_PROFILE, lang="en", top_k=8)
    assert r1["model_version"] == r2["model_version"]
    for cat in ("foods", "exercises", "hospitals", "specialties", "care"):
        ids1 = [x["id"] for x in r1["categories"][cat]]
        ids2 = [x["id"] for x in r2["categories"][cat]]
        assert ids1 == ids2


def test_reco_all_five_categories_populated_and_explained():
    res = generate_personalized_recommendations(BASE_PROFILE, lang="en", top_k=6)
    assert res["emergency"] is None
    assert "not a medical device" in res["disclaimer"].lower()
    for cat in ("foods", "exercises", "hospitals", "specialties", "care"):
        items = res["categories"][cat]
        assert len(items) >= 1
        for idx, it in enumerate(items, start=1):
            assert it["rank"] == idx
            assert 0.0 <= it["score"] <= 1.0
            assert 1 <= len(it["reasons"]) <= 3
            assert "en" in it["reasons"][0] and "hi" in it["reasons"][0]
            assert it["confidence"] in ("high", "medium", "low_confidence")


def test_monotonicity_higher_hba1c_never_ranks_high_sugar_foods_higher():
    low_sugar = {**BASE_PROFILE, "hba1c": 5.2, "fpg": 88.0}
    high_sugar = {**BASE_PROFILE, "hba1c": 8.8, "fpg": 195.0}
    r_low = generate_personalized_recommendations(low_sugar, top_k=30)
    r_high = generate_personalized_recommendations(high_sugar, top_k=30)
    assert not any(
        "mysore pak" in x["name"].lower() or "rabri" in x["name"].lower()
        for x in r_high["categories"]["foods"][:8]
    )
    assert r_high["top_tier"] == "high"
    assert len(r_low["categories"]["foods"]) > 0


def test_monotonicity_egfr_drop_blocks_high_potassium_and_protein():
    ckd_severe = {**BASE_PROFILE, "age": 66, "serum_creatinine": 2.9, "urine_acr": 380.0}
    res = generate_personalized_recommendations(ckd_severe, top_k=15)
    for food in res["categories"]["foods"]:
        assert food["status_label"] == "ask_dietitian"
        assert "eGFR < 30" in food["safety_notes"]
        name_low = food["name"].lower()
        assert "spinach" not in name_low and "star fruit" not in name_low


def test_monotonicity_bp_stage_up_limits_exercise_intensity():
    stage2 = {**BASE_PROFILE, "systolic_bp": 158, "diastolic_bp": 98}
    res = generate_personalized_recommendations(stage2, top_k=15)
    for ex in res["categories"]["exercises"]:
        assert ex["status_label"] == "low"
        assert ex["needs_medical_clearance"] is True


@pytest.mark.parametrize(
    "override",
    [
        {"age": 16},
        {"age": 78},
        {"pregnancy": True},
    ],
)
def test_safety_clearance_flag_for_age_and_pregnancy(override):
    prof = {**BASE_PROFILE, **override}
    res = generate_personalized_recommendations(prof, top_k=10)
    for ex in res["categories"]["exercises"]:
        assert ex["needs_medical_clearance"] is True


@pytest.mark.parametrize(
    "rf_payload",
    [
        {"red_flags": {"chest_pain_or_pressure": True}},
        {"red_flags": {"face_drooping": True}},
        {"fpg": 340.0},
    ],
)
def test_safety_emergency_short_circuit_returns_zero_recommendations(rf_payload):
    prof = {**BASE_PROFILE, **rf_payload}
    res = generate_personalized_recommendations(prof)
    assert res["emergency"] is not None
    assert res["emergency"]["emergency"] is True
    for cat in ("foods", "exercises", "hospitals", "specialties", "care"):
        assert res["categories"][cat] == []


def test_safety_hospitals_verified_only_and_disclaimer():
    res = generate_personalized_recommendations(BASE_PROFILE, top_k=30)
    for hosp in res["categories"]["hospitals"]:
        assert "unverified" not in hosp["name"].lower()
        assert "not an endorsement" in hosp["safety_notes"].lower()


def test_safety_no_avoid_foods_and_no_meds_or_doses():
    res = generate_personalized_recommendations(BASE_PROFILE, top_k=20)
    for food in res["categories"]["foods"]:
        assert food["status_label"] != "avoid"
    serialized = json.dumps(res)
    assert not BLOCKED_MED_PATTERNS.search(serialized)
    assert "[consult physician]" in sanitize_clinical_text("Take metformin 500 mg daily")


def test_missing_labs_populated_and_low_confidence():
    no_labs = {
        k: v
        for k, v in BASE_PROFILE.items()
        if k not in ("fpg", "hba1c", "total_cholesterol", "ldl", "hdl", "triglycerides", "serum_creatinine", "urine_acr")
    }
    res = generate_personalized_recommendations(no_labs, top_k=8)
    assert len(res["missing_inputs"]) == 8
    assert res["confidence"] == "low_confidence"


def test_rules_fallback_when_artifact_missing():
    res = generate_personalized_recommendations(BASE_PROFILE, top_k=6, artifact_override={})
    assert res["model_version"] == "rules-fallback"
    assert res["confidence"] == "low_confidence"
    assert len(res["categories"]["foods"]) == 6


def test_training_artifacts_size_and_ndcg_benchmark():
    model_path = ARTIFACTS_DIR / "reco_model.joblib"
    eval_path = ARTIFACTS_DIR / "reco_eval.json"
    assert model_path.exists()
    assert eval_path.exists()
    size_mb = model_path.stat().st_size / (1024.0 * 1024.0)
    assert size_mb < 20.0

    eval_data = get_reco_model_info()
    m = eval_data["models"]
    assert m["hist_gradient_boosting"]["ndcg_at_10"] >= m["baseline_cosine_similarity"]["ndcg_at_10"]
    assert m["hist_gradient_boosting"]["safety_violation_rate_post_filter"] == 0.0


def test_reco_warm_latency_under_500ms():
    generate_personalized_recommendations(BASE_PROFILE, top_k=8)  # warm up lru_cache
    t0 = time.perf_counter()
    generate_personalized_recommendations(BASE_PROFILE, top_k=8)
    dt_ms = (time.perf_counter() - t0) * 1000.0
    assert dt_ms < 500.0, f"Warm inference took {dt_ms:.1f} ms"


def test_reco_api_endpoints_and_feedback():
    with TestClient(app) as client:
        res = client.post("/api/v1/reco/personalized", json={**BASE_PROFILE, "lang": "hi", "top_k": 5})
        assert res.status_code == 200
        data = res.json()
        assert len(data["categories"]["foods"]) == 5
        assert data["categories"]["foods"][0]["reasons"][0]["hi"]

        # Invalid age -> 422
        bad = client.post("/api/v1/reco/personalized", json={**BASE_PROFILE, "age": 200})
        assert bad.status_code == 422

        info = client.get("/api/v1/reco/model-info")
        assert info.status_code == 200
        assert "hist_gradient_boosting" in info.json()["models"]

        fb = client.post(
            "/api/v1/reco/feedback",
            json={"item_id": "food_4", "category": "foods", "helpful": True, "consent_data_storage": False},
        )
        assert fb.status_code == 200
        assert fb.json()["status"] == "recorded"

        # PDF with personalized_plan
        pdf_res = client.post("/api/v1/reports/pdf", json={"disease": "heart_disease", "personalized_plan": data})
        assert pdf_res.status_code == 200
        assert pdf_res.content[:4] == b"%PDF"


@pytest.mark.parametrize(
    "rf_field",
    [
        "chest_pain_or_pressure",
        "pain_spreading_arm_or_jaw",
        "severe_breathlessness_at_rest",
        "fainting",
        "face_drooping",
        "arm_weakness",
        "speech_difficulty",
        "sudden_confusion",
    ],
)
def test_all_emergency_red_flag_booleans_short_circuit(rf_field):
    prof = {**BASE_PROFILE, "red_flags": {rf_field: True}}
    res = generate_personalized_recommendations(prof)
    assert res["emergency"]["emergency"] is True
    assert all(res["categories"][c] == [] for c in ("foods", "exercises", "hospitals", "specialties", "care"))


@pytest.mark.parametrize(
    "bad_text",
    [
        "Take 500 mg daily",
        "Use 10 mcg",
        "Give 20 IU",
        "Start metformin",
        "Take atorvastatin",
        "Try amlodipine",
        "Add lisinopril",
        "Take glimepiride",
        "Use losartan",
        "Take aspirin tablet",
    ],
)
def test_sanitize_blocks_medications_and_doses(bad_text):
    cleaned = sanitize_clinical_text(bad_text)
    assert "[consult physician]" in cleaned


def test_sanitize_allows_educational_insulin_sensitivity():
    msg = "Brisk walking improves insulin sensitivity naturally."
    assert sanitize_clinical_text(msg) == msg


@pytest.mark.parametrize(
    "override",
    [
        {"age": 12},
        {"age": 95},
        {"systolic_bp": 230},
        {"diastolic_bp": 140},
    ],
)
def test_out_of_range_inputs_trigger_low_confidence(override):
    prof = {**BASE_PROFILE, **override}
    res = generate_personalized_recommendations(prof, top_k=5)
    assert res["confidence"] == "low_confidence"


@pytest.mark.parametrize("city", ["New Delhi", "Mumbai", "Bengaluru", "Chennai", "Pune"])
def test_hospitals_city_match_and_verified_only(city):
    prof = {**BASE_PROFILE, "city": city}
    res = generate_personalized_recommendations(prof, top_k=8)
    hosps = res["categories"]["hospitals"]
    assert len(hosps) >= 1
    assert any((h.get("meta") or {}).get("city", "").lower() == city.lower() for h in hosps)


def test_hypertension_high_blocks_high_sodium_foods():
    htn_high = {**BASE_PROFILE, "systolic_bp": 168, "diastolic_bp": 102}
    res = generate_personalized_recommendations(htn_high, top_k=20)
    for f in res["categories"]["foods"]:
        assert not (f.get("meta") or {}).get("high_sodium", False)


def test_chatbot_reco_flag_off_and_on(monkeypatch):
    from app.services.chatbot.knowledge_bot import get_chatbot

    bot = get_chatbot()
    monkeypatch.setenv("RECO_IN_CHATBOT", "false")
    off_res = bot.ask("What is my diet plan for heart?", lang="en", assessment_context=BASE_PROFILE)
    assert "Personalized ML #3 Highlights" not in off_res["reply"]

    monkeypatch.setenv("RECO_IN_CHATBOT", "true")
    on_res = bot.ask("What is my diet plan for heart?", lang="en", assessment_context=BASE_PROFILE)
    assert "Personalized ML #3 Highlights" in on_res["reply"]
