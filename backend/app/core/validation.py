"""Input validation module supporting multiple clinical disease schemas."""

from typing import Dict, Any, List, Tuple, Optional, Union
import re

from app.core.clinical_config import (
    DEFAULT_DISEASE,
    DISEASES_CONFIG,
    get_disease_config,
    FEATURE_COLUMNS,
    CATEGORICAL_FEATURES,
    NUMERICAL_FEATURES,
    FEATURE_RANGES,
    FEATURE_DESCRIPTIONS,
)


class ValidationError(Exception):
    """Custom exception for validation errors."""
    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


class InputValidator:
    """Validates user inputs for clinical disease prediction systems."""

    def __init__(self, disease: str = DEFAULT_DISEASE):
        self.disease = disease
        self.config = get_disease_config(disease)
        self.feature_columns = self.config.get("feature_columns", FEATURE_COLUMNS)
        self.categorical_features = self.config.get("categorical_features", CATEGORICAL_FEATURES)
        self.numerical_features = self.config.get("numerical_features", NUMERICAL_FEATURES)
        self.feature_ranges = self.config.get("feature_ranges", FEATURE_RANGES)
        self.feature_descriptions = self.config.get("feature_descriptions", FEATURE_DESCRIPTIONS)

    def validate(self, input_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate input data against disease schema and return (is_valid, errors)."""
        errors = []

        # Check for missing features
        missing = set(self.feature_columns) - set(input_data.keys())
        if missing:
            errors.append(f"Missing required features: {', '.join(sorted(missing))}")

        # Check for extra features
        extra = set(input_data.keys()) - set(self.feature_columns)
        if extra:
            errors.append(f"Unexpected features: {', '.join(sorted(extra))}")

        # Validate each feature
        for feature in self.feature_columns:
            if feature not in input_data:
                continue

            value = input_data[feature]
            feature_errors = self._validate_feature(feature, value)
            errors.extend(feature_errors)

        return len(errors) == 0, errors

    def _validate_feature(self, feature: str, value: Any) -> List[str]:
        """Validate a single feature value."""
        errors = []

        # Check for None
        if value is None:
            errors.append(f"{feature}: value cannot be empty")
            return errors

        # Check for NaN
        if isinstance(value, float) and (value != value):
            errors.append(f"{feature}: value cannot be NaN")
            return errors

        # Type and range validation
        if feature in self.numerical_features:
            errors.extend(self._validate_numerical(feature, value))
        elif feature in self.categorical_features:
            errors.extend(self._validate_categorical(feature, value))

        return errors

    def _validate_numerical(self, feature: str, value: Any) -> List[str]:
        """Validate a numerical feature."""
        errors = []

        try:
            num_value = float(value)
        except (ValueError, TypeError):
            errors.append(f"{feature}: must be a number, got {type(value).__name__}")
            return errors

        # Check range
        if feature in self.feature_ranges:
            min_val, max_val = self.feature_ranges[feature]
            if num_value < min_val or num_value > max_val:
                errors.append(
                    f"{feature}: value {num_value} out of valid range [{min_val}, {max_val}]"
                )

        return errors

    def _get_valid_categorical_values(self, feature: str) -> List[int]:
        """Get valid values for a categorical feature across all diseases."""
        valid_values = {
            "sex": [0, 1],
            "Gender": [0, 1],
            "cp": [1, 2, 3, 4],
            "fbs": [0, 1],
            "restecg": [0, 1, 2],
            "exang": [0, 1],
            "slope": [1, 2, 3],
            "ca": [0, 1, 2, 3],
            "thal": [3, 6, 7],
        }
        return valid_values.get(feature, [])

    def _validate_categorical(self, feature: str, value: Any) -> List[str]:
        """Validate a categorical feature."""
        errors = []

        valid_values = self._get_valid_categorical_values(feature)
        if not valid_values:
            return errors

        try:
            int_value = int(value)
        except (ValueError, TypeError):
            errors.append(f"{feature}: must be an integer, got {type(value).__name__}")
            return errors

        if int_value not in valid_values:
            errors.append(
                f"{feature}: value {int_value} not in valid values {valid_values}"
            )

        return errors

    def sanitize_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize and convert input data to appropriate types."""
        sanitized = {}

        for feature in self.feature_columns:
            if feature not in input_data:
                continue

            value = input_data[feature]

            if feature in self.numerical_features:
                try:
                    sanitized[feature] = float(value)
                except (ValueError, TypeError):
                    sanitized[feature] = value
            elif feature in self.categorical_features:
                try:
                    sanitized[feature] = int(value)
                except (ValueError, TypeError):
                    sanitized[feature] = value
            else:
                sanitized[feature] = value

        return sanitized

    def get_feature_schema(self) -> Dict[str, Dict[str, Any]]:
        """Get the complete feature schema for UI generation."""
        schema = {}
        for feature in self.feature_columns:
            schema[feature] = {
                "name": feature,
                "description": self.feature_descriptions.get(feature, ""),
                "type": "numerical" if feature in self.numerical_features else "categorical",
                "required": True,
                "range": self.feature_ranges.get(feature),
            }

            if feature in self.categorical_features:
                valid_options_map = {
                    "sex": [{"value": 0, "label": "Female"}, {"value": 1, "label": "Male"}],
                    "Gender": [{"value": 0, "label": "Female"}, {"value": 1, "label": "Male"}],
                    "cp": [
                        {"value": 1, "label": "Typical Angina"},
                        {"value": 2, "label": "Atypical Angina"},
                        {"value": 3, "label": "Non-anginal Pain"},
                        {"value": 4, "label": "Asymptomatic"},
                    ],
                    "fbs": [{"value": 0, "label": "No (≤120 mg/dl)"}, {"value": 1, "label": "Yes (>120 mg/dl)"}],
                    "restecg": [
                        {"value": 0, "label": "Normal"},
                        {"value": 1, "label": "ST-T Wave Abnormality"},
                        {"value": 2, "label": "Left Ventricular Hypertrophy"},
                    ],
                    "exang": [{"value": 0, "label": "No"}, {"value": 1, "label": "Yes"}],
                    "slope": [
                        {"value": 1, "label": "Upsloping"},
                        {"value": 2, "label": "Flat"},
                        {"value": 3, "label": "Downsloping"},
                    ],
                    "ca": [
                        {"value": 0, "label": "0 vessels"},
                        {"value": 1, "label": "1 vessel"},
                        {"value": 2, "label": "2 vessels"},
                        {"value": 3, "label": "3 vessels"},
                    ],
                    "thal": [
                        {"value": 3, "label": "Normal"},
                        {"value": 6, "label": "Fixed Defect"},
                        {"value": 7, "label": "Reversible Defect"},
                    ],
                }
                schema[feature]["options"] = valid_options_map.get(feature, [])

        return schema


def validate_input(input_data: Dict[str, Any], disease: str = DEFAULT_DISEASE) -> Tuple[bool, List[str]]:
    """Convenience function to validate input for a disease."""
    validator = InputValidator(disease=disease)
    return validator.validate(input_data)


def sanitize_input(input_data: Dict[str, Any], disease: str = DEFAULT_DISEASE) -> Dict[str, Any]:
    """Convenience function to sanitize input for a disease."""
    validator = InputValidator(disease=disease)
    return validator.sanitize_input(input_data)


def get_feature_schema(disease: str = DEFAULT_DISEASE) -> Dict[str, Dict[str, Any]]:
    """Convenience function to get feature schema for a disease."""
    validator = InputValidator(disease=disease)
    return validator.get_feature_schema()
