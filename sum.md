# HealthBuddy v3.0 — Project Report (Easy Guide)

## 1. What Is HealthBuddy?
**HealthBuddy** is a bilingual (English + Hindi) health screening and guidance web app built for Indian users.  
It helps a person understand their health risks in plain language, see what to eat and how to exercise safely, and find verified Indian hospitals and specialists nearby — without ever claiming to replace a doctor.

### Core Safety Promise
- **Emergency First:** If someone reports chest pain, stroke signs (face drooping, arm weakness, speech trouble), severe breathlessness, or extreme blood sugar, HealthBuddy immediately stops normal scoring and tells them to call **112 / 108** right away.
- **No Guessing Missing Labs:** If you don't have blood test results (like creatinine, HbA1c, or triglycerides), those checks are cleanly marked **Skipped (`—`)** with an **Add lab values** button. It never invents numbers.
- **Educational Only:** A clear medical disclaimer stays visible at the top of the app at all times.

---

## 2. How the App Works (User Flow)

1. **New Assessment (3-Step Wizard):**
   - **Step 1 — Basics & Safety:** Emergency red-flag checklist first, followed by age, sex, height, weight, waist, blood pressure, and city/pincode.
   - **Step 2 — Lifestyle:** Physical activity level, smoking, alcohol, sleep, sitting hours, and family history of diabetes or heart disease.
   - **Step 3 — Optional Lab Reports:** Enter fasting glucose, HbA1c, cholesterol, triglycerides, creatinine, or urine ACR — or click any of the **5 built-in Sample Lab Presets** to test different patient profiles in one click.

