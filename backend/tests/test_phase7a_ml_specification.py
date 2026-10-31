"""
MediRisk 2.0 — Phase 7A ML Specification Tests

Tests all 16 required Phase 7A verification points:
  1.  All 10 disease specification files exist
  2.  All disease codes are unique
  3.  Every disease has a target column defined
  4.  Every target is binary (0/1)
  5.  Every disease has feature definitions
  6.  Feature names follow snake_case convention
  7.  No duplicate feature names within a disease
  8.  No feature name equals the target column name
  9.  Dataset registry contains exactly 10 diseases
  10. All registry entries reference valid specification files
  11. Experiment manifest contains both TabPFN and TabICLv2
  12. Experiment protocol contains all required metrics
  13. Split percentages equal 70/15/15
  14. Schema version file exists
  15. No dataset artifacts were generated (no .csv/.parquet/.pkl/.joblib)
  16. No ML training was executed (no trained model artifacts)

Existing 178 tests must remain unaffected.
"""

import os
import re
import glob
from pathlib import Path

import pytest
import yaml

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent.parent  # medi-risk 2.0/
ML_ROOT = PROJECT_ROOT / "ml"
SPEC_DIR = ML_ROOT / "specifications"
DATASETS_DIR = ML_ROOT / "datasets"
EXPERIMENTS_DIR = ML_ROOT / "experiments"


EXPECTED_DISEASE_CODES = {
    "DIABETES",
    "HEART_DISEASE",
    "STROKE",
    "ASTHMA",
    "CHRONIC_KIDNEY_DISEASE",
    "LIVER_DISEASE",
    "PARKINSONS",
    "BREAST_CANCER",
    "LUNG_CANCER",
    "HYPERTENSION",
}

EXPECTED_SPEC_FILES = {
    "diabetes.yaml",
    "heart_disease.yaml",
    "stroke.yaml",
    "asthma.yaml",
    "chronic_kidney_disease.yaml",
    "liver_disease.yaml",
    "parkinsons.yaml",
    "breast_cancer.yaml",
    "lung_cancer.yaml",
    "hypertension.yaml",
}

