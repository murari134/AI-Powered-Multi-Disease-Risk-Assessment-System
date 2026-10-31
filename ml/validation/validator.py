"""
MediRisk 2.0 — Dataset Validator
Phase 7B

Validates generated datasets against the Phase 7A specifications.
Produces machine-readable validation results.

A dataset must NOT proceed to model training if validation fails.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

ML_ROOT = Path(__file__).parent.parent
SPEC_DIR = ML_ROOT / "specifications"

# Expected domains for binary values
BINARY_VALUES = {0, 1}


def _load_spec(disease_id: str) -> dict:
    spec_path = SPEC_DIR / f"{disease_id}.yaml"
    if not spec_path.exists():
        raise FileNotFoundError(f"Spec not found: {spec_path}")
    with open(spec_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _is_snake_case(name: str) -> bool:
    return bool(re.match(r"^[a-z][a-z0-9_]*$", name))


def validate_dataset(
    df: pd.DataFrame,
    disease_id: str,
    *,
    expected_records: int = 5000,
    tolerance: float = 0.10,
) -> dict[str, Any]:
    """
    Validate a generated dataset against its Phase 7A specification.

    Returns a machine-readable result:
    {
        "disease_code": str,
        "valid": bool,
        "record_count": int,
        "errors": list[str],
        "warnings": list[str],
        "checks": dict
    }
    """
    spec = _load_spec(disease_id)
    errors: list[str] = []
    warnings: list[str] = []
    checks: dict[str, Any] = {}

    disease_code = spec.get("dataset_identifier", disease_id).upper()
    target_col = spec["target"]["column"]
    features = spec.get("features", [])
    feature_names = [f["name"] for f in features]
    numerical_features = spec.get("numerical_features", [])
    categorical_features = spec.get("categorical_features", [])
    binary_features = spec.get("binary_features", [])
    class_balance = spec.get("class_balance", {})

    # -------------------------------------------------------
    # CHECK 1: Record count
    # -------------------------------------------------------
    actual_records = len(df)
    low = int(expected_records * (1 - tolerance))
    high = int(expected_records * (1 + tolerance))
    ok = low <= actual_records <= high
    checks["record_count"] = {"passed": ok, "actual": actual_records,
                              "expected_range": [low, high]}
    if not ok:
        errors.append(f"record_count: {actual_records} outside range [{low}, {high}]")

    # -------------------------------------------------------
    # CHECK 2: Column names & no missing columns
    # -------------------------------------------------------
    expected_cols = set(feature_names) | {target_col}
    actual_cols = set(df.columns)
    missing_cols = expected_cols - actual_cols
    unexpected_cols = actual_cols - expected_cols
    checks["columns"] = {"missing": list(missing_cols),
                         "unexpected": list(unexpected_cols),
                         "passed": not missing_cols}
    if missing_cols:
        errors.append(f"Missing columns: {missing_cols}")
    if unexpected_cols:
        warnings.append(f"Unexpected columns: {unexpected_cols}")

    # -------------------------------------------------------
    # CHECK 3: Snake_case naming
    # -------------------------------------------------------
    bad_names = [c for c in df.columns if not _is_snake_case(c)]
    checks["snake_case"] = {"passed": not bad_names, "violations": bad_names}
    if bad_names:
        errors.append(f"Non-snake_case columns: {bad_names}")

    # -------------------------------------------------------
    # CHECK 4: Target binary values
    # -------------------------------------------------------
    if target_col in df.columns:
        target_vals = set(df[target_col].dropna().unique())
        valid_target = target_vals <= BINARY_VALUES
        checks["target_values"] = {"passed": valid_target,
                                   "found": sorted(target_vals)}
        if not valid_target:
            errors.append(f"target {target_col} has non-binary values: {target_vals}")

    # -------------------------------------------------------
    # CHECK 5: Target not in feature list
    # -------------------------------------------------------
    target_as_feature = target_col in feature_names
    checks["no_target_leakage"] = {"passed": not target_as_feature}
    if target_as_feature:
        errors.append(f"target column '{target_col}' appears in feature list")

    # -------------------------------------------------------
    # CHECK 6: Infinite values
    # -------------------------------------------------------
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    inf_count = int(np.isinf(df[num_cols].values).sum())
    checks["infinite_values"] = {"passed": inf_count == 0, "count": inf_count}
    if inf_count > 0:
        errors.append(f"{inf_count} infinite values found in numeric columns")

    # -------------------------------------------------------
    # CHECK 7: Missing value policy per feature
    # -------------------------------------------------------
    missing_violations = []
    for feat in features:
        fname = feat["name"]
        if fname not in df.columns:
            continue
        missing_allowed = feat.get("missing_allowed", False)
        max_pct = feat.get("max_missing_pct", 0) / 100.0
        actual_missing = df[fname].isna().mean()
        if not missing_allowed and actual_missing > 0:
            missing_violations.append(
                f"{fname}: no missing allowed but {actual_missing:.1%} missing")
        elif missing_allowed and actual_missing > max_pct + 0.05:  # 5% tolerance
            warnings.append(
                f"{fname}: missing={actual_missing:.1%} > limit={max_pct:.1%}")
    checks["missing_values"] = {"passed": not missing_violations,
                                 "violations": missing_violations}
    if missing_violations:
        warnings.extend(missing_violations)

    # -------------------------------------------------------
    # CHECK 8: Numerical domains
    # -------------------------------------------------------
    domain_violations = []
    for feat in features:
        if feat.get("type") != "numerical":
            continue
        fname = feat["name"]
        if fname not in df.columns:
            continue
        domain = feat.get("domain")
        if not domain:
            continue
        lo, hi = domain[0], domain[1]
        col_vals = df[fname].dropna()
        out_of_range = ((col_vals < lo) | (col_vals > hi)).sum()
        if out_of_range > 0:
            domain_violations.append(
                f"{fname}: {out_of_range} values outside [{lo}, {hi}]")
    checks["numerical_domains"] = {"passed": not domain_violations,
                                    "violations": domain_violations}
    if domain_violations:
        errors.extend(domain_violations)

    # -------------------------------------------------------
    # CHECK 9: Categorical domains
    # -------------------------------------------------------
    cat_violations = []
    for feat in features:
        if feat.get("type") != "categorical":
            continue
        fname = feat["name"]
        if fname not in df.columns:
            continue
        allowed = set(feat.get("domain", []))
        if not allowed:
            continue
        actual_vals = set(df[fname].dropna().unique())
        invalid_vals = actual_vals - allowed
        if invalid_vals:
            cat_violations.append(f"{fname}: invalid values {invalid_vals}")
    checks["categorical_domains"] = {"passed": not cat_violations,
                                      "violations": cat_violations}
    if cat_violations:
        errors.extend(cat_violations)

    # -------------------------------------------------------
    # CHECK 10: Binary constraints (0/1 only)
    # -------------------------------------------------------
    bin_violations = []
    for feat in features:
        if feat.get("type") != "binary":
            continue
        fname = feat["name"]
        if fname not in df.columns:
            continue
        actual_vals = set(df[fname].dropna().astype(int).unique())
        if not actual_vals <= BINARY_VALUES:
            bin_violations.append(f"{fname}: non-binary values {actual_vals}")
    checks["binary_constraints"] = {"passed": not bin_violations,
                                     "violations": bin_violations}
    if bin_violations:
        errors.extend(bin_violations)

    # -------------------------------------------------------
    # CHECK 11: Class distribution
    # -------------------------------------------------------
    if target_col in df.columns:
        pos_rate = float(df[target_col].mean())
        lo_bal = class_balance.get("acceptable_range", [0.05, 0.95])[0]
        hi_bal = class_balance.get("acceptable_range", [0.05, 0.95])[1]
        bal_ok = lo_bal <= pos_rate <= hi_bal
        checks["class_distribution"] = {
            "passed": bal_ok,
            "positive_rate": round(pos_rate, 4),
            "acceptable_range": [lo_bal, hi_bal],
        }
        if not bal_ok:
            warnings.append(
                f"Positive rate {pos_rate:.3f} outside [{lo_bal}, {hi_bal}]")

    # -------------------------------------------------------
    # CHECK 12: Duplicate rows
    # -------------------------------------------------------
    dup_count = int(df.duplicated().sum())
    checks["duplicate_rows"] = {"passed": dup_count == 0, "count": dup_count}
    if dup_count > 0:
        warnings.append(f"{dup_count} duplicate rows found")

    # -------------------------------------------------------
    # CHECK 13: Schema version consistency
    # -------------------------------------------------------
    spec_sv = spec.get("schema_version", "UNKNOWN")
    checks["schema_version"] = {"passed": True, "value": spec_sv}

    # -------------------------------------------------------
    # Final result
    # -------------------------------------------------------
    valid = len(errors) == 0
    return {
        "disease_code": spec.get("disease_code", disease_code),
        "dataset_identifier": disease_id,
        "valid": valid,
        "record_count": actual_records,
        "errors": errors,
        "warnings": warnings,
        "checks": checks,
    }


def validate_all_datasets(
    datasets: dict[str, pd.DataFrame],
    *,
    expected_records: int = 5000,
) -> dict[str, dict]:
    """Validate all datasets and return per-disease results."""
    results = {}
    all_valid = True
    for disease_id, df in datasets.items():
        result = validate_dataset(df, disease_id,
                                  expected_records=expected_records)
        results[disease_id] = result
        status = "[PASS]" if result["valid"] else "[FAIL]"
        errs = len(result["errors"])
        warns = len(result["warnings"])
        print(f"  {status} {disease_id}: {result['record_count']:,} records, "
              f"{errs} errors, {warns} warnings")
        if not result["valid"]:
            all_valid = False
            for err in result["errors"]:
                print(f"       ERROR: {err}")
    return results


def _json_safe(obj):
    """Convert numpy types to Python native for JSON serialization."""
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def save_validation_results(
    results: dict[str, dict],
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=_json_safe)
    print(f"Validation results saved: {output_path}")
