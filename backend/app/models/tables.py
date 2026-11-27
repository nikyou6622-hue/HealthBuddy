"""SQLAlchemy ORM data model for HealthBuddy v3.0."""

from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Table,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

hospital_services = Table(
    "hospital_services",
    Base.metadata,
    Column("hospital_id", Integer, ForeignKey("hospitals.id", ondelete="CASCADE"), primary_key=True),
    Column("service_id", Integer, ForeignKey("services.id", ondelete="CASCADE"), primary_key=True),
)

doctor_hospital = Table(
    "doctor_hospital",
    Base.metadata,
    Column("doctor_id", Integer, ForeignKey("doctors.id", ondelete="CASCADE"), primary_key=True),
    Column("hospital_id", Integer, ForeignKey("hospitals.id", ondelete="CASCADE"), primary_key=True),
    Column("availability_notes", String(255), nullable=True),
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String(32), nullable=False, default="patient")  # patient | clinician | admin
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    language = Column(String(16), nullable=False, default="en")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class Specialty(Base):
    __tablename__ = "specialties"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), unique=True, nullable=False)
    subspecialty = Column(String(120), nullable=True)


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), unique=True, nullable=False)


class Hospital(Base):
    __tablename__ = "hospitals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    address = Column(String(500), nullable=False)
    city = Column(String(120), nullable=False, index=True)
    pincode = Column(String(20), nullable=False, index=True)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    emergency_24x7 = Column(Boolean, default=False, nullable=False)
    insurance_notes = Column(String(500), nullable=True)
    phone = Column(String(64), nullable=True)
    website = Column(String(255), nullable=True)
    specialties_text = Column(Text, nullable=True)  # comma-separated specialties
    languages_text = Column(String(255), nullable=True)
    teleconsult = Column(Boolean, default=False, nullable=False)
    verified = Column(Boolean, default=False, nullable=False, index=True)
    verified_by = Column(String(255), nullable=True)
    verified_at = Column(String(64), nullable=True)
    source_url = Column(String(500), nullable=True)
    review_status = Column(String(32), default="submitted", nullable=False)  # submitted | reviewed | verified

    services = relationship("Service", secondary=hospital_services, lazy="joined")


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    specialty_id = Column(Integer, ForeignKey("specialties.id"), nullable=True)
    registration_no = Column(String(120), nullable=True)
    languages = Column(String(255), nullable=True)
    teleconsult = Column(Boolean, default=False, nullable=False)
    verified = Column(Boolean, default=False, nullable=False, index=True)
    verified_at = Column(String(64), nullable=True)
    source_url = Column(String(500), nullable=True)


class PredictionRecord(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    disease = Column(String(64), nullable=False, index=True)
    risk_level = Column(String(32), nullable=False)
    probability = Column(Float, nullable=True)
    model_version = Column(String(120), nullable=False)
    confidence_flag = Column(String(64), nullable=False)
    raw_inputs_json = Column(Text, nullable=True)  # Stored only with explicit consent
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)


class RecommendationLog(Base):
    __tablename__ = "recommendation_logs"

    id = Column(Integer, primary_key=True, index=True)
    prediction_id = Column(Integer, ForeignKey("predictions.id", ondelete="SET NULL"), nullable=True)
    rule_triggered = Column(String(255), nullable=False)
    hospital_ids_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class Consent(Base):
    __tablename__ = "consents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    consent_type = Column(String(64), nullable=False)  # location | data_storage
    granted = Column(Boolean, nullable=False, default=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor = Column(String(255), nullable=False)
    action = Column(String(120), nullable=False)
    entity = Column(String(120), nullable=False)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    inputs_json = Column(Text, nullable=True)
    outputs_json = Column(Text, nullable=False)
    consent_flag = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)


class FollowUp(Base):
    __tablename__ = "followups"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    condition = Column(String(64), nullable=False)
    tier = Column(String(32), nullable=False)
    due_date = Column(String(32), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class RecoFeedback(Base):
    __tablename__ = "reco_feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    item_id = Column(String(120), nullable=False, index=True)
    category = Column(String(64), nullable=False, index=True)
    helpful = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

