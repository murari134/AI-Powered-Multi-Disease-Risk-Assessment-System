"""
MediRisk 2.0 - Phase 7B Resume Script

Continues Phase 7B from verified interrupted state.
Only runs missing experiments. Preserves completed work.
Does NOT: regenerate datasets, regenerate splits, rerun 9 completed TabICLv2,
         fabricate results, declare a winner, or start Phase 7C.

DISCLAIMER: Synthetic research data only. Not clinically validated.
"""
from __future__ import annotations
import io, json, os, sys, uuid, importlib.metadata
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
else:
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
import yaml

ML_ROOT = Path(__file__).parent
sys.path.insert(0, str(ML_ROOT.parent))

from ml.preprocessing.preprocessor import MediRiskPreprocessor
from ml.experiments.runner import (
    _run_tabicl, _run_tabpfn, _env_info, _json_safe,
    EXPERIMENT_PROTOCOL_VERSION, PREPROCESSING_VERSION,
)

DATA_DIR    = ML_ROOT / "data"
SPLIT_DIR   = DATA_DIR / "splits"
META_DIR    = DATA_DIR / "metadata"
RESULTS_DIR = ML_ROOT / "results"
SPEC_DIR    = ML_ROOT / "specifications"
SEED = 42

ALL_DISEASES = [
    "diabetes","heart_disease","stroke","asthma","chronic_kidney_disease",
    "liver_disease","parkinsons","breast_cancer","lung_cancer","hypertension",
]


def _load_feature_spec(disease_id):
    spec_path = SPEC_DIR / f"{disease_id}.yaml"
    with open(spec_path, "r", encoding="utf-8") as f:
        spec = yaml.safe_load(f)
    return spec.get("features", [])


def _load_split(disease_id):
    split_dir = SPLIT_DIR / disease_id
    meta_files = list(split_dir.glob("*_split_metadata.json"))
    if not meta_files:
        raise FileNotFoundError(f"No split metadata for {disease_id}")
    meta = json.loads(meta_files[0].read_text(encoding="utf-8"))
    target_col = meta["target_column"]
    dv = meta["dataset_version"]
    train_df = pd.read_csv(split_dir / f"{disease_id}_v{dv}_train.csv")
    val_df   = pd.read_csv(split_dir / f"{disease_id}_v{dv}_val.csv")
    return train_df, val_df, target_col, meta


def _load_existing(disease_id, model):
    p = RESULTS_DIR / disease_id / model / "experiment_result.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def _check_tabpfn_token():
    if os.environ.get("TABPFN_TOKEN", "").strip():
        return True
    for fp in [Path.home() / ".cache" / "tabpfn" / "auth_token",
               Path.home() / ".tabpfn" / "token"]:
        if fp.exists() and fp.read_text().strip():
            return True
    return False


def _make_base(disease_id, meta, train_df, val_df, X_train, y_train, y_val, env):
    return {
        "experiment_id":              str(uuid.uuid4())[:8],
        "disease_code":               disease_id.upper(),
        "dataset_version":            meta["dataset_version"],
        "schema_version":             "1.0.0",
        "experiment_protocol_version": EXPERIMENT_PROTOCOL_VERSION,
        "preprocessing_version":      PREPROCESSING_VERSION,
        "random_seed":                SEED,
        "train_records":              len(train_df),
        "val_records":                len(val_df),
        "feature_count":              int(X_train.shape[1]),
        "train_positive_rate":        float(y_train.mean()),
        "val_positive_rate":          float(y_val.mean()),
        "split_config":               {"train": 0.70, "val": 0.15, "test": 0.15},
        "python_version":             env.get("python_version"),
        "torch_version":              env.get("torch_version"),
        "tabpfn_version":             env.get("tabpfn_version"),
        "tabicl_version":             env.get("tabicl_version"),
        "sklearn_version":            env.get("sklearn_version"),
        "cuda_available":             env.get("cuda_available"),
        "experiment_timestamp":       datetime.now(timezone.utc).isoformat(),
        "disclaimer":                 "SYNTHETIC RESEARCH DATA. Results do not represent clinical performance.",
    }


def _save(disease_id, model, payload):
    out = RESULTS_DIR / disease_id / model
    out.mkdir(parents=True, exist_ok=True)
    p = out / "experiment_result.json"
    p.write_text(json.dumps(payload, indent=2, default=_json_safe), encoding="utf-8")
    return p


