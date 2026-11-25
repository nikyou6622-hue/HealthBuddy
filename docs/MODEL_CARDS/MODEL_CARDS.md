# HealthBuddy Model Cards (v3.0)

## 1. Heart Disease (`heart_disease`)
- **Dataset:** UCI Cleveland Heart Disease (303 records, 13 features)
- **Champion Model:** Random Forest (`91.80%` accuracy, `0.9535` ROC-AUC)
- **Intended Use:** Non-invasive educational/research cardiovascular risk stratification.
- **Limitations:** Small historical cohort; not externally validated for clinical diagnosis.

## 2. Diabetes (`diabetes`)
- **Dataset:** NIDDK Pima Indians Diabetes (768 records, 8 features)
- **Champion Model:** Decision Tree (`79.22%` accuracy, `0.7858` ROC-AUC; Logistic Regression `0.8230` ROC-AUC)
- **Limitations:** Specific demographic cohort; physiological zeros handled via median imputation.

## 3. Parkinson's Disease (`parkinsons`)
- **Dataset:** Oxford Voice Acoustic Dataset (195 records, 22 features)
- **Champion Model:** KNN / Random Forest / Logistic Regression (`92.31%` accuracy, `0.9638` ROC-AUC for KNN)
- **Limitations:** Small sample size; requires standardized acoustic voice measurements.

## 4. Liver Disease (`liver_disease`)
- **Dataset:** UCI Indian Liver Patient Dataset (583 records, 10 features)
- **Champion Model:** Logistic Regression (`73.50%` accuracy, `0.8320` ROC-AUC)
- **Limitations:** Class imbalance lowers weighted F1 (`0.6754`); clinical confirmation required.

