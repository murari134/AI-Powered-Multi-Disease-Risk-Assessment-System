"""
MediRisk 2.0 — Phase 7B Pipeline Orchestrator

Runs the complete Phase 7B pipeline:
  1. Generate all 10 synthetic datasets
  2. Validate each dataset
  3. Split into train/val/test (70/15/15)
  4. Fit preprocessing (on train only)
  5. Run TabPFN + TabICLv2 experiments
  6. Collect all metrics
  7. Save results

Usage:
    python ml/pipeline.py

DISCLAIMER: Synthetic research data. Not clinically validated.
"""

from __future__ import annotations

import io
import json
import sys

# Force UTF-8 stdout on Windows to avoid cp1252 codec errors
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from datetime import datetime, timezone
from pathlib import Path

ML_ROOT = Path(__file__).parent
sys.path.insert(0, str(ML_ROOT.parent))

import yaml

from ml.generators.dataset_generator import (
    DISEASE_CODES,
    GENERATORS,
    generate_all_datasets,
)
from ml.validation.validator import validate_all_datasets, save_validation_results
from ml.preprocessing.preprocessor import (
    MediRiskPreprocessor,
    split_dataset,
    save_splits,
)
from ml.experiments.runner import (
    build_summary,
    run_experiment,
    save_experiment_result,
)

# ---- Output directories ----
DATA_DIR = ML_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
SPLIT_DIR = DATA_DIR / "splits"
META_DIR = DATA_DIR / "metadata"
RESULTS_DIR = ML_ROOT / "results"
VALIDATION_DIR = ML_ROOT / "data" / "validation"
SPEC_DIR = ML_ROOT / "specifications"

SEED = 42
N_RECORDS = 5000


def _load_feature_spec(disease_id: str) -> list[dict]:
    spec_path = SPEC_DIR / f"{disease_id}.yaml"
    with open(spec_path, "r", encoding="utf-8") as f:
        spec = yaml.safe_load(f)
    return spec.get("features", [])


