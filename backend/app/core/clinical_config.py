"""Configuration settings for the Multi-Disease Prediction System."""

import os
from pathlib import Path
from typing import Dict, Any, List

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"
DATABASE_PATH = str(PROJECT_ROOT / "predictions.db")

# Default disease key
DEFAULT_DISEASE = "heart_disease"

# Model configuration
RANDOM_STATE = 42
TEST_SIZE = 0.2
CV_FOLDS = 5
MODEL_SELECTION_CRITERION = "f1_weighted"

# Standard Model Configurations benchmarked across all diseases
MODEL_CONFIGS = {
    "logistic_regression": {
        "class": "LogisticRegression",
        "params": {"max_iter": 1000, "random_state": RANDOM_STATE},
        "needs_scaling": True,
        "description": "Linear classifier using logistic function for probabilistic estimation",
    },
    "decision_tree": {
        "class": "DecisionTreeClassifier",
        "params": {"random_state": RANDOM_STATE, "max_depth": 5},
        "needs_scaling": False,
        "description": "Non-linear rule-based tree model with orthogonal splits",
    },
    "random_forest": {
        "class": "RandomForestClassifier",
        "params": {"n_estimators": 100, "random_state": RANDOM_STATE, "max_depth": 5},
        "needs_scaling": False,
        "description": "Ensemble bagging model averaging 100 decorrelated decision trees",
    },
    "knn": {
        "class": "KNeighborsClassifier",
        "params": {"n_neighbors": 5},
        "needs_scaling": True,
        "description": "Instance-based learning utilizing Euclidean distance metrics",
    },
}

# ==============================================================================
# MULTI-DISEASE SPECIFICATIONS
# ==============================================================================

