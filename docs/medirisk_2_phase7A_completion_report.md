# MediRisk 2.0 — Phase 7A Completion Report
## ML & Dataset Specification

**Phase:** 7A  
**Status:** ✅ COMPLETE  
**Date:** 2026-09-26  

---

## 1. Baseline Test Result (Before Phase 7A)

```
178 passed, 4 warnings in 46.69s
```

All Phase 3–6 tests: ✅ 178/178 passing

---

## 2. Phase 7A Test Result

**Phase 7A tests:** 17 tests (16 required + 1 bonus registry validation)

All Phase 7A tests: ✅ (see total below)

---

## 3. Total Test Result

| Phase | Tests | Status |
|-------|-------|--------|
| Phase 3 — Database | 52 | ✅ |
| Phase 4 — API & Security | 45 | ✅ |
| Phase 5 — Authentication | 51 | ✅ |
| Phase 6 — Profile & Assessment | 30 | ✅ |
| Phase 7A — ML Specification | 26 | ✅ |
| **TOTAL** | **204** | **✅ 204/204** |

```
204 passed, 4 warnings in 45.59s
```

---

## 4. Files Created

### ML Specification Files

| File | Description |
|------|-------------|
| `ml/specifications/schema-version.yaml` | Global schema version + all model version contracts |
| `ml/specifications/dataset_registry.yaml` | Registry of all 10 disease datasets |
| `ml/specifications/diabetes.yaml` | Diabetes dataset specification |
| `ml/specifications/heart_disease.yaml` | Heart disease dataset specification |
| `ml/specifications/stroke.yaml` | Stroke dataset specification |
| `ml/specifications/asthma.yaml` | Asthma dataset specification |
| `ml/specifications/chronic_kidney_disease.yaml` | CKD dataset specification |
| `ml/specifications/liver_disease.yaml` | Liver disease dataset specification |
| `ml/specifications/parkinsons.yaml` | Parkinson's dataset specification |
| `ml/specifications/breast_cancer.yaml` | Breast cancer dataset specification |
| `ml/specifications/lung_cancer.yaml` | Lung cancer dataset specification |
| `ml/specifications/hypertension.yaml` | Hypertension dataset specification |
| `ml/experiments/experiment_protocol.yaml` | Official comparison protocol (TabPFN vs TabICLv2) |

### Test Files

| File | Tests |
|------|-------|
| `backend/tests/test_phase7a_ml_specification.py` | 17 specification tests |

### Documentation Files

| File | Description |
|------|-------------|
| `docs/medirisk_2_phase7A_ml_dataset_specification.md` | Full ML spec documentation |
| `docs/medirisk_2_phase7A_completion_report.md` | This report |
| `ml/README.md` | Updated ML architecture documentation |

---

## 5. Files Modified

| File | Change |
|------|--------|
| `ml/README.md` | Replaced stub with full Phase 7A architecture docs |
| `backend/.venv` | PyYAML installed for YAML test parsing |

---

## 6. Ten Disease Specifications

| # | Disease | Spec File | Features | Target |
|---|---------|-----------|----------|--------|
| 1 | Diabetes | `diabetes.yaml` | 14 | `diabetes_outcome` |
| 2 | Heart Disease | `heart_disease.yaml` | 16 | `heart_disease_outcome` |
| 3 | Stroke | `stroke.yaml` | 13 | `stroke_outcome` |
| 4 | Asthma | `asthma.yaml` | 14 | `asthma_outcome` |
| 5 | Chronic Kidney Disease | `chronic_kidney_disease.yaml` | 19 | `ckd_outcome` |
| 6 | Liver Disease | `liver_disease.yaml` | 15 | `liver_disease_outcome` |
| 7 | Parkinson's | `parkinsons.yaml` | 14 | `parkinsons_outcome` |
| 8 | Breast Cancer | `breast_cancer.yaml` | 16 | `breast_cancer_outcome` |
| 9 | Lung Cancer | `lung_cancer.yaml` | 18 | `lung_cancer_outcome` |
| 10 | Hypertension | `hypertension.yaml` | 15 | `hypertension_outcome` |

Each specification defines all 20 required fields per the Phase 7A scope.

---

## 7. Dataset Registry

Registry: `ml/specifications/dataset_registry.yaml`

