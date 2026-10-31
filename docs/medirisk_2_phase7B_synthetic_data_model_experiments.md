# MediRisk 2.0 — Phase 7B
## Synthetic Data Generation + Model Experiments

**Phase:** 7B
**Status:** COMPLETE
**Preceding Phase:** Phase 7A — ML & Dataset Specification (COMPLETE)
**Next Phase:** Phase 8 — Calibration, Risk Engine, SHAP API (NOT STARTED)

> ⚠️ **DISCLAIMER:** All datasets in this phase are **synthetically generated for research and development purposes only**. They do NOT represent real patient data, are NOT clinically validated, and must NOT be used for clinical decision-making.

---

## 1. Scope

Phase 7B covers:

1. Synthetic dataset generation for all 10 diseases
2. Dataset validation against Phase 7A specifications
3. Deterministic train/validation/test splitting (70/15/15)
4. Preprocessing pipeline (fit on training data only)
5. TabPFN 9.0.0 experiments on all 10 diseases
6. TabICLv2 2.2.0 experiments on all 10 diseases
7. Metric collection (12 required metrics per disease per model)
8. Resource measurement (RAM, latency, training time)
9. Reproducible experiment artifacts

**NOT in Phase 7B scope:**
- Production calibration (Isotonic Regression) — Phase 8
- Risk engine (LOW/MODERATE/HIGH) — Phase 8
- SHAP explanations — Phase 8
- Prediction API — Phase 8
- Frontend integration — Phase 8
- Model selection / winner declaration — NOT YET

---

## 2. Synthetic Datasets

### Generation Method

All datasets are generated deterministically using:

- `ml/generators/dataset_generator.py`
- Random seed: **42**
- Generator version: **1.0.0**
- Schema version: **1.0.0**

Each disease generator uses **logistic relationships** between features and the binary target to produce realistic-looking but synthetic correlations. No post-generation target thresholding was used to prevent trivial predictability.

### Dataset Summary

| # | Disease | File | Records | Positive Rate |
|---|---------|------|---------|---------------|
| 1 | Diabetes | `diabetes_v1.0.0.csv` | 5,000 | ~31.6% |
| 2 | Heart Disease | `heart_disease_v1.0.0.csv` | 5,000 | ~35.6% |
| 3 | Stroke | `stroke_v1.0.0.csv` | 5,000 | ~22.2% |
| 4 | Asthma | `asthma_v1.0.0.csv` | 5,000 | ~28.2% |
| 5 | CKD | `chronic_kidney_disease_v1.0.0.csv` | 5,000 | ~29.1% |
| 6 | Liver Disease | `liver_disease_v1.0.0.csv` | 5,000 | ~36.7% |
| 7 | Parkinson's | `parkinsons_v1.0.0.csv` | 5,000 | ~34.4% |
| 8 | Breast Cancer | `breast_cancer_v1.0.0.csv` | 5,000 | ~34.1% |
| 9 | Lung Cancer | `lung_cancer_v1.0.0.csv` | 5,000 | ~33.2% |
| 10 | Hypertension | `hypertension_v1.0.0.csv` | 5,000 | ~37.0% |
| | **TOTAL** | | **50,000** | |

### Synthetic Data Limitations

- All datasets are **SYNTHETIC**. They do NOT represent real patients.
- Correlation structures are prototypical and NOT medically validated.
- Feature distributions are approximate, not epidemiologically sourced.
- Class balance is artificially enriched for research benchmarking.
- Results must NOT be cited as clinical evidence.

---

## 3. Validation

All 10 datasets validated against Phase 7A specifications using `ml/validation/validator.py`.

**13 checks performed per dataset:**

1. Record count (within 10% of 5,000)
2. Column names (no missing, no unexpected)
3. Snake_case naming
4. Target binary values (0/1 only)
5. No target leakage (target not in feature list)
6. Infinite values (none allowed)
7. Missing value policy (per-feature limits)
8. Numerical domains (within spec ranges)
9. Categorical domains (only spec-allowed values)
10. Binary constraints (0/1 only for binary features)
11. Class distribution (within acceptable range)
12. Duplicate rows
13. Schema version consistency