DISEASES_CONFIG: Dict[str, Dict[str, Any]] = {
    "heart_disease": {
        "name": "Heart Disease",
        "icon": "❤️",
        "system": "Cardiovascular",
        "dataset_file": "heart_disease.csv",
        "dataset_url": "https://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/processed.cleveland.data",
        "has_header": False,
        "feature_columns": [
            "age", "sex", "cp", "trestbps", "chol", "fbs",
            "restecg", "thalach", "exang", "oldpeak", "slope", "ca", "thal"
        ],
        "target_column": "target",
        "categorical_features": ["sex", "cp", "fbs", "restecg", "exang", "slope", "ca", "thal"],
        "numerical_features": ["age", "trestbps", "chol", "thalach", "oldpeak"],
        "feature_descriptions": {
            "age": "Age in years",
            "sex": "Sex (0 = Female, 1 = Male)",
            "cp": "Chest Pain Type (1 = Typical Angina, 2 = Atypical Angina, 3 = Non-anginal Pain, 4 = Asymptomatic)",
            "trestbps": "Resting Blood Pressure (mm Hg)",
            "chol": "Serum Cholesterol (mg/dl)",
            "fbs": "Fasting Blood Sugar > 120 mg/dl (0 = No, 1 = Yes)",
            "restecg": "Resting ECG Results (0 = Normal, 1 = ST-T Wave Abnormality, 2 = Left Ventricular Hypertrophy)",
            "thalach": "Maximum Heart Rate Achieved (bpm)",
            "exang": "Exercise Induced Angina (0 = No, 1 = Yes)",
            "oldpeak": "ST Depression Induced by Exercise Relative to Rest (mm)",
            "slope": "Slope of Peak Exercise ST Segment (1 = Upsloping, 2 = Flat, 3 = Downsloping)",
            "ca": "Number of Major Vessels Colored by Fluoroscopy (0-3)",
            "thal": "Thalassemia (3 = Normal, 6 = Fixed Defect, 7 = Reversible Defect)",
        },
        "feature_ranges": {
            "age": (29, 77),
            "sex": (0, 1),
            "cp": (1, 4),
            "trestbps": (94, 200),
            "chol": (126, 564),
            "fbs": (0, 1),
            "restecg": (0, 2),
            "thalach": (71, 202),
            "exang": (0, 1),
            "oldpeak": (0.0, 6.2),
            "slope": (1, 3),
            "ca": (0, 3),
            "thal": (3, 7),
        },
        "target_mapping": {0: 0, 1: 1, 2: 1, 3: 1, 4: 1},
        "target_labels": {0: "No Heart Disease", 1: "Heart Disease"},
        "dataset_info": {
            "name": "Cleveland Heart Disease Dataset",
            "source": "UCI Machine Learning Repository",
            "samples": 303,
            "features": 13,
            "target_classes": "0: Healthy (54%), 1: Heart Disease (46%)",
            "citation": "Detrano, R., et al. (1989). International application of a new probability algorithm for the diagnosis of coronary artery disease. American Journal of Cardiology, 64(5), 304-310.",
        },
        "demo_presets": {
            "healthy": {
                "age": 35.0, "sex": 0, "cp": 1, "trestbps": 110.0, "chol": 175.0,
                "fbs": 0, "restecg": 0, "thalach": 175.0, "exang": 0, "oldpeak": 0.0,
                "slope": 1, "ca": 0, "thal": 3
            },
            "high_risk": {
                "age": 63.0, "sex": 1, "cp": 4, "trestbps": 155.0, "chol": 285.0,
                "fbs": 1, "restecg": 2, "thalach": 115.0, "exang": 1, "oldpeak": 2.8,
                "slope": 2, "ca": 2, "thal": 7
            }
        },
        "recommendations": {
            "healthy": [
                "Maintain cardiovascular health through 150 minutes of moderate aerobic exercise weekly.",
                "Sustain a Mediterranean-style diet low in saturated fats and sodium (<2,300 mg/day).",
                "Undergo routine lipid panel and blood pressure checks every 1-2 years.",
            ],
            "high_risk": [
                "URGENT: Consult a cardiologist for comprehensive diagnostic workup (12-lead ECG, stress echocardiography, angiography).",
                "Monitor daily resting blood pressure and reduce sodium intake strictly.",
                "Review cholesterol management therapy (e.g., statins) with healthcare provider.",
                "Seek immediate emergency care if chest pain, shortness of breath, or radiating jaw/arm pain occurs.",
            ]
        }
    },

    "diabetes": {
        "name": "Diabetes (Type 2)",
        "icon": "🩸",
        "system": "Endocrine & Metabolic",
        "dataset_file": "diabetes.csv",
        "dataset_url": "https://raw.githubusercontent.com/jbrownlee/Datasets/master/pima-indians-diabetes.data.csv",
        "has_header": True,
        "feature_columns": [
            "Pregnancies", "Glucose", "BloodPressure", "SkinThickness",
            "Insulin", "BMI", "DiabetesPedigreeFunction", "Age"
        ],
        "target_column": "Outcome",
        "categorical_features": [],
        "numerical_features": [
            "Pregnancies", "Glucose", "BloodPressure", "SkinThickness",
            "Insulin", "BMI", "DiabetesPedigreeFunction", "Age"
        ],
        "feature_descriptions": {
            "Pregnancies": "Number of times pregnant (0 - 17)",
            "Glucose": "Plasma glucose concentration at 2 hours in OGTT (mg/dl)",
            "BloodPressure": "Diastolic blood pressure (mm Hg)",
            "SkinThickness": "Triceps skin fold thickness (mm)",
            "Insulin": "2-Hour serum insulin (mu U/ml)",
            "BMI": "Body Mass Index (weight in kg / (height in m)^2)",
            "DiabetesPedigreeFunction": "Diabetes pedigree function (genetic risk score)",
            "Age": "Patient age in years (21 - 81)",
        },
        "feature_ranges": {
            "Pregnancies": (0, 17),
            "Glucose": (40.0, 200.0),
            "BloodPressure": (40.0, 130.0),
            "SkinThickness": (7.0, 99.0),
            "Insulin": (14.0, 846.0),
            "BMI": (15.0, 67.1),
            "DiabetesPedigreeFunction": (0.07, 2.42),
            "Age": (21, 81),
        },
        "target_mapping": {0: 0, 1: 1},
        "target_labels": {0: "Non-Diabetic", 1: "Diabetic Risk Detected"},
        "dataset_info": {
            "name": "Pima Indians Diabetes Database",
            "source": "National Institute of Diabetes and Digestive and Kidney Diseases (NIDDK) / UCI",
            "samples": 768,
            "features": 8,
            "target_classes": "0: Non-Diabetic (65%), 1: Diabetic (35%)",
            "citation": "Smith, J.W., Everhart, J.E., Dickson, W.C., Knowler, W.C., & Johannes, R.S. (1988). Using the ADAP learning algorithm to forecast the onset of diabetes mellitus. In Proceedings of the Symposium on Computer Applications and Medical Care (pp. 261-265).",
        },
        "demo_presets": {
            "healthy": {
                "Pregnancies": 1, "Glucose": 92.0, "BloodPressure": 68.0, "SkinThickness": 18.0,
                "Insulin": 75.0, "BMI": 22.4, "DiabetesPedigreeFunction": 0.22, "Age": 24
            },
            "high_risk": {
                "Pregnancies": 6, "Glucose": 168.0, "BloodPressure": 88.0, "SkinThickness": 35.0,
                "Insulin": 220.0, "BMI": 38.5, "DiabetesPedigreeFunction": 0.85, "Age": 52
            }
        },
        "recommendations": {
            "healthy": [
                "Continue balanced, low-glycemic dietary habits rich in dietary fiber and whole grains.",
                "Engage in routine physical activity to optimize peripheral insulin sensitivity.",
                "Perform annual fasting plasma glucose or HbA1c screening.",
            ],
            "high_risk": [
                "Schedule a clinical diagnostic evaluation for Glycated Hemoglobin (HbA1c) and Fasting Blood Glucose.",
                "Initiate medical nutrition therapy (MNT) focusing on strict carbohydrate counting and glycemic load control.",
                "Engage in 30 minutes of daily moderate-intensity exercise to stimulate GLUT-4 translocation in muscle tissue.",
                "Consult an endocrinologist regarding lifestyle intervention or potential metformin initiation.",
            ]
        }
    },

    "parkinsons": {
        "name": "Parkinson's Disease",
        "icon": "🧠",
        "system": "Neurological & Motor",
        "dataset_file": "parkinsons.csv",
        "dataset_url": "https://archive.ics.uci.edu/ml/machine-learning-databases/parkinsons/parkinsons.data",
        "has_header": True,
        "feature_columns": [
            "MDVP:Fo(Hz)", "MDVP:Fhi(Hz)", "MDVP:Flo(Hz)", "MDVP:Jitter(%)", "MDVP:Jitter(Abs)",
            "MDVP:RAP", "MDVP:PPQ", "Jitter:DDP", "MDVP:Shimmer", "MDVP:Shimmer(dB)",
            "Shimmer:APQ3", "Shimmer:APQ5", "MDVP:APQ", "Shimmer:DDA", "NHR",
            "HNR", "RPDE", "DFA", "spread1", "spread2", "D2", "PPE"
        ],
        "target_column": "status",
        "categorical_features": [],
        "numerical_features": [
            "MDVP:Fo(Hz)", "MDVP:Fhi(Hz)", "MDVP:Flo(Hz)", "MDVP:Jitter(%)", "MDVP:Jitter(Abs)",
            "MDVP:RAP", "MDVP:PPQ", "Jitter:DDP", "MDVP:Shimmer", "MDVP:Shimmer(dB)",
            "Shimmer:APQ3", "Shimmer:APQ5", "MDVP:APQ", "Shimmer:DDA", "NHR",
            "HNR", "RPDE", "DFA", "spread1", "spread2", "D2", "PPE"
        ],
        "feature_descriptions": {
            "MDVP:Fo(Hz)": "Average vocal fundamental frequency (Hz)",
            "MDVP:Fhi(Hz)": "Maximum vocal fundamental frequency (Hz)",
            "MDVP:Flo(Hz)": "Minimum vocal fundamental frequency (Hz)",
            "MDVP:Jitter(%)": "MDVP relative frequency perturbation (%)",
            "MDVP:Jitter(Abs)": "MDVP absolute frequency perturbation (seconds)",
            "MDVP:RAP": "Relative amplitude perturbation",
            "MDVP:PPQ": "Five-point period perturbation quotient",
            "Jitter:DDP": "Average absolute difference of differences between jitter cycles",
            "MDVP:Shimmer": "MDVP local shimmer amplitude variation",
            "MDVP:Shimmer(dB)": "MDVP local shimmer in decibels",
            "Shimmer:APQ3": "Three-point amplitude perturbation quotient",
            "Shimmer:APQ5": "Five-point amplitude perturbation quotient",
            "MDVP:APQ": "11-point amplitude perturbation quotient",
            "Shimmer:DDA": "Average absolute differences between consecutive amplitudes",
            "NHR": "Noise-to-harmonics ratio",
            "HNR": "Harmonics-to-noise ratio (dB)",
            "RPDE": "Recurrence period density entropy (dynamical complexity)",
            "DFA": "Detrended fluctuation analysis (signal fractal scaling exponent)",
            "spread1": "Nonlinear measure of fundamental frequency variation (spread 1)",
            "spread2": "Nonlinear measure of fundamental frequency variation (spread 2)",
            "D2": "Correlation dimension (fractal dimension of vocal attractor)",
            "PPE": "Pitch period entropy (vocal dysphonia measure)",
        },
        "feature_ranges": {
            "MDVP:Fo(Hz)": (88.0, 260.0),
            "MDVP:Fhi(Hz)": (102.0, 592.0),
            "MDVP:Flo(Hz)": (65.0, 240.0),
            "MDVP:Jitter(%)": (0.001, 0.035),
            "MDVP:Jitter(Abs)": (0.000007, 0.00026),
            "MDVP:RAP": (0.0006, 0.022),
            "MDVP:PPQ": (0.0009, 0.02),
            "Jitter:DDP": (0.002, 0.065),
            "MDVP:Shimmer": (0.009, 0.12),
            "MDVP:Shimmer(dB)": (0.08, 1.35),
            "Shimmer:APQ3": (0.004, 0.06),
            "Shimmer:APQ5": (0.005, 0.08),
            "MDVP:APQ": (0.007, 0.14),
            "Shimmer:DDA": (0.013, 0.17),
            "NHR": (0.0006, 0.32),
            "HNR": (8.4, 33.0),
            "RPDE": (0.25, 0.69),
            "DFA": (0.57, 0.83),
            "spread1": (-7.96, -2.43),
            "spread2": (0.006, 0.45),
            "D2": (1.42, 3.67),
            "PPE": (0.044, 0.53),
        },
        "target_mapping": {0: 0, 1: 1},
        "target_labels": {0: "Healthy (No Parkinson's Detected)", 1: "Parkinson's Disease Indicators Detected"},
        "dataset_info": {
            "name": "Oxford Parkinson's Disease Telemonitoring Dataset",
            "source": "University of Oxford & UCI Machine Learning Repository",
            "samples": 195,
            "features": 22,
            "target_classes": "0: Healthy (24.6%), 1: Parkinson's (75.4%)",
            "citation": "Little, M.A., McSharry, P.E., Roberts, S.J., Costello, D.A., & Moroz, I.M. (2007). Exploiting nonlinear recurrence and fractal scaling properties for voice disorder detection. BioMedical Engineering OnLine, 6(1), 23.",
        },
        "demo_presets": {
            "healthy": {
                "MDVP:Fo(Hz)": 202.4, "MDVP:Fhi(Hz)": 235.1, "MDVP:Flo(Hz)": 185.3,
                "MDVP:Jitter(%)": 0.0031, "MDVP:Jitter(Abs)": 0.000015, "MDVP:RAP": 0.0016,
                "MDVP:PPQ": 0.0018, "Jitter:DDP": 0.0048, "MDVP:Shimmer": 0.0175,
                "MDVP:Shimmer(dB)": 0.16, "Shimmer:APQ3": 0.0085, "Shimmer:APQ5": 0.0105,
                "MDVP:APQ": 0.014, "Shimmer:DDA": 0.0255, "NHR": 0.006, "HNR": 26.2,
                "RPDE": 0.38, "DFA": 0.64, "spread1": -6.8, "spread2": 0.12, "D2": 2.05, "PPE": 0.11
            },
            "high_risk": {
                "MDVP:Fo(Hz)": 116.5, "MDVP:Fhi(Hz)": 137.8, "MDVP:Flo(Hz)": 98.4,
                "MDVP:Jitter(%)": 0.0115, "MDVP:Jitter(Abs)": 0.000098, "MDVP:RAP": 0.0062,
                "MDVP:PPQ": 0.0069, "Jitter:DDP": 0.0186, "MDVP:Shimmer": 0.065,
                "MDVP:Shimmer(dB)": 0.62, "Shimmer:APQ3": 0.034, "Shimmer:APQ5": 0.041,
                "MDVP:APQ": 0.052, "Shimmer:DDA": 0.102, "NHR": 0.045, "HNR": 14.8,
                "RPDE": 0.61, "DFA": 0.77, "spread1": -3.9, "spread2": 0.33, "D2": 2.85, "PPE": 0.38
            }
        },
        "recommendations": {
            "healthy": [
                "Maintain vocal cord flexibility and lung capacity through vocal exercises or singing.",
                "Engage in aerobic and balance-focused physical conditioning (yoga, cycling, walking).",
                "Periodic neurological evaluation if family history of movement disorders is present.",
            ],
            "high_risk": [
                "Consult a neurologist / movement disorder specialist for Unified Parkinson's Disease Rating Scale (UPDRS) assessment.",
                "Undergo DaTscan (dopamine transporter neuroimaging) or electromyography if indicated by clinician.",
                "Consult a speech-language pathologist for Lee Silverman Voice Treatment (LSVT LOUD) speech rehabilitation.",
                "Engage in targeted physical and occupational therapy focusing on gait symmetry and motor control.",
            ]
        }
    },

    "liver_disease": {
        "name": "Liver Disease (ILPD)",
        "icon": "🩺",
        "system": "Hepatic & Digestive",
        "dataset_file": "liver_disease.csv",
        "dataset_url": "https://archive.ics.uci.edu/ml/machine-learning-databases/00225/Indian%20Liver%20Patient%20Dataset%20(ILPD).csv",
        "has_header": True,
        "feature_columns": [
            "Age", "Gender", "Total_Bilirubin", "Direct_Bilirubin",
            "Alkaline_Phosphotase", "Alamine_Aminotransferase", "Aspartate_Aminotransferase",
            "Total_Proteins", "Albumin", "Albumin_and_Globulin_Ratio"
        ],
        "target_column": "Dataset",
        "categorical_features": ["Gender"],
        "numerical_features": [
            "Age", "Total_Bilirubin", "Direct_Bilirubin", "Alkaline_Phosphotase",
            "Alamine_Aminotransferase", "Aspartate_Aminotransferase",
            "Total_Proteins", "Albumin", "Albumin_and_Globulin_Ratio"
        ],
        "feature_descriptions": {
            "Age": "Patient age in years (4 - 90)",
            "Gender": "Biological sex (0 = Female, 1 = Male)",
            "Total_Bilirubin": "Total Serum Bilirubin (mg/dl)",
            "Direct_Bilirubin": "Conjugated / Direct Bilirubin (mg/dl)",
            "Alkaline_Phosphotase": "Alkaline Phosphatase - ALP (IU/L)",
            "Alamine_Aminotransferase": "Alanine Aminotransferase - ALT / SGPT (IU/L)",
            "Aspartate_Aminotransferase": "Aspartate Aminotransferase - AST / SGOT (IU/L)",
            "Total_Proteins": "Total Serum Proteins (g/dl)",
            "Albumin": "Serum Albumin (g/dl)",
            "Albumin_and_Globulin_Ratio": "Albumin to Globulin (A/G) Ratio",
        },
        "feature_ranges": {
            "Age": (4, 90),
            "Gender": (0, 1),
            "Total_Bilirubin": (0.4, 75.0),
            "Direct_Bilirubin": (0.1, 19.7),
            "Alkaline_Phosphotase": (63, 2110),
            "Alamine_Aminotransferase": (10, 2000),
            "Aspartate_Aminotransferase": (10, 4929),
            "Total_Proteins": (2.7, 9.6),
            "Albumin": (0.9, 5.5),
            "Albumin_and_Globulin_Ratio": (0.3, 2.8),
        },
        "target_mapping": {1: 1, 0: 0},
        "target_labels": {0: "No Liver Disease Detected", 1: "Liver Disease Detected"},
        "dataset_info": {
            "name": "Indian Liver Patient Dataset (ILPD)",
            "source": "UCI Machine Learning Repository",
            "samples": 583,
            "features": 10,
            "target_classes": "0: Healthy (28.6%), 1: Liver Patient (71.4%)",
            "citation": "Ramana, B.V., Babu, M.S.P., & Venkateswarlu, N.B. (2011). A critical study of selected classification algorithms for liver disease diagnosis. International Journal of Database Management Systems, 3(2), 101-114.",
        },
        "demo_presets": {
            "healthy": {
                "Age": 32, "Gender": 1, "Total_Bilirubin": 0.8, "Direct_Bilirubin": 0.2,
                "Alkaline_Phosphotase": 160, "Alamine_Aminotransferase": 24, "Aspartate_Aminotransferase": 26,
                "Total_Proteins": 7.4, "Albumin": 4.2, "Albumin_and_Globulin_Ratio": 1.15
            },
            "high_risk": {
                "Age": 55, "Gender": 1, "Total_Bilirubin": 4.8, "Direct_Bilirubin": 2.4,
                "Alkaline_Phosphotase": 380, "Alamine_Aminotransferase": 95, "Aspartate_Aminotransferase": 140,
                "Total_Proteins": 5.6, "Albumin": 2.5, "Albumin_and_Globulin_Ratio": 0.65
            }
        },
        "recommendations": {
            "healthy": [
                "Maintain optimal liver metabolism through hydration and limiting alcohol intake.",
                "Ensure vaccination against Hepatitis A and Hepatitis B.",
                "Avoid unnecessary over-the-counter hepatotoxic analgesics (e.g. chronic acetaminophen overuse).",
            ],
            "high_risk": [
                "URGENT: Consult a hepatologist or gastroenterologist for comprehensive liver panel and hepatic ultrasound / elastography.",
                "Complete total cessation of alcohol and review all prescription medications for hepatic clearance.",
                "Screen for viral hepatitis (HBsAg, Anti-HCV) and non-alcoholic fatty liver disease (NAFLD/NASH).",
                "Follow a balanced hepatoprotective diet with adequate protein quality and restricted refined sugars.",
            ]
        }
    }
}

