"""API v1 router for HealthBuddy v3.0."""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.clinical_config import DEFAULT_DISEASE, DISEASES_CONFIG, list_supported_diseases
from app.core.config import ARTIFACTS_DIR, settings
from app.core.security import (
    create_access_token,
    get_current_user_optional,
    hash_password,
    require_role,
    require_user,
    verify_password,
)
from app.db.session import get_db
from app.models.tables import (
    Assessment,
    AuditLog,
    Consent,
    FollowUp,
    Hospital,
    PredictionRecord,
    RecommendationLog,
    User,
)
from app.schemas.api import (
    AssessRequest,
    CareRecommendRequest,
    ChatRequest,
    ClinicianFeedbackRequest,
    HospitalCreateRequest,
    HospitalVerifyRequest,
    LoginRequest,
    PredictRequest,
    RegisterRequest,
    ReportPdfRequest,
)
from app.services.assessment.orchestrator import run_full_assessment
from app.services.care.matcher import recommend_care
from app.services.chatbot.knowledge_bot import get_chatbot
from app.services.kb.records import build_knowledge_base_record, get_knowledge_base
from app.services.ml.predictor import HealthBuddyPredictor
from app.services.recommend.engine import get_recommendation_plan
from app.services.reports.pdf_report import generate_assessment_pdf
from app.services.safety.disclaimers import (
    CARE_MATCHING_DISCLAIMER,
    FULL_MEDICAL_DISCLAIMER,
    PERSISTENT_BANNER_DISCLAIMER,
)
from app.services.safety.red_flags import RedFlagInput, evaluate_red_flags

router = APIRouter()
_predictor_cache: Dict[str, HealthBuddyPredictor] = {}


def _get_predictor(disease: str) -> HealthBuddyPredictor:
    if disease not in DISEASES_CONFIG:
        raise HTTPException(status_code=404, detail=f"Unknown disease '{disease}'")
    if disease not in _predictor_cache:
        _predictor_cache[disease] = HealthBuddyPredictor(disease=disease)
    return _predictor_cache[disease]


@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "disclaimer": PERSISTENT_BANNER_DISCLAIMER,
    }


@router.get("/models/info")
def models_info():
    info = {}
    for disease in list_supported_diseases():
        pred = _get_predictor(disease)
        cfg = DISEASES_CONFIG[disease]
        info[disease] = {
            "name": cfg["name"],
            "system": cfg["system"],
            "features": cfg["feature_columns"],
            "feature_descriptions": cfg["feature_descriptions"],
            "feature_ranges": cfg["feature_ranges"],
            "categorical_features": cfg["categorical_features"],
            "demo_presets": cfg.get("demo_presets", {}),
            "metrics": pred.get_clinical_metrics(),
        }
    return {"app": settings.APP_NAME, "version": settings.APP_VERSION, "diseases": info}


@router.get("/models/benchmarks")
def models_benchmarks():
    """Return full 16-classifier benchmark metrics, confusion matrices, and feature importances."""
    matrix_rows: List[Dict[str, Any]] = []
    per_disease: Dict[str, Any] = {}
    for disease in list_supported_diseases():
        cfg = DISEASES_CONFIG[disease]
        eval_path = ARTIFACTS_DIR / disease / "evaluation_results.json"
        if not eval_path.exists() and disease == DEFAULT_DISEASE:
            eval_path = ARTIFACTS_DIR / "evaluation_results.json"
        if not eval_path.exists():
            continue
        with open(eval_path, "r", encoding="utf-8") as f:
            eval_data = json.load(f)
        per_disease[disease] = {"name": cfg["name"], "models": eval_data}
        for m_name, res in eval_data.items():
            if "error" not in res:
                matrix_rows.append(
                    {
                        "disease": disease,
                        "disease_name": cfg["name"],
                        "algorithm": m_name.replace("_", " ").title(),
                        "accuracy": res["accuracy"],
                        "precision_weighted": res["precision_weighted"],
                        "recall_weighted": res["recall_weighted"],
                        "f1_weighted": res["f1_weighted"],
                        "roc_auc": res.get("roc_auc") or 0.0,
                    }
                )
    return {"matrix": matrix_rows, "per_disease": per_disease}