**Validation result: 10/10 PASS, 0 errors, 0 warnings**

---

## 4. Train/Validation/Test Split

| Parameter | Value |
|-----------|-------|
| Train | **70%** (3,500 records) |
| Validation | **15%** (750 records) |
| Test | **15%** (750 records) |
| Stratified | Yes |
| Random seed | 42 |
| Test set policy | **Untouched — reserved for final evaluation** |

Splits are saved in `ml/data/splits/<disease>/`.

---

## 5. Preprocessing

Preprocessing implemented in `ml/preprocessing/preprocessor.py`.

| Feature Type | Strategy | Fit On |
|---|---|---|
| Numerical | StandardScaler + median imputation | **Train only** |
| Categorical | OrdinalEncoder + most_frequent imputation | **Train only** |
| Binary | Passthrough (fill missing with 0) | N/A |
| Missing indicator | Added for all imputed features | N/A |

**CRITICAL:** Preprocessing is fit **exclusively on training data**. Validation and test transforms apply the fitted preprocessors without re-fitting. Re-fitting raises `RuntimeError`.

---

## 6. Model Experiments

### Models

| Model | Version | Device | Notes |
|-------|---------|--------|-------|
| TabPFN | 9.0.0 | CPU | Prior-data fitted transformer |
| TabICLv2 | 2.2.0 | CPU | In-context learning |

Both models run on the same train/validation split. Test set not used.

No winner declared in this phase.

### Experiment Protocol

Defined in `ml/experiments/experiment_protocol.yaml`. All experiments follow:
- Same random seed (42)
- Same preprocessing pipeline
- Same train/val/test split
- CPU-first execution
- All 12 required metrics collected

---

## 7. Required Metrics

| Metric | Type |
|--------|------|
| ROC-AUC | Classification |
| PR-AUC | Classification |
| Accuracy | Classification |
| Precision | Classification |
| Recall / Sensitivity | Classification |
| Specificity | Classification |
| F1-score | Classification |
| Brier Score | Calibration |
| Expected Calibration Error | Calibration |
| Inference Latency (ms) | System |
| Peak RAM (MB) | System |
| VRAM (MB) | System (N/A — CPU only) |

---

## 8. Resource Monitoring

- **Device:** CPU (CUDA not assumed)
- **VRAM:** Not applicable (CPU execution)
- **RAM:** Peak process RSS measured per experiment
- **Latency:** Wall-clock inference time in milliseconds
- **Training time:** Wall-clock fit time in seconds

---

## 9. What Was NOT Implemented

| Item | Status |
|------|--------|
| Isotonic Regression calibration | NOT IMPLEMENTED — Phase 8 |
| Risk engine (LOW/MODERATE/HIGH) | NOT IMPLEMENTED — Phase 8 |
| SHAP explanations | NOT IMPLEMENTED — Phase 8 |
| Prediction API endpoints | NOT IMPLEMENTED — Phase 8 |
| Frontend ML integration | NOT IMPLEMENTED — Phase 8 |
| Model winner declaration | NOT APPLICABLE — evidence-based review pending |

---

## 10. Directory Structure

```
ml/
├── data/
│   ├── raw/                   # 10 CSV datasets + 10 metadata JSONs
│   ├── splits/                # train/val/test CSVs per disease
│   ├── validation/            # validation_results.json
│   └── metadata/              # pipeline_run_metadata.json
├── generators/
│   └── dataset_generator.py   # Deterministic synthetic generator
├── validation/
│   └── validator.py           # Schema validation framework
├── preprocessing/
│   └── preprocessor.py        # Leakage-safe preprocessing + splitting
├── experiments/
│   ├── experiment_protocol.yaml
│   ├── runner.py              # TabPFN + TabICLv2 runner
│   └── __init__.py
├── results/
│   ├── <disease>/
│   │   ├── tabpfn/experiment_result.json
│   │   └── tabicl/experiment_result.json
│   └── experiment_summary.csv
├── requirements.txt
├── pipeline.py
└── README.md
```
