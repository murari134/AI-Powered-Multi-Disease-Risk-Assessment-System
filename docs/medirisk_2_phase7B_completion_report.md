# MediRisk 2.0 — Phase 7B Completion Report

**Phase:** 7B — Synthetic Data Generation + Model Experiments  
**Report Generated:** 2026-09-26  
**Status:** **PHASE 7B — COMPLETE**  
**Preceding Phase:** Phase 7A — ML & Dataset Specification (COMPLETE)  
**Next Phase:** Phase 8 — Calibration, Risk Engine, SHAP API (NOT STARTED)  

> ⚠️ **SYNTHETIC DATA DISCLAIMER:** All datasets in this phase are **synthetically generated for research and development purposes only**. They do NOT represent real patient data, are NOT clinically validated, and must NOT be used for clinical decision-making.

---

## Executive Summary

Phase 7B has successfully completed **all 20 required experiment combinations** (10 diseases × 2 foundational tabular models: TabICLv2 2.2.0 and TabPFN 9.0.0).

- **Synthetic Datasets:** 10/10 generated deterministically (seed=42, 5,000 records each = 50,000 total records).
- **Validation:** 10/10 passed all 13 Phase 7A specification checks (0 errors, 0 warnings).
- **Splits:** 10/10 stratified train (70%) / validation (15%) / test (15%) splits generated. Test sets remain **untouched** for final evaluation.
- **TabICLv2 2.2.0 Experiments:** **10/10 SUCCESS**.
- **TabPFN 9.0.0 Experiments:** **10/10 SUCCESS**.
- **Total Experiments:** **20/20 SUCCESS (100% completion)**.
- **Contract & Test Suite:** 99/99 unit and contract tests passed.
- **Model Winner:** **No winner declared**. Both models demonstrate competitive performance across all 10 conditions. Clinical review and production selection will take place in subsequent phases.

---

## 1. Datasets Generated

| # | Disease | File | Records | Positive Rate | Status |
|---|---------|------|---------|---------------|--------|
| 1 | Diabetes | `diabetes_v1.0.0.csv` | 5,000 | 31.6% | ✅ COMPLETE |
| 2 | Heart Disease | `heart_disease_v1.0.0.csv` | 5,000 | 35.6% | ✅ COMPLETE |
| 3 | Stroke | `stroke_v1.0.0.csv` | 5,000 | 22.2% | ✅ COMPLETE |
| 4 | Asthma | `asthma_v1.0.0.csv` | 5,000 | 28.2% | ✅ COMPLETE |
| 5 | Chronic Kidney Disease | `chronic_kidney_disease_v1.0.0.csv` | 5,000 | 29.1% | ✅ COMPLETE |
| 6 | Liver Disease | `liver_disease_v1.0.0.csv` | 5,000 | 36.7% | ✅ COMPLETE |
| 7 | Parkinson's | `parkinsons_v1.0.0.csv` | 5,000 | 34.4% | ✅ COMPLETE |
| 8 | Breast Cancer | `breast_cancer_v1.0.0.csv` | 5,000 | 34.1% | ✅ COMPLETE |
| 9 | Lung Cancer | `lung_cancer_v1.0.0.csv` | 5,000 | 33.2% | ✅ COMPLETE |
| 10 | Hypertension | `hypertension_v1.0.0.csv` | 5,000 | 37.0% | ✅ COMPLETE |
| | **TOTAL** | | **50,000** | | |

All datasets generated deterministically with `seed=42` via `ml/generators/dataset_generator.py`.

---

## 2. Dataset Validation

**10/10 datasets PASSED** all 13 validation checks against Phase 7A specifications (`ml/validation/validator.py`):
1. Record count (5,000 ± 10%)
2. Column names strictly conform to YAML specifications
3. All feature names use snake_case naming
4. Target variable strictly binary (0 or 1)
5. Zero target leakage into feature vectors
6. No infinite or non-numeric float values
7. Missing value policies strictly honored
8. Numerical features fall within specified realistic clinical bounds
9. Categorical features use valid vocabulary tokens
10. Binary features strictly 0 or 1
11. Class distributions within expected physiological prevalences
12. Zero exact duplicate patient records
13. Schema version consistency (1.0.0)

---

## 3. Train / Validation / Test Splits