REQUIRED_METRICS = {
    "roc_auc",
    "pr_auc",
    "accuracy",
    "precision",
    "recall",
    "sensitivity",
    "specificity",
    "f1_score",
    "brier_score",
    "expected_calibration_error",
    "inference_latency_ms",
    "ram_consumption_mb",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_yaml(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_all_specs() -> dict[str, dict]:
    """Return {filename_stem: parsed_yaml} for all 10 disease specs."""
    specs = {}
    for fname in EXPECTED_SPEC_FILES:
        path = SPEC_DIR / fname
        assert path.exists(), f"Spec file missing: {path}"
        specs[fname.replace(".yaml", "")] = load_yaml(path)
    return specs


def is_snake_case(name: str) -> bool:
    """Returns True if name is lowercase snake_case with no spaces."""
    return bool(re.match(r"^[a-z][a-z0-9_]*$", name))


# ---------------------------------------------------------------------------
# Test 1: All 10 disease specification files exist
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("filename", sorted(EXPECTED_SPEC_FILES))
def test_specification_file_exists(filename):
    """Test 1 — Each of the 10 disease specification files must exist."""
    path = SPEC_DIR / filename
    assert path.exists(), f"Missing specification file: {path}"
    assert path.stat().st_size > 100, f"Specification file is suspiciously small: {path}"


# ---------------------------------------------------------------------------
# Test 2: All disease codes are unique
# ---------------------------------------------------------------------------
def test_disease_codes_are_unique():
    """Test 2 — Disease codes in the registry must be unique."""
    registry_path = SPEC_DIR / "dataset_registry.yaml"
    assert registry_path.exists(), "dataset_registry.yaml not found"
    registry = load_yaml(registry_path)
    codes = [d["disease_code"] for d in registry["datasets"]]
    assert len(codes) == len(set(codes)), f"Duplicate disease codes found: {codes}"


# ---------------------------------------------------------------------------
# Test 3: Every disease has a target column defined
# ---------------------------------------------------------------------------
def test_every_disease_has_target():
    """Test 3 — Every disease specification must define a target column."""
    specs = load_all_specs()
    for name, spec in specs.items():
        assert "target" in spec, f"{name}: missing 'target' section"
        assert "column" in spec["target"], f"{name}: target.column not defined"
        assert spec["target"]["column"], f"{name}: target.column is empty"


# ---------------------------------------------------------------------------
# Test 4: Every target is binary (type = binary, 0/1)
# ---------------------------------------------------------------------------
def test_every_target_is_binary():
    """Test 4 — Every target must be binary type with 0/1 class values."""
    specs = load_all_specs()
    for name, spec in specs.items():
        target = spec.get("target", {})
        assert target.get("type") == "binary", f"{name}: target.type must be 'binary'"
        neg = target.get("negative_class", {})
        pos = target.get("positive_class", {})
        assert neg.get("value") == 0, f"{name}: negative_class.value must be 0"
        assert pos.get("value") == 1, f"{name}: positive_class.value must be 1"


# ---------------------------------------------------------------------------
# Test 5: Every disease has feature definitions
# ---------------------------------------------------------------------------
def test_every_disease_has_features():
    """Test 5 — Every disease specification must define at least one feature."""
    specs = load_all_specs()
    for name, spec in specs.items():
        features = spec.get("features", [])
        assert len(features) >= 5, f"{name}: fewer than 5 features defined ({len(features)})"


# ---------------------------------------------------------------------------
# Test 6: Feature names follow snake_case
# ---------------------------------------------------------------------------
def test_feature_names_snake_case():
    """Test 6 — All feature names must be lowercase snake_case."""
    specs = load_all_specs()
    violations = []
    for name, spec in specs.items():
        for feat in spec.get("features", []):
            fname = feat.get("name", "")
            if not is_snake_case(fname):
                violations.append(f"{name}.{fname}")
    assert not violations, f"Non-snake_case feature names: {violations}"


# ---------------------------------------------------------------------------
# Test 7: No duplicate feature names within a disease
# ---------------------------------------------------------------------------
def test_no_duplicate_feature_names():
    """Test 7 — No feature name should appear more than once in a disease spec."""
    specs = load_all_specs()
    for name, spec in specs.items():
        names = [f["name"] for f in spec.get("features", [])]
        dupes = [n for n in set(names) if names.count(n) > 1]
        assert not dupes, f"{name}: duplicate features: {dupes}"


# ---------------------------------------------------------------------------
# Test 8: No feature name equals the target column name
# ---------------------------------------------------------------------------
def test_target_not_in_features():
    """Test 8 — The target column name must not appear as a feature name."""
    specs = load_all_specs()
    for name, spec in specs.items():
        target_col = spec.get("target", {}).get("column", "")
        feature_names = [f["name"] for f in spec.get("features", [])]
        assert target_col not in feature_names, (
            f"{name}: target column '{target_col}' appears in features list (direct leakage)"
        )


# ---------------------------------------------------------------------------
# Test 9: Dataset registry contains exactly 10 diseases
# ---------------------------------------------------------------------------
def test_registry_has_exactly_10_diseases():
    """Test 9 — The dataset registry must register exactly 10 diseases."""
    registry_path = SPEC_DIR / "dataset_registry.yaml"
    assert registry_path.exists(), "dataset_registry.yaml not found"
    registry = load_yaml(registry_path)
    datasets = registry.get("datasets", [])
    assert len(datasets) == 10, f"Registry has {len(datasets)} diseases, expected 10"
    assert registry.get("total_diseases") == 10


# ---------------------------------------------------------------------------
# Test 10: All registry entries reference valid specification files
# ---------------------------------------------------------------------------
def test_registry_references_valid_specs():
    """Test 10 — Every registry entry must point to a specification file that exists."""
    registry_path = SPEC_DIR / "dataset_registry.yaml"
    registry = load_yaml(registry_path)
    for entry in registry["datasets"]:
        spec_path = PROJECT_ROOT / entry["specification_file"]
        assert spec_path.exists(), (
            f"Registry entry '{entry['disease_code']}' references missing file: {spec_path}"
        )


# ---------------------------------------------------------------------------
# Test 11: Experiment manifest contains both TabPFN and TabICLv2
# ---------------------------------------------------------------------------
def test_experiment_protocol_has_both_models():
    """Test 11 — Experiment protocol must include TabPFN 9.0.0 and TabICLv2 2.2.0."""
    protocol_path = EXPERIMENTS_DIR / "experiment_protocol.yaml"
    assert protocol_path.exists(), "experiment_protocol.yaml not found"
    protocol = load_yaml(protocol_path)

    models = protocol.get("models", [])
    model_names = [m["name"] for m in models]
    model_versions = {m["name"]: m["version"] for m in models}

    assert "TabPFN" in model_names, "TabPFN not found in experiment protocol"
    assert "TabICLv2" in model_names, "TabICLv2 not found in experiment protocol"
    assert model_versions["TabPFN"] == "9.0.0", (
        f"TabPFN version must be 9.0.0, got {model_versions['TabPFN']}"
    )
    assert model_versions["TabICLv2"] == "2.2.0", (
        f"TabICLv2 version must be 2.2.0, got {model_versions['TabICLv2']}"
    )


# ---------------------------------------------------------------------------
# Test 12: Experiment protocol contains all required metrics
# ---------------------------------------------------------------------------
def test_experiment_protocol_has_required_metrics():
    """Test 12 — Experiment protocol must define all required evaluation metrics."""
    protocol_path = EXPERIMENTS_DIR / "experiment_protocol.yaml"
    protocol = load_yaml(protocol_path)

    metrics_section = protocol.get("metrics", {})
    found_metrics = set()
    for section in ["classification", "calibration", "system_performance"]:
        for m in metrics_section.get(section, []):
            found_metrics.add(m["name"])

    missing = REQUIRED_METRICS - found_metrics
    assert not missing, f"Missing metrics in experiment protocol: {missing}"


# ---------------------------------------------------------------------------
# Test 13: Split percentages equal 70/15/15
# ---------------------------------------------------------------------------
def test_split_is_70_15_15():
    """Test 13 — The data split must be exactly 70% / 15% / 15%."""
    protocol_path = EXPERIMENTS_DIR / "experiment_protocol.yaml"
    protocol = load_yaml(protocol_path)
    split = protocol.get("data_split", {})

    assert split.get("train") == 0.70, f"Train split must be 0.70, got {split.get('train')}"
    assert split.get("validation") == 0.15, f"Val split must be 0.15, got {split.get('validation')}"
    assert split.get("test") == 0.15, f"Test split must be 0.15, got {split.get('test')}"

    total = (split.get("train", 0) + split.get("validation", 0) + split.get("test", 0))
    assert abs(total - 1.0) < 1e-9, f"Split percentages do not sum to 1.0: {total}"


# ---------------------------------------------------------------------------
# Test 14: Schema version file exists and is valid
# ---------------------------------------------------------------------------
def test_schema_version_file_exists():
    """Test 14 — schema-version.yaml must exist and define a schema_version."""
    schema_path = SPEC_DIR / "schema-version.yaml"
    assert schema_path.exists(), "schema-version.yaml not found"
    schema = load_yaml(schema_path)
    assert "schema_version" in schema, "schema-version.yaml missing 'schema_version' field"
    assert schema["schema_version"], "schema_version is empty"
    # Verify model versions are correct
    mv = schema.get("model_versions", {})
    assert mv.get("tabpfn") == "9.0.0", f"schema-version.yaml tabpfn must be 9.0.0"
    assert mv.get("tabicl") == "2.2.0", f"schema-version.yaml tabicl must be 2.2.0"
    assert mv.get("torch") == "2.14.0", f"schema-version.yaml torch must be 2.14.0"
    assert mv.get("scikit_learn") == "1.5.2", f"schema-version.yaml scikit_learn must be 1.5.2"


# ---------------------------------------------------------------------------
# Test 15: No dataset artifacts were generated
# ---------------------------------------------------------------------------
def test_no_dataset_artifacts_generated():
    """Test 15 — Phase 7A must NOT generate any .csv/.parquet/.pkl/.joblib files."""
    prohibited_extensions = [".csv", ".parquet", ".pkl", ".joblib", ".h5", ".hdf5"]
    found_files = []
    for ext in prohibited_extensions:
        matches = list(ML_ROOT.rglob(f"*{ext}"))
        found_files.extend(matches)
    assert not found_files, (
        f"Phase 7A must not generate dataset artifact files. Found: {found_files}"
    )


# ---------------------------------------------------------------------------
# Test 16: No ML training was executed (no trained model artifact files)
# ---------------------------------------------------------------------------
def test_no_trained_model_artifacts():
    """Test 16 — Phase 7A must NOT produce trained model artifact files."""
    prohibited_patterns = ["*.pt", "*.pth", "*.onnx", "*.bin", "*.safetensors", "*.joblib", "*.pkl"]
    found_files = []
    for pattern in prohibited_patterns:
        matches = list(ML_ROOT.rglob(pattern))
        found_files.extend(matches)
    assert not found_files, (
        f"Phase 7A must not produce model training artifacts. Found: {found_files}"
    )


# ---------------------------------------------------------------------------
# Bonus: Verify registry codes match expected set
# ---------------------------------------------------------------------------
def test_registry_codes_match_expected():
    """Bonus — Registry must contain exactly the 10 expected disease codes."""
    registry_path = SPEC_DIR / "dataset_registry.yaml"
    registry = load_yaml(registry_path)
    actual_codes = {d["disease_code"] for d in registry["datasets"]}
    assert actual_codes == EXPECTED_DISEASE_CODES, (
        f"Registry codes mismatch.\n"
        f"Expected: {EXPECTED_DISEASE_CODES}\n"
        f"Got: {actual_codes}"
    )
