# MediRisk 2.0 — Phase 7A ML & Dataset Specification

**Phase:** 7A — ML & Dataset Specification  
**Status:** ✅ COMPLETE (Specification Only)  
**Date:** 2026-09-26  
**Preceding Phase:** Phase 6 — Profiles & Assessments (COMPLETE)  
**Next Phase:** Phase 7B — Synthetic Data Generation & Model Experiments  

> ⚠️ **DISCLAIMER:** All datasets described in this specification are synthetic research prototypes. They do NOT represent real patient data and have NOT been clinically validated. No clinical decisions should be made based on these specifications or any model trained on them.

---

## 1. ML Architecture

```
Authenticated User Assessment Input (from Phase 6 API)
              ↓
  Feature Vector (from HealthAssessment.input_data)
              ↓
  Schema Validation (ml/specifications/<disease>.yaml)
              ↓
  Preprocessing Pipeline (ml/preprocessing/)
      → fit on training data only
      → applied to validation/test without re-fitting
              ↓
  ┌─────────────────────┐   ┌─────────────────────┐
  │   TabPFN  9.0.0     │   │  TabICLv2  2.2.0    │
  │   (Candidate A)     │   │  (Candidate B)      │
  └──────────┬──────────┘   └──────────┬──────────┘
             └──────────────┬───────────┘
                            ↓
           Raw Probability  [0.0 – 1.0]
                            ↓
           Calibration  (Isotonic Regression)  [Phase 8]
                            ↓
           Calibrated Probability
                            ↓
           Risk Engine  → LOW / MODERATE / HIGH  [Phase 8]
                            ↓
           SHAP Explainability Attribution  [Phase 8]
                            ↓
           API Response → Frontend
```

---

## 2. Ten Disease Tasks

| # | Disease Code | Target Column | Positive Class Meaning |
|---|---|---|---|
| 1 | `DIABETES` | `diabetes_outcome` | Type 2 diabetes diagnosis |
| 2 | `HEART_DISEASE` | `heart_disease_outcome` | Coronary heart disease |
| 3 | `STROKE` | `stroke_outcome` | Stroke event occurred |
| 4 | `ASTHMA` | `asthma_outcome` | Asthma diagnosis |
| 5 | `CHRONIC_KIDNEY_DISEASE` | `ckd_outcome` | CKD present |
| 6 | `LIVER_DISEASE` | `liver_disease_outcome` | Liver disease present |
| 7 | `PARKINSONS` | `parkinsons_outcome` | Parkinson's disease |
| 8 | `BREAST_CANCER` | `breast_cancer_outcome` | Malignant breast cancer |
| 9 | `LUNG_CANCER` | `lung_cancer_outcome` | Lung cancer present |
| 10 | `HYPERTENSION` | `hypertension_outcome` | Hypertension present |

---

## 3. Dataset Specification

### Target Convention

- `0` = negative class (no disease)
- `1` = positive class (disease present)
- Task type: **binary classification** (all 10 diseases)
- Model output: **probability** in `[0.0, 1.0]`

### Record Targets

| Scope | Count |
|---|---|
| Records per disease | ~5,000 |
| Total records | ~50,000 |
| Nature | SYNTHETIC RESEARCH |
| Clinical validation | ❌ None |

---

## 4. Feature Schema Strategy

All feature schemas are defined in `ml/specifications/<disease>.yaml`.

### Feature Types

| Type | Preprocessing | Missing Strategy |
|---|---|---|
| Numerical | StandardScaler (train only) | Median + missingness indicator |
| Categorical | OrdinalEncoder (train only) | Most frequent + missingness indicator |
| Binary | Passthrough | None required |

### Feature Naming Rules

- Lowercase
- `snake_case`
- No spaces
- No ambiguous abbreviations
- Renaming requires a version bump

### Feature Counts Per Disease (Approximate)

| Disease | Features | Numerical | Categorical | Binary |
|---|---|---|---|---|
| Diabetes | 14 | 9 | 3 | 2 |
| Heart Disease | 16 | 7 | 6 | 3 |
| Stroke | 13 | 4 | 5 | 4 |
| Asthma | 14 | 5 | 4 | 5 |
| CKD | 19 | 11 | 4 | 4 |
| Liver Disease | 15 | 10 | 3 | 2 |
| Parkinson's | 14 | 10 | 1 | 3 |
| Breast Cancer | 16 | 11 | 2 | 3 |
| Lung Cancer | 18 | 4 | 4 | 10 |
| Hypertension | 15 | 6 | 6 | 3 |