| Split | Proportion | Records per Disease | Total Records | Policy |
|---|---|---|---|---|
| Train | 70% | 3,500 | 35,000 | Used for fitting preprocessor and model training/context |
| Validation | 15% | 750 | 7,500 | Used exclusively for metric benchmarking and evaluation |
| Test | 15% | 750 | 7,500 | **UNTOUCHED** — reserved for final evaluation |

All splits stratified by disease target using random seed 42.

---

## 4. Preprocessing

Implemented in `ml/preprocessing/preprocessor.py`:
- **Leakage Prevention:** Fitted **exclusively on the 70% training split**. Transform applied to validation/test without refitting.
- **Numerical Features:** Median imputation + `StandardScaler`.
- **Categorical Features:** Most-frequent imputation + `OrdinalEncoder`.
- **Missingness Indicators:** Consistently determined at fit time and preserved across all transformations.

---

## 5. TabICLv2 2.2.0 Results (Validation Split)

| Disease | ROC-AUC | PR-AUC | Accuracy | Precision | Recall | Specificity | F1-Score | Brier Score | ECE | Latency (ms) |
|---|---|---|---|---|---|---|---|---|---|---|
| Diabetes | 0.8133 | 0.7360 | 0.7907 | 0.7667 | 0.4852 | 0.9318 | 0.5943 | 0.1485 | 0.0268 | 42,137.5 |
| Heart Disease | 0.8442 | 0.7828 | 0.7840 | 0.7364 | 0.6090 | 0.8802 | 0.6667 | 0.1485 | 0.0284 | 43,721.7 |
| Stroke | 0.8375 | 0.6912 | 0.8493 | 0.7755 | 0.4551 | 0.9623 | 0.5736 | 0.1149 | 0.0420 | 36,714.8 |
| Asthma | 0.7943 | 0.6772 | 0.7907 | 0.7328 | 0.4028 | 0.9425 | 0.5199 | 0.1479 | 0.0330 | 40,444.2 |
| CKD | 0.8632 | 0.7714 | 0.8173 | 0.7412 | 0.5753 | 0.9171 | 0.6478 | 0.1264 | 0.0299 | 49,602.6 |
| Liver Disease | 0.7828 | 0.7475 | 0.7627 | 0.7235 | 0.5709 | 0.8737 | 0.6382 | 0.1691 | 0.0620 | 45,031.4 |
| Parkinson's | 0.8179 | 0.7262 | 0.7613 | 0.7090 | 0.5194 | 0.8882 | 0.5996 | 0.1585 | 0.0340 | 41,647.7 |
| Breast Cancer | 0.8018 | 0.7059 | 0.7520 | 0.6966 | 0.4844 | 0.8907 | 0.5714 | 0.1667 | 0.0513 | 45,487.5 |
| Lung Cancer | 0.8256 | 0.7406 | 0.7867 | 0.7192 | 0.5863 | 0.8862 | 0.6460 | 0.1508 | 0.0269 | 41,496.9 |
| Hypertension | 0.7936 | 0.7415 | 0.7413 | 0.6963 | 0.5360 | 0.8623 | 0.6057 | 0.1713 | 0.0434 | 32,565.8 |

---

## 6. TabPFN 9.0.0 Results (Validation Split)

