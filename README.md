# HealthBuddy 🩺

> **Clinical Risk Assessment & Care Guidance System for South Asian Cardiometabolic Health**
> An educational, clinical-grade decision support platform implementing deterministic calculators, machine learning risk estimations, verified healthcare care options, and doctor-reviewed guidance.

![HealthBuddy Dashboard](./healthbuddy_snapshot.jpg)

---

## 🌟 Key Highlights

- **Tailored for South Asian Phenotype**: Built around ICMR, Consensus South Asian BMI guidelines, IDRS (Dr. V. Mohan / MDRF), and WHO South Asia 10-year CVD risk charts.
- **Strict Server-Side Red-Flag Overrides**: Immediate short-circuit on acute cardiac, stroke, GI bleeding, or severe hyperglycemia symptoms to emergency tiles (112 / 108 emergency dispatch & 24/7 trauma hospitals).
- **Rule-Based & ML Segregation**: Deterministic clinical rules and ML outputs are never blended silently. Missing laboratory values return explicit `"needs_more_info"` statuses rather than inaccurate imputations.
- **Doctor-Reviewed Care Guidance**: Indian dietary guidance ("Eat more" millets/dal vs "Avoid" maida/sweets) and physical activity targets with clear medical clearance alerts.
- **Two-Page Vector PDF Export**: Generates doctor-ready medical summary reports using ReportLab.
- **Bilingual**: Full localization in English and Hindi (हिंदी) with `Intl` number and date formatting.

---

## 🛠 Tech Stack

- **Backend**: FastAPI, Python 3.10+, Pydantic v2, Scikit-Learn, ReportLab, SQLAlchemy, SQLite.
- **Frontend**: Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, Leaflet, Lucide Icons.
- **Testing**: pytest (16 unit & integration tests), Vitest (5 UI component & navigation tests).

---

## 🚀 Getting Started

### 1. Backend Setup
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Swagger API Documentation: `http://localhost:8000/docs`

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run build
npm start -- -p 3006
```
Open [http://localhost:3006](http://localhost:3006) in your browser.

### 3. Running Test Suites
```bash
# Backend unit & integration tests
cd backend && pytest -v

# Frontend component & accessibility tests
cd frontend && npm test
```

---

## 📖 Complete Master Specification

For complete mathematical derivations, clinical calculator cutoffs, database entity models, and architectural blueprints, read [HealthBuddy.md](./HealthBuddy.md).

---

## ⚖️ License & Disclaimer

HealthBuddy is an educational screening and risk stratification tool. It does not diagnose disease or prescribe medications. All results must be reviewed with a licensed healthcare provider.
