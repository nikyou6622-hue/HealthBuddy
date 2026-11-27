"""Data preprocessing pipeline module supporting multiple clinical disease datasets."""

import pandas as pd
import numpy as np
from typing import Tuple, List, Optional, Dict, Any
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import joblib
import logging

from app.core.clinical_config import (
    DEFAULT_DISEASE,
    get_disease_config,
    FEATURE_COLUMNS,
    TARGET_COLUMN,
    CATEGORICAL_FEATURES,
    NUMERICAL_FEATURES,
    TARGET_MAPPING,
    RANDOM_STATE,
    TEST_SIZE,
    MODELS_DIR,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PreprocessingPipeline:
    """Handles data preprocessing for multiple clinical disease prediction systems."""

    def __init__(self, disease: str = DEFAULT_DISEASE):
        self.disease = disease
        self.config = get_disease_config(disease)
        self.numerical_features = self.config.get("numerical_features", NUMERICAL_FEATURES)
        self.categorical_features = self.config.get("categorical_features", CATEGORICAL_FEATURES)
        self.feature_columns = self.config.get("feature_columns", FEATURE_COLUMNS)
        self.target_mapping = self.config.get("target_mapping", TARGET_MAPPING)

        self.preprocessor: Optional[ColumnTransformer] = None
        self.target_encoder: Optional[LabelEncoder] = None
        self.feature_names: List[str] = []
        self.preprocessing_decisions: Dict[str, Any] = {}

    def create_preprocessor(self, needs_scaling: bool = True) -> ColumnTransformer:
        """Create a ColumnTransformer for preprocessing."""
        transformers = []

        # Numerical features: impute missing values with median, then scale if needed
        if self.numerical_features:
            if needs_scaling:
                num_pipeline = Pipeline([
                    ("imputer", SimpleImputer(strategy="median")),
                    ("scaler", StandardScaler()),
                ])
            else:
                num_pipeline = Pipeline([
                    ("imputer", SimpleImputer(strategy="median")),
                ])
            transformers.append(("num", num_pipeline, self.numerical_features))

        # Categorical features: impute with most frequent
        if self.categorical_features:
            cat_pipeline = Pipeline([
                ("imputer", SimpleImputer(strategy="most_frequent")),
            ])
            transformers.append(("cat", cat_pipeline, self.categorical_features))

        preprocessor = ColumnTransformer(
            transformers=transformers,
            remainder="drop",
            verbose_feature_names_out=False,
        )

        return preprocessor

    def fit(self, X: pd.DataFrame, y: pd.Series, needs_scaling: bool = True) -> "PreprocessingPipeline":
        """Fit the preprocessing pipeline on training data."""
        logger.info(f"Fitting preprocessing pipeline for {self.disease}...")

        # Store feature names
        self.feature_names = self.feature_columns.copy()

        # Create and fit preprocessor
        self.preprocessor = self.create_preprocessor(needs_scaling=needs_scaling)
        self.preprocessor.fit(X)

        # Encode target
        self.target_encoder = LabelEncoder()
        y_binary = y.map(self.target_mapping)
        if y_binary.isnull().any():
            y_binary = y_binary.fillna(0).astype(int)
        self.target_encoder.fit(y_binary)

        # Record preprocessing decisions
        self.preprocessing_decisions = {
            "disease": self.disease,
            "numerical_features": self.numerical_features,
            "categorical_features": self.categorical_features,
            "needs_scaling": needs_scaling,
            "target_mapping": self.target_mapping,
            "target_classes": self.target_encoder.classes_.tolist(),
            "feature_names_in": self.feature_names,
            "random_state": RANDOM_STATE,
        }

        logger.info(f"Preprocessing pipeline for {self.disease} fitted successfully")
        return self

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        """Transform features using fitted preprocessor."""
        if self.preprocessor is None:
            raise ValueError("Preprocessor not fitted. Call fit() first.")
        return self.preprocessor.transform(X)

    def fit_transform(self, X: pd.DataFrame, y: pd.Series, needs_scaling: bool = True) -> Tuple[np.ndarray, np.ndarray]:
        """Fit and transform in one step."""
        self.fit(X, y, needs_scaling)
        X_transformed = self.transform(X)
        y_binary = y.map(self.target_mapping)
        if y_binary.isnull().any():
            y_binary = y_binary.fillna(0).astype(int)
        return X_transformed, y_binary.values

    def transform_target(self, y: pd.Series) -> np.ndarray:
        """Transform target using fitted encoder."""
        if self.target_encoder is None:
            raise ValueError("Target encoder not fitted. Call fit() first.")
        y_binary = y.map(self.target_mapping)
        if y_binary.isnull().any():
            y_binary = y_binary.fillna(0).astype(int)
        return self.target_encoder.transform(y_binary)

    def inverse_transform_target(self, y_encoded: np.ndarray) -> np.ndarray:
        """Convert encoded target back to original labels."""
        if self.target_encoder is None:
            raise ValueError("Target encoder not fitted. Call fit() first.")
        return self.target_encoder.inverse_transform(y_encoded)

    def get_feature_names_out(self) -> List[str]:
        """Get output feature names after preprocessing."""
        if self.preprocessor is None:
            raise ValueError("Preprocessor not fitted. Call fit() first.")
        return self.preprocessor.get_feature_names_out().tolist()

    def save(self, filepath: str) -> None:
        """Save the preprocessing pipeline to disk."""
        if self.preprocessor is None:
            raise ValueError("Preprocessor not fitted. Call fit() first.")

        save_dict = {
            "disease": self.disease,
            "preprocessor": self.preprocessor,
            "target_encoder": self.target_encoder,
            "feature_names": self.feature_names,
            "preprocessing_decisions": self.preprocessing_decisions,
        }
        joblib.dump(save_dict, filepath)
        logger.info(f"Preprocessing pipeline saved to {filepath}")

    @classmethod
    def load(cls, filepath: str) -> "PreprocessingPipeline":
        """Load a preprocessing pipeline from disk."""
        save_dict = joblib.load(filepath)
        disease = save_dict.get("disease", DEFAULT_DISEASE)
        pipeline = cls(disease=disease)
        pipeline.preprocessor = save_dict["preprocessor"]
        pipeline.target_encoder = save_dict["target_encoder"]
        pipeline.feature_names = save_dict["feature_names"]
        pipeline.preprocessing_decisions = save_dict.get("preprocessing_decisions", {})
        logger.info(f"Preprocessing pipeline loaded from {filepath}")
        return pipeline


def split_data(
    X: pd.DataFrame,
    y: pd.Series,
    test_size: float = TEST_SIZE,
    random_state: int = RANDOM_STATE,
    stratify: bool = True,
    disease: str = DEFAULT_DISEASE,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Split data into train and test sets with stratification."""
    cfg = get_disease_config(disease)
    target_mapping = cfg.get("target_mapping", TARGET_MAPPING)
    stratify_param = y.map(target_mapping) if stratify else None
    if stratify_param is not None and stratify_param.isnull().any():
        stratify_param = stratify_param.fillna(0).astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=stratify_param
    )
    logger.info(f"Data split for {disease}: train={X_train.shape[0]}, test={X_test.shape[0]}")
    return X_train, X_test, y_train, y_test


def check_class_balance(y: pd.Series, disease: str = DEFAULT_DISEASE) -> Dict[str, Any]:
    """Check class balance and return info."""
    cfg = get_disease_config(disease)
    target_mapping = cfg.get("target_mapping", TARGET_MAPPING)
    y_binary = y.map(target_mapping)
    if y_binary.isnull().any():
        y_binary = y_binary.fillna(0).astype(int)

    class_counts = y_binary.value_counts().sort_index()
    total = len(y_binary)
    balance_info = {
        "disease": disease,
        "class_counts": class_counts.to_dict(),
        "class_percentages": (class_counts / total * 100).to_dict(),
        "is_balanced": bool(min(class_counts) / max(class_counts) > 0.5),
        "imbalance_ratio": float(max(class_counts) / min(class_counts)),
    }
    logger.info(f"Class balance for {disease}: {balance_info}")
    return balance_info
