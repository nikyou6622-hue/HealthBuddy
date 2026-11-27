"""Model training module supporting multi-disease classifier benchmarking."""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, List, Optional
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.pipeline import Pipeline
import joblib
import logging
import json
from pathlib import Path

from config import (
    DEFAULT_DISEASE,
    DISEASES_CONFIG,
    get_disease_config,
    list_supported_diseases,
    MODEL_CONFIGS,
    RANDOM_STATE,
    CV_FOLDS,
    MODEL_SELECTION_CRITERION,
    MODELS_DIR,
    FEATURE_COLUMNS,
    TARGET_COLUMN,
    TARGET_LABELS,
)
from preprocessing import PreprocessingPipeline, split_data, check_class_balance
from data_loader import DataLoader, load_and_validate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelTrainer:
    """Handles training and evaluation of multiple ML models for clinical disease prediction."""

    def __init__(self, disease: str = DEFAULT_DISEASE):
        self.disease = disease
        self.config = get_disease_config(disease)
        self.feature_columns = self.config.get("feature_columns", FEATURE_COLUMNS)
        self.target_column = self.config.get("target_column", TARGET_COLUMN)
        self.target_labels = self.config.get("target_labels", TARGET_LABELS)
        self.target_mapping = self.config.get("target_mapping", {})

        self.models_dir = MODELS_DIR / self.disease
        self.models_dir.mkdir(parents=True, exist_ok=True)

        self.models: Dict[str, Pipeline] = {}
        self.cv_results: Dict[str, Dict[str, Any]] = {}
        self.best_model_name: Optional[str] = None
        self.best_score: float = 0.0
        self.training_metadata: Dict[str, Any] = {}

    def create_model_pipeline(self, model_name: str, preprocessor: PreprocessingPipeline) -> Pipeline:
        """Create a full pipeline with preprocessing and model."""
        config = MODEL_CONFIGS[model_name]
        model_class = {
            "LogisticRegression": LogisticRegression,
            "DecisionTreeClassifier": DecisionTreeClassifier,
            "RandomForestClassifier": RandomForestClassifier,
            "KNeighborsClassifier": KNeighborsClassifier,
        }[config["class"]]

        model = model_class(**config["params"])
        pipeline = Pipeline([
            ("preprocessor", preprocessor.preprocessor),
            ("model", model),
        ])
        return pipeline

    def train_model(
        self,
        model_name: str,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        preprocessor: PreprocessingPipeline,
    ) -> Pipeline:
        """Train a single model with stratified cross-validation."""
        logger.info(f"Training {model_name} for {self.disease}...")

        config = MODEL_CONFIGS[model_name]
        needs_scaling = config["needs_scaling"]

        # Create a fresh preprocessor for this model (to avoid data leakage)
        model_preprocessor = PreprocessingPipeline(disease=self.disease)
        model_preprocessor.fit(X_train, y_train, needs_scaling=needs_scaling)

        # Create full pipeline
        pipeline = self.create_model_pipeline(model_name, model_preprocessor)

        # Train on full training data
        y_train_binary = y_train.map(self.target_mapping)
        if y_train_binary.isnull().any():
            y_train_binary = y_train_binary.fillna(0).astype(int)

        pipeline.fit(X_train, y_train_binary)

        # Stratified Cross-validation on training data
        cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)
        cv_scores = cross_val_score(
            pipeline, X_train, y_train_binary, cv=cv, scoring="f1_weighted", n_jobs=-1
        )

        self.cv_results[model_name] = {
            "cv_scores": cv_scores.tolist(),
            "cv_mean": float(cv_scores.mean()),
            "cv_std": float(cv_scores.std()),
        }

        logger.info(
            f"[{self.disease}] {model_name} CV F1-weighted: "
            f"{cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})"
        )
        return pipeline

    def train_all_models(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        preprocessor: PreprocessingPipeline,
    ) -> Dict[str, Pipeline]:
        """Train all configured models for the disease."""
        logger.info(f"Training all models for {self.disease}...")

        for model_name in MODEL_CONFIGS.keys():
            try:
                pipeline = self.train_model(model_name, X_train, y_train, preprocessor)
                self.models[model_name] = pipeline
            except Exception as e:
                logger.error(f"Failed to train {model_name} for {self.disease}: {e}")
                self.cv_results[model_name] = {"error": str(e)}

        # Select best model
        self.select_best_model()
        return self.models

    def select_best_model(self) -> str:
        """Select the best model based on the selection criterion."""
        valid_results = {
            name: res for name, res in self.cv_results.items()
            if "cv_mean" in res
        }

        if not valid_results:
            raise ValueError(f"No models trained successfully for {self.disease}")

        self.best_model_name = max(valid_results, key=lambda x: valid_results[x]["cv_mean"])
        self.best_score = valid_results[self.best_model_name]["cv_mean"]

        logger.info(
            f"Best model for {self.disease}: {self.best_model_name} "
            f"({MODEL_SELECTION_CRITERION}={self.best_score:.4f})"
        )
        return self.best_model_name

    def save_model(self, model_name: str, filepath: str, preprocessor: PreprocessingPipeline) -> None:
        """Save a trained model with its preprocessor."""
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not trained for {self.disease}")

        model_data = {
            "disease": self.disease,
            "pipeline": self.models[model_name],
            "preprocessor": preprocessor,
            "model_name": model_name,
            "cv_results": self.cv_results.get(model_name, {}),
            "feature_names": self.feature_columns,
            "target_labels": self.target_labels,
            "target_mapping": self.target_mapping,
        }
        joblib.dump(model_data, filepath)
        logger.info(f"Model {model_name} ({self.disease}) saved to {filepath}")

    def save_best_model(self, preprocessor: PreprocessingPipeline) -> str:
        """Save the best model."""
        if self.best_model_name is None:
            raise ValueError("No best model selected")

        filepath = self.models_dir / f"best_model_{self.best_model_name}.joblib"
        self.save_model(self.best_model_name, str(filepath), preprocessor)

        # Backward compatibility for default heart disease in MODELS_DIR root
        if self.disease == DEFAULT_DISEASE:
            root_filepath = MODELS_DIR / f"best_model_{self.best_model_name}.joblib"
            self.save_model(self.best_model_name, str(root_filepath), preprocessor)

        return str(filepath)

    def save_all_models(self, preprocessor: PreprocessingPipeline) -> Dict[str, str]:
        """Save all trained models."""
        saved_paths = {}
        for model_name in self.models.keys():
            filepath = self.models_dir / f"model_{model_name}.joblib"
            self.save_model(model_name, str(filepath), preprocessor)
            saved_paths[model_name] = str(filepath)

            # Backward compatibility for default disease
            if self.disease == DEFAULT_DISEASE:
                root_filepath = MODELS_DIR / f"model_{model_name}.joblib"
                self.save_model(model_name, str(root_filepath), preprocessor)

        return saved_paths

    def save_training_metadata(self, filepath: str, X_train: pd.DataFrame, y_train: pd.Series) -> None:
        """Save training metadata."""
        self.training_metadata = {
            "disease": self.disease,
            "best_model": self.best_model_name,
            "best_score": self.best_score,
            "selection_criterion": MODEL_SELECTION_CRITERION,
            "cv_results": self.cv_results,
            "train_samples": len(X_train),
            "test_samples": 0,
            "features": self.feature_columns,
            "target_labels": self.target_labels,
            "target_mapping": self.target_mapping,
            "random_state": RANDOM_STATE,
            "cv_folds": CV_FOLDS,
            "class_balance": check_class_balance(y_train, disease=self.disease),
        }

        with open(filepath, "w") as f:
            json.dump(self.training_metadata, f, indent=2, default=str)
        logger.info(f"Training metadata for {self.disease} saved to {filepath}")

        # Backward compatibility for default disease
        if self.disease == DEFAULT_DISEASE:
            root_meta = MODELS_DIR / "training_metadata.json"
            with open(root_meta, "w") as f:
                json.dump(self.training_metadata, f, indent=2, default=str)


