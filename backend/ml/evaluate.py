"""Model evaluation module supporting multi-disease benchmark evaluation."""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score
)
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import json
import logging
from pathlib import Path

from config import (
    DEFAULT_DISEASE,
    DISEASES_CONFIG,
    get_disease_config,
    list_supported_diseases,
    MODELS_DIR,
    REPORTS_DIR,
    FEATURE_COLUMNS,
    TARGET_COLUMN,
    TARGET_LABELS,
    TARGET_MAPPING,
)
from preprocessing import PreprocessingPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelEvaluator:
    """Handles model evaluation and benchmarking across clinical diseases."""

    def __init__(self, disease: str = DEFAULT_DISEASE):
        self.disease = disease
        self.config = get_disease_config(disease)
        self.feature_columns = self.config.get("feature_columns", FEATURE_COLUMNS)
        self.target_column = self.config.get("target_column", TARGET_COLUMN)
        self.target_labels = self.config.get("target_labels", TARGET_LABELS)
        self.target_mapping = self.config.get("target_mapping", TARGET_MAPPING)

        self.models_dir = MODELS_DIR / self.disease
        self.reports_dir = REPORTS_DIR / self.disease
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        self.evaluation_results: Dict[str, Dict[str, Any]] = {}
        self.test_data: Optional[pd.DataFrame] = None

    def load_test_data(self) -> pd.DataFrame:
        """Load the test set for the disease."""
        test_path = self.models_dir / "test_set.csv"
        if not test_path.exists():
            # Check root models dir for heart disease backward compatibility
            if self.disease == DEFAULT_DISEASE and (MODELS_DIR / "test_set.csv").exists():
                test_path = MODELS_DIR / "test_set.csv"
            else:
                raise FileNotFoundError(f"Test set not found at {test_path}")

        self.test_data = pd.read_csv(test_path)
        logger.info(f"Loaded test data for {self.disease}: {self.test_data.shape}")
        return self.test_data

    def evaluate_model(
        self,
        model_name: str,
        model_path: str,
        X_test: pd.DataFrame,
        y_test: pd.Series,
    ) -> Dict[str, Any]:
        """Evaluate a single model on test data."""
        logger.info(f"Evaluating {model_name} for {self.disease}...")

        # Load model
        model_data = joblib.load(model_path)
        pipeline = model_data["pipeline"]

        # Predict
        y_pred = pipeline.predict(X_test)
        y_pred_proba = None
        model_step = pipeline.named_steps["model"]
        if hasattr(model_step, "predict_proba"):
            try:
                y_pred_proba = pipeline.predict_proba(X_test)[:, 1]
            except Exception:
                y_pred_proba = None

        # Convert test target to binary
        y_test_binary = y_test.map(self.target_mapping)
        if y_test_binary.isnull().any():
            y_test_binary = y_test_binary.fillna(0).astype(int)

        target_names = [self.target_labels.get(0, "Negative"), self.target_labels.get(1, "Positive")]

        # Calculate metrics
        results = {
            "disease": self.disease,
            "model_name": model_name,
            "accuracy": float(accuracy_score(y_test_binary, y_pred)),
            "precision_macro": float(precision_score(y_test_binary, y_pred, average="macro", zero_division=0)),
            "precision_weighted": float(precision_score(y_test_binary, y_pred, average="weighted", zero_division=0)),
            "recall_macro": float(recall_score(y_test_binary, y_pred, average="macro", zero_division=0)),
            "recall_weighted": float(recall_score(y_test_binary, y_pred, average="weighted", zero_division=0)),
            "f1_macro": float(f1_score(y_test_binary, y_pred, average="macro", zero_division=0)),
            "f1_weighted": float(f1_score(y_test_binary, y_pred, average="weighted", zero_division=0)),
            "confusion_matrix": confusion_matrix(y_test_binary, y_pred).tolist(),
            "classification_report": classification_report(
                y_test_binary, y_pred, target_names=target_names, output_dict=True, zero_division=0
            ),
        }

        # ROC AUC if probabilities available
        if y_pred_proba is not None:
            try:
                results["roc_auc"] = float(roc_auc_score(y_test_binary, y_pred_proba))
            except Exception:
                results["roc_auc"] = None
        else:
            results["roc_auc"] = None

        # Feature importance for tree-based models
        if hasattr(model_step, "feature_importances_"):
            feature_names = model_data.get("feature_names", self.feature_columns)
            preprocessor = model_data.get("preprocessor")
            if preprocessor and hasattr(preprocessor, "get_feature_names_out"):
                try:
                    feature_names_out = preprocessor.get_feature_names_out()
                except Exception:
                    feature_names_out = feature_names
            else:
                feature_names_out = feature_names

            importances = model_step.feature_importances_
            if len(importances) == len(feature_names_out):
                results["feature_importance"] = dict(zip(feature_names_out, [float(x) for x in importances]))
            else:
                results["feature_importance"] = dict(zip(feature_names, [float(x) for x in importances]))

        self.evaluation_results[model_name] = results
        logger.info(
            f"[{self.disease}] {model_name} - Accuracy: {results['accuracy']:.4f}, "
            f"F1-weighted: {results['f1_weighted']:.4f}"
        )
        return results

    def evaluate_all_models(self) -> Dict[str, Dict[str, Any]]:
        """Evaluate all saved models for the disease on test data."""
        if self.test_data is None:
            self.load_test_data()

        X_test = self.test_data[self.feature_columns]
        y_test = self.test_data[self.target_column]

        # Look in disease-specific models directory
        model_files = list(self.models_dir.glob("model_*.joblib"))
        if not model_files and self.disease == DEFAULT_DISEASE:
            # Fallback to root models dir
            model_files = list(MODELS_DIR.glob("model_*.joblib"))

        logger.info(f"Found {len(model_files)} model files for {self.disease}")

        for model_file in model_files:
            model_name = model_file.stem.replace("model_", "")
            try:
                self.evaluate_model(model_name, str(model_file), X_test, y_test)
            except Exception as e:
                logger.error(f"Failed to evaluate {model_name} for {self.disease}: {e}")
                self.evaluation_results[model_name] = {"error": str(e)}

        return self.evaluation_results

    def compare_models(self) -> pd.DataFrame:
        """Create a comparison DataFrame of all models."""
        if not self.evaluation_results:
            self.evaluate_all_models()

        comparison_data = []
        for name, results in self.evaluation_results.items():
            if "error" not in results:
                comparison_data.append({
                    "Model": name,
                    "Accuracy": results["accuracy"],
                    "Precision (Macro)": results["precision_macro"],
                    "Precision (Weighted)": results["precision_weighted"],
                    "Recall (Macro)": results["recall_macro"],
                    "Recall (Weighted)": results["recall_weighted"],
                    "F1 (Macro)": results["f1_macro"],
                    "F1 (Weighted)": results["f1_weighted"],
                    "ROC AUC": results.get("roc_auc"),
                })

        df = pd.DataFrame(comparison_data)
        if not df.empty and "F1 (Weighted)" in df.columns:
            return df.sort_values("F1 (Weighted)", ascending=False).reset_index(drop=True)
        return df

    def plot_confusion_matrices(self, save_path: Optional[str] = None) -> Optional[plt.Figure]:
        """Plot confusion matrices for all models."""
        valid_results = {k: v for k, v in self.evaluation_results.items() if "error" not in v}
        n_models = len(valid_results)
        if n_models == 0:
            return None

        fig, axes = plt.subplots(1, n_models, figsize=(5 * n_models, 4))
        if n_models == 1:
            axes = [axes]

        labels = [self.target_labels.get(0, "Negative"), self.target_labels.get(1, "Positive")]
        # Truncate labels for cleaner heatmaps if long
        short_labels = [l[:12] + ".." if len(l) > 14 else l for l in labels]

        for idx, (name, results) in enumerate(valid_results.items()):
            cm = np.array(results["confusion_matrix"])
            sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=axes[idx],
                        xticklabels=short_labels, yticklabels=short_labels)
            axes[idx].set_title(f"{name}\nAcc: {results['accuracy']:.3f} | F1: {results['f1_weighted']:.3f}")
            axes[idx].set_xlabel("Predicted")
            axes[idx].set_ylabel("Actual")

        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
            logger.info(f"Confusion matrices saved to {save_path}")
        plt.close(fig)
        return fig

    def plot_metric_comparison(self, metric: str = "f1_weighted", save_path: Optional[str] = None) -> Optional[plt.Figure]:
        """Plot comparison of a specific metric across models."""
        df = self.compare_models()
        if df.empty:
            return None

        metric_column_map = {
            "accuracy": "Accuracy",
            "f1_weighted": "F1 (Weighted)",
            "f1_macro": "F1 (Macro)",
            "precision_weighted": "Precision (Weighted)",
            "precision_macro": "Precision (Macro)",
            "recall_weighted": "Recall (Weighted)",
            "recall_macro": "Recall (Macro)",
            "roc_auc": "ROC AUC",
        }
        col_name = metric_column_map.get(metric, metric)

        if col_name not in df.columns:
            return None

        fig, ax = plt.subplots(figsize=(9, 4.5))
        bars = ax.bar(df["Model"], df[col_name], color="#3498db", edgecolor="#2980b9", width=0.5)
        ax.set_title(f"{self.config['name']} - Model Benchmark: {col_name}", fontsize=12, fontweight="bold")
        ax.set_ylabel(col_name)
        ax.set_ylim(0, 1.05)
        ax.grid(axis="y", linestyle="--", alpha=0.6)

        for bar in bars:
            height = bar.get_height()
            if pd.notna(height):
                ax.annotate(f"{height:.3f}",
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3), textcoords="offset points",
                            ha="center", va="bottom", fontweight="bold")

        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
            logger.info(f"Metric comparison saved to {save_path}")
        plt.close(fig)
        return fig

    def plot_feature_importance(self, model_name: str, top_n: int = 10, save_path: Optional[str] = None) -> Optional[plt.Figure]:
        """Plot feature importance for a specific tree-based model."""
        if model_name not in self.evaluation_results:
            return None

        results = self.evaluation_results[model_name]
        if "feature_importance" not in results or not results["feature_importance"]:
            return None

        importance = results["feature_importance"]
        sorted_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:top_n]
        if not sorted_features:
            return None

        fig, ax = plt.subplots(figsize=(10, 5))
        features, values = zip(*sorted_features)
        bars = ax.barh(range(len(features)), values, color="#2ecc71", edgecolor="#27ae60")
        ax.set_yticks(range(len(features)))
        ax.set_yticklabels(features)
        ax.set_xlabel("Relative Importance Score")
        ax.set_title(f"{self.config['name']} - Feature Importance ({model_name}, Top {top_n})", fontweight="bold")
        ax.invert_yaxis()

        for bar, val in zip(bars, values):
            ax.annotate(f"{val:.3f}",
                        xy=(val, bar.get_y() + bar.get_height() / 2),
                        xytext=(5, 0), textcoords="offset points",
                        ha="left", va="center", fontweight="bold")

        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
            logger.info(f"Feature importance saved to {save_path}")
        plt.close(fig)
        return fig

    def save_evaluation_results(self, filepath: str) -> None:
        """Save evaluation results to JSON."""
        def convert(obj):
            if isinstance(obj, (np.integer, np.floating)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert(v) for v in obj]
            return obj

        results = convert(self.evaluation_results)
        with open(filepath, "w") as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Evaluation results for {self.disease} saved to {filepath}")

    def generate_report(self) -> str:
        """Generate a text evaluation report."""
        if not self.evaluation_results:
            self.evaluate_all_models()

        df = self.compare_models()
        report = []
        report.append("=" * 80)
        report.append(f"CLINICAL DECISION SUPPORT BENCHMARK REPORT: {self.config['name'].upper()}")
        report.append("=" * 80)
        report.append(f"\nTest Set Size: {len(self.test_data) if self.test_data is not None else 'N/A'}")
        report.append(f"Features: {len(self.feature_columns)}")
        report.append(f"Models Evaluated: {len(self.evaluation_results)}")
        report.append("\n" + "=" * 80)
        report.append("COMPARISON TABLE")
        report.append("=" * 80)
        report.append(df.to_string(index=False) if not df.empty else "No results")
        report.append("\n" + "=" * 80)
        report.append("DETAILED METRIC BREAKDOWN")
        report.append("=" * 80)

        for name, results in self.evaluation_results.items():
            if "error" in results:
                report.append(f"\n{name}: ERROR - {results['error']}")
                continue
            report.append(f"\n--- {name} ---")
            report.append(f"  Accuracy:       {results['accuracy']:.4f}")
            report.append(f"  Precision (M):  {results['precision_macro']:.4f}")
            report.append(f"  Precision (W):  {results['precision_weighted']:.4f}")
            report.append(f"  Recall (M):     {results['recall_macro']:.4f}")
            report.append(f"  Recall (W):     {results['recall_weighted']:.4f}")
            report.append(f"  F1 (M):         {results['f1_macro']:.4f}")
            report.append(f"  F1 (W):         {results['f1_weighted']:.4f}")
            if results.get("roc_auc") is not None:
                report.append(f"  ROC AUC:        {results['roc_auc']:.4f}")
            report.append(f"  Confusion Matrix: {results['confusion_matrix']}")

        return "\n".join(report)


