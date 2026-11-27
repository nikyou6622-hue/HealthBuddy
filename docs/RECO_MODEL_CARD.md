# Model Card — HealthBuddy ML #3: Personalized Recommendation Engine (`reco-hgbr-v1.0-20261127`)

## 1. Overview
- **Purpose:** Educational, safety-filtered personalized ranking of Indian foods, exercises/yoga, verified hospitals, doctor specialties/tests, and care follow-ups tailored to a user's health assessment and optional lab values.
- **Model Family:** Hybrid content-based + pointwise learning-to-rank using `HistGradientBoostingRegressor` (scikit-learn), benchmarked against pure TF-IDF cosine similarity and a deterministic rule-table baseline.
- **Artifact:** `backend/artifacts/reco_model.joblib` (`0.196 MB`, well under the 20 MB Vercel serverless budget).
- **Warm Inference Latency:** < 500 ms (no training at request time; artifacts loaded once via `@lru_cache`).

## 2. Training Data & Generator Parameters (`backend/ml/reco/synth.py`)
Because no real clinical outcome labels exist, the ranker is trained on **20,000 synthetic Indian patient profiles** paired with curated knowledgebase items (`data/care/*.csv`):
- **Fixed Seed:** `SYNTH_SEED = 42`
- **Cohort Mix:**
  - General Indian adult profiles (~70%) with South Asian BMI/waist distributions
  - Deliberate clinical edge cases (~30%): CKD (low eGFR / elevated urine ACR), uncontrolled diabetes (elevated FPG/HbA1c), stage 2 hypertension, young healthy adults, and elderly (> 70 years)
- **Missing Labs:** ~40% of profiles have missing lab panels (never guessed or imputed into user-facing outputs; tracked via `SimpleImputer(strategy="median", add_indicator=True)` and surfaced as `missing_inputs[]`).
- **Train / Test Split:** `GroupShuffleSplit(test_size=0.20, random_state=42)` grouped strictly by `patient_id` (zero patient leakage across train and held-out test pairs).
- **Labeling (`backend/ml/reco/label_rules.py` + `rules/*.json`):** Each `(patient, item)` pair is assigned a relevance grade `0–3` from explicit JSON rule tables encoding the knowledgebase condition tags, nutrient flags, exercise intensity/clearance flags, and hospital city/24x7/specialty attributes.

## 3. Evaluation Metrics (Held-Out 20% Test Profiles)
| Model | NDCG@5 | NDCG@10 | Precision@5 | Precision@10 | Recall@10 | MAP | Hit-Rate@10 | Coverage | Post-Filter Safety Violations |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **HistGradientBoostingRegressor (ML #3)** | **0.9993** | **0.9995** | **0.9977** | **0.9985** | **0.2336** | **0.9974** | **1.0000** | **0.5835** | **0.0000** |
| Baseline: Pure TF-IDF Cosine | 0.6976 | 0.7258 | 0.5621 | 0.6041 | 0.1430 | 0.6303 | 0.9985 | 0.2539 | 0.0000 |
| Baseline: Rule-Table Only | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.2338 | 1.0000 | 1.0000 | 0.6147 | 0.0000 |

## 4. Honest Limitations & Scope
- **Synthetic & Rule-Derived Labels:** Labels are generated from clinical rule tables (`rules/*.json`), **not real patient clinical outcomes**. Therefore, the model learns to generalize and smoothly rank those rules across feature combinations and missing-lab patterns, and cannot claim real-world clinical efficacy.
- **Educational Only:** Never diagnoses conditions, never prescribes medications or dosages, and never replaces physician judgment.
- **Post-Model Safety Layer (`safety_filter.py`):** Always runs *after* ML scoring to enforce emergency 112/108 red-flag short-circuits, `eGFR < 30` potassium/protein food blocks, BP stage 2/crisis exercise limits, age/pregnancy clearance flags, and verified-only hospitals.
- **Confidence Gating:** Automatically flags `low_confidence` when > 50% of lab inputs are missing, any vital/age falls outside trained ranges, or top-item score margin < 0.05.