---

## 5. Target Definitions

All targets are binary (0/1). The model predicts **disease-class probability** only.

The application-level **risk engine** (Phase 8) transforms calibrated probability into `LOW / MODERATE / HIGH`. The ML model does **not** predict risk categories.

### Class Balance Targets

| Disease | Positive Proportion | Acceptable Range |
|---|---|---|
| Diabetes | 35% | 25–45% |
| Heart Disease | 40% | 30–50% |
| Stroke | 25% | 15–35% |
| Asthma | 30% | 20–40% |
| CKD | 35% | 25–45% |
| Liver Disease | 38% | 28–48% |
| Parkinson's | 35% | 25–45% |
| Breast Cancer | 37% | 27–47% |
| Lung Cancer | 35% | 25–45% |
| Hypertension | 40% | 30–50% |

> These proportions are synthetic and do NOT represent real-world clinical prevalence.

---

## 6. Missing Value Policy

| Rule | Policy |
|---|---|
| Max allowed missingness per feature | 20% |
| Missing indicator | Required for all imputed features |
| Numerical imputation | Median |
| Categorical imputation | Most frequent |
| Fit on | **Training data only** |
| Re-fit on validation/test | **NEVER** |

---

## 7. Data Leakage Policy

### Prohibited Field Classes

- Post-diagnosis treatment outcomes
- Final diagnosis labels used as features
- Future clinical outcomes
- Prediction-derived values
- Manually assigned risk categories
- Fields generated from the target
- Calibrated probabilities
- Risk level assignments

### Notable Leakage Risks per Disease

| Disease | High-Risk Fields | Risk Level |
|---|---|---|
| Diabetes | `glucose_level`, `insulin_level` | MEDIUM |
| Heart Disease | `num_major_vessels`, `st_depression` | HIGH / MEDIUM |
| Stroke | `avg_glucose_level` | MEDIUM |
| Asthma | `fev1_fvc_ratio` | HIGH |
| CKD | `serum_creatinine`, `blood_urea` | HIGH |
| Liver Disease | `alt`, `ast`, `total_bilirubin` | HIGH |
| Parkinson's | `tremor_score`, `rigidity_score` | HIGH |
| Breast Cancer | `radius_mean` (synthetic cell data) | HIGH |
| Lung Cancer | `hemoptysis` | HIGH |
| Hypertension | `blood_pressure_systolic` — **EXCLUDED** | CRITICAL |

---

## 8. Train / Validation / Test Strategy

| Split | Percentage | Seed |
|---|---|---|
| Train | **70%** | 42 |
| Validation | **15%** | 42 |
| Test | **15%** | 42 |

- Stratified by target class
- Test set: **untouched until final evaluation**
- No hyperparameter decisions using test data

---

## 9. Reproducibility

Every experiment must record:

| Field | Description |
|---|---|
| `dataset_version` | Version of the dataset specification |
| `schema_version` | Version of the schema contract |
| `random_seed` | Default: `42` |
| `model_name` | TabPFN or TabICLv2 |
| `model_version` | Exact pip version |
| `python_version` | Runtime Python version |
| `dependency_versions` | All frozen versions |
| `preprocessing_version` | Preprocessing pipeline version |
| `experiment_timestamp` | ISO 8601 UTC timestamp |

---

## 10. Synthetic Data Methodology

### Generation Contract (Phase 7B — NOT YET EXECUTED)

- Method: Deterministic synthetic generation
- Random seed: 42 (required)
- Generator must:
  - Produce schema-valid records
  - Generate realistic-looking value ranges (prototype only)
  - Avoid impossible values
  - Avoid direct target leakage
  - Record generator version and dataset version
  - Validate output before saving

> All synthetic correlations are **prototypes only**. They are NOT medically validated.

---

## 11. TabPFN 9.0.0

| Field | Value |
|---|---|
| Library | `tabpfn` |
| Version | `9.0.0` |
| Pip package | `tabpfn==9.0.0` |
| Type | Tabular foundation model (prior-data fitted network) |
| Role | Experimental candidate |
| Status | NOT TRAINED |

### Requirements for Phase 7B

- Deterministic configuration where supported
- Record inference latency (ms)
- Record RAM usage (MB)
- Record VRAM usage (MB, if GPU available)
- Record model version and environment versions
- Same train/val/test split as TabICLv2
- Same preprocessing

---

## 12. TabICLv2 2.2.0

