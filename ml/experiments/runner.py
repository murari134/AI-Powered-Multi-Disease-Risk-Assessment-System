"""
MediRisk 2.0 — Experiment Runner
Phase 7B

Runs TabPFN 9.0.0 and TabICLv2 2.2.0 experiments on all 10 diseases.

Rules:
- No winner declared before experiments.
- No fabricated results. Failures are recorded honestly.
- CPU-first; CUDA fallback if available.
- Test set untouched until final evaluation.
- Raw probabilities stored. No production calibration.
- No risk level conversion.

DISCLAIMER: Synthetic research data only.
"""

from __future__ import annotations

import gc
import importlib.metadata
import json
import platform
import sys
import time
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import psutil

ML_ROOT = Path(__file__).parent.parent

EXPERIMENT_PROTOCOL_VERSION = "1.0.0"
GENERATOR_VERSION = "1.0.0"
PREPROCESSING_VERSION = "1.0.0"


# ---------------------------------------------------------------------------
# Resource measurement utilities
# ---------------------------------------------------------------------------

def _get_ram_mb() -> float:
    """Current process RAM usage in MB."""
    proc = psutil.Process()
    return proc.memory_info().rss / (1024 ** 2)


def _peak_ram_context():
    """Simple RAM tracking context manager."""
    class _Ctx:
        def __init__(self):
            self.start_mb = 0.0
            self.peak_mb = 0.0

        def __enter__(self):
            gc.collect()
            self.start_mb = _get_ram_mb()
            return self

        def __exit__(self, *args):
            gc.collect()
            self.peak_mb = max(_get_ram_mb() - self.start_mb, 0.0)
    return _Ctx()


def _env_info() -> dict[str, str]:
    """Collect environment information."""
    info = {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "cpu_count": str(psutil.cpu_count()),
    }
    for pkg, key in [("torch", "torch_version"), ("tabpfn", "tabpfn_version"),
                      ("tabicl", "tabicl_version"), ("scikit-learn", "sklearn_version")]:
        try:
            info[key] = importlib.metadata.version(pkg)
        except importlib.metadata.PackageNotFoundError:
            info[key] = "NOT_INSTALLED"
    try:
        import torch
        info["cuda_available"] = str(torch.cuda.is_available())
        if torch.cuda.is_available():
            info["cuda_device"] = torch.cuda.get_device_name(0)
    except ImportError:
        info["cuda_available"] = "false"
    return info


# ---------------------------------------------------------------------------
# Metrics calculation
# ---------------------------------------------------------------------------

def _compute_metrics(
    y_true: np.ndarray,
    y_pred_class: np.ndarray,
    y_prob: np.ndarray,
) -> dict[str, float | None]:
    """Compute all required Phase 7A metrics."""
    from sklearn.metrics import (
        accuracy_score,
        average_precision_score,
        brier_score_loss,
        confusion_matrix,
        f1_score,
        precision_score,
        recall_score,
        roc_auc_score,
    )

    metrics: dict[str, float | None] = {}

    try:
        metrics["roc_auc"] = float(roc_auc_score(y_true, y_prob))
    except Exception as e:
        metrics["roc_auc"] = None
        metrics["roc_auc_error"] = str(e)

    try:
        metrics["pr_auc"] = float(average_precision_score(y_true, y_prob))
    except Exception:
        metrics["pr_auc"] = None

    try:
        metrics["accuracy"] = float(accuracy_score(y_true, y_pred_class))
    except Exception:
        metrics["accuracy"] = None

    try:
        metrics["precision"] = float(
            precision_score(y_true, y_pred_class, zero_division=0))
    except Exception:
        metrics["precision"] = None

    try:
        recall_val = float(recall_score(y_true, y_pred_class, zero_division=0))
        metrics["recall"] = recall_val
        metrics["sensitivity"] = recall_val  # sensitivity == recall
    except Exception:
        metrics["recall"] = None
        metrics["sensitivity"] = None

    try:
        cm = confusion_matrix(y_true, y_pred_class)
        if cm.shape == (2, 2):
            tn, fp, fn, tp = cm.ravel()
            metrics["specificity"] = float(tn / (tn + fp)) if (tn + fp) > 0 else None
        else:
            metrics["specificity"] = None
    except Exception:
        metrics["specificity"] = None

    try:
        metrics["f1_score"] = float(
            f1_score(y_true, y_pred_class, zero_division=0))
    except Exception:
        metrics["f1_score"] = None

    try:
        metrics["brier_score"] = float(brier_score_loss(y_true, y_prob))
    except Exception:
        metrics["brier_score"] = None

    # ECE
    try:
        metrics["expected_calibration_error"] = float(
            _compute_ece(y_true, y_prob, n_bins=10))
    except Exception:
        metrics["expected_calibration_error"] = None

    return metrics