# ==============================================================================
# BACKWARD COMPATIBILITY EXPORTS (Heart Disease Default)
# ==============================================================================

_default_cfg = DISEASES_CONFIG[DEFAULT_DISEASE]

DATASET_PATH = DATA_DIR / _default_cfg["dataset_file"]
DATASET_URL = _default_cfg["dataset_url"]
FEATURE_COLUMNS = _default_cfg["feature_columns"]
TARGET_COLUMN = _default_cfg["target_column"]
CATEGORICAL_FEATURES = _default_cfg["categorical_features"]
NUMERICAL_FEATURES = _default_cfg["numerical_features"]
FEATURE_DESCRIPTIONS = _default_cfg["feature_descriptions"]
FEATURE_RANGES = _default_cfg["feature_ranges"]
TARGET_MAPPING = _default_cfg["target_mapping"]
TARGET_LABELS = _default_cfg["target_labels"]
DATASET_INFO = _default_cfg["dataset_info"]


def get_disease_config(disease: str = DEFAULT_DISEASE) -> Dict[str, Any]:
    """Retrieve full configuration dictionary for a given disease."""
    if disease not in DISEASES_CONFIG:
        valid = list(DISEASES_CONFIG.keys())
        raise ValueError(f"Unknown disease '{disease}'. Valid options: {valid}")
    return DISEASES_CONFIG[disease]


def list_supported_diseases() -> List[str]:
    """Return list of supported disease identifiers."""
    return list(DISEASES_CONFIG.keys())


# ==============================================================================
# UI CONFIGURATION & MEDICAL DISCLAIMERS
# ==============================================================================

STREAMLIT_CONFIG = {
    "page_title": "MediSense ML - Multi-Disease Prediction System",
    "page_icon": "🩺",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

MEDICAL_DISCLAIMER = """
**DISCLAIMER**: This clinical decision support platform is designed for educational, research, 
and academic demonstration purposes only. It does NOT constitute medical advice, diagnosis, 
or clinical treatment recommendations. All diagnostic classifications are probabilistic outputs 
derived from machine learning algorithms on benchmark datasets. Always consult a licensed medical 
professional or qualified healthcare provider for clinical evaluation.
"""
