# HealthBuddy v3.0 — Project Summary

## 1. Overview
**HealthBuddy v3.0** is a safety-first, full-stack **Multi-Disease Clinical Decision Support System (CDSS)** covering **Heart Disease**, **Diabetes**, **Parkinson's Disease**, and **Liver Disease**. It combines calibrated machine learning screening, deterministic emergency red-flag overrides, verified hospital care matching, role-based authentication, bilingual UI (English & Hindi), and PDF clinical report generation.

> **Disclaimer:** HealthBuddy is intended strictly for educational, academic, and research purposes. It is not a certified medical device, does not provide a diagnosis, and must not replace advice from a qualified healthcare professional.

---

## 2. Branding & Logo
- **SVG Vector Logo:** `frontend/public/healthbuddy-logo.svg`
- **Generated Emblem:** `frontend/public/healthbuddy-logo.jpg`

---

## 3. Repository Structure

```text
heartbuddy/
├── backend/
│   ├── app/
│   │   ├── main.py                      # FastAPI application entrypoint & CORS/lifespan
│   │   ├── core/                        # Settings, clinical configs, validation, PBKDF2+JWT auth
│   │   ├── api/v1/routes.py             # All REST v1 endpoints
│   │   ├── schemas/api.py               # Pydantic request/response schemas
│   │   ├── models/tables.py             # SQLAlchemy ORM tables
│   │   ├── db/session.py                # DB initialization & care/user seeders
│   │   └── services/
│   │       ├── safety/                  # Hard-coded red-flag rules & disclaimers
│   │       ├── ml/predictor.py          # Inference, uncertainty flags, factor explanations, clinical metrics
│   │       ├── care/matcher.py          # Verified-only hospital matching, ranking & risk routing
│   │       └── reports/pdf_report.py    # ReportLab PDF assessment generator
│   ├── ml/                              # Data loader, zero-leakage preprocessing, train & evaluate
│   ├── artifacts/                       # Trained .joblib models, test sets & evaluation JSONs
│   ├── tests/
│   │   ├── unit/test_safety_and_care.py
│   │   └── integration/test_api.py
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── layout.tsx                   # Root layout & metadata
│   │   ├── globals.css                  # Tailwind & dark/light base styles
│   │   └── page.tsx                     # Full Next.js UI (Home, Wizard, Batch, Benchmarks, Care, History, Admin)
│   ├── components/
│   │   ├── banners/DisclaimerBanner.tsx
│   │   ├── charts/RiskGauge.tsx
│   │   ├── charts/ModelMetricsCard.tsx
│   │   └── map/HospitalMap.tsx          # Interactive OpenStreetMap embed
│   ├── lib/api.ts
│   ├── locales/{en.json,hi.json}        # English & Hindi translations
│   └── public/{healthbuddy-logo.svg,healthbuddy-logo.jpg}
├── dashboard/app.py                     # Legacy Streamlit clinician dashboard
├── data/
│   ├── clinical/                        # heart_disease.csv, diabetes.csv, parkinsons.csv, liver_disease.csv
│   └── care/                            # hospitals.csv, specialties.csv, services.csv
├── docs/
│   ├── MODEL_CARDS/MODEL_CARDS.md
│   ├── PRIVACY.md
│   └── VERIFICATION_PROCESS.md
├── docker-compose.yml
├── .github/workflows/ci.yml
├── .env.example
└── README.md
```

---

## 4. Key Capabilities

### Safety-First Clinical Flow
- **Red-Flag Override (`POST /api/v1/safety/check`):** Hard-coded rules for cardiac pain, stroke signs, severe GI bleeding, and hyperglycemic crisis (`glucose > 300 mg/dL` with warning signs). Triggering any rule displays a full-width emergency takeover screen with emergency numbers and nearest emergency-capable hospitals before any ML output.
- **Persistent Disclaimers:** Non-medical-device banner on every screen; care matching always carries *"These are matching options, not an endorsement or medical advice."*

### Machine Learning & Trust Features
- **Single Patient & Batch Cohort Screening:**
  - `POST /api/v1/predict/{disease}`: Risk tier (`Low`, `Moderate`, `High`), probability, confidence flag (`low_confidence` near 35–65% or out-of-range inputs), top contributing factors, and Sensitivity/Specificity/PPV/NPV/ROC-AUC metrics.
  - `POST /api/v1/predict/{disease}/batch` & `GET /api/v1/predict/{disease}/sample-cohort`: CSV batch upload or 15-patient sample cohort screening.
- **16-Classifier Benchmarks (`GET /api/v1/models/benchmarks`):** Cross-disease comparison across Logistic Regression, Decision Tree, Random Forest, and KNN.
- **Interactive What-If Simulator:** Real-time biomarker sliders on the result screen to test risk changes.

### Verified Care Matching & Privacy
- **Care Engine (`POST /api/v1/care/recommend`, `GET /api/v1/hospitals`):** Matches specialist types, suggested tests, urgency timelines, and **verified-only** hospitals with OpenStreetMap integration and transparent match reasons.
- **Auth, Consent & Data Deletion:** JWT auth (`patient`, `clinician`, `admin`), optional biomarker storage consent, `GET /api/v1/history`, `DELETE /api/v1/me/data`, `POST /api/v1/clinician/feedback`, and `CRUD /api/v1/admin/hospitals` verification workflow.
- **PDF Reports (`POST /api/v1/reports/pdf`):** Downloadable clinical screening summary.

---

## 5. Verification & Live Services
- **Backend Tests (`pytest -v`):** `8 passed in 11.57s`
- **Frontend Build (`npm run build`):** Compiled and type-checked cleanly (`exit code 0`)
- **Running URLs:**
  - **Next.js Frontend:** `http://localhost:3005`
  - **FastAPI Backend & Docs:** `http://localhost:8000` / `http://localhost:8000/docs`