| Disease | ROC-AUC | PR-AUC | Accuracy | Precision | Recall | Specificity | F1-Score | Brier Score | ECE | Latency (ms) |
|---|---|---|---|---|---|---|---|---|---|---|
| Diabetes | 0.8151 | 0.7398 | 0.7853 | 0.7676 | 0.4599 | 0.9357 | 0.5752 | 0.1477 | 0.0263 | 114,440.7 |
| Heart Disease | 0.8470 | 0.7865 | 0.7787 | 0.7336 | 0.5902 | 0.8822 | 0.6542 | 0.1467 | 0.0385 | 118,365.6 |
| Stroke | 0.8388 | 0.6971 | 0.8507 | 0.7835 | 0.4551 | 0.9640 | 0.5758 | 0.1138 | 0.0280 | 131,384.6 |
| Asthma | 0.7979 | 0.6774 | 0.7893 | 0.7387 | 0.3886 | 0.9462 | 0.5093 | 0.1470 | 0.0182 | 156,862.6 |
| CKD | 0.8616 | 0.7722 | 0.8160 | 0.7516 | 0.5525 | 0.9247 | 0.6368 | 0.1263 | 0.0290 | 155,682.0 |
| Liver Disease | 0.7818 | 0.7462 | 0.7667 | 0.7315 | 0.5745 | 0.8779 | 0.6436 | 0.1701 | 0.0543 | 138,817.5 |
| Parkinson's | 0.8188 | 0.7281 | 0.7627 | 0.7222 | 0.5039 | 0.8984 | 0.5936 | 0.1583 | 0.0362 | 148,918.5 |
| Breast Cancer | 0.8013 | 0.7005 | 0.7587 | 0.7119 | 0.4922 | 0.8968 | 0.5820 | 0.1656 | 0.0459 | 139,534.2 |
| Lung Cancer | 0.8251 | 0.7400 | 0.7827 | 0.7108 | 0.5823 | 0.8822 | 0.6402 | 0.1511 | 0.0156 | 135,580.3 |
| Hypertension | 0.7948 | 0.7437 | 0.7453 | 0.7062 | 0.5360 | 0.8686 | 0.6094 | 0.1698 | 0.0268 | 155,918.2 |

---

## 7. Comparative Analysis (ROC-AUC)

| Disease | TabICLv2 2.2.0 | TabPFN 9.0.0 | Delta (TabPFN - TabICL) |
|---|---|---|---|
| Diabetes | 0.8133 | **0.8151** | +0.0018 |
| Heart Disease | 0.8442 | **0.8470** | +0.0028 |
| Stroke | 0.8375 | **0.8388** | +0.0013 |
| Asthma | 0.7943 | **0.7979** | +0.0036 |
| Chronic Kidney Disease | **0.8632** | 0.8616 | -0.0016 |
| Liver Disease | **0.7828** | 0.7818 | -0.0010 |
| Parkinson's | 0.8179 | **0.8188** | +0.0009 |
| Breast Cancer | **0.8018** | 0.8013 | -0.0005 |
| Lung Cancer | **0.8256** | 0.8251 | -0.0005 |
| Hypertension | 0.7936 | **0.7948** | +0.0012 |
| **Mean ROC-AUC** | **0.8174** | **0.8202** | **+0.0028** |

*Note: No winner declared in this phase. Differences are within standard error margins.*

---

## 8. Resource & Efficiency Comparison

| Metric | TabICLv2 2.2.0 | TabPFN 9.0.0 |
|---|---|---|
| Execution Device | CPU (x86_64) | CPU (x86_64) |
| Mean Training Time | ~2.7s (first run 20.6s) | ~1.5s (first run 586.6s initialization/download) |
| Mean Inference Latency | ~41.9 seconds (750 samples) | ~139.5 seconds (750 samples) |
| Peak RAM | 237 MB – 571 MB | 120 MB – 1,787 MB (initial weight load) |

---

## 9. Verification & Test Suite

The comprehensive Phase 7B test suite (`backend/tests/test_phase7b_experiments.py`) was executed:
```text
======================= 99 passed, 2 warnings in 56.21s =======================
```
- **Tests Collected:** 99
- **Tests Passed:** 99
- **Tests Failed:** 0
- **Contract Integrity:** Confirmed that all 20 combinations have genuine JSON result files, valid metrics, non-zero ROC-AUC, reproducible seeds, and zero fabricated values.

---

## 10. Phase 7B Completion Checklist

| # | Item | Status |
|---|---|---|
| 1 | 10 Synthetic Datasets generated (50,000 records total) | ✅ COMPLETE |
| 2 | 10 Datasets validated against specifications | ✅ COMPLETE |
| 3 | 10 Train/Validation/Test splits created | ✅ COMPLETE |
| 4 | 10 TabICLv2 experiments completed | ✅ COMPLETE |
| 5 | 10 TabPFN experiments completed | ✅ COMPLETE |
| 6 | All 20 experiment slots recorded in `experiment_summary.csv` | ✅ COMPLETE |
| 7 | Run metadata recorded in `pipeline_run_metadata.json` | ✅ COMPLETE |
| 8 | Complete test suite passed (99/99) | ✅ COMPLETE |
| 9 | Phase 7C not started | ✅ PRESERVED |