def _run_disease(disease_id, model_name):
    train_df, val_df, target_col, meta = _load_split(disease_id)
    spec = _load_feature_spec(disease_id)
    prep = MediRiskPreprocessor(disease_id, spec)
    Xtr_raw = train_df.drop(columns=[target_col])
    prep.fit(Xtr_raw)
    X_train = prep.transform(Xtr_raw).values
    y_train = train_df[target_col].values.astype(int)
    Xv_raw  = val_df.drop(columns=[target_col])
    X_val   = prep.transform(Xv_raw).values
    y_val   = val_df[target_col].values.astype(int)
    feat_names = list(prep.transform(Xtr_raw).columns)
    env = _env_info()
    base = _make_base(disease_id, meta, train_df, val_df, X_train, y_train, y_val, env)
    if model_name == "tabicl":
        res = _run_tabicl(X_train, y_train, X_val, y_val, feat_names)
    else:
        res = _run_tabpfn(X_train, y_train, X_val, y_val, feat_names)
    return {**base, **res}


def _build_summary():
    rows = []
    for did in ALL_DISEASES:
        for model in ["tabpfn", "tabicl"]:
            p = RESULTS_DIR / did / model / "experiment_result.json"
            if p.exists():
                d = json.loads(p.read_text(encoding="utf-8"))
                m = d.get("metrics", {})
                rows.append({
                    "disease": did, "model": d.get("model_name", model.upper()),
                    "model_version": d.get("model_version",""), "status": d.get("status","UNKNOWN"),
                    "experiment_id": d.get("experiment_id",""),
                    "experiment_timestamp": d.get("experiment_timestamp",""),
                    "roc_auc": m.get("roc_auc"), "pr_auc": m.get("pr_auc"),
                    "accuracy": m.get("accuracy"), "precision": m.get("precision"),
                    "recall": m.get("recall"), "sensitivity": m.get("sensitivity"),
                    "specificity": m.get("specificity"), "f1_score": m.get("f1_score"),
                    "brier_score": m.get("brier_score"),
                    "ece": m.get("expected_calibration_error"),
                    "inference_latency_ms": d.get("inference_latency_ms"),
                    "peak_ram_mb": d.get("peak_ram_mb"), "vram_mb": d.get("vram_mb"),
                    "training_time_s": d.get("training_time_s"), "device": d.get("device"),
                    "error_type": d.get("error_type"),
                    "error_message": (d.get("error_message") or "")[:120],
                    "train_records": d.get("train_records"),
                    "val_records": d.get("val_records"),
                    "feature_count": d.get("feature_count"),
                    "disclaimer": d.get("disclaimer",""),
                })
            else:
                rows.append({
                    "disease": did, "model": model.upper(),
                    "model_version": "unknown", "status": "NOT_RUN",
                    "experiment_id": "", "experiment_timestamp": "",
                    "roc_auc": None, "pr_auc": None, "accuracy": None,
                    "precision": None, "recall": None, "sensitivity": None,
                    "specificity": None, "f1_score": None, "brier_score": None,
                    "ece": None, "inference_latency_ms": None, "peak_ram_mb": None,
                    "vram_mb": None, "training_time_s": None, "device": None,
                    "error_type": None, "error_message": "Result file not found",
                    "train_records": None, "val_records": None, "feature_count": None,
                    "disclaimer": "SYNTHETIC RESEARCH DATA. Results do not represent clinical performance.",
                })
    return pd.DataFrame(rows)


