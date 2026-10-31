"""
MediRisk 2.0 — Preprocessing Pipeline
Phase 7B

Implements the preprocessing contract defined in Phase 7A:
  - Numerical: StandardScaler (fit on train only)
  - Categorical: OrdinalEncoder (fit on train only)
  - Binary: passthrough
  - Missing: median/most_frequent imputation + missingness indicator

CRITICAL: preprocessing must ONLY be fit on training data.
Never fit on validation or test data.
"""

from __future__ import annotations

import json
import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OrdinalEncoder, StandardScaler

PREPROCESSING_VERSION = "1.0.0"
DEFAULT_SEED = 42
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15


class MediRiskPreprocessor:
    """
    Leakage-safe preprocessing pipeline for MediRisk 2.0.

    Fit ONLY on training data. Apply to val/test without re-fitting.
    """

    def __init__(self, disease_id: str, feature_spec: list[dict]):
        self.disease_id = disease_id
        self.feature_spec = feature_spec
        self.version = PREPROCESSING_VERSION

        # Categorize features
        self.numerical_features: list[str] = []
        self.categorical_features: list[str] = []
        self.binary_features: list[str] = []
        self.feature_order: list[str] = []

        for feat in feature_spec:
            name = feat["name"]
            ftype = feat.get("type", "numerical")
            self.feature_order.append(name)
            if ftype == "numerical":
                self.numerical_features.append(name)
            elif ftype == "categorical":
                self.categorical_features.append(name)
            elif ftype == "binary":
                self.binary_features.append(name)

        # Fitted components (set during fit())
        self._num_imputer: SimpleImputer | None = None
        self._cat_imputer: SimpleImputer | None = None
        self._scaler: StandardScaler | None = None
        self._encoder: OrdinalEncoder | None = None
        self._fitted: bool = False
        self._fit_timestamp: str | None = None
        # Features that had missing values in training data — always emit
        # missingness indicators for these features to keep column schema
        # consistent across train/val/test transforms.
        self._missing_indicator_features: list[str] = []

    def fit(self, X_train: pd.DataFrame) -> "MediRiskPreprocessor":
        """Fit imputers and transformers on training data ONLY."""
        if self._fitted:
            raise RuntimeError("Preprocessor already fitted. Do not re-fit.")

        available_num = [f for f in self.numerical_features if f in X_train.columns]
        available_cat = [f for f in self.categorical_features if f in X_train.columns]

        # Numerical imputation (median)
        if available_num:
            self._num_imputer = SimpleImputer(strategy="median")
            self._num_imputer.fit(X_train[available_num])
            self._scaler = StandardScaler()
            imputed_train_num = self._num_imputer.transform(X_train[available_num])
            self._scaler.fit(imputed_train_num)

        # Categorical imputation (most frequent) + encoding
        if available_cat:
            self._cat_imputer = SimpleImputer(strategy="most_frequent")
            self._cat_imputer.fit(X_train[available_cat])
            self._encoder = OrdinalEncoder(
                handle_unknown="use_encoded_value",
                unknown_value=-1,
            )
            imputed_train_cat = self._cat_imputer.transform(X_train[available_cat])
            imputed_df = pd.DataFrame(imputed_train_cat, columns=available_cat)
            self._encoder.fit(imputed_df)

        # Record which features had any missing values in training data.
        # This determines which _missing indicator columns will be emitted
        # by transform() — always, regardless of the incoming split's
        # missing-value pattern.  Ensures consistent column schema.
        self._missing_indicator_features = [
            f for f in (available_num + available_cat)
            if X_train[f].isna().any()
        ]

        self._fitted = True
        self._fit_timestamp = datetime.now(timezone.utc).isoformat()
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Transform a feature DataFrame using fitted preprocessing."""
        if not self._fitted:
            raise RuntimeError("Preprocessor not fitted. Call fit() first.")

        X = X.copy()
        available_num = [f for f in self.numerical_features if f in X.columns]
        available_cat = [f for f in self.categorical_features if f in X.columns]
        available_bin = [f for f in self.binary_features if f in X.columns]

        result_parts = {}

        # Emit missingness indicators for exactly the features that had
        # missing values in the training data (recorded at fit time).
        # This ensures a consistent output column schema across splits —
        # even when val/test happens to have no missing values for a feature
        # that was missing in training.
        for fname in self._missing_indicator_features:
            if fname in X.columns:
                result_parts[f"{fname}_missing"] = X[fname].isna().astype(int)
            else:
                # Feature absent in this split — emit all-zero indicator
                result_parts[f"{fname}_missing"] = pd.Series(
                    [0] * len(X), index=X.index, dtype=int)

        # Numerical: impute + scale
        if available_num and self._num_imputer is not None:
            imputed = self._num_imputer.transform(X[available_num])
            scaled = self._scaler.transform(imputed)
            for i, fname in enumerate(available_num):
                result_parts[fname] = scaled[:, i]

        # Categorical: impute + encode
        if available_cat and self._cat_imputer is not None:
            imputed_cat = self._cat_imputer.transform(X[available_cat])
            imputed_df = pd.DataFrame(imputed_cat, columns=available_cat,
                                       index=X.index)
            encoded = self._encoder.transform(imputed_df)
            for i, fname in enumerate(available_cat):
                result_parts[fname] = encoded[:, i]

        # Binary: passthrough (fill missing with 0)
        for fname in available_bin:
            result_parts[fname] = X[fname].fillna(0).astype(int).values

        result_df = pd.DataFrame(result_parts, index=X.index)
        return result_df

    def fit_transform(self, X_train: pd.DataFrame) -> pd.DataFrame:
        """Fit on training data and transform it."""
        return self.fit(X_train).transform(X_train)

    def to_dict(self) -> dict[str, Any]:
        return {
            "disease_id": self.disease_id,
            "version": self.version,
            "numerical_features": self.numerical_features,
            "categorical_features": self.categorical_features,
            "binary_features": self.binary_features,
            "feature_order": self.feature_order,
            "fitted": self._fitted,
            "fit_timestamp": self._fit_timestamp,
        }


def split_dataset(
    df: pd.DataFrame,
    target_col: str,
    *,
    train_ratio: float = TRAIN_RATIO,
    val_ratio: float = VAL_RATIO,
    test_ratio: float = TEST_RATIO,
    seed: int = DEFAULT_SEED,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Stratified 70/15/15 split.

    Returns: (train_df, val_df, test_df)

    IMPORTANT: The test set must remain untouched until final evaluation.
    """
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-9, \
        "Split ratios must sum to 1.0"

    X = df.drop(columns=[target_col])
    y = df[target_col]

    # First split: train vs (val+test)
    val_test_ratio = val_ratio + test_ratio
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=val_test_ratio, random_state=seed, stratify=y
    )

    # Second split: val vs test
    test_frac_of_temp = test_ratio / val_test_ratio
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=test_frac_of_temp,
        random_state=seed, stratify=y_temp
    )

    train_df = pd.concat([X_train, y_train], axis=1)
    val_df = pd.concat([X_val, y_val], axis=1)
    test_df = pd.concat([X_test, y_test], axis=1)

    return train_df, val_df, test_df