class BatchPredictRequest(BaseModel):
    records: List[Dict[str, Any]]


@router.get("/predict/{disease}/sample-cohort")
def get_sample_cohort(disease: str, limit: int = 15):
    """Return sample holdout rows for batch cohort screening."""
    if disease not in DISEASES_CONFIG:
        raise HTTPException(status_code=404, detail=f"Unknown disease '{disease}'")
    sample_path = ARTIFACTS_DIR / disease / "test_set.csv"
    if not sample_path.exists() and disease == DEFAULT_DISEASE:
        sample_path = ARTIFACTS_DIR / "test_set.csv"
    if not sample_path.exists():
        raise HTTPException(status_code=404, detail="Sample cohort not found")
    df = pd.read_csv(sample_path).head(limit)
    req_cols = DISEASES_CONFIG[disease]["feature_columns"]
    records = df[req_cols].to_dict(orient="records")
    return {"disease": disease, "records": records}


@router.post("/predict/{disease}/batch")
def predict_disease_batch(disease: str, payload: BatchPredictRequest):
    """Run batch risk screening across a cohort of patient records."""
    predictor = _get_predictor(disease)
    results = []
    for idx, rec in enumerate(payload.records):
        res = predictor.predict(rec)
        results.append(
            {
                "patient_index": idx + 1,
                "success": res.get("success", False),
                "label": res.get("label", "Validation Error"),
                "risk_level": res.get("risk_level", "N/A"),
                "probability": res.get("probability"),
                "confidence_flag": res.get("confidence_flag", "N/A"),
                "errors": res.get("errors", []),
            }
        )
    valid = [r for r in results if r["success"]]
    probs = [r["probability"] for r in valid if r["probability"] is not None]
    summary = {
        "total": len(results),
        "valid": len(valid),
        "high_risk": sum(1 for r in valid if r["risk_level"] == "High"),
        "moderate_risk": sum(1 for r in valid if r["risk_level"] == "Moderate"),
        "low_risk": sum(1 for r in valid if r["risk_level"] == "Low"),
        "mean_probability": round(sum(probs) / len(probs), 4) if probs else None,
    }
    return {"disease": disease, "summary": summary, "results": results, "disclaimer": FULL_MEDICAL_DISCLAIMER}


@router.post("/safety/check")
def safety_check(payload: RedFlagInput):
    result = evaluate_red_flags(payload)
    result["disclaimer"] = PERSISTENT_BANNER_DISCLAIMER
    return result


@router.post("/predict/{disease}")
def predict_disease(
    disease: str,
    payload: PredictRequest,
    db: Session = Depends(get_db),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional),
):
    predictor = _get_predictor(disease)
    res = predictor.predict(payload.features)
    if not res.get("success"):
        raise HTTPException(status_code=422, detail=res.get("errors", ["Validation failed"]))

    user_id = current_user.get("user_id") if current_user else None
    raw_json = json.dumps(payload.features) if payload.consent_data_storage else None

    record = PredictionRecord(
        user_id=user_id,
        disease=disease,
        risk_level=res["risk_level"],
        probability=res["probability"],
        model_version=res["model_version"],
        confidence_flag=res["confidence_flag"],
        raw_inputs_json=raw_json,
    )
    db.add(record)
    db.flush()

    if user_id is not None:
        db.add(Consent(user_id=user_id, consent_type="data_storage", granted=payload.consent_data_storage))

    db.add(
        AuditLog(
            actor=current_user.get("sub") if current_user else "anonymous",
            action="predict",
            entity=f"prediction:{record.id}",
            details=f"disease={disease}, risk={res['risk_level']}",
        )
    )
    db.commit()
    db.refresh(record)

    res["prediction_id"] = record.id
    res["disclaimer"] = FULL_MEDICAL_DISCLAIMER
    return res


