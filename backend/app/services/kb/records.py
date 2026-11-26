"""Structured Knowledge Base record builder for hospitals, doctors, risk modules, guidance, FAQs, and care."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.config import ARTIFACTS_DIR, BACKEND_DIR, CARE_DATA_DIR, REPO_ROOT

CONTENT_DIR = BACKEND_DIR / "app" / "services" / "recommend" / "content"
FRONTEND_PLANS_EN = REPO_ROOT / "frontend" / "data" / "plans.en.json"
KNOWLEDGE_BASE_JSON_PATH = ARTIFACTS_DIR / "knowledge_base.json"

SPECIALTY_CONDITIONS: Dict[str, List[str]] = {
    "Cardiologist": ["Heart Disease", "Hypertension", "Metabolic Syndrome"],
    "Interventional Cardiologist": ["Acute Coronary Care", "High-Risk Heart Disease"],
    "Preventive Cardiologist": ["Cholesterol / Lipids", "Heart Disease Prevention", "Hypertension"],
    "Endocrinologist": ["Diabetes", "Prediabetes", "Metabolic Syndrome", "Obesity"],
    "Diabetologist": ["Diabetes", "Prediabetes"],
    "Neurologist": ["Parkinson's Disease", "Stroke Red-Flag Evaluation"],
    "Hepatologist": ["Liver Disease", "Fatty Liver / Fibrosis"],
    "Gastroenterologist": ["Liver Disease", "GI Bleeding Evaluation"],
    "Nephrologist": ["Kidney Health (CKD)", "Proteinuria / Albuminuria", "Resistant Hypertension"],
    "General Physician": ["Primary Risk Assessment", "Diabetes", "Hypertension", "Preventive Screening"],
    "Clinical Dietitian": ["Indian Medical Nutrition", "Diabetes Diet", "DASH Low-Sodium Diet", "Weight Management"],
    "Physiotherapist": ["Cardiac Rehabilitation", "Safe Exercise Progression", "Obesity Mobility"],
    "Pulmonologist": ["Tobacco Cessation", "Sleep Apnea", "Breathlessness Evaluation"],
    "Ophthalmologist": ["Diabetic Retinopathy Screening", "Hypertensive Retinopathy"],
    "Psychiatrist": ["Stress & Sleep Health", "Chronic Illness Adherence"],
    "Bariatric & Metabolic Specialist": ["Severe Obesity", "Metabolic Syndrome"],
    "Emergency Medicine": ["Chest Pain", "FAST Stroke", "Hypertensive Crisis", "Hyperglycemic Crisis"],
    "Yoga Therapist": ["Stress Reduction", "Blood Pressure & Glycemic Support"],
}

RISK_MODULE_KNOWLEDGE: List[Dict[str, Any]] = [
    {
        "id": "heart_who_cvd",
        "condition_key": "heart",
        "title": "Heart Disease (WHO South Asia 10-Year CVD Risk)",
        "methodology": "Continuous South-Asia-calibrated 10-year cardiovascular & stroke risk model (ages 40–74) using lab-based total cholesterol or non-lab BMI.",
        "why_it_matters": "South Asians experience coronary artery disease and stroke roughly 5–10 years earlier than global averages, often with modest LDL cholesterol.",
        "thresholds": {
            "low": "< 10% 10-year CVD risk",
            "moderate": "10% – 19.9% 10-year CVD risk",
            "high": ">= 20% 10-year CVD risk",
            "skipped": "Outside ages 40–74 (displays modifiable risk-factor count instead of guessed %)",
        },
        "modifiable_drivers": ["Systolic blood pressure", "Tobacco / smoking", "Total cholesterol", "Glycemic control (diabetes)", "BMI / waist circumference"],
        "recommended_tests": ["Fasting Lipid Profile (Total Chol, LDL, HDL, TG)", "12-lead ECG", "HbA1c / Fasting Glucose"],
        "red_flags": ["Chest pain/pressure radiating to arm or jaw", "Sudden shortness of breath", "FAST stroke signs (Face, Arm, Speech)"],
    },
    {
        "id": "obesity_anthropometry",
        "condition_key": "obesity",
        "title": "BMI & Central Obesity (Indian Consensus Cutoffs)",
        "methodology": "Indian Consensus BMI (<18.5 underweight, 18.5–22.9 normal, 23.0–24.9 overweight, >=25.0 obese) paired with waist circumference (>=90 cm men, >=80 cm women).",
        "why_it_matters": "Indians accumulate higher visceral/abdominal fat at lower BMI ('thin-fat' phenotype), driving insulin resistance even when BMI looks borderline.",
        "thresholds": {
            "low": "BMI 18.5–22.9 kg/m² AND waist <90 cm (M) / <80 cm (F)",
            "moderate": "BMI 23.0–24.9 kg/m² (overweight) without central obesity",
            "high": "BMI >= 25.0 kg/m² (obese) OR central obesity (waist >=90 cm M / >=80 cm F)",
            "skipped": "Requires positive height and weight",
        },
        "modifiable_drivers": ["Refined carbs & added sugars", "Sedentary sitting time", "Waist-to-height ratio", "Sleep duration"],
        "recommended_tests": ["Fasting Glucose / HbA1c", "Fasting Lipid Profile", "Liver ultrasound / ALT if central obesity present"],
        "red_flags": ["Rapid unexplained weight gain with leg swelling or breathlessness (possible fluid retention)"],
    },
    {
        "id": "metabolic_syndrome",
        "condition_key": "metabolic",
        "title": "Metabolic Syndrome (Harmonized South Asian Criteria)",
        "methodology": "Counts 5 cardiometabolic criteria: elevated waist (>=90M/80F), BP >=130/85, FPG >=100 mg/dL, Triglycerides >=150 mg/dL, low HDL (<40M/50F).",
        "why_it_matters": "Meeting >=3 of 5 criteria doubles 10-year cardiovascular risk and strongly predicts type 2 diabetes and fatty liver (MASLD).",
        "thresholds": {
            "low": "0–1 of 5 criteria met",
            "moderate": "2 of 5 criteria met",
            "high": ">= 3 of 5 criteria met",
            "skipped": "Skipped when fasting glucose, triglycerides, and HDL are all missing (never guessed)",
        },
        "modifiable_drivers": ["Triglycerides (cut sugar, alcohol, refined flour)", "Low HDL (brisk aerobic exercise)", "Abdominal waist", "Fasting glucose & BP"],
        "recommended_tests": ["Fasting Plasma Glucose", "Fasting Triglycerides & HDL", "SGOT/SGPT (Liver enzymes)"],
        "red_flags": ["Co-existing chest discomfort, severe fatigue, or persistent hypertension >=180/120"],
    },
    {
        "id": "diabetes_idrs",
        "condition_key": "diabetes",
        "title": "Diabetes Risk (MDRF Indian Diabetes Risk Score)",
        "methodology": "Validated Indian screening score (0–100) combining age, waist circumference, physical activity, and parental diabetes history.",
        "why_it_matters": "Over 50% of Indians with early type 2 diabetes are asymptomatic; IDRS identifies high-risk individuals before complications begin.",
        "thresholds": {
            "low": "Score < 30",
            "moderate": "Score 30 – 59",
            "high": "Score >= 60 (high probability of undiagnosed dysglycemia)",
            "skipped": "Requires waist measurement",
        },
        "modifiable_drivers": ["Daily physical activity (30–45 min brisk walking)", "Waist reduction (5–7% weight loss)", "Whole-grain / millet meal timing"],
        "recommended_tests": ["HbA1c", "Fasting Plasma Glucose (FPG)", "2-hour OGTT if borderline"],
        "red_flags": ["Extreme thirst/urination with nausea, confusion, or glucose >400 / <54 mg/dL"],
    },
    {
        "id": "hypertension_bp",
        "condition_key": "hypertension",
        "title": "Blood Pressure (ACC/AHA & Indian Hypertension Staging)",
        "methodology": "Stages systolic/diastolic BP into Normal (<120/80), Elevated (120–129/<80), Stage 1 (130–139 or 80–89), Stage 2 (>=140 or >=90), Crisis (>=180 or >=120).",
        "why_it_matters": "High blood pressure is the #1 modifiable driver of stroke, heart failure, and chronic kidney disease in India.",
        "thresholds": {
            "low": "Normal (<120 / <80 mmHg)",
            "moderate": "Elevated (120–129/<80) or Stage 1 (130–139 / 80–89 mmHg)",
            "high": "Stage 2 (>=140 / >=90 mmHg) or Hypertensive Crisis (>=180 / >=120 mmHg)",
            "skipped": "Requires positive systolic and diastolic BP",
        },
        "modifiable_drivers": ["Dietary sodium (<5 g salt/day; cut pickles & papad)", "Potassium-rich vegetables", "Weight & stress", "Medication adherence"],
        "recommended_tests": ["Home BP log (morning & evening for 7 days)", "Serum Creatinine + Urine ACR", "12-lead ECG"],
        "red_flags": ["BP >=180/120 with headache, vision changes, chest pain, or weakness -> Call 112/108"],
    },
    {
        "id": "kidney_ckd_epi",
        "condition_key": "kidney",
        "title": "Kidney Health (CKD-EPI 2021 Race-Free eGFR + Urine ACR)",
        "methodology": "KDIGO-aligned CKD-EPI 2021 race-free filtration equation (G1 >=90 to G5 <15 mL/min/1.73m²) combined with Urine ACR albuminuria staging (A1–A3).",
        "why_it_matters": "Diabetic and hypertensive kidney damage is silent until advanced; catching eGFR <60 or ACR >=30 early allows kidney-protective therapy.",
        "thresholds": {
            "low": "eGFR >= 60 mL/min/1.73m² AND Urine ACR < 30 mg/g (if tested)",
            "moderate": "eGFR 45–59 (G3a) OR Urine ACR 30–300 mg/g (A2)",
            "high": "eGFR < 45 (G3b–G5) OR Urine ACR > 300 mg/g (A3)",
            "skipped": "Requires serum creatinine lab value (never guessed)",
        },
        "modifiable_drivers": ["Strict BP control (<130/80)", "Glycemic control (HbA1c)", "Avoiding unnecessary NSAID painkillers", "Hydration"],
        "recommended_tests": ["Serum Creatinine (eGFR)", "Spot Urine Albumin-to-Creatinine Ratio (ACR)", "Serum Electrolytes (K+)"],
        "red_flags": ["Sudden drop in urine output, severe leg/facial swelling, or breathlessness"],
    },
]

CARE_ROUTING_LEVELS = [
    {
        "id": "care_emergency",
        "name": "Immediate Emergency Override",
        "urgency": "immediate",
        "description": "Triggered by chest pain, stroke signs (FAST), severe GI bleeding, or hyperglycemic crisis. Bypasses ML scores and routes to 24x7 emergency care (112 / 108).",
        "category": "care_routing",
    },
    {
        "id": "care_urgent",
        "name": "Urgent Specialist Review (24–72 hours)",
        "urgency": "24_72_hours",
        "description": "Recommended for High risk tier modules (e.g., Stage 2 hypertension, high WHO CVD risk, or high IDRS with elevated HbA1c).",
        "category": "care_routing",
    },
    {
        "id": "care_moderate",
        "name": "Scheduled OPD Consultation (2–4 weeks)",
        "urgency": "within_2_weeks",
        "description": "Recommended for Moderate risk tier modules with lifestyle, diet, and confirmatory lab work.",
        "category": "care_routing",
    },
    {
        "id": "care_routine",
        "name": "Preventive Primary Care (6–12 months)",
        "urgency": "routine",
        "description": "Recommended for Low risk tier modules to maintain healthy biomarkers and annual screening.",
        "category": "care_routing",
    },
]


def _load_frontend_plans() -> Dict[str, Any]:
    if FRONTEND_PLANS_EN.exists():
        try:
            with open(FRONTEND_PLANS_EN, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def build_knowledge_base_record(save: bool = True) -> Dict[str, Any]:
    """Build and optionally persist the unified HealthBuddy Knowledge Base JSON record."""
    hospitals: List[Dict[str, Any]] = []
    hosp_csv = CARE_DATA_DIR / "hospitals.csv"
    if hosp_csv.exists():
        with open(hosp_csv, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if str(row.get("verified", "")).lower() != "true":
                    continue
                spec_raw = row.get("specialties") or row.get("specialties_text") or ""
                serv_raw = row.get("services") or row.get("facilities_text") or ""
                lang_raw = row.get("languages") or row.get("languages_text") or ""
                hospitals.append(
                    {
                        "id": row.get("id", ""),
                        "name": row.get("name", ""),
                        "address": row.get("address", ""),
                        "city": row.get("city", ""),
                        "pincode": row.get("pincode", ""),
                        "phone": row.get("phone", ""),
                        "website": row.get("website", ""),
                        "emergency_24x7": str(row.get("emergency_24x7", "")).lower() == "true",
                        "teleconsult": str(row.get("teleconsult", "")).lower() == "true",
                        "insurance_notes": row.get("insurance_notes", ""),
                        "specialties": [s.strip() for s in spec_raw.split(",") if s.strip()],
                        "facilities": [s.strip() for s in serv_raw.split(",") if s.strip()],
                        "languages": [s.strip() for s in lang_raw.split(",") if s.strip()],
                        "verified": True,
                    }
                )

    doctors: List[Dict[str, Any]] = []
    spec_csv = CARE_DATA_DIR / "specialties.csv"
    if spec_csv.exists():
        with open(spec_csv, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                name = (row.get("name") or "").strip()
                matched_hospitals = [
                    h["name"] for h in hospitals if any(name.lower() == s.lower() for s in h["specialties"])
                ]
                doctors.append(
                    {
                        "id": row.get("id", ""),
                        "name": name,
                        "subspecialty": (row.get("subspecialty") or "").strip(),
                        "conditions_covered": SPECIALTY_CONDITIONS.get(name, ["General Clinical Care"]),
                        "available_at_hospitals": matched_hospitals,
                    }
                )

    guidance: List[Dict[str, Any]] = []
    frontend_plans = _load_frontend_plans()
    if CONTENT_DIR.exists():
        for path in sorted(CONTENT_DIR.glob("*.json")):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            cond = data.get("condition", path.stem)
            title = data.get("title", cond.title())
            source = data.get("source", "Clinical Guidelines")
            reviewer = data.get("reviewed_by", "Clinical Review Board")
            fe_cond = frontend_plans.get(cond, {})
            for tier_name, tier_data in data.get("tiers", {}).items():
                fe_tier = fe_cond.get(tier_name, {})
                guidance.append(
                    {
                        "id": f"{cond}_{tier_name}",
                        "condition": cond,
                        "title": title,
                        "tier": tier_name,
                        "eat_more": fe_tier.get("eat_more", []),
                        "avoid": fe_tier.get("avoid", []),
                        "food_notes": tier_data.get("food", []),
                        "exercise_target": fe_tier.get("exercise_target", ""),
                        "exercise": tier_data.get("exercise", []),
                        "doctor_tests": tier_data.get("doctor_tests", []),
                        "hospital_guidance": tier_data.get("hospital_guidance", ""),
                        "followup_days": tier_data.get("followup_days", 30),
                        "source": source,
                        "reviewer": reviewer,
                    }
                )

    care: List[Dict[str, Any]] = list(CARE_ROUTING_LEVELS)
    serv_csv = CARE_DATA_DIR / "services.csv"
    if serv_csv.exists():
        with open(serv_csv, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                sname = (row.get("name") or "").strip()
                matched_hospitals = [
                    h["name"] for h in hospitals if any(sname.lower() == fac.lower() for fac in h["facilities"])
                ]
                care.append(
                    {
                        "id": f"service_{row.get('id', sname)}",
                        "name": sname,
                        "category": "clinical_service",
                        "description": f"Verified hospital facility/service: {sname}.",
                        "available_at_hospitals": matched_hospitals,
                    }
                )

    faqs: List[Dict[str, Any]] = []
    faq_csv = CARE_DATA_DIR / "kb_faqs.csv"
    if faq_csv.exists():
        with open(faq_csv, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                faqs.append(
                    {
                        "id": (row.get("id") or "").strip(),
                        "category": (row.get("category") or "guidance").strip(),
                        "title": (row.get("title") or "").strip(),
                        "summary": (row.get("summary") or "").strip(),
                        "answer": (row.get("answer") or "").strip(),
                        "tags": [t.strip() for t in (row.get("tags") or "").split(",") if t.strip()],
                    }
                )

    risk_modules = list(RISK_MODULE_KNOWLEDGE)

    record = {
        "name": "HealthBuddy Clinical Knowledge Base",
        "version": "3.1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "counts": {
            "hospitals": len(hospitals),
            "doctors": len(doctors),
            "guidance": len(guidance),
            "care": len(care),
            "risk_modules": len(risk_modules),
            "faqs": len(faqs),
            "total": len(hospitals) + len(doctors) + len(guidance) + len(care) + len(risk_modules) + len(faqs),
        },
        "hospitals": hospitals,
        "doctors": doctors,
        "guidance": guidance,
        "care": care,
        "risk_modules": risk_modules,
        "faqs": faqs,
    }

    if save:
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        with open(KNOWLEDGE_BASE_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2, ensure_ascii=False)

    return record


def get_knowledge_base(category: Optional[str] = None, query: Optional[str] = None) -> Dict[str, Any]:
    """Load the persisted Knowledge Base record (building if missing) and optionally filter."""
    record: Optional[Dict[str, Any]] = None
    if KNOWLEDGE_BASE_JSON_PATH.exists():
        try:
            with open(KNOWLEDGE_BASE_JSON_PATH, "r", encoding="utf-8") as f:
                record = json.load(f)
        except Exception:
            record = None

    if record is None or "risk_modules" not in record or "faqs" not in record:
        record = build_knowledge_base_record(save=True)

    q = (query or "").strip().lower()
    categories = ["hospitals", "doctors", "guidance", "care", "risk_modules", "faqs"]
    selected_cats = [category] if category in categories else categories

    filtered: Dict[str, List[Dict[str, Any]]] = {}
    for cat in categories:
        items = record.get(cat, []) if cat in selected_cats else []
        if q and items:
            items = [item for item in items if q in json.dumps(item, ensure_ascii=False).lower()]
        filtered[cat] = items

    return {
        "name": record.get("name"),
        "version": record.get("version"),
        "generated_at": record.get("generated_at"),
        "counts": {
            **{cat: len(filtered[cat]) for cat in categories},
            "total": sum(len(v) for v in filtered.values()),
        },
        **filtered,
    }