def _compute_ece(y_true: np.ndarray, y_prob: np.ndarray,
                 n_bins: int = 10) -> float:
    """Expected Calibration Error."""
    bins = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    n = len(y_true)
    for i in range(n_bins):
        mask = (y_prob >= bins[i]) & (y_prob < bins[i + 1])
        if mask.sum() == 0:
            continue
        bin_acc = y_true[mask].mean()
        bin_conf = y_prob[mask].mean()
        ece += mask.sum() * abs(bin_acc - bin_conf)
    return ece / n


# ---------------------------------------------------------------------------
# TabPFN experiment
# ---------------------------------------------------------------------------

def _run_tabpfn(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    feature_names: list[str],
) -> dict[str, Any]:
    """Run TabPFN 9.0.0 experiment. Returns result dict."""
    result: dict[str, Any] = {
        "model_name": "TabPFN",
        "model_version": "9.0.0",
        "status": "PENDING",
    }

    try:
        import tabpfn
        actual_version = importlib.metadata.version("tabpfn")
        result["actual_version"] = actual_version

        from tabpfn import TabPFNClassifier

        load_start = time.perf_counter()
        clf = TabPFNClassifier(device="cpu")
        load_time = time.perf_counter() - load_start

        with _peak_ram_context() as ram_ctx:
            train_start = time.perf_counter()
            clf.fit(X_train, y_train)
            train_time = time.perf_counter() - train_start

            inf_start = time.perf_counter()
            y_prob = clf.predict_proba(X_val)[:, 1]
            inf_time = time.perf_counter() - inf_start

        y_pred = (y_prob >= 0.5).astype(int)
        metrics = _compute_metrics(y_val, y_pred, y_prob)

        result.update({
            "status": "SUCCESS",
            "device": "cpu",
            "model_load_time_s": round(load_time, 4),
            "training_time_s": round(train_time, 4),
            "inference_latency_ms": round(inf_time * 1000, 2),
            "peak_ram_mb": round(ram_ctx.peak_mb, 2),
            "vram_mb": None,
            "metrics": metrics,
            "sample_probabilities": y_prob[:5].tolist(),
        })

    except ImportError as e:
        result["status"] = "BLOCKED_IMPORT_ERROR"
        result["error_type"] = "ImportError"
        result["error_message"] = str(e)
        result["metrics"] = {}
    except Exception as e:
        result["status"] = "FAILED"
        result["error_type"] = type(e).__name__
        result["error_message"] = str(e)
        result["traceback"] = traceback.format_exc()[-2000:]
        result["metrics"] = {}

    return result


# ---------------------------------------------------------------------------
# TabICLv2 experiment
# ---------------------------------------------------------------------------

