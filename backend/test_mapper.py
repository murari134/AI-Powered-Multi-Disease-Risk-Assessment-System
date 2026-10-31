import sys
from app.services.ml_engine import ml_engine, SUPPORTED_DISEASES
from app.services.feature_mapper import FeatureMapper

sample_unified_intake = {
    # Demographics & Lifestyle
    "age": 52,
    "sex": "male",
    "bmi": 27.5,
    "smoking_status": "former",
    "physical_activity": "moderate",
    "alcohol_consumption": "light",
    # Vitals & Labs
    "blood_pressure_systolic": 135,
    "blood_pressure_diastolic": 85,
    "glucose_level": 110,
    "cholesterol_total": 210,
    "heart_rate_resting": 74,
    # Flags
    "hypertension_flag": 0,
    "diabetes_flag": 0,
    "family_history_heart_disease": 1,
    "family_history_diabetes": 0,
}

print("Testing FeatureMapper with all 10 diseases...")
for d in SUPPORTED_DISEASES:
    mapped = FeatureMapper.map_for_disease(d, sample_unified_intake)
    res = ml_engine.predict(d, mapped, model_name="tabicl")
    print(f"  [OK] {d:25s} -> prob: {res['raw_probability']:.4f}, risk: {res['risk_level']:8s}, latency: {res['inference_latency_ms']}ms")

print("All 10 diseases successfully mapped and evaluated!")
