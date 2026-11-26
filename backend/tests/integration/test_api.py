"""Integration tests for HealthBuddy v3.0 FastAPI endpoints."""

from fastapi.testclient import TestClient
from app.main import app


def test_health_and_models_info():
    with TestClient(app) as client:
        r = client.get("/api/v1/health")
        assert r.status_code == 200
        assert r.json()["app"] == "HealthBuddy"

        m = client.get("/api/v1/models/info")
        assert m.status_code == 200
        diseases = m.json()["diseases"]
        assert set(diseases.keys()) == {"heart_disease", "diabetes", "parkinsons", "liver_disease"}


def test_safety_check_and_predict_and_care_flow():
    with TestClient(app) as client:
        s = client.post("/api/v1/safety/check", json={"face_drooping": True})
        assert s.status_code == 200
        assert s.json()["emergency"] is True

        p = client.post(
            "/api/v1/predict/heart_disease",
            json={
                "features": {
                    "age": 63, "sex": 1, "cp": 4, "trestbps": 155, "chol": 285,
                    "fbs": 1, "restecg": 2, "thalach": 115, "exang": 1,
                    "oldpeak": 2.8, "slope": 2, "ca": 2, "thal": 7,
                },
                "consent_data_storage": False,
            },
        )
        assert p.status_code == 200
        pdata = p.json()
        assert pdata["risk_level"] in {"Low", "Moderate", "High"}
        assert "top_factors" in pdata
        assert "not a certified medical device" in pdata["disclaimer"].lower()

        c = client.post(
            "/api/v1/care/recommend",
            json={"disease": "heart_disease", "risk_level": pdata["risk_level"], "city": "New Delhi"},
        )
        assert c.status_code == 200
        cdata = c.json()
        assert cdata["disclaimer"] == "Matching options, not an endorsement or medical advice."
        assert all(h["verified"] is True for h in cdata["matched_hospitals"])


def test_auth_history_and_delete_my_data():
    with TestClient(app) as client:
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": "testuser@healthbuddy.local", "password": "Password123!", "role": "patient"},
        )
        assert reg.status_code in (201, 409)
        login = client.post(
            "/api/v1/auth/login",
            json={"email": "testuser@healthbuddy.local", "password": "Password123!"},
        )
        assert login.status_code == 200
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        hist = client.get("/api/v1/history", headers=headers)
        assert hist.status_code == 200

        del_res = client.delete("/api/v1/me/data", headers=headers)
        assert del_res.status_code == 200


def test_benchmarks_and_batch_screening():
    with TestClient(app) as client:
        b = client.get("/api/v1/models/benchmarks")
        assert b.status_code == 200
        assert len(b.json()["matrix"]) == 16

        sc = client.get("/api/v1/predict/heart_disease/sample-cohort?limit=5")
        assert sc.status_code == 200
        records = sc.json()["records"]
        assert len(records) == 5

        batch = client.post("/api/v1/predict/heart_disease/batch", json={"records": records})
        assert batch.status_code == 200
        assert batch.json()["summary"]["total"] == 5


def test_assess_red_flag_suppresses_scores_and_plans():
    with TestClient(app) as client:
        res = client.post(
            "/api/v1/assess",
            json={
                "age": 55,
                "sex": "male",
                "height_cm": 170,
                "weight_kg": 75,
                "waist_cm": 96,
                "systolic_bp": 150,
                "diastolic_bp": 95,
                "physical_activity": "sedentary",
                "family_diabetes": "one_parent",
                "red_flags": {"chest_pain_or_pressure": True},
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["emergency"]["emergency"] is True
        assert "modules" not in data
        assert "plans" not in data
        assert "ml_results" not in data


def test_assess_missing_labs_produce_skipped_modules_and_ml_needs_more_info():
    with TestClient(app) as client:
        res = client.post(
            "/api/v1/assess",
            json={
                "age": 48,
                "sex": "female",
                "height_cm": 160,
                "weight_kg": 64,
                "waist_cm": 84,
                "systolic_bp": 128,
                "diastolic_bp": 82,
                "physical_activity": "moderate",
                "family_diabetes": "none",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["emergency"] is None
        assert len(data["what_to_do_first"]) <= 3
        by_mod = {m["module"]: m for m in data["modules"]}
        assert by_mod["glucose_classification"]["status"] == "skipped"
        assert by_mod["kidney_ckd_epi"]["status"] == "skipped"
        assert by_mod["metabolic_syndrome"]["status"] == "skipped"
        assert by_mod["diabetes_idrs"]["status"] == "computed"
        assert by_mod["heart_who_cvd"]["status"] == "computed"

        ml_by_mod = {m["module"]: m for m in data["ml_results"]}
        assert ml_by_mod["ml_parkinsons"]["status"] == "needs_more_info"
        assert ml_by_mod["ml_liver_disease"]["status"] == "needs_more_info"

        rec = client.get("/api/v1/recommendations/heart?tier=high")
        assert rec.status_code == 200
        assert any("get medical clearance first" in ex.lower() for ex in rec.json()["exercise"])


def test_healthbuddy_ml_chatbot():
    with TestClient(app) as client:
        st = client.get("/api/v1/chat/status")
        assert st.status_code == 200
        st_data = st.json()
        assert st_data["name"] == "HealthBuddy"
        assert st_data["doc_count"] >= 20

        # Normal ML knowledgebase retrieval with personalized context
        res = client.post(
            "/api/v1/chat",
            json={
                "message": "What foods should I eat and avoid for my heart?",
                "lang": "en",
                "assessment_context": {"heart": "moderate", "diabetes": "low"},
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["emergency"] is False
        assert data["confidence"] > 0.08
        assert len(data["sources"]) > 0
        assert "not a medical device" in data["disclaimer"].lower()

        # Emergency red-flag override in chat
        em = client.post(
            "/api/v1/chat",
            json={"message": "I have severe chest pain and shortness of breath", "lang": "en"},
        )
        assert em.status_code == 200
        em_data = em.json()
        assert em_data["emergency"] is True
        assert "112" in em_data["reply"]


def test_knowledge_base_records_endpoint():
    with TestClient(app) as client:
        r = client.get("/api/v1/kb")
        assert r.status_code == 200
        data = r.json()
        assert data["counts"]["hospitals"] >= 60
        assert data["counts"]["doctors"] >= 15
        assert data["counts"]["guidance"] >= 18
        assert data["counts"]["care"] >= 35
        assert data["counts"]["risk_modules"] >= 6
        assert data["counts"]["faqs"] >= 25
        assert data["counts"]["foods"] >= 250
        assert data["counts"]["exercises"] >= 50
        assert data["counts"]["total"] >= 500

        filtered = client.get("/api/v1/kb?category=doctors&q=Cardiologist")
        assert filtered.status_code == 200
        fdata = filtered.json()
        assert len(fdata["doctors"]) >= 1
        assert len(fdata["hospitals"]) == 0

        foods_res = client.get("/api/v1/kb?category=foods&q=barley")
        assert foods_res.status_code == 200
        assert len(foods_res.json()["foods"]) >= 1



