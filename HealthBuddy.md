# HealthBuddy: Comprehensive Master Clinical, Architecture, and Engineering Specification

> **Regulatory & Clinical Safety Notice**
> HealthBuddy is an educational risk assessment and clinical decision-support screening platform. It is **not** an FDA/CE-cleared or CDSCO-cleared medical device, does not diagnose pathology, and does not prescribe medical therapeutics. All risk classifications represent population-level probability bands derived from peer-reviewed clinical guidelines (WHO, ICMR, KDIGO, ACC/AHA) and must be reviewed by a licensed healthcare professional.

---

## Table of Contents
1. [System Overview & Healthcare Objectives](#1-system-overview--healthcare-objectives)
2. [Clinical Safety Principles & Non-Negotiable Rules](#2-clinical-safety-principles--non-negotiable-rules)
3. [Full Architecture & Data Flow Diagram](#3-full-architecture--data-flow-diagram)
4. [Exhaustive Mathematical & Clinical Calculator Specifications](#4-exhaustive-mathematical--clinical-calculator-specifications)
   - 4.1 [South Asian Anthropometry (BMI)](#41-south-asian-anthropometry-bmi)
   - 4.2 [Blood Pressure Staging (JNC7 / ACC / AHA)](#42-blood-pressure-staging-jnc7--acc--aha)
   - 4.3 [Glycemic Classification & IFCC/NGSP Conversion](#43-glycemic-classification--ifccngsp-conversion)
   - 4.4 [Indian Diabetes Risk Score (IDRS)](#44-indian-diabetes-risk-score-idrs)
   - 4.5 [WHO South Asia 10-Year Cardiovascular Disease Risk](#45-who-south-asia-10-year-cardiovascular-disease-risk)
   - 4.6 [CKD-EPI 2021 Race-Free eGFR & Urine ACR Staging](#46-ckd-epi-2021-race-free-egfr--urine-acr-staging)
   - 4.7 [Harmonized South Asian Metabolic Syndrome Criteria](#47-harmonized-south-asian-metabolic-syndrome-criteria)
5. [Machine Learning Engine & Pipeline Architecture](#5-machine-learning-engine--pipeline-architecture)
   - 5.1 [Feature Compatibility & Missing Data Safeguards](#51-feature-compatibility--missing-data-safeguards)
   - 5.2 [Probability Calibration & Coarse Risk Banding](#52-probability-calibration--coarse-risk-banding)
   - 5.3 [Secondary ML Modules (Parkinson's & Liver Disease)](#53-secondary-ml-modules-parkinsons--liver-disease)
6. [Backend API Reference & Pipeline Lifecycle](#6-backend-api-reference--pipeline-lifecycle)
   - 6.1 [POST /api/v1/assess](#61-post-apiv1assess)
   - 6.2 [POST /api/v1/care/recommend](#62-post-apiv1carerecommend)
   - 6.3 [POST /api/v1/reports/pdf](#63-post-apiv1reportspdf)
   - 6.4 [Authentication & History Persistence](#64-authentication--history-persistence)
7. [Frontend Architecture & Component System](#7-frontend-architecture--component-system)
   - 7.1 [Phase A: 3-Step Input Wizard](#71-phase-a-3-step-input-wizard)
   - 7.2 [Phase B: Snapshot Dashboard & Hero Layout](#72-phase-b-snapshot-dashboard--hero-layout)
   - 7.3 [Care Guidance: Food Precautions & Exercise Guidelines](#73-care-guidance-food-precautions--exercise-guidelines)
   - 7.4 [Verified Facilities Directory & Interactive Map](#74-verified-facilities-directory--interactive-map)
8. [Design System & Accessibility Standards](#8-design-system--accessibility-standards)
9. [Internationalization & Localization (English & Hindi)](#9-internationalization--localization-english--hindi)
10. [Database Schema & Entity Relationship Model](#10-database-schema--entity-relationship-model)
11. [Testing Matrix & Verification Protocols](#11-testing-matrix--verification-protocols)
12. [Deployment & Operations Manual](#12-deployment--operations-manual)

---

## 1. System Overview & Healthcare Objectives

HealthBuddy was engineered to address the specific cardiometabolic phenotype prevalent across South Asia—commonly termed the **"Asian Indian Phenotype"**. This phenotype is clinically characterized by:
- Increased visceral adiposity and waist circumference despite lower absolute BMI.
- Heightened insulin resistance and early onset of Type 2 Diabetes (often 10–15 years earlier than Western cohorts).
- Premature and accelerated Coronary Artery Disease (CAD).
- High prevalence of dyslipidemia marked by elevated triglycerides and depressed HDL cholesterol.

HealthBuddy solves the critical triage bottleneck by providing a zero-barrier, deterministic, and machine learning-augmented assessment that can be completed by patients in under 3 minutes, producing structured risk tiers, clear next steps, and verified care routing.

---

## 2. Clinical Safety Principles & Non-Negotiable Rules

To ensure patient safety, HealthBuddy enforces seven foundational clinical rules:

1. **Mandatory Educational Disclaimer**:
   - A non-dismissible clinical banner is displayed across every screen:
     > *"HealthBuddy is an educational screening tool, not a medical device. It does not diagnose disease or prescribe medications. Review all results with a qualified healthcare provider."*
2. **Server-Side Red-Flag Short-Circuit**:
   - Step 1 of the assessment asks four red-flag triage questions:
     1. Acute chest pain radiating to arm, neck, jaw, or back with pressure/sweating.
     2. Sudden onset of stroke warning signs (facial droop, unilateral arm weakness, slurred speech).
     3. Acute severe gastrointestinal bleeding (hematemesis or melena/black tarry stools).
     4. Extreme symptomatic hyperglycemia accompanied by confusion or respiratory distress.
   - **Enforcement**: This check occurs strictly on the server before any calculators run. If triggered, `/api/v1/assess` returns only `{ emergency: { ... } }`. Scoring, nutrition, and exercise advice are completely suppressed. The UI immediately renders a full-screen emergency modal with direct dial buttons for emergency dispatch (112 / 108) and nearest 24/7 trauma centers.
3. **Restricted Medical Vocabulary**:
   - The platform strictly employs:
     - *"Estimated risk band"* (Never *"chance you have the disease"* or *"your diagnosis"*).
     - *"Care guidance"* (Never *"cure"* or *"treatment"*).
     - *"Recommended care options"* (Never *"best hospital"* or *"guaranteed doctor"*).
     - Zero medication drug names, dosages, or titration protocols are suggested.
4. **Physician Attribution & Production Guard**:
   - Every guidance plan references:
     - `Based on: {Clinical Guideline / Society}` (e.g., ICMR, WHO, KDIGO).
     - `Reviewed by: {Physician Name / Credentials}` (e.g., Dr. A. Sharma, MD Internal Medicine).
     - If reviewer status is `"pending"`, a prominent badge is rendered.
5. **Strict Segregation of Rule-Based Scores & ML Outputs**:
   - Rule-based clinical scores (e.g., WHO 10-year risk, IDRS) and ML estimates are presented separately. They are never averaged or blended. If a discrepancy exists, both are displayed with an explanatory label.
6. **Explicit Handling of Missing Data**:
   - When required clinical features are absent, modules return `status: "skipped"` or `"needs_more_info"`. The system never imputes clinical laboratory numbers silently.
7. **Sample Data Identification**:
   - Any default or preview data is visibly marked with the chip: `Illustrative results`.

---

## 3. Full Architecture & Data Flow Diagram

```
+---------------------------------------------------------------------------------------+
|                                CLIENT LAYER (Next.js 14)                              |
|                                                                                       |
|  +--------------------+     +-----------------------+     +------------------------+  |
|  |   Step 1: Basics   | --> |   Step 2: Lifestyle   | --> |   Step 3: Optional     |  |
|  | - Red Flags Check  |     | - Physical Activity   |     |   Lab Values           |  |
|  | - Vitals & BMI     |     | - Smoking & Alcohol   |     | - Glucose & HbA1c      |  |
|  | - Location         |     | - Sleep & Family Hx   |     | - Lipids & Creatinine  |  |
|  +--------------------+     +-----------------------+     +------------------------+  |
+-------------------------------------------+-------------------------------------------+
                                            | JSON Payload (POST /api/v1/assess)
                                            v
+---------------------------------------------------------------------------------------+
|                                BACKEND ENGINE (FastAPI)                               |
|                                                                                       |
|  [Step 1] Request Validation & Schema Sanitization (Pydantic v2)                      |
|                                            |                                          |
|                                            v                                          |
|  [Step 2] Safety Engine: Evaluate Red-Flag Triggers (safety.py)                       |
|           |                                                                           |
|           +-- [RED FLAG DETECTED?] --> Return Emergency Payload & Short-Circuit       |
|           |                                                                           |
|           v [ALL CLEAR]                                                               |
|  [Step 3] Deterministic Clinical Calculators (Sequential & Independent)               |
|           +-- anthropometry.py (BMI Indian Classification)                            |
|           +-- bp.py (Blood Pressure Classification)                                   |
|           +-- glucose.py (FPG, HbA1c, OGTT with IFCC auto-conversion)                 |
|           +-- idrs.py (Indian Diabetes Risk Score)                                    |
|           +-- who_cvd.py (WHO South Asia 10-Year CVD Risk: Lab & Non-Lab)            |
|           +-- kidney.py (CKD-EPI 2021 Race-Free eGFR + ACR Staging)                   |
|           +-- metabolic.py (Harmonized South Asian MetSyn Criteria)                   |
|                                            |                                          |
|                                            v                                          |
|  [Step 4] Machine Learning Engine (predictor.py)                                      |
|           +-- Verify input feature vector compatibility                               |
|           +-- Missing features -> status: "needs_more_info"                           |
|           +-- Present features -> Calibrated probability -> Coarse risk band          |
|                                            |                                          |
|                                            v                                          |
|  [Step 5] Recommendation & Care Router (care_matcher.py)                              |
|           +-- Determine highest condition urgency (Immediate, 2 weeks, Routine)       |
|           +-- Match up to 3 verified hospitals (distance, specialty, public/private)  |
|           +-- Synthesize Top 3 "What To Do First" clinical action items               |
|           +-- Attach physician-reviewed Diet, Exercise & Follow-up plans              |
|                                            |                                          |
|                                            v                                          |
|  [Step 6] Persistence Layer (SQLAlchemy / SQLite)                                     |
|           +-- If consent granted -> Persist assessment snapshot & follow-up dates     |
+-------------------------------------------+-------------------------------------------+
                                            | Full JSON Assessment Response
                                            v
+---------------------------------------------------------------------------------------+
|                                DASHBOARD & EXPORT LAYER                               |
|                                                                                       |
|  - Organic Warm Healthcare Canvas (#FFF8E3 with ambient radial glow)                  |
|  - Hero Summary Progress Ring (5/6 checks completed, overall category)               |
|  - Next Steps Action Card with Stethoscope Illustration                               |
|  - 4 Primary Condition Cards (Heart, Prediabetes, Diabetes Risk, Blood Pressure)      |
|  - Secondary Clinical Cards (BMI, Metabolic Syndrome, Kidney Health)                 |
|  - Care Options & Interactive Leaflet Hospital Map                                    |
|  - Precautions (Eat More vs Avoid) & Activity Targets                                 |
|  - Follow-up Schedule & 2-Page Vector PDF Download (ReportLab)                        |
+---------------------------------------------------------------------------------------+
```

---

## 4. Exhaustive Mathematical & Clinical Calculator Specifications

### 4.1 South Asian Anthropometry (BMI)
- **Clinical Source**: WHO / ICMR / Consensus Guidelines for Asian Indians.
- **Formula**:
  $$\text{BMI} = \frac{\text{Weight in kg}}{(\text{Height in meters})^2}$$
- **Classification Boundaries**:
  - Underweight: $< 18.5 \text{ kg/m}^2$
  - Normal: $18.5 \text{ to } 22.9 \text{ kg/m}^2$
  - Overweight: $23.0 \text{ to } 24.9 \text{ kg/m}^2$
  - Obese: $\ge 25.0 \text{ kg/m}^2$
- **Abdominal Obesity Metric (Waist Circumference)**:
  - Male: Normal $< 90\text{ cm}$, Elevated $\ge 90\text{ cm}$
  - Female: Normal $< 80\text{ cm}$, Elevated $\ge 80\text{ cm}$

### 4.2 Blood Pressure Staging (JNC7 / ACC / AHA)
Evaluates Systolic Blood Pressure (SBP) and Diastolic Blood Pressure (DBP):
- **Normal**: $\text{SBP} < 120\text{ mmHg}$ and $\text{DBP} < 80\text{ mmHg}$
- **Elevated**: $\text{SBP } 120–129\text{ mmHg}$ and $\text{DBP} < 80\text{ mmHg}$
- **Stage 1 Hypertension**: $\text{SBP } 130–139\text{ mmHg}$ or $\text{DBP } 80–89\text{ mmHg}$
- **Stage 2 Hypertension**: $\text{SBP } \ge 140\text{ mmHg}$ or $\text{DBP } \ge 90\text{ mmHg}$
- **Hypertensive Crisis**: $\text{SBP } > 180\text{ mmHg}$ or $\text{DBP } > 120\text{ mmHg}$ (requires immediate clinical evaluation).

### 4.3 Glycemic Classification & IFCC/NGSP Conversion
- **Automatic IFCC ($\text{mmol/mol}$) to NGSP ($\%$) Formula**:
  $$\text{HbA1c}_{\%} = (\text{HbA1c}_{\text{mmol/mol}} \times 0.09148) + 2.152$$
- **Classification Table**:
  | Glycemic Status | Fasting Plasma Glucose (FPG) | HbA1c (%) | 2-Hour OGTT |
  |---|---|---|---|
  | **Normal** | $< 100\text{ mg/dL}$ | $< 5.7\%$ | $< 140\text{ mg/dL}$ |
  | **Prediabetes** | $100 – 125\text{ mg/dL}$ | $5.7 – 6.4\%$ | $140 – 199\text{ mg/dL}$ |
  | **Diabetes** | $\ge 126\text{ mg/dL}$ | $\ge 6.5\%$ | $\ge 200\text{ mg/dL}$ |

### 4.4 Indian Diabetes Risk Score (IDRS)
Validated by Dr. V. Mohan and the Madras Diabetes Research Foundation (MDRF):
- **Age Criteria**:
  - $< 35\text{ years}$: $+0$ points
  - $35 – 49\text{ years}$: $+20$ points
  - $\ge 50\text{ years}$: $+30$ points
- **Abdominal Obesity (Waist)**:
  - Female $< 80\text{ cm}$ / Male $< 90\text{ cm}$: $+0$ points
  - Female $80 – 89\text{ cm}$ / Male $90 – 99\text{ cm}$: $+10$ points
  - Female $\ge 90\text{ cm}$ / Male $\ge 100\text{ cm}$: $+20$ points
- **Physical Activity**:
  - Vigorous exercise or strenuous work: $+0$ points
  - Moderate exercise or moderate work: $+10$ points
  - Mild exercise or sedentary lifestyle: $+20$ points
  - Totally sedentary (no exercise, sitting job): $+30$ points
- **Family History of Diabetes**:
  - Neither parent: $+0$ points
  - One parent: $+10$ points
  - Both parents: $+20$ points
- **Risk Stratification**:
  - $< 30$: Low Risk (re-screen in 12 months)
  - $30 – 59$: Moderate Risk (lifestyle modifications recommended)
  - $\ge 60$: High Risk (fasting glucose / HbA1c laboratory confirmation indicated).

### 4.5 WHO South Asia 10-Year Cardiovascular Disease Risk
- **Applicability Range**: Ages 40–74. For ages $<40$ or $>74$, returns `status: "skipped"` with reason `"WHO CVD risk charts validated only for ages 40-74."`
- **Two Parallel Models**:
  1. *Laboratory Model*: Age, Sex, Smoking Status, SBP, Total Cholesterol.
  2. *Non-Laboratory Model*: Age, Sex, Smoking Status, SBP, BMI.
- **Risk Tiers**:
  - $< 10\%$: Low 10-year CVD risk.
  - $10 – 19\%$: Moderate risk.
  - $20 – 29\%$: High risk.
  - $\ge 30\%$: Very High risk.

### 4.6 CKD-EPI 2021 Race-Free eGFR & Urine ACR Staging
- **Clinical Guideline**: KDIGO 2024 / National Kidney Foundation race-free formula.
- **Formula ($\text{mL/min}/1.73\text{m}^2$)**:
  $$\text{eGFR} = 142 \times \min\left(\frac{S_{\text{cr}}}{\kappa}, 1\right)^\alpha \times \max\left(\frac{S_{\text{cr}}}{\kappa}, 1\right)^{-1.200} \times 0.9938^{\text{Age}} \times [1.012 \text{ if female}]$$
  Where:
  - Females: $\kappa = 0.7$, $\alpha = -0.241$
  - Males: $\kappa = 0.9$, $\alpha = -0.302$
  - $S_{\text{cr}}$ = Serum Creatinine in $\text{mg/dL}$.
- **Kidney Damage Staging**:
  - **G1**: $\text{eGFR } \ge 90$ (Normal/High)
  - **G2**: $\text{eGFR } 60–89$ (Mildly decreased)
  - **G3a**: $\text{eGFR } 45–59$ (Mild to moderately decreased)
  - **G3b**: $\text{eGFR } 30–44$ (Moderately to severely decreased)
  - **G4**: $\text{eGFR } 15–29$ (Severely decreased)
  - **G5**: $\text{eGFR } < 15$ (Kidney failure)
- **Urine Albumin-to-Creatinine Ratio (ACR)**:
  - **A1**: $< 30\text{ mg/g}$ (Normal to mildly increased)
  - **A2**: $30 – 300\text{ mg/g}$ (Moderately increased / Microalbuminuria)
  - **A3**: $> 300\text{ mg/g}$ (Severely increased / Macroalbuminuria).

### 4.7 Harmonized South Asian Metabolic Syndrome Criteria
Requires at least **3 out of 5** components:
1. **Elevated Waist Circumference**: $\ge 90\text{ cm}$ (Men) or $\ge 80\text{ cm}$ (Women).
2. **Elevated Triglycerides**: $\ge 150\text{ mg/dL}$ (or specific treatment).
3. **Depressed HDL Cholesterol**: $< 40\text{ mg/dL}$ (Men) or $< 50\text{ mg/dL}$ (Women).
4. **Elevated Blood Pressure**: $\text{SBP} \ge 130\text{ mmHg}$ or $\text{DBP} \ge 85\text{ mmHg}$.
5. **Elevated Fasting Glucose**: $\ge 100\text{ mg/dL}$.

---

## 5. Machine Learning Engine & Pipeline Architecture

### 5.1 Feature Compatibility & Missing Data Safeguards
The ML inference engine (`backend/app/services/predictor.py`) implements a strict feature inspection protocol:
- It introspects the exact feature names required by each trained model.
- If a single mandatory feature is missing from the patient's payload (e.g., direct laboratory enzyme values), the engine outputs:
  ```json
  {
    "module": "liver_disease_ml",
    "status": "needs_more_info",
    "skip_reason": "Required laboratory markers (ALT, AST, ALP) were not entered in the assessment.",
    "kind": "ml"
  }
  ```
- **Rule**: Never interpolate, average, or guess laboratory values silently.

### 5.2 Probability Calibration & Coarse Risk Banding
- **Internal Model**: Random Forest, Gradient Boosting, or Logistic Regression with isotonic or Platt calibration.
- **Output Presentation**: Raw continuous probabilities (e.g., $0.18742$) are kept internal. Patients are shown calibrated, coarse risk bands:
  - **Low**: Calibrated probability $< 10\%$
  - **Moderate**: Calibrated probability $10\% – 30\%$
  - **High**: Calibrated probability $> 30\%$
- Includes confidence indicator flag (`"high"`, `"medium"`, `"low"`) and the top 3 contributing feature weights.

### 5.3 Secondary ML Modules (Parkinson's & Liver Disease)
Accessible via the Secondary Opinion section:
1. **Parkinson's Disease Voice Biomarkers**: Evaluates 22 acoustic parameters (Jitter, Shimmer, NHR, HNR, RPDE, DFA, PPE).
2. **Liver Function ML Screening**: Evaluates 10 clinical and biochemical markers (Age, Sex, Total Bilirubin, Direct Bilirubin, ALP, ALT, AST, Total Proteins, Albumin, A/G Ratio).

---

## 6. Backend API Reference & Pipeline Lifecycle

### 6.1 POST /api/v1/assess
The primary orchestrator endpoint. Accepts the comprehensive wizard payload:

```json
{
  "red_flags": {
    "chest_pain": false,
    "stroke_symptoms": false,
    "severe_bleeding": false,
    "high_sugar_symptoms": false
  },
  "basics": {
    "age": 48,
    "sex": "male",
    "height_cm": 172.0,
    "weight_kg": 73.8,
    "waist_cm": 92.0,
    "systolic_bp": 135,
    "diastolic_bp": 85,
    "resting_heart_rate": 74,
    "city": "New Delhi"
  },
  "lifestyle": {
    "smoking": "non_smoker",
    "alcohol_drinks_per_week": 0,
    "physical_activity": "moderate",
    "sitting_hours_per_day": 7,
    "sleep_hours_per_night": 7,
    "family_history_diabetes": "one_parent",
    "family_history_heart_disease": true
  },
  "labs": {
    "fasting_glucose_mg_dl": 108.0,
    "hba1c_pct": 5.8,
    "cholesterol_total_mg_dl": 195.0,
    "creatinine_mg_dl": null,
    "urine_acr_mg_g": null
  },
  "consent_data_storage": true
}
```

**Response Format**:
```json
{
  "emergency": null,
  "urgency": "within_2_weeks",
  "what_to_do_first": [
    "Review your moderate cardiovascular risk with a physician.",
    "Add missing kidney labs (creatinine & urine ACR) if advised.",
    "Follow the Indian food and activity guidance for your plan."
  ],
  "modules": [
    {
      "module": "heart_who_cvd",
      "status": "computed",
      "score": 12.0,
      "category": "low",
      "unit": "%",
      "method": "WHO South Asia Non-Lab Chart (includes Stroke)",
      "factors": ["SBP 135 mmHg", "Age 48 yrs"],
      "kind": "rule"
    },
    {
      "module": "diabetes_idrs",
      "status": "computed",
      "score": 40,
      "category": "moderate",
      "unit": "/100",
      "method": "IDRS (<30 Low, 30-59 Moderate, >=60 High)",
      "factors": ["Age 35-49 (+20)", "Waist 92 cm (+10)", "Moderate activity (+10)"],
      "kind": "rule"
    },
    {
      "module": "kidney_ckd_epi",
      "status": "skipped",
      "skip_reason": "Creatinine and urine ACR not entered yet.",
      "score": null,
      "category": null,
      "unit": "mL/min/1.73m2",
      "method": "CKD-EPI 2021 (Race-Free)",
      "factors": [],
      "kind": "rule"
    }
  ],
  "care": {
    "specialist_types": ["Cardiologist", "Diabetologist"],
    "matched_hospitals": [...]
  },
  "followups": [
    { "condition": "heart", "tier": "low", "due_date": "2027-11-25" },
    { "condition": "diabetes", "tier": "moderate", "due_date": "2027-05-25" }
  ]
}
```

### 6.2 POST /api/v1/care/recommend
Accepts `{ condition: string, tier: string, city: string }` and returns up to 3 verified healthcare facilities matching geography and clinical specialty, with emergency capabilities and government/private designations.

### 6.3 POST /api/v1/reports/pdf
Consumes the complete assessment JSON and returns a multi-page, vector-rendered clinical PDF generated via ReportLab. Includes summary tables, risk chips, nutrition guidance, and clinician signature blocks.

### 6.4 Authentication & History Persistence
- Optional user registration via `POST /api/v1/auth/register` and login via `POST /api/v1/auth/login`.
- Evaluates `consent_data_storage`. If `false`, results are computed in-memory and discarded from persistence immediately after the response is rendered.

---

## 7. Frontend Architecture & Component System

### 7.1 Phase A: 3-Step Input Wizard
1. **Step 1: Basics & Safety**:
   - Urgent 4-item red-flag checklist rendered in a high-visibility container.
   - Demographics: Age, sex, height (cm), weight (kg). BMI is auto-calculated live.
   - Hemodynamics: Systolic and diastolic BP, resting heart rate, city/PIN code.
2. **Step 2: Lifestyle & Family History**:
   - Smoking status (Non-smoker, Ex-smoker, Current smoker).
   - Alcohol consumption (drinks per week).
   - Physical activity category (Vigorous, Moderate, Mild, Sedentary).
   - Sleep duration (hours/night), Sitting duration (hours/day).
   - Family history of diabetes (None, One parent, Both parents) and CAD.
3. **Step 3: Optional Lab Reports**:
   - Prominent button: *"Skip, I don't have lab reports"*.
   - Fasting glucose, HbA1c (with auto IFCC to NGSP detection), 2-hour OGTT.
   - Lipid profile: Total cholesterol, LDL, HDL, Triglycerides.
   - Renal markers: Serum creatinine, Urine ACR.
   - Consent checkbox: *"Save my results to History"* (defaults to unchecked).

### 7.2 Phase B: Snapshot Dashboard & Hero Layout
- **Brand Lockup**: `HealthBuddy` with signature yellow-square dark heart and ECG wave.
- **Top Utility Bar**: Health search input, `Download PDF`, `Re-check my health`, and user avatar badge.
- **Hero Grid (Two Cards)**:
  - *Left Card (Yellow Gradient)*: Circular SVG progress ring showing `5/6 checks done`, vertical separator line, `✔ Overall Summary` pill, and synthesis text.
  - *Right Card (White Soft Shadow)*: `✦ Your Next Steps`, 3 numbered amber badges, custom stethoscope vector illustration, and `See full plan ->` button.
- **Condition Cards Grid (4 Primary Cards)**:
  1. **Heart Disease**: Pink heart icon, `12%`, `Low Risk` green chip, smooth pink sparkline wave.
  2. **Prediabetes**: Purple droplet icon, `40/100`, `Moderate Risk` amber chip, smooth purple sparkline wave.
  3. **Diabetes Risk**: Red droplet icon, `Moderate`, `Needs Attention` orange chip, smooth orange sparkline wave.
  4. **Blood Pressure**: Blue gauge icon, `135/85 mmHg`, `Normal Range` green chip, smooth cyan/blue sparkline wave.
- **Bottom Motivational Banner**: Runner silhouette in white circular badge, motivational text, and golden `♥ HealthBuddy` button with pine tree landscape background.

### 7.3 Care Guidance: Food Precautions & Exercise Guidelines
- Condition-specific guidance loaded from localized JSON files (`plans.en.json` and `plans.hi.json`).
- Two-column card:
  - **Eat More (Green)**: Whole millets (bajra, ragi, jowar), split pulses, methi, leafy greens, bitter gourd.
  - **Avoid (Red)**: Maida, samosas, pakoras, mithai, high-sodium pickles, carbonated beverages, trans fats.
- Physical activity targets aligned with ICMR/WHO guidelines (e.g., 150 minutes/week of moderate activity), featuring bold warnings (*"Get medical clearance first"*) for high-risk cardiac users.

### 7.4 Verified Facilities Directory & Interactive Map
- Displays verified healthcare centers with:
  - Verified Checkmark badge.
  - 24x7 Emergency-capable indicator.
  - Public / Private sector filter.
  - Specialty tagging (Cardiology, Diabetology, Nephrology).
  - One-click interactive Leaflet map pin navigation.

---

## 8. Design System & Accessibility Standards

- **Color Palette Tokens**:
  - `bg-warm-canvas`: `#FFF8E3` with radial ambient gradients (`rgba(255, 200, 61, 0.42)` and `rgba(255, 205, 75, 0.35)`).
  - `hb-amber`: `#FFC83D` (Primary Action) / `#F5B81D` (Hover).
  - `hb-brown`: `#2B2208` (Primary Ink, contrast ratio $> 11:1$ on cream).
  - `hb-muted`: `#6B5B2E` / `#7C6C3E` (Subtitles, contrast ratio $> 4.8:1$).
  - `hb-border`: `#EFE4BE` / `#F3EACB`.
- **Card Styling**: Pillowy `rounded-[22px]` to `rounded-[24px]` radius, soft warm ambient shadows (`box-shadow: 0 10px 30px -10px rgba(43, 34, 8, 0.08)`).
- **Accessibility & WCAG AA Compliance**:
  - Minimum touch targets of $44 \times 44\text{px}$.
  - Visible focus rings on all interactive elements (`ring-2 ring-amber-500 ring-offset-2`).
  - No color-only status indicators; every badge couples color with an explicit text label and icon.
  - Reduced-motion queries respected via `prefers-reduced-motion: reduce`.

---

## 9. Internationalization & Localization (English & Hindi)

- **Bi-directional Localization**: Complete translation coverage across `frontend/locales/en.json` and `frontend/locales/hi.json`.
- **Dynamic Number & Date Formatting**:
  - Formatted using `Intl.NumberFormat` and `Intl.DateTimeFormat` with active locale (`en-IN` or `hi-IN`).
- **Font Stack**:
  - English: `Plus Jakarta Sans`.
  - Hindi: `Noto Sans Devanagari`.
- Header provides an instantaneous one-click language toggle.

---

## 10. Database Schema & Entity Relationship Model

```
+-----------------------------------+
|               Users               |
+-----------------------------------+
| id            INTEGER (PK)        |
| email         VARCHAR(255) (UQ)   |
| password_hash VARCHAR(255)        |
| created_at    DATETIME            |
+-----------------+-----------------+
                  | 1
                  |
                  | N
+-----------------v-----------------+
|            Assessments            |
+-----------------------------------+
| id            INTEGER (PK)        |
| user_id       INTEGER (FK)        |
| timestamp     DATETIME            |
| overall_tier  VARCHAR(50)         |
| payload_json  TEXT                |
| results_json  TEXT                |
| consent_saved BOOLEAN             |
+-----------------+-----------------+
                  | 1
                  |
                  | N
+-----------------v-----------------+
|             Followups             |
+-----------------------------------+
| id            INTEGER (PK)        |
| assessment_id INTEGER (FK)        |
| condition     VARCHAR(50)         |
| tier          VARCHAR(50)         |
| due_date      DATE                |
| is_completed  BOOLEAN             |
+-----------------------------------+
```

---

## 11. Testing Matrix & Verification Protocols

### 11.1 Backend Test Coverage (`pytest`)
- `test_anthropometry`: Verifies boundary conditions at $22.9$, $23.0$, $24.9$, and $25.0\text{ kg/m}^2$.
- `test_bp`: Validates JNC7 classification cutoffs.
- `test_glucose`: Confirms IFCC to NGSP conversion and FPG/HbA1c staging.
- `test_idrs`: Boundary tests for age ($34/35/49/50$) and waist thresholds.
- `test_who_cvd`: Ensures ages $<40$ or $>74$ return `"skipped"`.
- `test_red_flags`: Asserts emergency payload overrides all scoring logic.
- `test_missing_labs`: Confirms missing labs produce `"skipped"` modules rather than 500 exceptions.

### 11.2 Frontend Test Coverage (`Vitest` + React Testing Library)
- Plan lookup safety: Confirms safe fallback to general physician guidance on missing keys.
- ConditionCard rendering: Asserts skipped cards display `—` and trigger `"Add lab values"`.
- ARIA keyboard navigation: Validates `ArrowRight`, `Home`, and `End` keys on Plan tabs.
- Wizard form state: Asserts answers are preserved during Back-navigation.
- Language toggle: Confirms strings and numerals update between English and Hindi.

---

## 12. Deployment & Operations Manual

### Quick Start Commands
1. **Backend Server**:
   ```bash
   cd /media/nik/B/Healthcore/heartbuddy/backend
   source .venv/bin/activate
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
2. **Frontend Client**:
   ```bash
   cd /media/nik/B/Healthcore/heartbuddy/frontend
   npm run build
   npm start -- -p 3006
   ```
3. **Execute Test Suites**:
   ```bash
   # Backend Unit Tests
   cd /media/nik/B/Healthcore/heartbuddy/backend && .venv/bin/pytest -v

   # Frontend Unit Tests
   cd /media/nik/B/Healthcore/heartbuddy/frontend && npm test
   ```
