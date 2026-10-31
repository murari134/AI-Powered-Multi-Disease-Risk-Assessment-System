"""
MediRisk 2.0 — Feature Mapping Engine for Multi-Disease Assessment
Phase 9: Complete Unified Health Assessment

Maps a unified patient intake questionnaire into 10 disease-specific feature maps
adhering strictly to each disease's YAML specification and training domains.
"""

from typing import Any, Dict


class FeatureMapper:
    """Extracts and formats disease-specific input feature vectors from a unified assessment form."""

    @staticmethod
    def map_for_disease(disease_id: str, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map common and specialized fields into the exact feature names required by disease_id."""
        method_name = f"_map_{disease_id}"
        mapper_fn = getattr(FeatureMapper, method_name, None)
        if mapper_fn is not None:
            return mapper_fn(raw_data)
        # Fallback to direct raw_data copy
        return dict(raw_data)

    @staticmethod
    def _get_num(data: Dict[str, Any], key: str, default: float) -> float:
        val = data.get(key)
        if val is None or val == "":
            return default
        try:
            return float(val)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def _get_int(data: Dict[str, Any], key: str, default: int) -> int:
        val = data.get(key)
        if val is None or val == "":
            return default
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return 1 if str(val).lower() in ("true", "yes", "1", "y") else 0

    @staticmethod
    def _get_str(data: Dict[str, Any], key: str, default: str) -> str:
        val = data.get(key)
        if val is None or val == "":
            return default
        return str(val).lower().strip()

    @classmethod
    def _map_diabetes(cls, d: Dict[str, Any]) -> Dict[str, Any]:
        sbp = cls._get_num(d, "blood_pressure_systolic", 120.0)
        gluc = cls._get_num(d, "glucose_level", cls._get_num(d, "blood_glucose_random", 95.0))
        sex = cls._get_str(d, "sex", "female")
        num_preg = cls._get_num(d, "num_pregnancies", 0.0) if sex == "female" else 0.0

        return {
            "age": cls._get_num(d, "age", 45.0),
            "bmi": cls._get_num(d, "bmi", 24.5),
            "glucose_level": gluc,
            "blood_pressure_systolic": sbp,
            "blood_pressure_diastolic": cls._get_num(d, "blood_pressure_diastolic", 80.0),
            "insulin_level": cls._get_num(d, "insulin_level", 80.0),
            "skin_thickness": cls._get_num(d, "skin_thickness", 20.0),
            "diabetes_pedigree": cls._get_num(d, "diabetes_pedigree", 0.35),
            "num_pregnancies": num_preg,
            "sex": sex,
            "smoking_status": cls._get_str(d, "smoking_status", "never"),
            "physical_activity": cls._get_str(d, "physical_activity", "moderate"),
            "family_history_diabetes": cls._get_int(d, "family_history_diabetes", 0),
            "hypertension_flag": cls._get_int(d, "hypertension_flag", 1 if sbp >= 140 else 0),
        }

    @classmethod
    def _map_heart_disease(cls, d: Dict[str, Any]) -> Dict[str, Any]:
        sbp = cls._get_num(d, "resting_blood_pressure", cls._get_num(d, "blood_pressure_systolic", 120.0))
        gluc = cls._get_num(d, "glucose_level", cls._get_num(d, "blood_glucose_random", 95.0))
        fbs = cls._get_int(d, "fasting_blood_sugar_high", 1 if gluc > 120.0 else 0)
        diab_flag = cls._get_int(d, "diabetes_flag", 1 if gluc >= 126.0 else 0)

        return {
            "age": cls._get_num(d, "age", 50.0),
            "sex": cls._get_str(d, "sex", "male"),
            "chest_pain_type": cls._get_str(d, "chest_pain_type", "typical_angina"),
            "resting_blood_pressure": sbp,
            "cholesterol_total": cls._get_num(d, "cholesterol_total", 195.0),
            "fasting_blood_sugar_high": fbs,
            "resting_ecg": cls._get_str(d, "resting_ecg", "normal"),
            "max_heart_rate": cls._get_num(d, "max_heart_rate", 150.0),
            "exercise_induced_angina": cls._get_int(d, "exercise_induced_angina", 0),
            "st_depression": cls._get_num(d, "st_depression", 0.5),
            "slope_peak_st": cls._get_str(d, "slope_peak_st", "upsloping"),
            "num_major_vessels": cls._get_num(d, "num_major_vessels", 0.0),
            "thalassemia_type": cls._get_str(d, "thalassemia_type", "normal"),
            "smoking_status": cls._get_str(d, "smoking_status", "never"),
            "diabetes_flag": diab_flag,
            "bmi": cls._get_num(d, "bmi", 25.0),
        }

    @classmethod
    def _map_stroke(cls, d: Dict[str, Any]) -> Dict[str, Any]:
        sbp = cls._get_num(d, "blood_pressure_systolic", 120.0)
        hyp = cls._get_int(d, "hypertension_flag", 1 if sbp >= 140 else 0)
        gluc = cls._get_num(d, "avg_glucose_level", cls._get_num(d, "glucose_level", 95.0))

        # Stroke uses ['never', 'formerly_smoked', 'smokes', 'unknown']
        raw_smk = cls._get_str(d, "smoking_status", "never")
        if raw_smk in ("current", "active_smoker"):
            smk = "smokes"
        elif raw_smk in ("former", "past"):
            smk = "formerly_smoked"
        elif raw_smk in ("passive", "unknown"):
            smk = "unknown"
        else:
            smk = "never"

        return {
            "age": cls._get_num(d, "age", 55.0),
            "sex": cls._get_str(d, "sex", "male"),
            "hypertension_flag": hyp,
            "heart_disease_flag": cls._get_int(d, "heart_disease_flag", 0),
            "ever_married": cls._get_int(d, "ever_married", 1),
            "work_type": cls._get_str(d, "work_type", "private"),
            "residence_type": cls._get_str(d, "residence_type", "urban"),
            "avg_glucose_level": gluc,
            "bmi": cls._get_num(d, "bmi", 25.2),
            "smoking_status": smk,
            "atrial_fibrillation_flag": cls._get_int(d, "atrial_fibrillation_flag", 0),
            "cholesterol_total": cls._get_num(d, "cholesterol_total", 195.0),
            "physical_activity": cls._get_str(d, "physical_activity", "moderate"),
        }

    @classmethod
    def _map_asthma(cls, d: Dict[str, Any]) -> Dict[str, Any]:
        # exercise_frequency: ['never', 'rarely', 'sometimes', 'regularly']
        raw_act = cls._get_str(d, "physical_activity", cls._get_str(d, "exercise_frequency", "moderate"))
        if raw_act in ("sedentary", "never"):
            ex_freq = "never"
        elif raw_act in ("light", "rarely"):
            ex_freq = "rarely"
        elif raw_act in ("active", "regularly"):
            ex_freq = "regularly"
        else:
            ex_freq = "sometimes"

        return {
            "age": cls._get_num(d, "age", 35.0),
            "sex": cls._get_str(d, "sex", "female"),
            "family_history_asthma": cls._get_int(d, "family_history_asthma", 0),
            "allergic_rhinitis_flag": cls._get_int(d, "allergic_rhinitis_flag", 0),
            "eczema_flag": cls._get_int(d, "eczema_flag", 0),
            "smoking_status": cls._get_str(d, "smoking_status", "never"),
            "occupational_exposure": cls._get_str(d, "occupational_exposure", "none"),
            "air_quality_index": cls._get_num(d, "air_quality_index", 45.0),
            "bmi": cls._get_num(d, "bmi", 23.5),
            "exercise_frequency": ex_freq,
            "pet_exposure": cls._get_int(d, "pet_exposure", 0),
            "mold_exposure": cls._get_int(d, "mold_exposure", 0),
            "fev1_fvc_ratio": cls._get_num(d, "fev1_fvc_ratio", 0.82),
            "num_respiratory_infections_past_year": cls._get_num(d, "num_respiratory_infections_past_year", 0.0),
        }

    @classmethod
    def _map_chronic_kidney_disease(cls, d: Dict[str, Any]) -> Dict[str, Any]:
        sbp = cls._get_num(d, "blood_pressure_systolic", 120.0)
        gluc = cls._get_num(d, "blood_glucose_random", cls._get_num(d, "glucose_level", 98.0))
        hyp = cls._get_int(d, "hypertension_flag", 1 if sbp >= 140 else 0)
        diab = cls._get_int(d, "diabetes_flag", 1 if gluc >= 126 else 0)

        return {
            "age": cls._get_num(d, "age", 50.0),
            "sex": cls._get_str(d, "sex", "male"),
            "blood_pressure_systolic": sbp,
            "blood_glucose_random": gluc,
            "blood_urea": cls._get_num(d, "blood_urea", 32.0),
            "serum_creatinine": cls._get_num(d, "serum_creatinine", 1.05),
            "sodium": cls._get_num(d, "sodium", 138.0),
            "potassium": cls._get_num(d, "potassium", 4.3),
            "hemoglobin": cls._get_num(d, "hemoglobin", 14.5),
            "packed_cell_volume": cls._get_num(d, "packed_cell_volume", 42.0),
            "white_blood_cell_count": cls._get_num(d, "white_blood_cell_count", 7500.0),
            "red_blood_cell_count": cls._get_num(d, "red_blood_cell_count", 4.8),
            "hypertension_flag": hyp,
            "diabetes_flag": diab,
            "anemia_flag": cls._get_int(d, "anemia_flag", 0),
            "urine_albumin": cls._get_str(d, "urine_albumin", "normal"),
            "urine_sugar": cls._get_str(d, "urine_sugar", "normal"),
            "pus_cell": cls._get_str(d, "pus_cell", "normal"),
            "bacteria_in_urine": cls._get_int(d, "bacteria_in_urine", 0),
        }

    @classmethod
    def _map_liver_disease(cls, d: Dict[str, Any]) -> Dict[str, Any]:
        sbp = cls._get_num(d, "blood_pressure_systolic", 120.0)
        gluc = cls._get_num(d, "glucose_level", 95.0)

        return {
            "age": cls._get_num(d, "age", 48.0),
            "sex": cls._get_str(d, "sex", "male"),
            "total_bilirubin": cls._get_num(d, "total_bilirubin", 0.85),
            "direct_bilirubin": cls._get_num(d, "direct_bilirubin", 0.22),
            "alkaline_phosphatase": cls._get_num(d, "alkaline_phosphatase", 185.0),
            "alt": cls._get_num(d, "alt", 26.0),
            "ast": cls._get_num(d, "ast", 27.0),
            "total_proteins": cls._get_num(d, "total_proteins", 7.1),
            "albumin": cls._get_num(d, "albumin", 4.2),
            "albumin_globulin_ratio": cls._get_num(d, "albumin_globulin_ratio", 1.15),
            "bmi": cls._get_num(d, "bmi", 24.2),
            "alcohol_consumption": cls._get_str(d, "alcohol_consumption", "none"),
            "smoking_status": cls._get_str(d, "smoking_status", "never"),
            "diabetes_flag": cls._get_int(d, "diabetes_flag", 1 if gluc >= 126 else 0),
            "hypertension_flag": cls._get_int(d, "hypertension_flag", 1 if sbp >= 140 else 0),
        }

    @classmethod
    def _map_parkinsons(cls, d: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "age": cls._get_num(d, "age", 62.0),
            "sex": cls._get_str(d, "sex", "male"),
            "vocal_jitter_pct": cls._get_num(d, "vocal_jitter_pct", 0.0055),
            "vocal_shimmer_pct": cls._get_num(d, "vocal_shimmer_pct", 0.024),
            "nhr": cls._get_num(d, "nhr", 0.022),
            "hnr": cls._get_num(d, "hnr", 23.5),
            "rpde": cls._get_num(d, "rpde", 0.46),
            "dfa": cls._get_num(d, "dfa", 0.66),
            "tremor_score": cls._get_num(d, "tremor_score", 0.0),
            "rigidity_score": cls._get_num(d, "rigidity_score", 0.0),
            "bradykinesia_score": cls._get_num(d, "bradykinesia_score", 0.0),
            "family_history_parkinsons": cls._get_int(d, "family_history_parkinsons", 0),
            "pesticide_exposure": cls._get_int(d, "pesticide_exposure", 0),
            "head_injury_history": cls._get_int(d, "head_injury_history", 0),
        }

    @classmethod
    def _map_breast_cancer(cls, d: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "age": cls._get_num(d, "age", 52.0),
            "radius_mean": cls._get_num(d, "radius_mean", 13.8),
            "texture_mean": cls._get_num(d, "texture_mean", 18.5),
            "perimeter_mean": cls._get_num(d, "perimeter_mean", 88.0),
            "area_mean": cls._get_num(d, "area_mean", 580.0),
            "smoothness_mean": cls._get_num(d, "smoothness_mean", 0.096),
            "compactness_mean": cls._get_num(d, "compactness_mean", 0.092),
            "concavity_mean": cls._get_num(d, "concavity_mean", 0.075),
            "symmetry_mean": cls._get_num(d, "symmetry_mean", 0.18),
            "fractal_dimension_mean": cls._get_num(d, "fractal_dimension_mean", 0.062),
            "family_history_breast_cancer": cls._get_int(d, "family_history_breast_cancer", 0),
            "brca_mutation_known": cls._get_int(d, "brca_mutation_known", 0),
            "menopause_status": cls._get_str(d, "menopause_status", "pre"),
            "hormone_therapy_history": cls._get_int(d, "hormone_therapy_history", 0),
            "bmi": cls._get_num(d, "bmi", 23.8),
            "alcohol_consumption": cls._get_str(d, "alcohol_consumption", "none"),
        }

    @classmethod
    def _map_lung_cancer(cls, d: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "age": cls._get_num(d, "age", 58.0),
            "sex": cls._get_str(d, "sex", "male"),
            "smoking_status": cls._get_str(d, "smoking_status", "never"),
            "pack_years": cls._get_num(d, "pack_years", 0.0),
            "years_since_quitting": cls._get_num(d, "years_since_quitting", 0.0),
            "chronic_cough": cls._get_int(d, "chronic_cough", 0),
            "shortness_of_breath": cls._get_int(d, "shortness_of_breath", 0),
            "chest_pain": cls._get_int(d, "chest_pain", 0),
            "hemoptysis": cls._get_int(d, "hemoptysis", 0),
            "weight_loss_unexplained": cls._get_int(d, "weight_loss_unexplained", 0),
            "fatigue": cls._get_int(d, "fatigue", 0),
            "wheezing": cls._get_int(d, "wheezing", 0),
            "radon_exposure": cls._get_str(d, "radon_exposure", "none"),
            "occupational_carcinogen_exposure": cls._get_int(d, "occupational_carcinogen_exposure", 0),
            "family_history_lung_cancer": cls._get_int(d, "family_history_lung_cancer", 0),
            "copd_flag": cls._get_int(d, "copd_flag", 0),
            "bmi": cls._get_num(d, "bmi", 24.1),
            "alcohol_consumption": cls._get_str(d, "alcohol_consumption", "none"),
        }

    @classmethod
    def _map_hypertension(cls, d: Dict[str, Any]) -> Dict[str, Any]:
        gluc = cls._get_num(d, "glucose_level", 95.0)

        return {
            "age": cls._get_num(d, "age", 48.0),
            "sex": cls._get_str(d, "sex", "male"),
            "bmi": cls._get_num(d, "bmi", 25.2),
            "sodium_intake": cls._get_str(d, "sodium_intake", "moderate"),
            "physical_activity": cls._get_str(d, "physical_activity", "moderate"),
            "smoking_status": cls._get_str(d, "smoking_status", "never"),
            "alcohol_consumption": cls._get_str(d, "alcohol_consumption", "none"),
            "family_history_hypertension": cls._get_int(d, "family_history_hypertension", 0),
            "diabetes_flag": cls._get_int(d, "diabetes_flag", 1 if gluc >= 126 else 0),
            "ckd_flag": cls._get_int(d, "ckd_flag", 0),
            "stress_level": cls._get_str(d, "stress_level", "moderate"),
            "sleep_hours_per_night": cls._get_num(d, "sleep_hours_per_night", 7.5),
            "cholesterol_total": cls._get_num(d, "cholesterol_total", 195.0),
            "heart_rate_resting": cls._get_num(d, "heart_rate_resting", 72.0),
            "waist_circumference": cls._get_num(d, "waist_circumference", 84.0),
        }
