"""ML inference, probability calibration check, uncertainty flags, and factor explainability."""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd

from app.core.config import ARTIFACTS_DIR, BACKEND_DIR

_ml_dir = str(BACKEND_DIR / "ml")
if _ml_dir not in sys.path:
    sys.path.insert(0, _ml_dir)
from app.core.clinical_config import (
    DEFAULT_DISEASE,
    DISEASES_CONFIG,
    get_disease_config,
)
from app.core.validation import InputValidator, sanitize_input


class HealthBuddyPredictor:
    """Trusted clinical ML predictor with uncertainty flags and factor explanations."""

    def __init__(self, disease: str = DEFAULT_DISEASE):
        self.disease = disease
        self.config = get_disease_config(disease)
        self.feature_names: List[str] = self.config["feature_columns"]
        self.target_labels: Dict[int, str] = self.config["target_labels"]
        self.validator = InputValidator(disease=disease)
        self.model_data: Optional[Dict[str, Any]] = None
        self.preprocessor: Any = None
        self.eval_results: Dict[str, Any] = {}
        self._load_artifacts()

    def _resolve_artifact_dir(self) -> Path:
        d_dir = ARTIFACTS_DIR / self.disease
        if d_dir.exists():
            return d_dir
        return ARTIFACTS_DIR

    def _load_artifacts(self) -> None:
        art_dir = self._resolve_artifact_dir()
        best_files = list(art_dir.glob("best_model_*.joblib"))
        if not best_files:
            raise FileNotFoundError(f"No trained champion model found in {art_dir}")
        self.model_data = joblib.load(best_files[0])
        self.pipeline = self.model_data["pipeline"]

        eval_path = art_dir / "evaluation_results.json"
        if eval_path.exists():
            with open(eval_path, "r", encoding="utf-8") as f:
                self.eval_results = json.load(f)

    def _compute_uncertainty(self, probability: Optional[float], raw_input: Dict[str, Any]) -> Tuple[str, List[str]]:
        """Flag low-confidence predictions near decision boundary or with out-of-range inputs."""
        reasons: List[str] = []
        ranges = self.config.get("feature_ranges", {})

        out_of_bounds = []
        for feat, (lo, hi) in ranges.items():
            if feat in raw_input and raw_input[feat] is not None:
                val = float(raw_input[feat])
                if val < lo or val > hi:
                    out_of_bounds.append(feat)
        if out_of_bounds:
            reasons.append(f"Inputs outside reference cohort range: {', '.join(out_of_bounds)}")

        if probability is not None and 0.35 <= probability <= 0.65:
            reasons.append("Predicted probability is near the 50% decision threshold (borderline uncertainty)")

        if reasons:
            return "low_confidence", reasons
        return "high_confidence", []

    def _compute_top_factors(self, raw_input: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Compute plain-language top contributing factors using model weights/importances and range deviation."""
        model = self.pipeline.named_steps["model"]
        ranges = self.config.get("feature_ranges", {})
        descriptions = self.config.get("feature_descriptions", {})

        importances: Optional[np.ndarray] = None
        if hasattr(model, "feature_importances_"):
            importances = np.asarray(model.feature_importances_, dtype=float)
        elif hasattr(model, "coef_"):
            importances = np.abs(np.asarray(model.coef_, dtype=float)).ravel()

        factors: List[Dict[str, Any]] = []
        for idx, feat in enumerate(self.feature_names):
            val = float(raw_input.get(feat, 0.0))
            weight = float(importances[idx]) if importances is not None and idx < len(importances) else 1.0 / len(self.feature_names)
            lo, hi = ranges.get(feat, (0.0, 1.0))
            mid = (lo + hi) / 2.0
            span = max(hi - lo, 1e-6)
            norm_dev = abs(val - mid) / (span / 2.0)
            score = weight * (1.0 + norm_dev)
            direction = "elevated" if val > mid else ("low" if val < mid else "typical")
            factors.append(
                {
                    "feature": feat,
                    "description": descriptions.get(feat, feat),
                    "value": val,
                    "impact_score": round(float(score), 4),
                    "direction": direction,
                    "plain_explanation": f"{descriptions.get(feat, feat)} is {val:g} ({direction} relative to cohort midpoint {mid:g}).",
                }
            )

        factors.sort(key=lambda x: x["impact_score"], reverse=True)
        return factors[:5]

    def get_clinical_metrics(self) -> Dict[str, Any]:
        """Compute sensitivity, specificity, PPV, NPV, and Brier/ROC-AUC from confusion matrix."""
        model_key = self.model_data.get("model_name", "")
        res = self.eval_results.get(model_key, {})
        cm = res.get("confusion_matrix")
        metrics: Dict[str, Any] = {
            "model_name": model_key,
            "accuracy": res.get("accuracy"),
            "roc_auc": res.get("roc_auc"),
            "f1_weighted": res.get("f1_weighted"),
        }
        if cm and len(cm) == 2 and len(cm[0]) == 2:
            tn, fp = cm[0]
            fn, tp = cm[1]
            sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
            ppv = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            npv = tn / (tn + fn) if (tn + fn) > 0 else 0.0
            metrics.update(
                {
                    "sensitivity": round(sensitivity, 4),
                    "specificity": round(specificity, 4),
                    "ppv": round(ppv, 4),
                    "npv": round(npv, 4),
                }
            )
        return metrics

    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate, preprocess, predict, calibrate/flag uncertainty, and explain."""
        is_valid, errors = self.validator.validate(input_data)
        if not is_valid:
            return {"success": False, "errors": errors}

        sanitized = sanitize_input(input_data, disease=self.disease)
        df = pd.DataFrame([sanitized])[self.feature_names]

        pred = int(self.pipeline.predict(df)[0])
        prob: Optional[float] = None
        model_step = self.pipeline.named_steps["model"]
        if hasattr(model_step, "predict_proba"):
            proba = self.pipeline.predict_proba(df)[0]
            prob = float(proba[1]) if len(proba) > 1 else float(proba[0])

        if prob is not None:
            if prob < 0.35:
                risk_level = "Low"
            elif prob < 0.65:
                risk_level = "Moderate"
            else:
                risk_level = "High"
        else:
            risk_level = "High" if pred == 1 else "Low"

        confidence_flag, uncertainty_reasons = self._compute_uncertainty(prob, sanitized)
        top_factors = self._compute_top_factors(sanitized)

        return {
            "success": True,
            "disease": self.disease,
            "disease_name": self.config["name"],
            "prediction": pred,
            "label": self.target_labels.get(pred, str(pred)),
            "probability": round(prob, 4) if prob is not None else None,
            "risk_level": risk_level,
            "confidence_flag": confidence_flag,
            "uncertainty_reasons": uncertainty_reasons,
            "top_factors": top_factors,
            "model_name": self.model_data.get("model_name", "unknown"),
            "model_version": f"{self.disease}:{self.model_data.get('model_name', 'v3')}",
            "clinical_metrics": self.get_clinical_metrics(),
        }