def save_splits(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    disease_id: str,
    dataset_version: str,
    output_dir: Path,
) -> dict[str, Any]:
    """Save the three splits and return split metadata."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    target_col = [c for c in train_df.columns if c.endswith("_outcome")][0]

    for split_name, split_df in [("train", train_df), ("val", val_df),
                                   ("test", test_df)]:
        path = output_dir / f"{disease_id}_v{dataset_version}_{split_name}.csv"
        split_df.to_csv(path, index=False)

    split_meta = {
        "disease_id": disease_id,
        "dataset_version": dataset_version,
        "schema_version": "1.0.0",
        "random_seed": DEFAULT_SEED,
        "target_column": target_col,
        "train_records": len(train_df),
        "val_records": len(val_df),
        "test_records": len(test_df),
        "train_positive_rate": float(train_df[target_col].mean()),
        "val_positive_rate": float(val_df[target_col].mean()),
        "test_positive_rate": float(test_df[target_col].mean()),
        "split_ratios": {"train": TRAIN_RATIO, "val": VAL_RATIO, "test": TEST_RATIO},
        "stratified": True,
    }
    meta_path = output_dir / f"{disease_id}_v{dataset_version}_split_metadata.json"
    meta_path.write_text(json.dumps(split_meta, indent=2))
    return split_meta