@router.post("/assess")
def assess_patient(
    payload: AssessRequest,
    db: Session = Depends(get_db),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional),
):
    """Unified assessment endpoint: validate -> safety check -> calculators -> ML -> recommendations."""
    result = run_full_assessment(payload.model_dump(), db=db)

    # If a red flag fired, return ONLY { emergency: {...}, disclaimer } with NO scores or plans
    if result.get("emergency"):
        return result

    if payload.consent_data_storage:
        user_id = current_user.get("user_id") if current_user else None
        assess_rec = Assessment(
            user_id=user_id,
            inputs_json=json.dumps(payload.model_dump()),
            outputs_json=json.dumps(result),
            consent_flag=True,
        )
        db.add(assess_rec)
        db.flush()

        for fu in result.get("followups", []):
            db.add(
                FollowUp(
                    assessment_id=assess_rec.id,
                    condition=fu["condition"],
                    tier=fu["tier"],
                    due_date=fu["due_date"],
                )
            )
        db.commit()
        result["assessment_id"] = assess_rec.id
    return result


@router.get("/recommendations/{condition}")
def get_recommendations(condition: str, tier: str = "moderate"):
    """Return doctor-reviewed care guidance plan for a condition and tier."""
    try:
        return get_recommendation_plan(condition=condition, tier=tier)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/care/recommend")
def care_recommend(
    payload: CareRecommendRequest,
    db: Session = Depends(get_db),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional),
):
    user_lat = payload.lat if payload.consent_location else None
    user_lon = payload.lon if payload.consent_location else None

    cond_to_disease = {
        "heart": "heart_disease",
        "hypertension": "heart_disease",
        "diabetes": "diabetes",
        "obesity": "diabetes",
        "metabolic": "diabetes",
        "kidney": "diabetes",
        "parkinsons": "parkinsons",
        "liver_disease": "liver_disease",
    }
    resolved_disease = payload.disease or cond_to_disease.get((payload.condition or "").lower(), "heart_disease")
    raw_tier = payload.risk_level or (payload.tier.capitalize() if payload.tier else "Moderate")
    if raw_tier not in ("Low", "Moderate", "High"):
        raw_tier = "Moderate"

    result = recommend_care(
        db=db,
        disease=resolved_disease,
        risk_level=raw_tier,
        city=payload.city,
        pincode=payload.pincode,
        user_lat=user_lat,
        user_lon=user_lon,
        teleconsult_only=payload.teleconsult_only,
        language=payload.language,
    )

    hosp_ids = [h["id"] for h in result["matched_hospitals"]]
    db.add(
        RecommendationLog(
            prediction_id=payload.prediction_id,
            rule_triggered=f"{resolved_disease}:{raw_tier}",
            hospital_ids_json=json.dumps(hosp_ids),
        )
    )
    if current_user is not None:
        db.add(Consent(user_id=current_user["user_id"], consent_type="location", granted=payload.consent_location))
    db.commit()
    return result


@router.get("/hospitals")
def list_verified_hospitals(city: Optional[str] = None, db: Session = Depends(get_db)):
    if db.query(Hospital).count() == 0:
        from app.db.session import seed_care_data
        seed_care_data(db)
    q = db.query(Hospital).filter(Hospital.verified.is_(True))
    if city:
        q = q.filter(Hospital.city.ilike(f"%{city.strip()}%"))
    hospitals = q.all()
    return {
        "disclaimer": CARE_MATCHING_DISCLAIMER,
        "hospitals": [
            {
                "id": h.id,
                "name": h.name,
                "address": h.address,
                "city": h.city,
                "pincode": h.pincode,
                "lat": h.lat,
                "lon": h.lon,
                "emergency_24x7": h.emergency_24x7,
                "teleconsult": h.teleconsult,
                "phone": h.phone,
                "website": h.website,
                "verified": h.verified,
                "verified_at": h.verified_at,
                "source_url": h.source_url,
                "services": [s.name for s in h.services],
            }
            for h in hospitals
        ],
    }


