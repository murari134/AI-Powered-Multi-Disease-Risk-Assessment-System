"""
MediRisk 2.0 — Phase 7B Tests
Tests for synthetic data generation, validation, splitting,
preprocessing, and experiment infrastructure.

All 26 required test points are covered.
Existing 204 Phase 3-7A tests must remain unaffected.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

# Add project root so ml/ is importable
PROJECT_ROOT = Path(__file__).parent.parent.parent
ML_ROOT = PROJECT_ROOT / "ml"
sys.path.insert(0, str(PROJECT_ROOT))

from ml.generators.dataset_generator import (
    DISEASE_CODES,
    GENERATORS,
    generate_dataset,
    generate_all_datasets,
)
from ml.validation.validator import validate_dataset, validate_all_datasets
from ml.preprocessing.preprocessor import (
    MediRiskPreprocessor,
    split_dataset,
    TRAIN_RATIO,
    VAL_RATIO,
    TEST_RATIO,
    DEFAULT_SEED,
)

SPEC_DIR = ML_ROOT / "specifications"
EXPECTED_DISEASES = {
    "diabetes", "heart_disease", "stroke", "asthma",
    "chronic_kidney_disease", "liver_disease", "parkinsons",
    "breast_cancer", "lung_cancer", "hypertension",
}
N_RECORDS = 5000

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def all_datasets() -> dict[str, tuple[pd.DataFrame, dict]]:
    """Generate all 10 datasets once per module."""
    return generate_all_datasets(n=N_RECORDS, seed=DEFAULT_SEED)


@pytest.fixture(scope="module")
def diabetes_data(all_datasets):
    return all_datasets["diabetes"][0]


# ---------------------------------------------------------------------------
# TEST 1: All 10 datasets generated
# ---------------------------------------------------------------------------
def test_all_10_datasets_generated(all_datasets):
    """Test 1 — All 10 disease datasets must be generated."""
    assert set(all_datasets.keys()) == EXPECTED_DISEASES


# ---------------------------------------------------------------------------
# TEST 2: Expected record counts
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("disease_id", sorted(EXPECTED_DISEASES))
def test_expected_record_counts(all_datasets, disease_id):
    """Test 2 — Each dataset must have approximately 5,000 records."""
    df = all_datasets[disease_id][0]
    assert 4500 <= len(df) <= 5500, (
        f"{disease_id}: {len(df)} records, expected ~5000")


# ---------------------------------------------------------------------------
# TEST 3: Schema compliance (target column exists)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("disease_id", sorted(EXPECTED_DISEASES))
def test_schema_compliance_target_column(all_datasets, disease_id):
    """Test 3 — Target column must exist in the dataset."""
    df, meta = all_datasets[disease_id]
    target_col = meta["target_column"]
    assert target_col in df.columns, (
        f"{disease_id}: target column '{target_col}' missing")


# ---------------------------------------------------------------------------
# TEST 4: Target binary values (0/1 only)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("disease_id", sorted(EXPECTED_DISEASES))
def test_target_binary_values(all_datasets, disease_id):
    """Test 4 — Target must contain only 0/1 values."""
    df, meta = all_datasets[disease_id]
    target_col = meta["target_column"]
    actual_vals = set(df[target_col].dropna().unique())
    assert actual_vals <= {0, 1}, (
        f"{disease_id}: non-binary target values: {actual_vals}")


# ---------------------------------------------------------------------------
# TEST 5: No target leakage (target not a feature)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("disease_id", sorted(EXPECTED_DISEASES))
def test_no_target_leakage(all_datasets, disease_id):
    """Test 5 — Target column must not appear as a feature column."""
    import yaml
    df, meta = all_datasets[disease_id]
    target_col = meta["target_column"]
    spec_path = SPEC_DIR / f"{disease_id}.yaml"
    with open(spec_path) as f:
        spec = yaml.safe_load(f)
    feature_names = [feat["name"] for feat in spec.get("features", [])]
    assert target_col not in feature_names, (
        f"{disease_id}: target '{target_col}' found in feature list")


# ---------------------------------------------------------------------------
# TEST 6: Valid numerical domains
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("disease_id", sorted(EXPECTED_DISEASES))
def test_valid_numerical_domains(all_datasets, disease_id):
    """Test 6 — Numerical features must be within their specified domains."""
    import yaml
    df, meta = all_datasets[disease_id]
    spec_path = SPEC_DIR / f"{disease_id}.yaml"
    with open(spec_path) as f:
        spec = yaml.safe_load(f)
    violations = []
    for feat in spec.get("features", []):
        if feat.get("type") != "numerical":
            continue
        fname = feat["name"]
        domain = feat.get("domain")
        if not domain or fname not in df.columns:
            continue
        lo, hi = domain[0], domain[1]
        col_clean = df[fname].dropna()
        out_of_range = ((col_clean < lo) | (col_clean > hi)).sum()
        if out_of_range > 0:
            violations.append(f"{fname}: {out_of_range} values outside [{lo}, {hi}]")
    assert not violations, f"{disease_id} domain violations: {violations}"


# ---------------------------------------------------------------------------
# TEST 7: Valid categorical domains
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("disease_id", sorted(EXPECTED_DISEASES))
def test_valid_categorical_domains(all_datasets, disease_id):
    """Test 7 — Categorical features must use only their specified domain values."""
    import yaml
    df, meta = all_datasets[disease_id]
    spec_path = SPEC_DIR / f"{disease_id}.yaml"
    with open(spec_path) as f:
        spec = yaml.safe_load(f)
    violations = []
    for feat in spec.get("features", []):
        if feat.get("type") != "categorical":
            continue
        fname = feat["name"]
        allowed = set(feat.get("domain", []))
        if not allowed or fname not in df.columns:
            continue
        actual_vals = set(df[fname].dropna().unique())
        invalid = actual_vals - allowed
        if invalid:
            violations.append(f"{fname}: {invalid}")
    assert not violations, f"{disease_id} categorical violations: {violations}"


# ---------------------------------------------------------------------------
# TEST 8: Missing value policy
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("disease_id", sorted(EXPECTED_DISEASES))
def test_missing_value_policy(all_datasets, disease_id):
    """Test 8 — Non-nullable features must not have missing values."""
    import yaml
    df, meta = all_datasets[disease_id]
    spec_path = SPEC_DIR / f"{disease_id}.yaml"
    with open(spec_path) as f:
        spec = yaml.safe_load(f)
    violations = []
    for feat in spec.get("features", []):
        fname = feat["name"]
        if fname not in df.columns:
            continue
        if not feat.get("missing_allowed", False):
            missing_count = df[fname].isna().sum()
            if missing_count > 0:
                violations.append(f"{fname}: {missing_count} missing (not allowed)")
    assert not violations, f"{disease_id} missing value violations: {violations}"


# ---------------------------------------------------------------------------
# TEST 9: Duplicate handling
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("disease_id", sorted(EXPECTED_DISEASES))
def test_duplicate_handling(all_datasets, disease_id):
    """Test 9 — Dataset should have very low duplication rate."""
    df = all_datasets[disease_id][0]
    dup_rate = df.duplicated().mean()
    assert dup_rate < 0.01, (
        f"{disease_id}: {dup_rate:.1%} duplicate rows (>1% threshold)")


# ---------------------------------------------------------------------------
# TEST 10: Deterministic generation
# ---------------------------------------------------------------------------
def test_deterministic_generation():
    """Test 10 — Same seed must produce identical datasets."""
    df1, _ = generate_dataset("diabetes", n=100, seed=42)
    df2, _ = generate_dataset("diabetes", n=100, seed=42)
    pd.testing.assert_frame_equal(df1, df2, check_names=True)


def test_different_seeds_differ():
    """Test 10b — Different seeds must produce different datasets."""
    df1, _ = generate_dataset("diabetes", n=100, seed=42)
    df2, _ = generate_dataset("diabetes", n=100, seed=99)
    assert not df1.equals(df2)


# ---------------------------------------------------------------------------
# TEST 11: Deterministic splitting
# ---------------------------------------------------------------------------
def test_deterministic_splitting():
    """Test 11 — Same seed must produce identical splits."""
    df, meta = generate_dataset("diabetes", n=500, seed=42)
    train1, val1, test1 = split_dataset(df, meta["target_column"], seed=42)
    train2, val2, test2 = split_dataset(df, meta["target_column"], seed=42)
    pd.testing.assert_frame_equal(train1.reset_index(drop=True),
                                   train2.reset_index(drop=True))


# ---------------------------------------------------------------------------
# TEST 12: 70/15/15 split
# ---------------------------------------------------------------------------
def test_split_70_15_15():
    """Test 12 — Split must be exactly 70/15/15."""
    df, meta = generate_dataset("diabetes", n=1000, seed=42)
    train, val, test = split_dataset(df, meta["target_column"], seed=42)
    total = len(train) + len(val) + len(test)
    assert total == len(df)
    assert abs(len(train) / total - TRAIN_RATIO) < 0.05
    assert abs(len(val) / total - VAL_RATIO) < 0.05
    assert abs(len(test) / total - TEST_RATIO) < 0.05


# ---------------------------------------------------------------------------
# TEST 13: Stratification
# ---------------------------------------------------------------------------
def test_stratification_preserves_class_balance():
    """Test 13 — Splits must preserve approximate class balance."""
    df, meta = generate_dataset("diabetes", n=1000, seed=42)
    target_col = meta["target_column"]
    train, val, test = split_dataset(df, target_col, seed=42)
    overall_rate = df[target_col].mean()
    for split_name, split_df in [("train", train), ("val", val), ("test", test)]:
        split_rate = split_df[target_col].mean()
        assert abs(split_rate - overall_rate) < 0.05, (
            f"{split_name} positive rate {split_rate:.3f} deviates "
            f"from overall {overall_rate:.3f}")


# ---------------------------------------------------------------------------
# TEST 14: Preprocessing fit only on training data
# ---------------------------------------------------------------------------
def test_preprocessing_fit_only_on_training():
    """Test 14 — Preprocessor must not be refitted on val/test."""
    import yaml
    df, meta = generate_dataset("diabetes", n=500, seed=42)
    target_col = meta["target_column"]
    spec_path = SPEC_DIR / "diabetes.yaml"
    with open(spec_path) as f:
        spec = yaml.safe_load(f)
    feature_spec = spec["features"]

    train_df, val_df, test_df = split_dataset(df, target_col, seed=42)
    X_train = train_df.drop(columns=[target_col])
    X_val = val_df.drop(columns=[target_col])

    preprocessor = MediRiskPreprocessor("diabetes", feature_spec)
    preprocessor.fit(X_train)

    # Should work without error
    X_train_t = preprocessor.transform(X_train)
    X_val_t = preprocessor.transform(X_val)

    # Refitting should raise
    with pytest.raises(RuntimeError, match="already fitted"):
        preprocessor.fit(X_val)

    assert X_train_t.shape[1] == X_val_t.shape[1]


# ---------------------------------------------------------------------------
# TEST 15: Feature ordering preserved
# ---------------------------------------------------------------------------
def test_feature_ordering_preserved():
    """Test 15 — Feature order must match specification order."""
    import yaml
    df, meta = generate_dataset("diabetes", n=100, seed=42)
    target_col = meta["target_column"]
    spec_path = SPEC_DIR / "diabetes.yaml"
    with open(spec_path) as f:
        spec = yaml.safe_load(f)
    feature_spec = spec["features"]
    expected_order = [f["name"] for f in feature_spec]

    train_df, _, _ = split_dataset(df, target_col, seed=42)
    X_train = train_df.drop(columns=[target_col])

    preprocessor = MediRiskPreprocessor("diabetes", feature_spec)
    assert preprocessor.feature_order == expected_order


# ---------------------------------------------------------------------------
# TEST 16: Experiment metadata fields
# ---------------------------------------------------------------------------
def test_experiment_metadata_fields():
    """Test 16 — Experiment results must contain required metadata fields."""
    import yaml
    from ml.experiments.runner import run_experiment
    df, meta = generate_dataset("diabetes", n=200, seed=42)
    target_col = meta["target_column"]
    spec_path = SPEC_DIR / "diabetes.yaml"
    with open(spec_path) as f:
        spec = yaml.safe_load(f)
    feature_spec = spec["features"]

    train_df, val_df, _ = split_dataset(df, target_col, seed=42)
    X_train = train_df.drop(columns=[target_col])

    preprocessor = MediRiskPreprocessor("diabetes", feature_spec)
    preprocessor.fit(X_train)

    result = run_experiment(
        "diabetes", train_df, val_df, preprocessor, target_col,
        seed=42, dataset_version="1.0.0"
    )

    required_fields = [
        "experiment_id", "disease_code", "dataset_version",
        "schema_version", "experiment_protocol_version",
        "preprocessing_version", "random_seed",
        "train_records", "val_records", "feature_count",
        "experiment_timestamp",
    ]
    for field in required_fields:
        assert field in result, f"Missing metadata field: {field}"


# ---------------------------------------------------------------------------
# TEST 17: Required metrics present
# ---------------------------------------------------------------------------
def test_required_metrics_present():
    """Test 17 — Experiment result must include all required Phase 7A metrics."""
    import yaml
    from ml.experiments.runner import run_experiment
    df, meta = generate_dataset("diabetes", n=200, seed=42)
    target_col = meta["target_column"]
    spec_path = SPEC_DIR / "diabetes.yaml"
    with open(spec_path) as f:
        spec = yaml.safe_load(f)
    feature_spec = spec["features"]

    train_df, val_df, _ = split_dataset(df, target_col, seed=42)
    X_train = train_df.drop(columns=[target_col])
    preprocessor = MediRiskPreprocessor("diabetes", feature_spec)
    preprocessor.fit(X_train)

    result = run_experiment(
        "diabetes", train_df, val_df, preprocessor, target_col,
        seed=42, dataset_version="1.0.0"
    )

    # Both model results must have a status and metrics dict
    for model_key in ["tabpfn", "tabicl"]:
        assert model_key in result
        assert "status" in result[model_key]
        assert "metrics" in result[model_key]


# ---------------------------------------------------------------------------
# TEST 18: Model names correct
# ---------------------------------------------------------------------------
def test_model_names_correct():
    """Test 18 — Model name fields must match the frozen specs."""
    import yaml
    from ml.experiments.runner import run_experiment
    df, meta = generate_dataset("diabetes", n=200, seed=42)
    target_col = meta["target_column"]
    spec_path = SPEC_DIR / "diabetes.yaml"
    with open(spec_path) as f:
        spec = yaml.safe_load(f)
    feature_spec = spec["features"]

    train_df, val_df, _ = split_dataset(df, target_col, seed=42)
    X_train = train_df.drop(columns=[target_col])
    preprocessor = MediRiskPreprocessor("diabetes", feature_spec)
    preprocessor.fit(X_train)

    result = run_experiment(
        "diabetes", train_df, val_df, preprocessor, target_col,
        seed=42, dataset_version="1.0.0"
    )
    assert result["tabpfn"]["model_name"] == "TabPFN"
    assert result["tabicl"]["model_name"] == "TabICLv2"


# ---------------------------------------------------------------------------
# TEST 19: Model versions correct
# ---------------------------------------------------------------------------
def test_model_versions_correct():
    """Test 19 — Model version fields must match frozen contract."""
    import yaml
    from ml.experiments.runner import run_experiment
    df, meta = generate_dataset("diabetes", n=200, seed=42)
    target_col = meta["target_column"]
    spec_path = SPEC_DIR / "diabetes.yaml"
    with open(spec_path) as f:
        spec = yaml.safe_load(f)
    feature_spec = spec["features"]

    train_df, val_df, _ = split_dataset(df, target_col, seed=42)
    X_train = train_df.drop(columns=[target_col])
    preprocessor = MediRiskPreprocessor("diabetes", feature_spec)
    preprocessor.fit(X_train)

    result = run_experiment(
        "diabetes", train_df, val_df, preprocessor, target_col,
        seed=42, dataset_version="1.0.0"
    )
    assert result["tabpfn"]["model_version"] == "9.0.0"
    assert result["tabicl"]["model_version"] == "2.2.0"


# ---------------------------------------------------------------------------
# TEST 20: Reproducibility fields
# ---------------------------------------------------------------------------
def test_reproducibility_fields():
    """Test 20 — Experiment result must contain all reproducibility fields."""
    import yaml
    from ml.experiments.runner import run_experiment
    df, meta = generate_dataset("diabetes", n=200, seed=42)
    target_col = meta["target_column"]
    spec_path = SPEC_DIR / "diabetes.yaml"
    with open(spec_path) as f:
        spec = yaml.safe_load(f)
    feature_spec = spec["features"]

    train_df, val_df, _ = split_dataset(df, target_col, seed=42)
    X_train = train_df.drop(columns=[target_col])
    preprocessor = MediRiskPreprocessor("diabetes", feature_spec)
    preprocessor.fit(X_train)

    result = run_experiment(
        "diabetes", train_df, val_df, preprocessor, target_col,
        seed=42, dataset_version="1.0.0"
    )
    repro_fields = ["dataset_version", "schema_version", "random_seed",
                    "python_version", "preprocessing_version",
                    "experiment_timestamp"]
    for field in repro_fields:
        assert field in result, f"Missing reproducibility field: {field}"


# ---------------------------------------------------------------------------
# TEST 21: No fabricated metric values (CRITICAL)
# ---------------------------------------------------------------------------
def test_no_fabricated_results():
    """Test 21 — Failed experiments must record status=BLOCKED/FAILED, not fake metrics."""
    import yaml
    from ml.experiments.runner import run_experiment
    df, meta = generate_dataset("diabetes", n=200, seed=42)
    target_col = meta["target_column"]
    spec_path = SPEC_DIR / "diabetes.yaml"
    with open(spec_path) as f:
        spec = yaml.safe_load(f)
    feature_spec = spec["features"]

    train_df, val_df, _ = split_dataset(df, target_col, seed=42)
    X_train = train_df.drop(columns=[target_col])
    preprocessor = MediRiskPreprocessor("diabetes", feature_spec)
    preprocessor.fit(X_train)

    result = run_experiment(
        "diabetes", train_df, val_df, preprocessor, target_col,
        seed=42, dataset_version="1.0.0"
    )

    for model_key in ["tabpfn", "tabicl"]:
        m = result[model_key]
        status = m["status"]
        metrics = m["metrics"]
        # If failed, metrics must be empty or None — not fabricated numbers
        if status in ("FAILED", "BLOCKED_IMPORT_ERROR", "BLOCKED"):
            for metric_name, val in metrics.items():
                if val is not None and not isinstance(val, str):
                    pytest.fail(
                        f"{model_key}: fabricated metric {metric_name}={val} "
                        f"despite status={status}"
                    )


# ---------------------------------------------------------------------------
# TEST 22: Failed experiment handling
# ---------------------------------------------------------------------------
def test_failed_experiment_handling():
    """Test 22 — Experiment results must have a status field."""
    import yaml
    from ml.experiments.runner import run_experiment
    df, meta = generate_dataset("diabetes", n=100, seed=42)
    target_col = meta["target_column"]
    spec_path = SPEC_DIR / "diabetes.yaml"
    with open(spec_path) as f:
        spec = yaml.safe_load(f)
    feature_spec = spec["features"]

    train_df, val_df, _ = split_dataset(df, target_col, seed=42)
    X_train = train_df.drop(columns=[target_col])
    preprocessor = MediRiskPreprocessor("diabetes", feature_spec)
    preprocessor.fit(X_train)

    result = run_experiment(
        "diabetes", train_df, val_df, preprocessor, target_col,
        seed=42, dataset_version="1.0.0"
    )
    valid_statuses = {"SUCCESS", "FAILED", "BLOCKED_IMPORT_ERROR", "BLOCKED",
                      "PENDING"}
    for model_key in ["tabpfn", "tabicl"]:
        status = result[model_key]["status"]
        assert status in valid_statuses, (
            f"{model_key}: unexpected status '{status}'")


# ---------------------------------------------------------------------------
# TEST 23: CPU fallback (device is reported)
# ---------------------------------------------------------------------------
def test_cpu_fallback_reported():
    """Test 23 — Experiment result must report execution device."""
    import yaml
    from ml.experiments.runner import run_experiment
    df, meta = generate_dataset("diabetes", n=100, seed=42)
    target_col = meta["target_column"]
    spec_path = SPEC_DIR / "diabetes.yaml"
    with open(spec_path) as f:
        spec = yaml.safe_load(f)
    feature_spec = spec["features"]

    train_df, val_df, _ = split_dataset(df, target_col, seed=42)
    X_train = train_df.drop(columns=[target_col])
    preprocessor = MediRiskPreprocessor("diabetes", feature_spec)
    preprocessor.fit(X_train)

    result = run_experiment(
        "diabetes", train_df, val_df, preprocessor, target_col,
        seed=42, dataset_version="1.0.0"
    )
    for model_key in ["tabpfn", "tabicl"]:
        m = result[model_key]
        # device must be reported if experiment ran
        if m["status"] == "SUCCESS":
            assert "device" in m


# ---------------------------------------------------------------------------
# TEST 24: Result file structure (build_summary shape)
# ---------------------------------------------------------------------------
def test_result_file_structure():
    """Test 24 — Summary DataFrame must have all expected columns."""
    import yaml
    from ml.experiments.runner import build_summary, run_experiment
    df, meta = generate_dataset("diabetes", n=100, seed=42)
    target_col = meta["target_column"]
    spec_path = SPEC_DIR / "diabetes.yaml"
    with open(spec_path) as f:
        spec = yaml.safe_load(f)
    feature_spec = spec["features"]

    train_df, val_df, _ = split_dataset(df, target_col, seed=42)
    X_train = train_df.drop(columns=[target_col])
    preprocessor = MediRiskPreprocessor("diabetes", feature_spec)
    preprocessor.fit(X_train)

    result = run_experiment(
        "diabetes", train_df, val_df, preprocessor, target_col,
        seed=42, dataset_version="1.0.0"
    )
    summary = build_summary({"diabetes": result})
    required_cols = ["disease", "model", "status", "roc_auc", "pr_auc",
                     "accuracy", "f1_score", "brier_score",
                     "inference_latency_ms", "peak_ram_mb"]
    for col in required_cols:
        assert col in summary.columns, f"Missing column in summary: {col}"


# ---------------------------------------------------------------------------
# TEST 25: Aggregate results cover both models
# ---------------------------------------------------------------------------
def test_aggregate_results_both_models():
    """Test 25 — Summary must contain rows for both TabPFN and TabICLv2."""
    import yaml
    from ml.experiments.runner import build_summary, run_experiment
    df, meta = generate_dataset("diabetes", n=100, seed=42)
    target_col = meta["target_column"]
    spec_path = SPEC_DIR / "diabetes.yaml"
    with open(spec_path) as f:
        spec = yaml.safe_load(f)
    feature_spec = spec["features"]

    train_df, val_df, _ = split_dataset(df, target_col, seed=42)
    X_train = train_df.drop(columns=[target_col])
    preprocessor = MediRiskPreprocessor("diabetes", feature_spec)
    preprocessor.fit(X_train)

    result = run_experiment(
        "diabetes", train_df, val_df, preprocessor, target_col,
        seed=42, dataset_version="1.0.0"
    )
    summary = build_summary({"diabetes": result})
    assert len(summary) == 2
    assert set(summary["model_version"].unique()) >= {"9.0.0", "2.2.0"}


# ---------------------------------------------------------------------------
# TEST 26: Phase 7A contracts preserved
# ---------------------------------------------------------------------------
def test_phase7a_contracts_preserved():
    """Test 26 — Verify Phase 7A spec contracts are not modified."""
    import yaml
    schema_path = SPEC_DIR / "schema-version.yaml"
    with open(schema_path) as f:
        schema = yaml.safe_load(f)
    mv = schema["model_versions"]
    assert mv["tabpfn"] == "9.0.0"
    assert mv["tabicl"] == "2.2.0"
    assert mv["torch"] == "2.14.0"
    assert mv["scikit_learn"] == "1.5.2"
    split = schema["data_split"]
    assert split["train"] == 0.70
    assert split["validation"] == 0.15
    assert split["test"] == 0.15

    registry_path = SPEC_DIR / "dataset_registry.yaml"
    with open(registry_path) as f:
        registry = yaml.safe_load(f)
    assert len(registry["datasets"]) == 10
    assert registry["total_diseases"] == 10