def _run_tabicl(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    feature_names: list[str],
) -> dict[str, Any]:
    """Run TabICLv2 2.2.0 experiment. Returns result dict."""
    result: dict[str, Any] = {
        "model_name": "TabICLv2",
        "model_version": "2.2.0",
        "status": "PENDING",
    }

    try:
        import tabicl
        actual_version = importlib.metadata.version("tabicl")
        result["actual_version"] = actual_version

        from tabicl import TabICLClassifier

        load_start = time.perf_counter()
        clf = TabICLClassifier()
        load_time = time.perf_counter() - load_start

        with _peak_ram_context() as ram_ctx:
            train_start = time.perf_counter()
            clf.fit(X_train, y_train)
            train_time = time.perf_counter() - train_start

            inf_start = time.perf_counter()
            y_prob = clf.predict_proba(X_val)[:, 1]
            inf_time = time.perf_counter() - inf_start

        y_pred = (y_prob >= 0.5).astype(int)
        metrics = _compute_metrics(y_val, y_pred, y_prob)

        result.update({
            "status": "SUCCESS",
            "device": "cpu",
            "model_load_time_s": round(load_time, 4),
            "training_time_s": round(train_time, 4),
            "inference_latency_ms": round(inf_time * 1000, 2),
            "peak_ram_mb": round(ram_ctx.peak_mb, 2),
            "vram_mb": None,
            "metrics": metrics,
            "sample_probabilities": y_prob[:5].tolist(),
        })

    except ImportError as e:
        result["status"] = "BLOCKED_IMPORT_ERROR"
        result["error_type"] = "ImportError"
        result["error_message"] = str(e)
        result["metrics"] = {}
    except Exception as e:
        result["status"] = "FAILED"
        result["error_type"] = type(e).__name__
        result["error_message"] = str(e)
        result["traceback"] = traceback.format_exc()[-2000:]
        result["metrics"] = {}

    return result


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def run_experiment(
    disease_id: str,
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    preprocessor,
    target_col: str,
    *,
    seed: int = 42,
    dataset_version: str = "1.0.0",
) -> dict[str, Any]:
    """
    Run both TabPFN and TabICLv2 for one disease.
    Returns structured experiment result. No results are fabricated.
    """
    experiment_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now(timezone.utc).isoformat()
    env = _env_info()

    X_train_raw = train_df.drop(columns=[target_col])
    y_train = train_df[target_col].values.astype(int)
    X_val_raw = val_df.drop(columns=[target_col])
    y_val = val_df[target_col].values.astype(int)

    # Preprocess
    X_train = preprocessor.transform(X_train_raw).values
    X_val_p = preprocessor.transform(X_val_raw).values
    feature_names = list(preprocessor.transform(X_train_raw).columns)

    base_record = {
        "experiment_id": experiment_id,
        "disease_code": disease_id.upper(),
        "dataset_version": dataset_version,
        "schema_version": "1.0.0",
        "experiment_protocol_version": EXPERIMENT_PROTOCOL_VERSION,
        "preprocessing_version": PREPROCESSING_VERSION,
        "random_seed": seed,
        "train_records": len(train_df),
        "val_records": len(val_df),
        "feature_count": X_train.shape[1],
        "train_positive_rate": float(y_train.mean()),
        "val_positive_rate": float(y_val.mean()),
        "split_config": {"train": 0.70, "val": 0.15, "test": 0.15},
        "python_version": env.get("python_version"),
        "torch_version": env.get("torch_version"),
        "tabpfn_version": env.get("tabpfn_version"),
        "tabicl_version": env.get("tabicl_version"),
        "sklearn_version": env.get("sklearn_version"),
        "cuda_available": env.get("cuda_available"),
        "experiment_timestamp": timestamp,
        "disclaimer": (
            "SYNTHETIC RESEARCH DATA. Results do not represent clinical performance."
        ),
    }

    print(f"  Running TabPFN on {disease_id}...")
    tabpfn_result = _run_tabpfn(X_train, y_train, X_val_p, y_val, feature_names)

    print(f"  Running TabICLv2 on {disease_id}...")
    tabicl_result = _run_tabicl(X_train, y_train, X_val_p, y_val, feature_names)

    return {
        **base_record,
        "tabpfn": tabpfn_result,
        "tabicl": tabicl_result,
    }


def _json_safe(obj):
    """Convert numpy scalars to Python native types for JSON serialization."""
    import numpy as np
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.bool_):
        return bool(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def save_experiment_result(
    result: dict[str, Any],
    disease_id: str,
    output_dir: Path,
) -> None:
    """Save per-disease experiment result to JSON."""
    for model in ["tabpfn", "tabicl"]:
        model_dir = output_dir / disease_id / model
        model_dir.mkdir(parents=True, exist_ok=True)
        result_path = model_dir / "experiment_result.json"
        payload = {**{k: v for k, v in result.items()
                      if k not in ("tabpfn", "tabicl")},
                   **result[model]}
        result_path.write_text(
            json.dumps(payload, indent=2, default=_json_safe),
            encoding="utf-8",
        )


def build_summary(all_results: dict[str, dict]) -> pd.DataFrame:
    """Build aggregate comparison table."""
    rows = []
    for disease_id, result in all_results.items():
        for model in ["tabpfn", "tabicl"]:
            model_res = result.get(model, {})
            metrics = model_res.get("metrics", {})
            row = {
                "disease": disease_id,
                "model": model_res.get("model_name", model.upper()),
                "model_version": model_res.get("model_version", "unknown"),
                "status": model_res.get("status", "UNKNOWN"),
                "roc_auc": metrics.get("roc_auc"),
                "pr_auc": metrics.get("pr_auc"),
                "accuracy": metrics.get("accuracy"),
                "precision": metrics.get("precision"),
                "recall": metrics.get("recall"),
                "sensitivity": metrics.get("sensitivity"),
                "specificity": metrics.get("specificity"),
                "f1_score": metrics.get("f1_score"),
                "brier_score": metrics.get("brier_score"),
                "ece": metrics.get("expected_calibration_error"),
                "inference_latency_ms": model_res.get("inference_latency_ms"),
                "peak_ram_mb": model_res.get("peak_ram_mb"),
                "vram_mb": model_res.get("vram_mb"),
                "training_time_s": model_res.get("training_time_s"),
                "device": model_res.get("device"),
                "error": model_res.get("error_message"),
            }
            rows.append(row)
    return pd.DataFrame(rows)
