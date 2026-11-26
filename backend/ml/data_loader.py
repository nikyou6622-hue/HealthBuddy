"""Data loading and validation module supporting multiple clinical disease datasets."""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List
import logging

from config import (
    DATA_DIR,
    DEFAULT_DISEASE,
    DISEASES_CONFIG,
    get_disease_config,
    DATASET_PATH,
    FEATURE_COLUMNS,
    TARGET_COLUMN,
    FEATURE_RANGES,
    DATASET_INFO,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataLoader:
    """Handles loading and validation of clinical disease datasets."""

    def __init__(self, filepath: Optional[str] = None, disease: str = DEFAULT_DISEASE):
        self.disease = disease
        self.config = get_disease_config(disease)
        self.filepath = filepath or str(DATA_DIR / self.config["dataset_file"])
        self.data: Optional[pd.DataFrame] = None
        self._validation_report: Dict[str, Any] = {}

    def load(self) -> pd.DataFrame:
        """Load the dataset from CSV file according to disease configuration."""
        path_obj = Path(self.filepath)
        if not path_obj.exists():
            raise FileNotFoundError(f"Dataset not found at {self.filepath}")

        logger.info(f"Loading {self.disease} dataset from {self.filepath}")

        has_header = self.config.get("has_header", True)
        feature_cols = self.config["feature_columns"]
        target_col = self.config["target_column"]

        if not has_header:
            df = pd.read_csv(
                self.filepath,
                header=None,
                names=feature_cols + [target_col],
                na_values=["?", "NA", "nan", ""],
            )
        else:
            df = pd.read_csv(
                self.filepath,
                na_values=["?", "NA", "nan", ""],
            )

        # Drop identifier columns if present (e.g. 'name' in Parkinson's)
        if "name" in df.columns and "name" not in feature_cols:
            df = df.drop(columns=["name"])

        # Special dataset cleanups
        if self.disease == "liver_disease":
            if "Gender" in df.columns and df["Gender"].dtype == object:
                df["Gender"] = df["Gender"].map({"Female": 0, "Male": 1}).fillna(0).astype(int)
            if target_col in df.columns:
                # Target in raw ILPD is 1 (patient) vs 2 (healthy)
                if set(df[target_col].unique()).issubset({1, 2}):
                    df[target_col] = df[target_col].map({1: 1, 2: 0})

        self.data = df
        logger.info(f"Loaded {self.disease} dataset with shape: {self.data.shape}")
        return self.data

    def validate(self, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """Validate the dataset and return a validation report."""
        if df is None:
            df = self.data
        if df is None:
            raise ValueError("No data loaded. Call load() first.")

        feature_cols = self.config["feature_columns"]
        target_col = self.config["target_column"]
        feature_ranges = self.config.get("feature_ranges", {})

        report = {
            "disease": self.disease,
            "shape": df.shape,
            "columns": df.columns.tolist(),
            "dtypes": {k: str(v) for k, v in df.dtypes.items()},
            "missing_values": df.isnull().sum().to_dict(),
            "duplicate_rows": int(df.duplicated().sum()),
            "target_distribution": (
                df[target_col].value_counts().sort_index().to_dict()
                if target_col in df.columns else {}
            ),
            "feature_stats": (
                df[feature_cols].describe().to_dict()
                if all(c in df.columns for c in feature_cols) else {}
            ),
            "feature_ranges_check": {},
            "issues": [],
        }

        # Check feature ranges
        for feature, (min_val, max_val) in feature_ranges.items():
            if feature in df.columns:
                actual_min = df[feature].min()
                actual_max = df[feature].max()
                in_range = bool(
                    pd.notna(actual_min) and pd.notna(actual_max) and
                    (actual_min >= min_val) and (actual_max <= max_val)
                )
                report["feature_ranges_check"][feature] = {
                    "expected_min": min_val,
                    "expected_max": max_val,
                    "actual_min": float(actual_min) if pd.notna(actual_min) else None,
                    "actual_max": float(actual_max) if pd.notna(actual_max) else None,
                    "in_range": in_range,
                }
                if not in_range:
                    report["issues"].append(
                        f"Feature '{feature}' has values outside expected range "
                        f"[{min_val}, {max_val}]: actual [{actual_min}, {actual_max}]"
                    )

        # Check for missing values
        missing = df.isnull().sum()
        if missing.any():
            report["issues"].append(f"Missing values found: {missing[missing > 0].to_dict()}")

        # Check target column
        if target_col not in df.columns:
            report["issues"].append(f"Target column '{target_col}' not found")

        # Check all feature columns present
        missing_features = set(feature_cols) - set(df.columns)
        if missing_features:
            report["issues"].append(f"Missing feature columns: {missing_features}")

        self._validation_report = report
        logger.info(f"Validation for {self.disease} complete. Issues found: {len(report['issues'])}")
        return report

    def get_validation_report(self) -> Dict[str, Any]:
        """Return the validation report."""
        if not self._validation_report:
            self.validate()
        return self._validation_report

    def get_feature_data(self) -> Tuple[pd.DataFrame, pd.Series]:
        """Extract features X and target y."""
        if self.data is None:
            self.load()
        feature_cols = self.config["feature_columns"]
        target_col = self.config["target_column"]
        X = self.data[feature_cols]
        y = self.data[target_col]
        return X, y


def load_and_validate(
    filepath: Optional[str] = None,
    disease: str = DEFAULT_DISEASE
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Convenience function to load and validate a disease dataset."""
    loader = DataLoader(filepath=filepath, disease=disease)
    data = loader.load()
    report = loader.validate()
    return data, report