| Field | Value |
|---|---|
| Library | `tabicl` |
| Version | `2.2.0` |
| Pip package | `tabicl==2.2.0` |
| Type | In-context learning model for tabular data |
| Role | Experimental candidate |
| Status | NOT TRAINED |

> Same evaluation protocol as TabPFN. No winner declared before experiments.

---

## 13. Evaluation Metrics

### Classification
| Metric | Description |
|---|---|
| ROC-AUC | Area Under the ROC Curve (primary) |
| PR-AUC | Area Under Precision-Recall Curve (primary) |
| Accuracy | Classification accuracy |
| Precision | Positive predictive value |
| Recall / Sensitivity | True positive rate |
| Specificity | True negative rate |
| F1-score | Harmonic mean of precision and recall |

### Calibration
| Metric | Description |
|---|---|
| Brier Score | MSE of predicted probabilities vs outcomes |
| ECE | Expected Calibration Error |

### System Performance
| Metric | Unit |
|---|---|
| Inference latency | ms |
| RAM consumption | MB |
| VRAM consumption | MB (if GPU) |

> **No composite score in Phase 7B. No ranking before all experiments complete. Model selection is evidence-based.**

---

## 14. Calibration Protocol

| Field | Value |
|---|---|
| Method | Isotonic Regression |
| Fit on | Validation set only |
| Test set | Untouched until final evaluation |
| Status | NOT IMPLEMENTED (Phase 8) |
| Outputs | `raw_probability`, `calibrated_probability` |

---

## 15. Risk Engine Contract

| Field | Value |
|---|---|
| Input | `calibrated_probability` |
| Output | `LOW`, `MODERATE`, `HIGH` |
| Status | NOT IMPLEMENTED (Phase 8) |
| Clinical validation | ❌ None |

**Prototype thresholds (not clinically validated):**

| Range | Class |
|---|---|
| < 30% | LOW |
| 30% – 70% | MODERATE |
| > 70% | HIGH |

---

## 16. Explainability Contract

| Field | Value |
|---|---|
| Library | SHAP |
| Version | `0.46.0` |
| Status | NOT IMPLEMENTED (Phase 8) |
| Storage | `prediction_attributions` |

> SHAP values indicate **feature contribution to model output** only. They must NOT be interpreted as causal medical relationships.

---

## 17. Dataset Registry

Registry file: `ml/specifications/dataset_registry.yaml`

All 10 diseases registered with:
- `disease_code` (unique)
- `dataset_identifier`
- `dataset_version`
- `schema_version`
- `specification_file` path
- `target_column`
- `record_target`
- `status: SPECIFICATION_ONLY`
- `generated: false`

---

## 18. Experiment Manifest

Manifest file: `ml/experiments/experiment_protocol.yaml`

Defines:
- `experiment_version`
- `dataset_versions` (all 10)
- `models` (TabPFN + TabICLv2)
- `data_split` (70/15/15)
- `random_seed` (42)
- `metrics` (all required)
- `calibration_method`
- `resource_metrics`
- `reproducibility_fields`

---

## 19. What Was Intentionally NOT Executed in Phase 7A

| Item | Status |
|---|---|
| Synthetic dataset generation (.csv/.parquet/.pkl) | ❌ NOT generated |
| ML model training | ❌ NOT executed |
| Model weight download | ❌ NOT downloaded |
| TabPFN inference | ❌ NOT run |
| TabICLv2 inference | ❌ NOT run |
| Calibration fitting | ❌ NOT implemented |
| Risk engine | ❌ NOT implemented |
| SHAP attribution | ❌ NOT implemented |
| Prediction API endpoints | ❌ NOT created |
| Frontend prediction UI | ❌ NOT built |
| Benchmark GPU/CPU | ❌ NOT executed |
| Old project access (`Multi disease`) | ❌ NEVER accessed |

---

## 20. Next Phase: Phase 7B

**Phase 7B — Synthetic Data Generation & Model Experiments** will:

1. Generate all 10 synthetic datasets (5,000 records each)
2. Validate each dataset against its schema specification
3. Create the preprocessing pipeline (fit on training data only)
4. Run TabPFN 9.0.0 experiments on all 10 diseases
5. Run TabICLv2 2.2.0 experiments on all 10 diseases
6. Collect all evaluation metrics (ROC-AUC, PR-AUC, Brier, ECE, latency, RAM, VRAM)
7. Produce comparative results (no winner declared yet)

**Do NOT start Phase 7B until this Phase 7A specification is reviewed and approved.**
