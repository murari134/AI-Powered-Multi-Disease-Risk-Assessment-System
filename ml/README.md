# MediRisk 2.0 — Machine Learning Layer

> **Phase 7A Status:** Specification complete. No datasets generated. No models trained. No weights downloaded.

---

## ML Architecture Overview

```
Authenticated User Assessment Input
            ↓
   Feature Vector (from HealthAssessment.input_data)
            ↓
   Schema Validation (ml/specifications/)
            ↓
   Preprocessing Pipeline (ml/preprocessing/)
       fit on train only — never on full dataset
            ↓
   ┌─────────────────┐     ┌─────────────────┐
   │  TabPFN 9.0.0   │     │ TabICLv2 2.2.0  │
   │  (Candidate A)  │     │  (Candidate B)  │
   └────────┬────────┘     └────────┬────────┘
            └──────────┬────────────┘
                       ↓
          Raw Probability [0.0, 1.0]
                       ↓
          Calibration (Isotonic Regression)
                       ↓
          Calibrated Probability
                       ↓
          Risk Engine → LOW / MODERATE / HIGH
                       ↓
          SHAP Explainability Attribution
                       ↓
          API Response → Frontend
```

---

## Phase Boundaries

| Phase | Scope | Status |
|-------|-------|--------|
| Phase 7A | ML & Dataset Specification | ✅ COMPLETE |
| Phase 7B | Synthetic Data Generation + Model Experiments | ✅ COMPLETE |
| Phase 8  | Calibration, Risk Engine, Explainability, API | ⏳ NOT STARTED |

---

## Disease Tasks

| # | Disease Code | Target Column | Records |
|---|---|---|---|
| 1 | `DIABETES` | `diabetes_outcome` | 5,000 |
| 2 | `HEART_DISEASE` | `heart_disease_outcome` | 5,000 |
| 3 | `STROKE` | `stroke_outcome` | 5,000 |
| 4 | `ASTHMA` | `asthma_outcome` | 5,000 |
| 5 | `CHRONIC_KIDNEY_DISEASE` | `ckd_outcome` | 5,000 |
| 6 | `LIVER_DISEASE` | `liver_disease_outcome` | 5,000 |
| 7 | `PARKINSONS` | `parkinsons_outcome` | 5,000 |
| 8 | `BREAST_CANCER` | `breast_cancer_outcome` | 5,000 |
| 9 | `LUNG_CANCER` | `lung_cancer_outcome` | 5,000 |
| 10 | `HYPERTENSION` | `hypertension_outcome` | 5,000 |
| | **TOTAL** | | **50,000** |

All targets are binary: `0 = negative`, `1 = positive`.

---

## Primary ML Models

| Model | Version | Role |
|---|---|---|
| **TabPFN** | `9.0.0` | Experimental candidate |
| **TabICLv2** | `2.2.0` | Experimental candidate |

> **IMPORTANT:** Neither model is the declared winner. Model selection must be evidence-based after Phase 7B experiments.

**Prohibited primary models:** XGBoost, LightGBM, Random Forest.

---

## Frozen Dependency Versions

| Package | Version |
|---|---|
| `tabpfn` | 9.0.0 |
| `tabicl` | 2.2.0 |
| `torch` | 2.14.0 |
| `scikit-learn` | 1.5.2 |
| `numpy` | 1.26.4 |
| `pandas` | 2.2.2 |
| `shap` | 0.46.0 |

Do **NOT** silently change any version. If a compatibility problem is found, stop and document it.

---

## Directory Structure

```
ml/
├── specifications/          # Disease dataset specifications (YAML)
│   ├── schema-version.yaml  # Global schema + version contract
│   ├── dataset_registry.yaml
│   ├── diabetes.yaml
│   ├── heart_disease.yaml
│   ├── stroke.yaml
│   ├── asthma.yaml
│   ├── chronic_kidney_disease.yaml
│   ├── liver_disease.yaml
│   ├── parkinsons.yaml
│   ├── breast_cancer.yaml
│   ├── lung_cancer.yaml
│   └── hypertension.yaml
├── datasets/                # Synthetic datasets (Phase 7B — NOT YET CREATED)
├── preprocessing/           # Feature preprocessing pipelines (Phase 7B)
├── models/
│   ├── tabpfn/              # TabPFN wrapper (Phase 7B)
│   └── tabicl/              # TabICLv2 wrapper (Phase 7B)
├── calibration/             # Isotonic regression calibrator (Phase 8)
├── evaluation/              # Evaluation benchmarks (Phase 7B)
├── explainability/          # SHAP attribution (Phase 8)
├── inference/               # End-to-end inference pipeline (Phase 8)
├── experiments/
│   └── experiment_protocol.yaml  # Official comparison protocol
└── README.md
```

---

## Key Contracts

### Target Convention
- `0` = negative class (no disease)
- `1` = positive class (disease present)
- Task type: binary classification
- Output: disease-class probability `[0.0, 1.0]`

### Data Split
- Train: **70%** | Validation: **15%** | Test: **15%**
- Stratified split | Random seed: **42**
- Test set untouched until final evaluation

### Preprocessing Rules
- Fit preprocessing on **training data only**
- Never fit on full dataset before splitting
- Numerical: `StandardScaler`
- Categorical: `OrdinalEncoder`
- Binary: passthrough
- Missing: median/most_frequent + missingness indicator

### Data Leakage Policy
- Post-diagnosis treatment outcomes: **PROHIBITED**
- Final diagnosis labels as features: **PROHIBITED**
- Future clinical outcomes: **PROHIBITED**
- Risk level / calibrated probability: **PROHIBITED**

---

## Disclaimer

> All datasets in this layer are **synthetically generated for research and development purposes only**.
> They do **NOT** represent real patient data and have **NOT** been clinically validated.
> No clinical decisions should be made based on these datasets or any model trained on them.