def main():
    run_start = datetime.now(timezone.utc)
    print("=" * 70)
    print("MediRisk 2.0 - Phase 7B RESUME (Incremental Completion)")
    print(f"Started: {run_start.isoformat()}")
    print("=" * 70)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    META_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Token check
    print("\n[Step 1] TabPFN authentication check...")
    tabpfn_ok = _check_tabpfn_token()
    if tabpfn_ok:
        print("  TabPFN token FOUND.")
    else:
        print("  TabPFN token NOT found. TabPFN will fail with TabPFNLicenseError.")
        print("  Fix: set TABPFN_TOKEN env var from https://ux.priorlabs.ai")

    # Step 2: Hypertension TabICLv2 (only missing TabICLv2)
    print("\n[Step 2] Hypertension TabICLv2...")
    existing = _load_existing("hypertension", "tabicl")
    if existing and existing.get("status") == "SUCCESS":
        print("  Already SUCCESS - skipping (preserving result)")
    else:
        try:
            payload = _run_disease("hypertension", "tabicl")
            status = payload.get("status")
            if status == "SUCCESS":
                roc = payload.get("metrics", {}).get("roc_auc")
                lat = payload.get("inference_latency_ms")
                print(f"  SUCCESS: ROC-AUC={roc:.4f}  latency={lat:.1f}ms")
            else:
                print(f"  {status}: {(payload.get('error_message') or '')[:80]}")
            p = _save("hypertension", "tabicl", payload)
            print(f"  Saved: {p}")
        except Exception as e:
            print(f"  EXCEPTION: {e}")

    # Step 3: TabPFN all 10 diseases
    print("\n[Step 3] TabPFN - all 10 diseases...")
    tabpfn_summary = {}
    for did in ALL_DISEASES:
        print(f"\n  [{did}] TabPFN...")
        existing = _load_existing(did, "tabpfn")
        if existing and existing.get("status") == "SUCCESS":
            print("    Already SUCCESS - preserving")
            tabpfn_summary[did] = "PRESERVED_SUCCESS"
            continue
        try:
            payload = _run_disease(did, "tabpfn")
            status = payload.get("status")
            if status == "SUCCESS":
                roc = payload.get("metrics", {}).get("roc_auc")
                lat = payload.get("inference_latency_ms")
                print(f"    SUCCESS: ROC-AUC={roc:.4f}  latency={lat:.1f}ms")
                tabpfn_summary[did] = "SUCCESS"
            else:
                et = payload.get("error_type", "Unknown")
                em = (payload.get("error_message") or "")[:80]
                print(f"    {status}: [{et}] {em}")
                tabpfn_summary[did] = f"{status}:{et}"
            p = _save(did, "tabpfn", payload)
            print(f"    Saved: {p}")
        except Exception as e:
            print(f"    EXCEPTION: {e}")
            tabpfn_summary[did] = f"EXCEPTION:{type(e).__name__}"

    # Step 4: experiment_summary.csv
    print("\n[Step 4] Building experiment_summary.csv...")
    df = _build_summary()
    csv_path = RESULTS_DIR / "experiment_summary.csv"
    df.to_csv(csv_path, index=False)
    print(f"  Saved: {csv_path}  ({len(df)} rows)")

    print("\n" + "=" * 100)
    print("PHASE 7B - EXPERIMENT RESULTS (Validation Split Only)")
    print("NOTE: No winner declared. Factual results only.")
    print("=" * 100)
    cols = ["disease","model","status","roc_auc","pr_auc","accuracy",
            "f1_score","brier_score","inference_latency_ms","peak_ram_mb"]
    print(df[cols].to_string(index=False))

    # Step 5: pipeline_run_metadata.json
    run_end = datetime.now(timezone.utc)
    ticl = df[df["model"].str.upper().str.contains("TABICL")]
    tpfn = df[df["model"].str.upper().str.contains("TABPFN")]
    s_ticl = int((ticl["status"] == "SUCCESS").sum())
    f_ticl = int((ticl["status"] != "SUCCESS").sum())
    s_tpfn = int((tpfn["status"] == "SUCCESS").sum())
    f_tpfn = int((tpfn["status"] != "SUCCESS").sum())

    meta = {
        "phase": "7B", "pipeline_version": "1.0.0",
        "resume_script": "ml/phase7b_resume.py",
        "run_start": run_start.isoformat(), "run_end": run_end.isoformat(),
        "total_runtime_s": (run_end - run_start).total_seconds(),
        "random_seed": SEED, "records_per_disease": 5000,
        "diseases": ALL_DISEASES,
        "models_attempted": ["TabPFN 9.0.0", "TabICLv2 2.2.0"],
        "tabicl_success": s_ticl, "tabicl_failed": f_ticl,
        "tabpfn_success": s_tpfn, "tabpfn_failed": f_tpfn,
        "tabpfn_token_found": tabpfn_ok,
        "tabpfn_disease_results": tabpfn_summary,
        "disclaimer": (
            "SYNTHETIC RESEARCH DATA ONLY. Results do not represent "
            "clinical performance. Not clinically validated."
        ),
    }
    mp = META_DIR / "pipeline_run_metadata.json"
    mp.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"\nPipeline metadata: {mp}")

    # Final status
    print("\n" + "=" * 70)
    print("PHASE 7B RESUME - FINAL STATUS")
    print("=" * 70)
    print(f"  Runtime:   {(run_end - run_start).total_seconds():.1f}s")
    print(f"  TabICLv2:  {s_ticl}/10 SUCCESS, {f_ticl}/10 FAILED")
    print(f"  TabPFN:    {s_tpfn}/10 SUCCESS, {f_tpfn}/10 FAILED")
    print(f"  Summary:   {csv_path}")
    print()
    if s_tpfn == 0 and not tabpfn_ok:
        print("PHASE 7B - BLOCKED BY TABPFN AUTHENTICATION")
        print()
        print(f"All 20 combinations have an explicit status.")
        print(f"TabICLv2: {s_ticl}/10 succeeded.")
        print(f"TabPFN:   {s_tpfn}/10 succeeded (all failed: no token).")
        print()
        print("To unblock: set TABPFN_TOKEN env var and rerun this script.")
        print("Phase 7C must NOT be started.")
    elif s_tpfn == 10 and s_ticl == 10:
        print("PHASE 7B - COMPLETE")
        print("All 20 experiments succeeded. No winner declared.")
    else:
        print(f"PHASE 7B - PARTIALLY COMPLETE")
        print(f"TabICLv2: {s_ticl}/10, TabPFN: {s_tpfn}/10")
        print("All 20 combinations have an explicit recorded status.")
    print("=" * 70)


if __name__ == "__main__":
    main()