"""Constants, specialist mappings, and risk routing rules for HealthBuddy v3.0."""

from typing import Dict, Any

DISEASE_CARE_MAPPING: Dict[str, Dict[str, Any]] = {
    "heart_disease": {
        "specialists": ["Cardiologist", "Interventional Cardiologist"],
        "capabilities": ["cath lab", "ECG", "echo", "cardiac ICU"],
        "suggested_tests": ["ECG", "Echocardiogram", "Lipid Profile", "Exercise Stress Test"],
    },
    "diabetes": {
        "specialists": ["Endocrinologist", "Diabetologist"],
        "capabilities": ["diabetes clinic", "lab", "eye and nephrology support"],
        "suggested_tests": ["Fasting Plasma Glucose", "HbA1c", "Kidney Function Test (KFT)", "Lipid Profile"],
    },
    "parkinsons": {
        "specialists": ["Neurologist"],
        "capabilities": ["MRI", "physiotherapy", "speech therapy"],
        "suggested_tests": ["Neurological Examination", "Brain MRI", "Speech & Acoustic Assessment"],
    },
    "liver_disease": {
        "specialists": ["Hepatologist", "Gastroenterologist"],
        "capabilities": ["liver clinic", "ultrasound", "FibroScan", "endoscopy"],
        "suggested_tests": ["Liver Function Tests (LFT)", "Abdominal Ultrasound", "Hepatitis Screening", "FibroScan"],
    },
}

RISK_ROUTING_GUIDANCE: Dict[str, Dict[str, Any]] = {
    "High": {
        "urgency_timeline": "Urgent specialist consultation (within 24–72 hours); seek emergency care immediately if red-flag symptoms appear.",
        "guidance": "Your risk score is elevated. Schedule an urgent specialist evaluation and bring your biomarker report. Prioritize emergency-capable hospitals.",
        "emergency_first": True,
    },
    "Moderate": {
        "urgency_timeline": "Book a specialist OPD appointment within 2 to 4 weeks.",
        "guidance": "Discuss the suggested confirmatory laboratory tests with a specialist and monitor your biomarkers.",
        "emergency_first": False,
    },
    "Low": {
        "urgency_timeline": "Routine primary care follow-up in 6 to 12 months.",
        "guidance": "Maintain healthy lifestyle habits and repeat routine preventive screening in 6 to 12 months.",
        "emergency_first": False,
    },
}

EMERGENCY_NUMBERS: Dict[str, str] = {
    "India": "112 / 108",
    "US / Canada": "911",
    "UK": "999 / 111",
    "EU": "112",
}

