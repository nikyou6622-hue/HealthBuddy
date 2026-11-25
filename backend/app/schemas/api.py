"""Pydantic request and response schemas for HealthBuddy v3.0 API."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=6, max_length=128)
    role: str = Field(default="patient")
    language: str = Field(default="en")


class LoginRequest(BaseModel):
    email: str
    password: str


class PredictRequest(BaseModel):
    features: Dict[str, Any]
    consent_data_storage: bool = False


class CareRecommendRequest(BaseModel):
    disease: Optional[str] = None
    risk_level: Optional[str] = Field(default=None, pattern="^(Low|Moderate|High)$")
    condition: Optional[str] = None
    tier: Optional[str] = Field(default=None, pattern="^(low|moderate|high|Low|Moderate|High)$")
    city: Optional[str] = None
    pincode: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    consent_location: bool = False
    teleconsult_only: bool = False
    language: Optional[str] = None
    prediction_id: Optional[int] = None


class AssessRequest(BaseModel):
    # Step 1: Basics & Safety
    age: int = Field(..., ge=1, le=120)
    sex: str = Field(..., pattern="^(male|female|other|m|f)$")
    height_cm: float = Field(..., ge=50, le=250)
    weight_kg: float = Field(..., ge=15, le=300)
    waist_cm: float = Field(..., ge=30, le=220)
    systolic_bp: float = Field(..., ge=60, le=260)
    diastolic_bp: float = Field(..., ge=30, le=180)
    resting_hr: Optional[int] = Field(default=None, ge=30, le=220)
    city: Optional[str] = None
    pincode: Optional[str] = None

    # Step 2: Lifestyle
    smoker: bool = False
    alcohol_drinks_per_week: float = Field(default=0.0, ge=0.0, le=100.0)
    physical_activity: str = Field(..., pattern="^(vigorous|moderate|mild|sedentary)$")
    sitting_hours: Optional[float] = Field(default=None, ge=0.0, le=24.0)
    sleep_hours: Optional[float] = Field(default=None, ge=0.0, le=24.0)
    family_diabetes: str = Field(..., pattern="^(none|one_parent|both)$")
    family_heart_disease: bool = False
    region: str = Field(default="IN")

    # Step 3: Optional Labs
    hba1c: Optional[float] = Field(default=None, ge=2.0, le=200.0)
    fpg: Optional[float] = Field(default=None, ge=20.0, le=1000.0)
    ogtt_2h: Optional[float] = Field(default=None, ge=20.0, le=1000.0)
    total_cholesterol: Optional[float] = Field(default=None, ge=50.0, le=800.0)
    ldl: Optional[float] = Field(default=None, ge=10.0, le=500.0)
    triglycerides: Optional[float] = Field(default=None, ge=20.0, le=2000.0)
    hdl: Optional[float] = Field(default=None, ge=10.0, le=150.0)
    serum_creatinine: Optional[float] = Field(default=None, ge=0.1, le=20.0)
    urine_acr: Optional[float] = Field(default=None, ge=0.0, le=5000.0)

    # Safety, ML & Consent
    red_flags: Optional[Dict[str, Any]] = None
    ml_disease: Optional[str] = "heart_disease"
    ml_features: Optional[Dict[str, Any]] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    consent_location: bool = False
    consent_data_storage: bool = False


class HospitalCreateRequest(BaseModel):
    name: str
    address: str
    city: str
    pincode: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    emergency_24x7: bool = False
    insurance_notes: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    specialties_text: Optional[str] = None
    languages_text: Optional[str] = "English"
    teleconsult: bool = False
    source_url: str


class HospitalVerifyRequest(BaseModel):
    review_status: str = Field(..., pattern="^(submitted|reviewed|verified)$")
    verified: bool


class ClinicianFeedbackRequest(BaseModel):
    prediction_id: int
    agree: bool
    notes: Optional[str] = None


class ReportPdfRequest(BaseModel):
    disease: str = "heart_disease"
    disease_name: Optional[str] = None
    risk_level: str = "Moderate"
    label: str = "Assessment Summary"
    probability: Optional[float] = None
    confidence_flag: str = "high_confidence"
    model_version: str = "v3.0"
    top_factors: List[Dict[str, Any]] = []
    specialist_types: List[str] = []
    matched_hospitals: List[Dict[str, Any]] = []
    modules: List[Dict[str, Any]] = []
    plan: Optional[Dict[str, Any]] = None
    followups: List[Dict[str, Any]] = []