@router.get("/hospitals/{hospital_id}")
def get_hospital(hospital_id: int, db: Session = Depends(get_db)):
    h = db.query(Hospital).filter(Hospital.id == hospital_id, Hospital.verified.is_(True)).first()
    if not h:
        raise HTTPException(status_code=404, detail="Verified hospital not found")
    return {
        "id": h.id,
        "name": h.name,
        "address": h.address,
        "city": h.city,
        "pincode": h.pincode,
        "lat": h.lat,
        "lon": h.lon,
        "emergency_24x7": h.emergency_24x7,
        "teleconsult": h.teleconsult,
        "insurance_notes": h.insurance_notes,
        "phone": h.phone,
        "website": h.website,
        "verified": h.verified,
        "verified_at": h.verified_at,
        "source_url": h.source_url,
        "services": [s.name for s in h.services],
        "disclaimer": CARE_MATCHING_DISCLAIMER,
    }


@router.post("/reports/pdf")
def export_pdf_report(payload: ReportPdfRequest):
    pdf_bytes = generate_assessment_pdf(payload.model_dump())
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=healthbuddy_assessment_report.pdf"},
    )


@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email.lower()).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    role = payload.role if payload.role in ("patient", "clinician") else "patient"
    user = User(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        role=role,
        language=payload.language,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(subject=user.email, role=user.role, user_id=user.id)
    return {"access_token": token, "token_type": "bearer", "role": user.role, "email": user.email}


@router.post("/auth/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(subject=user.email, role=user.role, user_id=user.id)
    return {"access_token": token, "token_type": "bearer", "role": user.role, "email": user.email}


@router.get("/history")
def get_history(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_user),
):
    q = db.query(PredictionRecord)
    if current_user.get("role") == "patient":
        q = q.filter(PredictionRecord.user_id == current_user["user_id"])
    rows = q.order_by(PredictionRecord.created_at.desc()).limit(50).all()
    return {
        "history": [
            {
                "id": r.id,
                "disease": r.disease,
                "risk_level": r.risk_level,
                "probability": r.probability,
                "model_version": r.model_version,
                "confidence_flag": r.confidence_flag,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ]
    }


@router.delete("/me/data")
def delete_my_data(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_user),
):
    uid = current_user["user_id"]
    deleted_preds = db.query(PredictionRecord).filter(PredictionRecord.user_id == uid).delete()
    deleted_consents = db.query(Consent).filter(Consent.user_id == uid).delete()
    db.add(
        AuditLog(
            actor=current_user["sub"],
            action="delete_my_data",
            entity=f"user:{uid}",
            details=f"predictions_deleted={deleted_preds}, consents_deleted={deleted_consents}",
        )
    )
    db.commit()
    return {"deleted_predictions": deleted_preds, "deleted_consents": deleted_consents}


@router.post("/clinician/feedback")
def clinician_feedback(
    payload: ClinicianFeedbackRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("clinician", "admin")),
):
    pred = db.query(PredictionRecord).filter(PredictionRecord.id == payload.prediction_id).first()
    if not pred:
        raise HTTPException(status_code=404, detail="Prediction record not found")
    db.add(
        AuditLog(
            actor=current_user["sub"],
            action="clinician_feedback",
            entity=f"prediction:{payload.prediction_id}",
            details=f"agree={payload.agree}; notes={payload.notes or ''}",
        )
    )
    db.commit()
    return {"status": "recorded", "prediction_id": payload.prediction_id, "agree": payload.agree}


@router.get("/admin/hospitals")
def admin_list_hospitals(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("admin")),
):
    hospitals = db.query(Hospital).all()
    return {
        "hospitals": [
            {
                "id": h.id,
                "name": h.name,
                "city": h.city,
                "pincode": h.pincode,
                "verified": h.verified,
                "review_status": h.review_status,
                "source_url": h.source_url,
                "verified_at": h.verified_at,
            }
            for h in hospitals
        ]
    }