def main() -> None:
    run_start = datetime.now(timezone.utc)
    print("=" * 60)
    print("MediRisk 2.0 — Phase 7B Pipeline")
    print(f"Started: {run_start.isoformat()}")
    print("=" * 60)

    # -------------------------------------------------------
    # STEP 1: Generate datasets
    # -------------------------------------------------------
    print("\n[1/6] Generating synthetic datasets...")
    all_datasets = generate_all_datasets(n=N_RECORDS, seed=SEED,
                                          output_dir=RAW_DIR)

    # -------------------------------------------------------
    # STEP 2: Validate datasets
    # -------------------------------------------------------
    print("\n[2/6] Validating datasets...")
    dataset_dfs = {k: v[0] for k, v in all_datasets.items()}
    validation_results = validate_all_datasets(dataset_dfs,
                                                expected_records=N_RECORDS)
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
    save_validation_results(
        validation_results,
        VALIDATION_DIR / "validation_results.json"
    )

    failed_validation = [d for d, r in validation_results.items()
                         if not r["valid"]]
    if failed_validation:
        print(f"\n⚠️  Validation FAILED for: {failed_validation}")
        print("Datasets with errors will be excluded from experiments.")

    # -------------------------------------------------------
    # STEP 3 & 4: Split + Preprocess
    # -------------------------------------------------------
    print("\n[3/6] Splitting and preprocessing datasets...")
    splits: dict = {}
    preprocessors: dict = {}

    for disease_id, (df, meta) in all_datasets.items():
        if disease_id in failed_validation:
            print(f"  SKIP {disease_id} (failed validation)")
            continue

        target_col = meta["target_column"]
        feature_spec = _load_feature_spec(disease_id)
        dataset_version = meta["dataset_version"]

        # Split
        train_df, val_df, test_df = split_dataset(
            df, target_col, seed=SEED)
        split_meta = save_splits(
            train_df, val_df, test_df,
            disease_id, dataset_version,
            SPLIT_DIR / disease_id,
        )
        splits[disease_id] = {
            "train": train_df,
            "val": val_df,
            "test": test_df,
            "target_col": target_col,
            "meta": split_meta,
        }

        # Preprocess — fit on TRAIN only
        preprocessor = MediRiskPreprocessor(disease_id, feature_spec)
        X_train_raw = train_df.drop(columns=[target_col])
        preprocessor.fit(X_train_raw)
        preprocessors[disease_id] = preprocessor

        print(f"  {disease_id}: train={len(train_df):,} "
              f"val={len(val_df):,} test={len(test_df):,}  "
              f"pos_rate(train)={split_meta['train_positive_rate']:.3f}")

    # -------------------------------------------------------
    # STEP 5: Run experiments
    # -------------------------------------------------------
    print("\n[4/6] Running model experiments...")
    print("  ⚠️  NOTE: Test sets are NOT used for experiments (reserved).")
    print("  ⚠️  Models evaluated on validation split only.")

    all_experiment_results: dict = {}
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    for disease_id in splits:
        print(f"\n  [{disease_id}]")
        split_info = splits[disease_id]
        result = run_experiment(
            disease_id=disease_id,
            train_df=split_info["train"],
            val_df=split_info["val"],
            preprocessor=preprocessors[disease_id],
            target_col=split_info["target_col"],
            seed=SEED,
            dataset_version=all_datasets[disease_id][1]["dataset_version"],
        )
        all_experiment_results[disease_id] = result
        save_experiment_result(result, disease_id, RESULTS_DIR)

        for model in ["tabpfn", "tabicl"]:
            m = result[model]
            status = m.get("status", "UNKNOWN")
            if status == "SUCCESS":
                roc = m.get("metrics", {}).get("roc_auc")
                roc_str = f"ROC-AUC={roc:.4f}" if roc else "ROC-AUC=N/A"
                lat = m.get("inference_latency_ms")
                lat_str = f"latency={lat:.1f}ms" if lat else ""
                print(f"    {model.upper()}: ✅ {roc_str} {lat_str}")
            else:
                err = m.get("error_message", "unknown error")[:80]
                print(f"    {model.upper()}: ❌ {status}: {err}")

    # -------------------------------------------------------
    # STEP 6: Build and save summary
    # -------------------------------------------------------
    print("\n[5/6] Building experiment summary...")
    summary_df = build_summary(all_experiment_results)
    summary_path = RESULTS_DIR / "experiment_summary.csv"
    summary_df.to_csv(summary_path, index=False)
    print(f"  Summary saved: {summary_path}")

    # Print comparison table
    print("\n" + "=" * 100)
    print("PHASE 7B — EXPERIMENT COMPARISON (Validation Split)")
    print("NOTE: No winner declared. Factual results only.")
    print("=" * 100)
    display_cols = ["disease", "model", "status", "roc_auc", "pr_auc",
                    "accuracy", "f1_score", "brier_score", "inference_latency_ms",
                    "peak_ram_mb"]
    print(summary_df[display_cols].to_string(index=False))

    # -------------------------------------------------------
    # STEP 7: Save overall pipeline metadata
    # -------------------------------------------------------
    run_end = datetime.now(timezone.utc)
    pipeline_meta = {
        "phase": "7B",
        "pipeline_version": "1.0.0",
        "run_start": run_start.isoformat(),
        "run_end": run_end.isoformat(),
        "total_runtime_s": (run_end - run_start).total_seconds(),
        "random_seed": SEED,
        "records_per_disease": N_RECORDS,
        "diseases": list(splits.keys()),
        "models_attempted": ["TabPFN 9.0.0", "TabICLv2 2.2.0"],
        "validation_passed": [d for d in dataset_dfs if d not in failed_validation],
        "validation_failed": failed_validation,
        "disclaimer": (
            "SYNTHETIC RESEARCH DATA ONLY. Results do not represent "
            "clinical performance. Not clinically validated."
        ),
    }
    META_DIR.mkdir(parents=True, exist_ok=True)
    (META_DIR / "pipeline_run_metadata.json").write_text(
        json.dumps(pipeline_meta, indent=2), encoding="utf-8")

    print("\n[6/6] Pipeline complete.")
    print(f"  Runtime: {pipeline_meta['total_runtime_s']:.1f}s")
    print(f"  Results: {RESULTS_DIR}")
    print("=" * 60)
    print("PHASE 7B STATUS: COMPLETE")
    print("No winner declared. Review experiment_summary.csv.")
    print("=" * 60)


if __name__ == "__main__":
    main()
