"""Database session management and idempotent seed loader for HealthBuddy v3.0."""

import csv
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings, CARE_DATA_DIR
from app.core.security import hash_password
from app.models.tables import Base, Hospital, Service, Specialty, User

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all database tables and seed initial verified care data."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_care_data(db)
        seed_default_users(db)
    finally:
        db.close()


def seed_default_users(db: Session) -> None:
    """Seed demo patient, clinician, and admin users if none exist."""
    if db.query(User).count() > 0:
        return
    demo_users = [
        User(email="patient@healthbuddy.local", role="patient", password_hash=hash_password("Patient123!"), language="en"),
        User(email="clinician@healthbuddy.local", role="clinician", password_hash=hash_password("Clinician123!"), language="en"),
        User(email="admin@healthbuddy.local", role="admin", password_hash=hash_password("Admin123!"), language="en"),
    ]
    db.add_all(demo_users)
    db.commit()


def seed_care_data(db: Session) -> None:
    """Seed specialties, services, and verified hospitals from CSVs."""
    spec_csv = CARE_DATA_DIR / "specialties.csv"
    if spec_csv.exists() and db.query(Specialty).count() == 0:
        with open(spec_csv, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                db.add(Specialty(name=row["name"].strip(), subspecialty=row.get("subspecialty", "").strip()))
        db.commit()

    svc_csv = CARE_DATA_DIR / "services.csv"
    svc_map = {s.name: s for s in db.query(Service).all()}
    if svc_csv.exists() and not svc_map:
        with open(svc_csv, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                s = Service(name=row["name"].strip())
                db.add(s)
                svc_map[s.name] = s
        db.commit()
        svc_map = {s.name: s for s in db.query(Service).all()}

    hosp_csv = CARE_DATA_DIR / "hospitals.csv"
    if hosp_csv.exists() and db.query(Hospital).count() == 0:
        with open(hosp_csv, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                is_verified = row.get("verified", "false").strip().lower() == "true"
                hosp = Hospital(
                    name=row["name"].strip(),
                    address=row["address"].strip(),
                    city=row["city"].strip(),
                    pincode=row["pincode"].strip(),
                    lat=float(row["lat"]) if row.get("lat") else None,
                    lon=float(row["lon"]) if row.get("lon") else None,
                    emergency_24x7=row.get("emergency_24x7", "false").strip().lower() == "true",
                    insurance_notes=row.get("insurance_notes", "").strip(),
                    phone=row.get("phone", "").strip(),
                    website=row.get("website", "").strip(),
                    specialties_text=row.get("specialties", "").strip(),
                    languages_text=row.get("languages", "").strip(),
                    teleconsult=row.get("teleconsult", "false").strip().lower() == "true",
                    verified=is_verified,
                    verified_by=row.get("verified_by", "").strip() or None,
                    verified_at=row.get("verified_at", "").strip() or None,
                    source_url=row.get("source_url", "").strip() or None,
                    review_status="verified" if is_verified else "submitted",
                )
                for svc_name in [s.strip() for s in row.get("services", "").split(",") if s.strip()]:
                    if svc_name not in svc_map:
                        new_svc = Service(name=svc_name)
                        db.add(new_svc)
                        db.flush()
                        svc_map[svc_name] = new_svc
                    hosp.services.append(svc_map[svc_name])
                db.add(hosp)
        db.commit()