@router.post("/admin/hospitals", status_code=status.HTTP_201_CREATED)
def admin_create_hospital(
    payload: HospitalCreateRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("admin")),
):
    hosp = Hospital(
        name=payload.name,
        address=payload.address,
        city=payload.city,
        pincode=payload.pincode,
        lat=payload.lat,
        lon=payload.lon,
        emergency_24x7=payload.emergency_24x7,
        insurance_notes=payload.insurance_notes,
        phone=payload.phone,
        website=payload.website,
        specialties_text=payload.specialties_text,
        languages_text=payload.languages_text,
        teleconsult=payload.teleconsult,
        source_url=payload.source_url,
        verified=False,
        review_status="submitted",
    )
    db.add(hosp)
    db.flush()
    db.add(AuditLog(actor=current_user["sub"], action="create_hospital", entity=f"hospital:{hosp.id}"))
    db.commit()
    db.refresh(hosp)
    return {"id": hosp.id, "name": hosp.name, "review_status": hosp.review_status, "verified": hosp.verified}


@router.patch("/admin/hospitals/{hospital_id}/verify")
def admin_verify_hospital(
    hospital_id: int,
    payload: HospitalVerifyRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("admin")),
):
    hosp = db.query(Hospital).filter(Hospital.id == hospital_id).first()
    if not hosp:
        raise HTTPException(status_code=404, detail="Hospital not found")
    hosp.review_status = payload.review_status
    hosp.verified = payload.verified
    if payload.verified:
        hosp.verified_by = current_user["sub"]
        hosp.verified_at = datetime.now(timezone.utc).isoformat()
    db.add(
        AuditLog(
            actor=current_user["sub"],
            action="verify_hospital",
            entity=f"hospital:{hosp.id}",
            details=f"status={payload.review_status}, verified={payload.verified}",
        )
    )
    db.commit()
    return {"id": hosp.id, "verified": hosp.verified, "review_status": hosp.review_status}


@router.delete("/admin/hospitals/{hospital_id}")
def admin_delete_hospital(
    hospital_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("admin")),
):
    hosp = db.query(Hospital).filter(Hospital.id == hospital_id).first()
    if not hosp:
        raise HTTPException(status_code=404, detail="Hospital not found")
    db.delete(hosp)
    db.add(AuditLog(actor=current_user["sub"], action="delete_hospital", entity=f"hospital:{hospital_id}"))
    db.commit()
    return {"deleted": hospital_id}


@router.get("/chat/status")
def chat_status():
    """Return ML knowledgebase status for the HealthBuddy chatbot."""
    bot = get_chatbot()
    return {
        "name": "HealthBuddy",
        "model": "TF-IDF + Cosine Similarity Knowledgebase",
        "doc_count": len(bot.documents),
        "trained_at": bot.trained_at,
    }


@router.post("/chat")
def chat_ask(payload: ChatRequest):
    """Answer user health questions using the ML-trained clinical knowledgebase and safety overrides."""
    bot = get_chatbot()
    return bot.ask(
        message=payload.message,
        lang=payload.lang,
        assessment_context=payload.assessment_context,
    )


@router.post("/chat/retrain")
def chat_retrain(current_user: Dict[str, Any] = Depends(require_role("admin"))):
    """Rebuild and persist the HealthBuddy TF-IDF knowledgebase artifact (admin only)."""
    bot = get_chatbot()
    return bot.retrain()


@router.get("/kb")
def read_knowledge_base(
    category: Optional[str] = Query(default=None, pattern="^(hospitals|doctors|guidance|care|risk_modules|faqs|foods|exercises)$"),
    q: Optional[str] = Query(default=None, max_length=120),
):
    """Return structured Knowledge Base records for hospitals, doctors, guidance, and care."""
    return get_knowledge_base(category=category, query=q)


@router.post("/kb/rebuild")
def rebuild_knowledge_base(current_user: Dict[str, Any] = Depends(require_role("admin"))):
    """Rebuild the Knowledge Base JSON record and retrain the HealthBuddy ML chatbot (admin only)."""
    record = build_knowledge_base_record(save=True)
    bot_info = get_chatbot().retrain()
    return {"kb_counts": record["counts"], "chatbot": bot_info}


