"""
MediRisk 2.0 — Synthetic Dataset Generator
Phase 7B

Generates approximately 5,000 synthetic records per disease using the
Phase 7A specifications as the authoritative schema.

DISCLAIMER:
All generated data is SYNTHETIC RESEARCH data only.
It does NOT represent real patients, is NOT clinically validated,
and must NOT be used for clinical decision-making.

Generator version: 1.0.0
Schema version: 1.0.0
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

GENERATOR_VERSION = "1.0.0"
SCHEMA_VERSION = "1.0.0"
DEFAULT_SEED = 42
RECORDS_PER_DISEASE = 5000
ML_ROOT = Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(seed)


def _bernoulli(rng: np.random.Generator, p: float, n: int) -> np.ndarray:
    return rng.binomial(1, p, n).astype(np.int8)


def _normal_clipped(rng: np.random.Generator, mu: float, sigma: float,
                    lo: float, hi: float, n: int) -> np.ndarray:
    vals = rng.normal(mu, sigma, n)
    return np.clip(vals, lo, hi)


def _choice(rng: np.random.Generator, options: list, probs: list | None,
            n: int) -> np.ndarray:
    return rng.choice(options, size=n, p=probs)


def _inject_missing(rng: np.random.Generator, series: pd.Series,
                    rate: float) -> pd.Series:
    """Replace `rate` fraction of values with NaN."""
    if rate <= 0:
        return series
    mask = rng.random(len(series)) < rate
    series = series.astype(object)
    series[mask] = np.nan
    return series


# ---------------------------------------------------------------------------
# Individual disease generators
# ---------------------------------------------------------------------------

def _gen_diabetes(rng: np.random.Generator, n: int) -> pd.DataFrame:
    pos_prop = 0.35
    # Base covariates
    age = _normal_clipped(rng, 50, 15, 18, 90, n)
    bmi = _normal_clipped(rng, 28, 6, 15, 60, n)
    sex = _choice(rng, ["male", "female"], [0.49, 0.51], n)
    family_history = _bernoulli(rng, 0.30, n)
    smoking_status = _choice(rng, ["never", "former", "current"],
                             [0.50, 0.30, 0.20], n)
    physical_activity = _choice(rng, ["sedentary", "light", "moderate", "active"],
                                [0.30, 0.30, 0.25, 0.15], n)
    hypertension_flag = _bernoulli(rng, 0.28, n)
    num_pregnancies = np.where(sex == "female",
                               np.clip(rng.poisson(2, n), 0, 20), 0)

    # Glucose: higher for positive cases (correlated with target seed)
    glucose_base = _normal_clipped(rng, 100, 30, 50, 300, n)
    insulin_level = _normal_clipped(rng, 80, 60, 0, 900, n)
    blood_pressure_systolic = _normal_clipped(rng, 120, 18, 70, 200, n)
    blood_pressure_diastolic = _normal_clipped(rng, 79, 12, 40, 130, n)
    skin_thickness = _normal_clipped(rng, 20, 10, 0, 100, n)
    diabetes_pedigree = _normal_clipped(rng, 0.47, 0.33, 0.0, 2.5, n)

    # Target: logistic relationship
    log_odds = (-6.0
                + 0.04 * (age - 50)
                + 0.08 * (bmi - 25)
                + 0.012 * (glucose_base - 100)
                + 0.5 * family_history
                + 0.4 * hypertension_flag
                - 0.3 * (physical_activity == "active").astype(float)
                + 0.3 * (smoking_status == "current").astype(float))
    prob = 1 / (1 + np.exp(-log_odds))
    prob = prob / prob.mean() * pos_prop
    prob = np.clip(prob, 0.01, 0.99)
    target = rng.binomial(1, prob).astype(np.int8)

    df = pd.DataFrame({
        "age": age.round(1),
        "bmi": bmi.round(2),
        "glucose_level": glucose_base.round(1),
        "blood_pressure_systolic": blood_pressure_systolic.round(0).astype(int),
        "blood_pressure_diastolic": blood_pressure_diastolic.round(0).astype(int),
        "insulin_level": insulin_level.round(1),
        "skin_thickness": skin_thickness.round(1),
        "diabetes_pedigree": diabetes_pedigree.round(3),
        "num_pregnancies": num_pregnancies.astype(int),
        "sex": sex,
        "smoking_status": smoking_status,
        "physical_activity": physical_activity,
        "family_history_diabetes": family_history,
        "hypertension_flag": hypertension_flag,
        "diabetes_outcome": target,
    })
    # Inject missingness per spec
    df["bmi"] = _inject_missing(rng, df["bmi"], 0.05)
    df["glucose_level"] = _inject_missing(rng, df["glucose_level"], 0.05)
    df["blood_pressure_systolic"] = _inject_missing(rng, df["blood_pressure_systolic"], 0.07)
    df["blood_pressure_diastolic"] = _inject_missing(rng, df["blood_pressure_diastolic"], 0.07)
    df["insulin_level"] = _inject_missing(rng, df["insulin_level"], 0.12)
    df["skin_thickness"] = _inject_missing(rng, df["skin_thickness"], 0.12)
    df["diabetes_pedigree"] = _inject_missing(rng, df["diabetes_pedigree"], 0.05)
    df["smoking_status"] = _inject_missing(rng, df["smoking_status"], 0.05)
    df["physical_activity"] = _inject_missing(rng, df["physical_activity"], 0.05)
    return df


def _gen_heart_disease(rng: np.random.Generator, n: int) -> pd.DataFrame:
    pos_prop = 0.40
    age = _normal_clipped(rng, 54, 12, 18, 90, n)
    sex = _choice(rng, ["male", "female"], [0.60, 0.40], n)
    bmi = _normal_clipped(rng, 27, 5, 15, 60, n)
    resting_bp = _normal_clipped(rng, 130, 18, 70, 200, n)
    cholesterol = _normal_clipped(rng, 245, 50, 100, 600, n)
    fbs_high = _bernoulli(rng, 0.15, n)
    max_hr = _normal_clipped(rng, 150, 22, 60, 220, n)
    ex_angina = _bernoulli(rng, 0.33, n)
    st_dep = _normal_clipped(rng, 1.0, 1.1, 0.0, 7.0, n)
    num_vessels = np.clip(rng.poisson(0.7, n), 0, 3).astype(int)
    diabetes_flag = _bernoulli(rng, 0.15, n)
    smoking_status = _choice(rng, ["never", "former", "current"],
                             [0.45, 0.35, 0.20], n)
    chest_pain = _choice(rng, ["typical_angina", "atypical_angina",
                                "non_anginal", "asymptomatic"],
                         [0.15, 0.25, 0.35, 0.25], n)
    resting_ecg = _choice(rng, ["normal", "st_t_abnormality",
                                 "left_ventricular_hypertrophy"],
                          [0.50, 0.35, 0.15], n)
    slope = _choice(rng, ["upsloping", "flat", "downsloping"],
                    [0.30, 0.45, 0.25], n)
    thal = _choice(rng, ["normal", "fixed_defect", "reversible_defect"],
                   [0.55, 0.15, 0.30], n)

    log_odds = (-4.5
                + 0.05 * (age - 54)
                + 0.03 * (resting_bp - 130)
                + 0.005 * (cholesterol - 245)
                + 0.6 * (sex == "male").astype(float)
                + 0.7 * ex_angina
                + 0.3 * st_dep
                + 0.5 * (thal == "reversible_defect").astype(float)
                + 0.4 * (chest_pain == "typical_angina").astype(float)
                - 0.3 * (max_hr - 150) / 22)
    prob = 1 / (1 + np.exp(-log_odds))
    prob = prob / prob.mean() * pos_prop
    prob = np.clip(prob, 0.01, 0.99)
    target = rng.binomial(1, prob).astype(np.int8)

    df = pd.DataFrame({
        "age": age.round(1),
        "sex": sex,
        "chest_pain_type": chest_pain,
        "resting_blood_pressure": resting_bp.round(0).astype(int),
        "cholesterol_total": cholesterol.round(0).astype(int),
        "fasting_blood_sugar_high": fbs_high,
        "resting_ecg": resting_ecg,
        "max_heart_rate": max_hr.round(0).astype(int),
        "exercise_induced_angina": ex_angina,
        "st_depression": st_dep.round(2),
        "slope_peak_st": slope,
        "num_major_vessels": num_vessels,
        "thalassemia_type": thal,
        "smoking_status": smoking_status,
        "diabetes_flag": diabetes_flag,
        "bmi": bmi.round(2),
        "heart_disease_outcome": target,
    })
    df["chest_pain_type"] = _inject_missing(rng, df["chest_pain_type"], 0.05)
    df["resting_blood_pressure"] = _inject_missing(rng, df["resting_blood_pressure"], 0.05)
    df["cholesterol_total"] = _inject_missing(rng, df["cholesterol_total"], 0.07)
    df["resting_ecg"] = _inject_missing(rng, df["resting_ecg"], 0.08)
    df["max_heart_rate"] = _inject_missing(rng, df["max_heart_rate"], 0.05)
    df["exercise_induced_angina"] = _inject_missing(rng, df["exercise_induced_angina"], 0.05)
    df["st_depression"] = _inject_missing(rng, df["st_depression"], 0.07)
    df["slope_peak_st"] = _inject_missing(rng, df["slope_peak_st"], 0.08)
    df["num_major_vessels"] = _inject_missing(rng, df["num_major_vessels"], 0.12)
    df["thalassemia_type"] = _inject_missing(rng, df["thalassemia_type"], 0.12)
    df["bmi"] = _inject_missing(rng, df["bmi"], 0.05)
    return df


def _gen_stroke(rng: np.random.Generator, n: int) -> pd.DataFrame:
    pos_prop = 0.25
    age = _normal_clipped(rng, 55, 18, 18, 95, n)
    sex = _choice(rng, ["male", "female"], [0.49, 0.51], n)
    hypertension_flag = _bernoulli(rng, 0.27, n)
    heart_disease_flag = _bernoulli(rng, 0.12, n)
    ever_married = _bernoulli(rng, 0.65, n)
    work_type = _choice(rng, ["private", "self_employed", "government",
                               "children", "never_worked"],
                        [0.57, 0.16, 0.13, 0.10, 0.04], n)
    residence = _choice(rng, ["urban", "rural"], [0.55, 0.45], n)
    glucose = _normal_clipped(rng, 105, 45, 50, 280, n)
    bmi = _normal_clipped(rng, 28, 6, 15, 60, n)
    smoking = _choice(rng, ["never", "formerly_smoked", "smokes", "unknown"],
                      [0.37, 0.22, 0.18, 0.23], n)
    afib = _bernoulli(rng, 0.08, n)
    cholesterol = _normal_clipped(rng, 200, 40, 100, 600, n)
    physical_activity = _choice(rng, ["sedentary", "light", "moderate", "active"],
                                [0.28, 0.32, 0.25, 0.15], n)

    log_odds = (-5.0
                + 0.06 * (age - 55)
                + 0.8 * hypertension_flag
                + 0.7 * heart_disease_flag
                + 0.9 * afib
                + 0.4 * (smoking == "smokes").astype(float)
                + 0.005 * (glucose - 105)
                + 0.02 * (bmi - 28))
    prob = 1 / (1 + np.exp(-log_odds))
    prob = prob / prob.mean() * pos_prop
    prob = np.clip(prob, 0.01, 0.99)
    target = rng.binomial(1, prob).astype(np.int8)

    df = pd.DataFrame({
        "age": age.round(1),
        "sex": sex,
        "hypertension_flag": hypertension_flag,
        "heart_disease_flag": heart_disease_flag,
        "ever_married": ever_married,
        "work_type": work_type,
        "residence_type": residence,
        "avg_glucose_level": glucose.round(1),
        "bmi": bmi.round(2),
        "smoking_status": smoking,
        "atrial_fibrillation_flag": afib,
        "cholesterol_total": cholesterol.round(0).astype(int),
        "physical_activity": physical_activity,
        "stroke_outcome": target,
    })
    df["work_type"] = _inject_missing(rng, df["work_type"], 0.05)
    df["avg_glucose_level"] = _inject_missing(rng, df["avg_glucose_level"], 0.05)
    df["bmi"] = _inject_missing(rng, df["bmi"], 0.08)
    df["smoking_status"] = _inject_missing(rng, df["smoking_status"], 0.08)
    df["cholesterol_total"] = _inject_missing(rng, df["cholesterol_total"], 0.08)
    df["physical_activity"] = _inject_missing(rng, df["physical_activity"], 0.05)
    return df


def _gen_asthma(rng: np.random.Generator, n: int) -> pd.DataFrame:
    pos_prop = 0.30
    age = _normal_clipped(rng, 35, 18, 5, 90, n)
    sex = _choice(rng, ["male", "female"], [0.49, 0.51], n)
    family_history = _bernoulli(rng, 0.28, n)
    allergic_rhinitis = _bernoulli(rng, 0.35, n)
    eczema = _bernoulli(rng, 0.18, n)
    smoking = _choice(rng, ["never", "former", "current", "passive"],
                      [0.45, 0.22, 0.15, 0.18], n)
    occ_exposure = _choice(rng, ["none", "low", "moderate", "high"],
                           [0.50, 0.25, 0.15, 0.10], n)
    aqi = _normal_clipped(rng, 80, 50, 0, 500, n)
    bmi = _normal_clipped(rng, 27, 5, 12, 60, n)
    exercise = _choice(rng, ["never", "rarely", "sometimes", "regularly"],
                       [0.20, 0.25, 0.30, 0.25], n)
    pet_exposure = _bernoulli(rng, 0.38, n)
    mold_exposure = _bernoulli(rng, 0.15, n)
    fev_ratio = _normal_clipped(rng, 0.78, 0.12, 0.3, 1.0, n)
    num_resp_inf = np.clip(rng.poisson(1.5, n), 0, 10).astype(int)

    log_odds = (-4.0
                + 1.0 * family_history
                + 0.8 * allergic_rhinitis
                + 0.5 * eczema
                + 0.4 * (smoking == "current").astype(float)
                + 0.3 * (occ_exposure == "high").astype(float)
                + 0.005 * (aqi - 80)
                - 0.7 * (fev_ratio - 0.78) / 0.12
                + 0.2 * num_resp_inf)
    prob = 1 / (1 + np.exp(-log_odds))
    prob = prob / prob.mean() * pos_prop
    prob = np.clip(prob, 0.01, 0.99)
    target = rng.binomial(1, prob).astype(np.int8)

    df = pd.DataFrame({
        "age": age.round(1),
        "sex": sex,
        "family_history_asthma": family_history,
        "allergic_rhinitis_flag": allergic_rhinitis,
        "eczema_flag": eczema,
        "smoking_status": smoking,
        "occupational_exposure": occ_exposure,
        "air_quality_index": aqi.round(1),
        "bmi": bmi.round(2),
        "exercise_frequency": exercise,
        "pet_exposure": pet_exposure,
        "mold_exposure": mold_exposure,
        "fev1_fvc_ratio": fev_ratio.round(3),
        "num_respiratory_infections_past_year": num_resp_inf,
        "asthma_outcome": target,
    })
    df["occupational_exposure"] = _inject_missing(rng, df["occupational_exposure"], 0.08)
    df["air_quality_index"] = _inject_missing(rng, df["air_quality_index"], 0.12)
    df["bmi"] = _inject_missing(rng, df["bmi"], 0.05)
    df["exercise_frequency"] = _inject_missing(rng, df["exercise_frequency"], 0.05)
    df["fev1_fvc_ratio"] = _inject_missing(rng, df["fev1_fvc_ratio"], 0.12)
    df["num_respiratory_infections_past_year"] = _inject_missing(
        rng, df["num_respiratory_infections_past_year"], 0.08)
    return df


def _gen_ckd(rng: np.random.Generator, n: int) -> pd.DataFrame:
    pos_prop = 0.35
    age = _normal_clipped(rng, 52, 16, 18, 90, n)
    sex = _choice(rng, ["male", "female"], [0.55, 0.45], n)
    bp_sys = _normal_clipped(rng, 130, 22, 70, 220, n)
    glucose = _normal_clipped(rng, 120, 60, 50, 500, n)
    blood_urea = _normal_clipped(rng, 40, 30, 5, 300, n)
    creatinine = _normal_clipped(rng, 1.2, 0.8, 0.4, 15.0, n)
    sodium = _normal_clipped(rng, 137, 5, 115, 165, n)
    potassium = _normal_clipped(rng, 4.2, 0.7, 2.5, 8.0, n)
    hemoglobin = _normal_clipped(rng, 13.5, 2.5, 5.0, 20.0, n)
    pcv = _normal_clipped(rng, 40, 7, 15, 65, n)
    wbc = _normal_clipped(rng, 8000, 2500, 2000, 20000, n)
    rbc = _normal_clipped(rng, 4.5, 0.7, 2.0, 7.0, n)
    hypertension_flag = _bernoulli(rng, 0.38, n)
    diabetes_flag = _bernoulli(rng, 0.22, n)
    anemia_flag = _bernoulli(rng, 0.20, n)
    urine_albumin = _choice(rng, ["normal", "abnormal"], [0.70, 0.30], n)
    urine_sugar = _choice(rng, ["normal", "abnormal"], [0.88, 0.12], n)
    pus_cell = _choice(rng, ["normal", "abnormal"], [0.75, 0.25], n)
    bacteria = _bernoulli(rng, 0.10, n)

    log_odds = (-4.5
                + 0.04 * (age - 52)
                + 0.6 * hypertension_flag
                + 0.7 * diabetes_flag
                + 0.8 * (urine_albumin == "abnormal").astype(float)
                + 1.0 * (creatinine - 1.2)
                + 0.02 * (blood_urea - 40))
    prob = 1 / (1 + np.exp(-log_odds))
    prob = prob / prob.mean() * pos_prop
    prob = np.clip(prob, 0.01, 0.99)
    target = rng.binomial(1, prob).astype(np.int8)

    df = pd.DataFrame({
        "age": age.round(1),
        "sex": sex,
        "blood_pressure_systolic": bp_sys.round(0).astype(int),
        "blood_glucose_random": glucose.round(1),
        "blood_urea": blood_urea.round(1),
        "serum_creatinine": creatinine.round(2),
        "sodium": sodium.round(1),
        "potassium": potassium.round(2),
        "hemoglobin": hemoglobin.round(1),
        "packed_cell_volume": pcv.round(1),
        "white_blood_cell_count": wbc.round(0).astype(int),
        "red_blood_cell_count": rbc.round(2),
        "hypertension_flag": hypertension_flag,
        "diabetes_flag": diabetes_flag,
        "anemia_flag": anemia_flag,
        "urine_albumin": urine_albumin,
        "urine_sugar": urine_sugar,
        "pus_cell": pus_cell,
        "bacteria_in_urine": bacteria,
        "ckd_outcome": target,
    })
    for col, rate in [("blood_pressure_systolic", 0.05), ("blood_glucose_random", 0.08),
                      ("blood_urea", 0.08), ("serum_creatinine", 0.05),
                      ("sodium", 0.08), ("potassium", 0.08),
                      ("hemoglobin", 0.08), ("packed_cell_volume", 0.08),
                      ("white_blood_cell_count", 0.08), ("red_blood_cell_count", 0.08),
                      ("urine_albumin", 0.12), ("urine_sugar", 0.12),
                      ("pus_cell", 0.12), ("bacteria_in_urine", 0.12)]:
        df[col] = _inject_missing(rng, df[col], rate)
    return df


def _gen_liver_disease(rng: np.random.Generator, n: int) -> pd.DataFrame:
    pos_prop = 0.38
    age = _normal_clipped(rng, 44, 16, 18, 90, n)
    sex = _choice(rng, ["male", "female"], [0.60, 0.40], n)
    bilirubin_total = _normal_clipped(rng, 3.0, 4.0, 0.1, 30.0, n)
    bilirubin_direct = _normal_clipped(rng, 1.5, 2.5, 0.0, 20.0, n)
    alk_phos = _normal_clipped(rng, 290, 300, 20, 2000, n)
    alt = _normal_clipped(rng, 80, 120, 5, 2000, n)
    ast = _normal_clipped(rng, 75, 110, 5, 2000, n)
    total_proteins = _normal_clipped(rng, 6.5, 1.5, 3.0, 12.0, n)
    albumin = _normal_clipped(rng, 3.5, 0.8, 1.0, 6.0, n)
    ag_ratio = _normal_clipped(rng, 1.0, 0.4, 0.3, 3.0, n)
    bmi = _normal_clipped(rng, 27, 5, 15, 60, n)
    alcohol = _choice(rng, ["none", "light", "moderate", "heavy"],
                      [0.35, 0.30, 0.25, 0.10], n)
    smoking = _choice(rng, ["never", "former", "current"],
                      [0.48, 0.30, 0.22], n)
    diabetes_flag = _bernoulli(rng, 0.18, n)
    hypertension_flag = _bernoulli(rng, 0.22, n)

    log_odds = (-4.0
                + 0.03 * (age - 44)
                + 0.5 * (sex == "male").astype(float)
                + 0.4 * (alcohol == "heavy").astype(float)
                + 0.3 * (alcohol == "moderate").astype(float)
                + 0.5 * np.log1p(alt / 40)
                + 0.3 * np.log1p(ast / 40)
                + 0.8 * np.log1p(bilirubin_total))
    prob = 1 / (1 + np.exp(-log_odds))
    prob = prob / prob.mean() * pos_prop
    prob = np.clip(prob, 0.01, 0.99)
    target = rng.binomial(1, prob).astype(np.int8)

    df = pd.DataFrame({
        "age": age.round(1),
        "sex": sex,
        "total_bilirubin": bilirubin_total.round(2),
        "direct_bilirubin": bilirubin_direct.round(2),
        "alkaline_phosphatase": alk_phos.round(0).astype(int),
        "alt": alt.round(1),
        "ast": ast.round(1),
        "total_proteins": total_proteins.round(2),
        "albumin": albumin.round(2),
        "albumin_globulin_ratio": ag_ratio.round(3),
        "bmi": bmi.round(2),
        "alcohol_consumption": alcohol,
        "smoking_status": smoking,
        "diabetes_flag": diabetes_flag,
        "hypertension_flag": hypertension_flag,
        "liver_disease_outcome": target,
    })
    for col, rate in [("total_bilirubin", 0.05), ("direct_bilirubin", 0.05),
                      ("alkaline_phosphatase", 0.08), ("alt", 0.08), ("ast", 0.08),
                      ("total_proteins", 0.08), ("albumin", 0.08),
                      ("albumin_globulin_ratio", 0.08), ("bmi", 0.05),
                      ("alcohol_consumption", 0.08), ("smoking_status", 0.05)]:
        df[col] = _inject_missing(rng, df[col], rate)
    return df


def _gen_parkinsons(rng: np.random.Generator, n: int) -> pd.DataFrame:
    pos_prop = 0.35
    age = _normal_clipped(rng, 62, 10, 40, 90, n)
    sex = _choice(rng, ["male", "female"], [0.60, 0.40], n)
    jitter = _normal_clipped(rng, 0.6, 0.8, 0.0, 5.0, n)
    shimmer = _normal_clipped(rng, 3.0, 3.5, 0.0, 20.0, n)
    nhr = _normal_clipped(rng, 0.025, 0.03, 0.0, 0.5, n)
    hnr = _normal_clipped(rng, 22, 5, 5.0, 40.0, n)
    rpde = _normal_clipped(rng, 0.50, 0.10, 0.0, 1.0, n)
    dfa = _normal_clipped(rng, 0.72, 0.08, 0.0, 1.0, n)
    tremor = np.clip(rng.poisson(2, n), 0, 10).astype(int)
    rigidity = np.clip(rng.poisson(1.5, n), 0, 10).astype(int)
    bradykinesia = np.clip(rng.poisson(1.5, n), 0, 10).astype(int)
    family_history = _bernoulli(rng, 0.12, n)
    pesticide = _bernoulli(rng, 0.15, n)
    head_injury = _bernoulli(rng, 0.08, n)

    log_odds = (-4.5
                + 0.06 * (age - 62)
                + 0.5 * (sex == "male").astype(float)
                + 0.3 * jitter
                + 0.05 * shimmer
                + 0.4 * tremor
                + 0.3 * rigidity
                + 0.3 * bradykinesia
                + 0.6 * family_history
                + 0.4 * pesticide)
    prob = 1 / (1 + np.exp(-log_odds))
    prob = prob / prob.mean() * pos_prop
    prob = np.clip(prob, 0.01, 0.99)
    target = rng.binomial(1, prob).astype(np.int8)

    df = pd.DataFrame({
        "age": age.round(1),
        "sex": sex,
        "vocal_jitter_pct": jitter.round(4),
        "vocal_shimmer_pct": shimmer.round(4),
        "nhr": nhr.round(5),
        "hnr": hnr.round(3),
        "rpde": rpde.round(4),
        "dfa": dfa.round(4),
        "tremor_score": tremor,
        "rigidity_score": rigidity,
        "bradykinesia_score": bradykinesia,
        "family_history_parkinsons": family_history,
        "pesticide_exposure": pesticide,
        "head_injury_history": head_injury,
        "parkinsons_outcome": target,
    })
    for col, rate in [("vocal_jitter_pct", 0.12), ("vocal_shimmer_pct", 0.12),
                      ("nhr", 0.12), ("hnr", 0.12), ("rpde", 0.12), ("dfa", 0.12),
                      ("tremor_score", 0.08), ("rigidity_score", 0.08),
                      ("bradykinesia_score", 0.08)]:
        df[col] = _inject_missing(rng, df[col], rate)
    return df


def _gen_breast_cancer(rng: np.random.Generator, n: int) -> pd.DataFrame:
    pos_prop = 0.37
    age = _normal_clipped(rng, 55, 15, 20, 90, n)
    radius = _normal_clipped(rng, 14.1, 3.5, 5.0, 30.0, n)
    texture = _normal_clipped(rng, 19.3, 4.3, 5.0, 45.0, n)
    perimeter = _normal_clipped(rng, 92, 24, 40, 200, n)
    area = _normal_clipped(rng, 655, 350, 140, 2500, n)
    smoothness = _normal_clipped(rng, 0.096, 0.014, 0.05, 0.20, n)
    compactness = _normal_clipped(rng, 0.104, 0.053, 0.0, 0.4, n)
    concavity = _normal_clipped(rng, 0.089, 0.080, 0.0, 0.5, n)
    symmetry = _normal_clipped(rng, 0.181, 0.028, 0.1, 0.4, n)
    fractal = _normal_clipped(rng, 0.063, 0.007, 0.05, 0.12, n)
    family_history = _bernoulli(rng, 0.15, n)
    brca = _bernoulli(rng, 0.05, n)
    menopause = _choice(rng, ["pre", "peri", "post"], [0.35, 0.15, 0.50], n)
    hormone_therapy = _bernoulli(rng, 0.12, n)
    bmi = _normal_clipped(rng, 27, 5, 15, 60, n)
    alcohol = _choice(rng, ["none", "light", "moderate", "heavy"],
                      [0.40, 0.35, 0.18, 0.07], n)

    log_odds = (-4.0
                + 0.03 * (age - 55)
                + 0.4 * (radius - 14.1) / 3.5
                + 0.3 * (texture - 19.3) / 4.3
                + 0.5 * (concavity - 0.089) / 0.080
                + 0.6 * family_history
                + 0.8 * brca
                + 0.3 * (menopause == "post").astype(float))
    prob = 1 / (1 + np.exp(-log_odds))
    prob = prob / prob.mean() * pos_prop
    prob = np.clip(prob, 0.01, 0.99)
    target = rng.binomial(1, prob).astype(np.int8)

    df = pd.DataFrame({
        "age": age.round(1),
        "radius_mean": radius.round(3),
        "texture_mean": texture.round(3),
        "perimeter_mean": perimeter.round(3),
        "area_mean": area.round(3),
        "smoothness_mean": smoothness.round(5),
        "compactness_mean": compactness.round(5),
        "concavity_mean": concavity.round(5),
        "symmetry_mean": symmetry.round(4),
        "fractal_dimension_mean": fractal.round(5),
        "family_history_breast_cancer": family_history,
        "brca_mutation_known": brca,
        "menopause_status": menopause,
        "hormone_therapy_history": hormone_therapy,
        "bmi": bmi.round(2),
        "alcohol_consumption": alcohol,
        "breast_cancer_outcome": target,
    })
    for col, rate in [("radius_mean", 0.05), ("texture_mean", 0.05),
                      ("perimeter_mean", 0.05), ("area_mean", 0.05),
                      ("smoothness_mean", 0.05), ("compactness_mean", 0.05),
                      ("concavity_mean", 0.05), ("symmetry_mean", 0.05),
                      ("fractal_dimension_mean", 0.05), ("bmi", 0.05),
                      ("brca_mutation_known", 0.45), ("menopause_status", 0.05),
                      ("hormone_therapy_history", 0.08), ("alcohol_consumption", 0.08)]:
        df[col] = _inject_missing(rng, df[col], rate)
    return df


def _gen_lung_cancer(rng: np.random.Generator, n: int) -> pd.DataFrame:
    pos_prop = 0.35
    age = _normal_clipped(rng, 60, 12, 18, 90, n)
    sex = _choice(rng, ["male", "female"], [0.58, 0.42], n)
    smoking = _choice(rng, ["never", "former", "current"],
                      [0.30, 0.38, 0.32], n)
    pack_years = np.where(smoking == "never", 0.0,
                          np.clip(rng.normal(25, 18, n), 0, 100))
    yrs_quit = np.where(smoking == "former",
                        np.clip(rng.normal(10, 8, n), 0, 50), 0.0)
    chronic_cough = _bernoulli(rng, 0.30, n)
    sob = _bernoulli(rng, 0.35, n)
    chest_pain = _bernoulli(rng, 0.22, n)
    hemoptysis = _bernoulli(rng, 0.12, n)
    weight_loss = _bernoulli(rng, 0.20, n)
    fatigue = _bernoulli(rng, 0.38, n)
    wheezing = _bernoulli(rng, 0.22, n)
    radon = _choice(rng, ["none", "low", "moderate", "high"],
                    [0.50, 0.28, 0.15, 0.07], n)
    occ_carcino = _bernoulli(rng, 0.12, n)
    family_history = _bernoulli(rng, 0.10, n)
    copd_flag = _bernoulli(rng, 0.15, n)
    bmi = _normal_clipped(rng, 26, 5, 15, 60, n)
    alcohol = _choice(rng, ["none", "light", "moderate", "heavy"],
                      [0.35, 0.35, 0.20, 0.10], n)

    log_odds = (-4.5
                + 0.05 * (age - 60)
                + 1.2 * (smoking == "current").astype(float)
                + 0.8 * (smoking == "former").astype(float)
                + 0.02 * pack_years
                + 0.6 * hemoptysis
                + 0.4 * weight_loss
                + 0.5 * copd_flag
                + 0.4 * family_history
                + 0.3 * (radon == "high").astype(float)
                + 0.3 * occ_carcino)
    prob = 1 / (1 + np.exp(-log_odds))
    prob = prob / prob.mean() * pos_prop
    prob = np.clip(prob, 0.01, 0.99)
    target = rng.binomial(1, prob).astype(np.int8)

    df = pd.DataFrame({
        "age": age.round(1),
        "sex": sex,
        "smoking_status": smoking,
        "pack_years": pack_years.round(1),
        "years_since_quitting": yrs_quit.round(1),
        "chronic_cough": chronic_cough,
        "shortness_of_breath": sob,
        "chest_pain": chest_pain,
        "hemoptysis": hemoptysis,
        "weight_loss_unexplained": weight_loss,
        "fatigue": fatigue,
        "wheezing": wheezing,
        "radon_exposure": radon,
        "occupational_carcinogen_exposure": occ_carcino,
        "family_history_lung_cancer": family_history,
        "copd_flag": copd_flag,
        "bmi": bmi.round(2),
        "alcohol_consumption": alcohol,
        "lung_cancer_outcome": target,
    })
    df["pack_years"] = _inject_missing(rng, df["pack_years"], 0.12)
    df["years_since_quitting"] = _inject_missing(rng, df["years_since_quitting"], 0.18)
    df["radon_exposure"] = _inject_missing(rng, df["radon_exposure"], 0.12)
    df["bmi"] = _inject_missing(rng, df["bmi"], 0.05)
    df["alcohol_consumption"] = _inject_missing(rng, df["alcohol_consumption"], 0.08)
    return df


def _gen_hypertension(rng: np.random.Generator, n: int) -> pd.DataFrame:
    pos_prop = 0.40
    age = _normal_clipped(rng, 48, 15, 18, 90, n)
    sex = _choice(rng, ["male", "female"], [0.49, 0.51], n)
    bmi = _normal_clipped(rng, 27, 5, 15, 60, n)
    sodium_intake = _choice(rng, ["low", "moderate", "high", "very_high"],
                            [0.15, 0.35, 0.35, 0.15], n)
    physical_activity = _choice(rng, ["sedentary", "light", "moderate", "active"],
                                [0.28, 0.30, 0.27, 0.15], n)
    smoking = _choice(rng, ["never", "former", "current"],
                      [0.50, 0.28, 0.22], n)
    alcohol = _choice(rng, ["none", "light", "moderate", "heavy"],
                      [0.35, 0.32, 0.23, 0.10], n)
    family_history = _bernoulli(rng, 0.40, n)
    diabetes_flag = _bernoulli(rng, 0.12, n)
    ckd_flag = _bernoulli(rng, 0.08, n)
    stress = _choice(rng, ["low", "moderate", "high", "very_high"],
                     [0.20, 0.38, 0.30, 0.12], n)
    sleep_hrs = _normal_clipped(rng, 7.0, 1.5, 2.0, 12.0, n)
    cholesterol = _normal_clipped(rng, 210, 40, 100, 600, n)
    heart_rate = _normal_clipped(rng, 73, 12, 40, 120, n)
    waist = _normal_clipped(rng, 90, 15, 50, 160, n)

    log_odds = (-4.0
                + 0.04 * (age - 48)
                + 0.04 * (bmi - 25)
                + 0.5 * family_history
                + 0.6 * diabetes_flag
                + 0.7 * ckd_flag
                + 0.4 * (sodium_intake == "very_high").astype(float)
                + 0.2 * (sodium_intake == "high").astype(float)
                + 0.3 * (alcohol == "heavy").astype(float)
                + 0.3 * (stress == "very_high").astype(float)
                - 0.3 * (sleep_hrs - 7.0)
                - 0.3 * (physical_activity == "active").astype(float))
    prob = 1 / (1 + np.exp(-log_odds))
    prob = prob / prob.mean() * pos_prop
    prob = np.clip(prob, 0.01, 0.99)
    target = rng.binomial(1, prob).astype(np.int8)

    df = pd.DataFrame({
        "age": age.round(1),
        "sex": sex,
        "bmi": bmi.round(2),
        "sodium_intake": sodium_intake,
        "physical_activity": physical_activity,
        "smoking_status": smoking,
        "alcohol_consumption": alcohol,
        "family_history_hypertension": family_history,
        "diabetes_flag": diabetes_flag,
        "ckd_flag": ckd_flag,
        "stress_level": stress,
        "sleep_hours_per_night": sleep_hrs.round(1),
        "cholesterol_total": cholesterol.round(0).astype(int),
        "heart_rate_resting": heart_rate.round(0).astype(int),
        "waist_circumference": waist.round(1),
        "hypertension_outcome": target,
    })
    df["bmi"] = _inject_missing(rng, df["bmi"], 0.05)
    df["sodium_intake"] = _inject_missing(rng, df["sodium_intake"], 0.08)
    df["physical_activity"] = _inject_missing(rng, df["physical_activity"], 0.05)
    df["smoking_status"] = _inject_missing(rng, df["smoking_status"], 0.05)
    df["alcohol_consumption"] = _inject_missing(rng, df["alcohol_consumption"], 0.05)
    df["stress_level"] = _inject_missing(rng, df["stress_level"], 0.12)
    df["sleep_hours_per_night"] = _inject_missing(rng, df["sleep_hours_per_night"], 0.08)
    df["cholesterol_total"] = _inject_missing(rng, df["cholesterol_total"], 0.08)
    df["heart_rate_resting"] = _inject_missing(rng, df["heart_rate_resting"], 0.08)
    df["waist_circumference"] = _inject_missing(rng, df["waist_circumference"], 0.08)
    return df


# ---------------------------------------------------------------------------
# Generator registry
# ---------------------------------------------------------------------------

GENERATORS: dict[str, Any] = {
    "diabetes": (_gen_diabetes, "diabetes_outcome", "1.0.0"),
    "heart_disease": (_gen_heart_disease, "heart_disease_outcome", "1.0.0"),
    "stroke": (_gen_stroke, "stroke_outcome", "1.0.0"),
    "asthma": (_gen_asthma, "asthma_outcome", "1.0.0"),
    "chronic_kidney_disease": (_gen_ckd, "ckd_outcome", "1.0.0"),
    "liver_disease": (_gen_liver_disease, "liver_disease_outcome", "1.0.0"),
    "parkinsons": (_gen_parkinsons, "parkinsons_outcome", "1.0.0"),
    "breast_cancer": (_gen_breast_cancer, "breast_cancer_outcome", "1.0.0"),
    "lung_cancer": (_gen_lung_cancer, "lung_cancer_outcome", "1.0.0"),
    "hypertension": (_gen_hypertension, "hypertension_outcome", "1.0.0"),
}

DISEASE_CODES: dict[str, str] = {
    "diabetes": "DIABETES",
    "heart_disease": "HEART_DISEASE",
    "stroke": "STROKE",
    "asthma": "ASTHMA",
    "chronic_kidney_disease": "CHRONIC_KIDNEY_DISEASE",
    "liver_disease": "LIVER_DISEASE",
    "parkinsons": "PARKINSONS",
    "breast_cancer": "BREAST_CANCER",
    "lung_cancer": "LUNG_CANCER",
    "hypertension": "HYPERTENSION",
}


# ---------------------------------------------------------------------------
# Generate and save datasets
# ---------------------------------------------------------------------------

def generate_dataset(
    disease_id: str,
    n: int = RECORDS_PER_DISEASE,
    seed: int = DEFAULT_SEED,
    output_dir: Path | None = None,
) -> tuple[pd.DataFrame, dict]:
    """Generate one disease dataset and return (DataFrame, metadata)."""
    if disease_id not in GENERATORS:
        raise ValueError(f"Unknown disease: {disease_id}")

    gen_fn, target_col, dataset_version = GENERATORS[disease_id]
    rng = _rng(seed)
    df = gen_fn(rng, n)

    metadata = {
        "disease_code": DISEASE_CODES[disease_id],
        "dataset_identifier": disease_id,
        "dataset_version": dataset_version,
        "schema_version": SCHEMA_VERSION,
        "record_count": len(df),
        "feature_count": len(df.columns) - 1,
        "target_column": target_col,
        "random_seed": seed,
        "generator_version": GENERATOR_VERSION,
        "generation_timestamp": datetime.now(timezone.utc).isoformat(),
        "synthetic": True,
        "clinical_validation": False,
        "disclaimer": (
            "SYNTHETIC RESEARCH DATA ONLY. Does not represent real patients. "
            "Not clinically validated. Must not be used for clinical decisions."
        ),
        "positive_rate": float(df[target_col].mean()),
        "columns": list(df.columns),
    }

    if output_dir is not None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        csv_path = output_dir / f"{disease_id}_v{dataset_version}.csv"
        meta_path = output_dir / f"{disease_id}_v{dataset_version}_metadata.json"
        df.to_csv(csv_path, index=False)
        meta_path.write_text(json.dumps(metadata, indent=2))
        print(f"  Saved: {csv_path.name}  ({len(df):,} records, "
              f"pos_rate={metadata['positive_rate']:.3f})")

    return df, metadata


def generate_all_datasets(
    n: int = RECORDS_PER_DISEASE,
    seed: int = DEFAULT_SEED,
    output_dir: Path | None = None,
) -> dict[str, tuple[pd.DataFrame, dict]]:
    """Generate all 10 disease datasets."""
    results = {}
    for disease_id in GENERATORS:
        print(f"Generating {disease_id}...")
        df, meta = generate_dataset(disease_id, n=n, seed=seed,
                                    output_dir=output_dir)
        results[disease_id] = (df, meta)
    print(f"\nTotal: {sum(len(r[0]) for r in results.values()):,} records across "
          f"{len(results)} diseases.")
    return results


if __name__ == "__main__":
    raw_dir = ML_ROOT / "data" / "raw"
    print("MediRisk 2.0 — Synthetic Dataset Generator")
    print(f"Output: {raw_dir}")
    print("-" * 50)
    generate_all_datasets(output_dir=raw_dir)