def load_model(filepath: str) -> Dict[str, Any]:
    """Load a saved model."""
    return joblib.load(filepath)


def train_pipeline(disease: str = DEFAULT_DISEASE) -> Tuple[ModelTrainer, PreprocessingPipeline, Dict[str, Any]]:
    """Run the complete training pipeline for a given disease."""
    logger.info(f"Starting training pipeline for {disease}...")

    # Load and validate data
    loader = DataLoader(disease=disease)
    data = loader.load()
    validation_report = loader.validate()
    X, y = loader.get_feature_data()

    # Split data
    X_train, X_test, y_train, y_test = split_data(X, y, disease=disease)

    # Fit base preprocessor (for reference)
    base_preprocessor = PreprocessingPipeline(disease=disease)
    base_preprocessor.fit(X_train, y_train, needs_scaling=True)

    # Train models
    trainer = ModelTrainer(disease=disease)
    trainer.train_all_models(X_train, y_train, base_preprocessor)

    # Save best model and all models
    trainer.save_best_model(base_preprocessor)
    trainer.save_all_models(base_preprocessor)

    # Save base preprocessor
    prep_path = trainer.models_dir / "preprocessor.joblib"
    base_preprocessor.save(str(prep_path))
    if disease == DEFAULT_DISEASE:
        base_preprocessor.save(str(MODELS_DIR / "preprocessor.joblib"))

    # Save training metadata
    meta_path = trainer.models_dir / "training_metadata.json"
    trainer.save_training_metadata(str(meta_path), X_train, y_train)

    # Save test set for evaluation
    test_data = X_test.copy()
    test_data[trainer.target_column] = y_test
    test_data.to_csv(trainer.models_dir / "test_set.csv", index=False)
    if disease == DEFAULT_DISEASE:
        test_data.to_csv(MODELS_DIR / "test_set.csv", index=False)

    logger.info(f"Training pipeline for {disease} completed successfully")
    return trainer, base_preprocessor, validation_report


def train_all_diseases() -> Dict[str, ModelTrainer]:
    """Train benchmark models across all supported clinical diseases."""
    trainers = {}
    diseases = list_supported_diseases()
    logger.info(f"Commencing full training across all diseases: {diseases}")
    for d in diseases:
        trainer, _, _ = train_pipeline(disease=d)
        trainers[d] = trainer
    return trainers


if __name__ == "__main__":
    trainers = train_all_diseases()
    print("\n" + "="*60)
    print("MULTI-DISEASE TRAINING COMPLETE!")
    print("="*60)
    for d, tr in trainers.items():
        print(f"\n🩺 {d.upper()}:")
        print(f"  Best Model: {tr.best_model_name}")
        print(f"  Best CV F1: {tr.best_score:.4f}")
        for m, res in tr.cv_results.items():
            if "cv_mean" in res:
                print(f"    - {m}: {res['cv_mean']:.4f} (+/- {res['cv_std']:.4f})")