2. **Health Snapshot Dashboard:**
   - **Summary Header:** Shows how many checks were completed (e.g., `5/6 checks done`), overall status, last assessed date, and a **Re-check my health** button.
   - **Your Next Steps:** Gives up to 3 clear, prioritized actions.
   - **Risk & Biomarker Breakdown (`#sec-risk`):** 6 color-and-icon-coded cards sorted with urgent items first, plus a **Clinical Risk Knowledge Base** panel explaining how each score works.
   - **Health Trends:** Line chart tracking blood pressure and BMI over time when saved history exists.
   - **Guidance & Follow-Up (`#sec-guidance`):** Automatically focuses on your highest-risk condition from the lab report, with 4 tabs:
     - **Food:** Eat more / Avoid lists + searchable **Indian Food Guide (291 foods)** in English & Hindi tailored to your condition (`OK`, `Watch`, `Limit`, `Avoid`, `Ask Dietitian`).
     - **Exercise:** Recommended weekly targets + searchable **Exercise & Yoga Library (55 routines)** with high-risk safety sorting and medical clearance flags.
     - **Doctor & Lab Tests (KB):** Specific lab tests to discuss with your doctor and clinical FAQs.
     - **Follow-Up:** Recommended re-check dates.
   - **Care & Verified Hospitals (`#sec-care`):** Interactive map + list of matched verified hospitals (with city search, **24x7 Emergency** / **Government** / **Private** filters, phone numbers, insurance schemes like PMJAY/CGHS, and teleconsultation info), plus a Specialist Directory and Hospital Services guide.
   - **Secondary ML Screening (`#sec-ml`):** Optional, clearly labeled non-diagnostic ML screening (Parkinson's voice metrics, Liver lab panel) with confidence flags and model performance metrics.

3. **Other Built-In Views:**
   - **Knowledge Base:** Searchable directory of all **514 clinical records** across hospitals, doctors, foods, exercises, guidance, and care services.
   - **My Plan / History / Reports / Settings:** Full condition diet/exercise plans, login & saved assessment history, printable clinical summary + **Download PDF**, and Dark Mode / Hindi-English language toggle.
   - **Ask HealthBuddy Chatbot:** Floating AI assistant drawer (also works as a full-width bottom sheet on mobile phones).

---

## 3. The 6 Health Risk Checks

| Check | Method Used | What It Tells You |
|---|---|---|
| **Heart Disease** | WHO South Asia 10-Year CVD Risk (lab & non-lab) | Continuous 10-year heart & stroke risk % for ages 40–74 (`<10%` Low, `10–19.9%` Moderate, `>=20%` High). Outside 40–74, shows risk-factor count instead of guessing. |
| **Diabetes Risk (IDRS)** | MDRF Indian Diabetes Risk Score (`0–100`) | Screening risk from age, waist size, exercise, and family history (`<30` Low, `30–59` Moderate, `>=60` High). |
| **Blood Pressure** | ACC/AHA & Indian Hypertension Guidelines | Classifies BP into Normal, Elevated, Stage 1, Stage 2, or Hypertensive Crisis. |
| **BMI (Indian)** | Indian Consensus Cutoffs + Waist | Uses stricter South Asian thresholds (`>=23` Overweight, `>=25` Obese) plus central obesity waist cutoffs (`>=90 cm` men, `>=80 cm` women). |
| **Metabolic Syndrome** | Harmonized South Asian Criteria (`0–5`) | Counts how many of 5 risk markers (waist, BP, fasting sugar, triglycerides, low HDL) are elevated. Skipped if labs are missing. |
| **Kidney Health** | CKD-EPI 2021 (Race-Free eGFR + Urine ACR) | Estimates kidney filtration rate (`G1–G5`) and urine protein (`A1–A3`). Skipped if creatinine is missing. |

---

## 4. Deep Knowledge Base (**514 Total Records**)

| Category | Count | Source File |
|---|---|---|
| **Indian Foods (English + Hindi)** | 291 | `data/care/foods.csv` |
| **Verified Indian Hospitals** | 60 | `data/care/hospitals.csv` |
| **Exercises, Yoga & Pranayama** | 55 | `data/care/exercises.csv` |
| **Care Services & Routing Levels** | 39 | `data/care/services.csv` + `records.py` |
| **Clinical FAQs** | 27 | `data/care/kb_faqs.csv` |
| **Doctor Specialties** | 18 | `data/care/specialties.csv` |
| **Condition Guidance Plans** | 18 | `backend/app/services/recommend/content/*.json` |
| **Risk Module Deep Guides** | 6 | `backend/app/services/kb/records.py` |
| **Total** | **514** | Persisted in `backend/artifacts/knowledge_base.json` |

---

## 5. Where Machine Learning Is Used (Exact Places in the App & Code)

HealthBuddy uses Machine Learning in **two main places**, while keeping the 6 primary health scores strictly rule-based and medical-guideline-driven:

| Feature / UI Location | ML Concept Used | Exact Backend File | What It Does in Simple Words |
|---|---|---|---|
| **Secondary ML Screening (`#sec-ml` card on Dashboard)** | `LogisticRegression` (Heart, Diabetes, Liver) & `RandomForestClassifier` (Parkinson's) | `backend/app/services/ml/predictor.py` + `backend/ml/train.py` | Runs optional secondary risk screening when specialized lab/voice features are provided, and returns a risk band instead of a diagnosis. |
| **Model Training & Preprocessing** | `ColumnTransformer`, `SimpleImputer` (median), `StandardScaler`, `StratifiedKFold` CV | `backend/ml/preprocessing.py` + `backend/ml/train.py` | Cleans missing values, scales numbers, and benchmarks 4 models (`LogisticRegression`, `RandomForest`, `DecisionTree`, `KNN`) without data leakage. |
| **"Why?" Top Factors & Confidence Flag (`#sec-ml`)** | Feature weights (`feature_importances_` / `coef_`), uncertainty bounds (`0.35–0.65`) | `backend/app/services/ml/predictor.py` | Explains the top 5 reasons behind an ML score in plain English and warns `low_confidence` if inputs are out of range or borderline. |
| **Model Performance Table (`#sec-ml`)** | Confusion matrix metrics (Sensitivity, Specificity, PPV, NPV, ROC-AUC, F1) | `backend/app/services/ml/predictor.py` + `backend/ml/evaluate.py` | Shows how accurate and reliable each trained ML model was on test data. |
| **Ask HealthBuddy AI Chatbot (Floating chat button & drawer)** | `TfidfVectorizer` (1–2 word n-grams) + **Cosine Similarity** | `backend/app/services/chatbot/knowledge_bot.py` | Searches **558 clinical documents** (foods, exercises, hospitals, risk guides, FAQs) to answer questions in English or Hindi, personalized to your risk tiers. |
| **6 Primary Risk Cards (`#sec-risk`: Heart, Diabetes IDRS, BP, BMI, Metabolic, Kidney)** | **No ML** (Deterministic clinical formulas & Indian guidelines) | `backend/app/services/calculators/*.py` | Uses trusted medical equations (WHO CVD chart, MDRF IDRS, CKD-EPI 2021, Indian BMI) so missing labs are safely marked **Skipped (`—`)** rather than guessed. |

---

## 6. Tech Stack & Deployment

- **Frontend:** Next.js 14 (React + TypeScript + Tailwind CSS), Lucide icons, responsive desktop sidebar + mobile bottom tab bar + bottom-sheet chat, bilingual `en.json` / `hi.json`, Light & Dark themes.
- **Backend:** FastAPI (Python 3.12), SQLAlchemy + SQLite (`healthbuddy.db`, `/tmp/healthbuddy.db` on Vercel), `scikit-learn`, `joblib`, ReportLab PDF generator.
- **Deployment Ready:** Configured in `vercel.json` as a multi-service Vercel project (`frontend` + `backend` with `/api/(.*)` rewrites and `BACKEND_URL` service binding) and hosted on GitHub at `nikyou6622-hue/HealthBuddy`.

---

## 7. Current Verification Status
- **Backend Tests (`pytest -v`):** **63 / 63 passed** (calculators, monotonicity invariants, API endpoints, safety red-flags, KB counts).
- **Frontend Checks (`npx tsc --noEmit && npm test`):** **6 / 6 passed** (zero TypeScript errors, component & accessibility tests passing).