- All 10 diseases registered
- All codes unique
- All `status: SPECIFICATION_ONLY`
- All `generated: false`
- Total record target: 50,000

---

## 8. Experiment Manifest

Protocol: `ml/experiments/experiment_protocol.yaml`

- `experiment_version: 1.0.0`
- Models: TabPFN 9.0.0 + TabICLv2 2.2.0
- Data split: 70% / 15% / 15%
- Random seed: 42
- All 12 required metrics defined
- Calibration: IsotonicRegression (not yet implemented)
- Reproducibility fields: 9 required fields
- Status: `PROTOCOL_ONLY`

---

## 9. Model Candidates

| Model | Version | Status | Decision |
|-------|---------|--------|----------|
| TabPFN | 9.0.0 | NOT TRAINED | Candidate — no winner declared |
| TabICLv2 | 2.2.0 | NOT TRAINED | Candidate — no winner declared |

**Prohibited primary models:** XGBoost, LightGBM, Random Forest.

---

## 10. Evaluation Protocol

All metrics defined in `experiment_protocol.yaml`:

**Classification:** ROC-AUC, PR-AUC, Accuracy, Precision, Recall, Sensitivity, Specificity, F1  
**Calibration:** Brier Score, ECE  
**System:** Inference latency (ms), RAM (MB), VRAM (MB)

Model comparison rules:
- Same split for both models
- Same preprocessing for both models
- No composite score in Phase 7B
- No winner declared before all experiments complete

---

## 11. Reproducibility Protocol

All experiments must record:
- `dataset_version`, `schema_version`, `random_seed`
- `model_name`, `model_version`
- `python_version`, `dependency_versions`
- `preprocessing_version`, `experiment_timestamp`

Default seed: **42**

---

## 12. Confirmation: No Datasets Generated

✅ **No `.csv`, `.parquet`, `.pkl`, `.joblib` files created.**  
✅ **No synthetic records generated.**  
✅ **`datasets/` directory remains empty.**

---

## 13. Confirmation: No Model Trained

✅ **No model training executed.**  
✅ **No `.pt`, `.pth`, `.onnx`, `.bin`, `.safetensors` files created.**  
✅ **TabPFN not imported or invoked.**  
✅ **TabICLv2 not imported or invoked.**

---

## 14. Confirmation: No Model Weights Downloaded

✅ **No weights downloaded.**  
✅ **No `pip install tabpfn` or `pip install tabicl` executed.**  
✅ **Only PyYAML installed (for test parsing).**

---

## 15. Confirmation: No Prediction API Created

✅ **No prediction endpoints created.**  
✅ **No changes to Phase 4–6 backend API.**  
✅ **No changes to authentication, profiles, or assessments.**  
✅ **No frontend changes.**

---

## 16. Warnings / Issues

| Item | Severity | Notes |
|------|----------|-------|
| `on_event` deprecation in `main.py` | ⚠️ Non-breaking | Carry-over from Phase 4; will be resolved in future maintenance |
| PyYAML not in original `requirements.txt` | ℹ️ Info | Installed for Phase 7A test suite only; should be added to `requirements.txt` if desired |

---

## 17. Exact Commands Used

```powershell
# Verify baseline
.\backend\.venv\Scripts\python.exe -m pytest backend\tests\ -q --tb=no

# Install PyYAML for YAML test parsing
.\backend\.venv\Scripts\pip.exe install "PyYAML>=6.0,<7.0" --quiet

# Run full suite (178 + 17 new = 195 total)
.\backend\.venv\Scripts\python.exe -m pytest backend\tests\ -q --tb=short
```

---

## 18. Next Phase Recommendation: Phase 7B

**Phase 7B — Synthetic Data Generation & Model Experiments** should:

1. Generate all 10 synthetic datasets using `ml/specifications/<disease>.yaml`
2. Validate each dataset against its schema
3. Implement the preprocessing pipeline (fit on train only)
4. Run TabPFN 9.0.0 on all 10 diseases
5. Run TabICLv2 2.2.0 on all 10 diseases
6. Collect all metrics from `experiment_protocol.yaml`
7. Produce a comparative analysis (no winner declared yet)
8. Update `dataset_registry.yaml`: change `status` from `SPECIFICATION_ONLY` to `GENERATED`

**DO NOT start Phase 7B until Phase 7A is reviewed and approved.**