def evaluate_pipeline(disease: str = DEFAULT_DISEASE) -> ModelEvaluator:
    """Run the complete evaluation pipeline for a specific disease."""
    logger.info(f"Starting evaluation pipeline for {disease}...")

    evaluator = ModelEvaluator(disease=disease)
    evaluator.evaluate_all_models()

    # Save results to disease directory
    eval_json_path = evaluator.models_dir / "evaluation_results.json"
    evaluator.save_evaluation_results(str(eval_json_path))

    # Backward compatibility for default disease
    if disease == DEFAULT_DISEASE:
        evaluator.save_evaluation_results(str(MODELS_DIR / "evaluation_results.json"))

    # Generate and save plots to disease reports directory
    evaluator.plot_confusion_matrices(str(evaluator.reports_dir / "confusion_matrices.png"))
    evaluator.plot_metric_comparison("f1_weighted", str(evaluator.reports_dir / "f1_comparison.png"))
    evaluator.plot_metric_comparison("accuracy", str(evaluator.reports_dir / "accuracy_comparison.png"))

    for model_name in ["decision_tree", "random_forest"]:
        evaluator.plot_feature_importance(
            model_name, save_path=str(evaluator.reports_dir / f"feature_importance_{model_name}.png")
        )

    # Save report
    report = evaluator.generate_report()
    with open(evaluator.reports_dir / "evaluation_report.txt", "w") as f:
        f.write(report)

    # Backward compatibility for default disease
    if disease == DEFAULT_DISEASE:
        evaluator.plot_confusion_matrices(str(REPORTS_DIR / "confusion_matrices.png"))
        evaluator.plot_metric_comparison("f1_weighted", str(REPORTS_DIR / "f1_comparison.png"))
        evaluator.plot_metric_comparison("accuracy", str(REPORTS_DIR / "accuracy_comparison.png"))
        for model_name in ["decision_tree", "random_forest"]:
            evaluator.plot_feature_importance(
                model_name, save_path=str(REPORTS_DIR / f"feature_importance_{model_name}.png")
            )
        with open(REPORTS_DIR / "evaluation_report.txt", "w") as f:
            f.write(report)

    logger.info(f"Evaluation pipeline for {disease} completed successfully")
    return evaluator


def evaluate_all_diseases() -> Dict[str, ModelEvaluator]:
    """Run evaluation across all supported clinical diseases."""
    evaluators = {}
    diseases = list_supported_diseases()
    for d in diseases:
        ev = evaluate_pipeline(disease=d)
        evaluators[d] = ev
    return evaluators


if __name__ == "__main__":
    evaluators = evaluate_all_diseases()
    for d, ev in evaluators.items():
        print("\n" + "=" * 60)
        print(f"BENCHMARK SUMMARY: {d.upper()}")
        print("=" * 60)
        print(ev.compare_models().to_string(index=False))
