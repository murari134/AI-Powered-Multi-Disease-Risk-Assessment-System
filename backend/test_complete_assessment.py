import asyncio
import uuid
from app.db.session import AsyncSessionLocal
from app.services.prediction_service import PredictionService
from app.models.models import User, Profile
from sqlalchemy import select

sample_input = {
    "age": 54,
    "sex": "female",
    "bmi": 28.2,
    "smoking_status": "former",
    "physical_activity": "moderate",
    "alcohol_consumption": "light",
    "blood_pressure_systolic": 138,
    "blood_pressure_diastolic": 88,
    "glucose_level": 115,
    "cholesterol_total": 220,
    "heart_rate_resting": 76,
    "hypertension_flag": 0,
    "diabetes_flag": 0,
    "family_history_heart_disease": 1,
    "family_history_diabetes": 1,
    "fev1_fvc_ratio": 0.81,
    "serum_creatinine": 1.1,
    "total_bilirubin": 0.9,
    "alt": 28,
}

async def run_test():
    async with AsyncSessionLocal() as session:
        # Fetch or create a test user
        res = await session.execute(select(User).limit(1))
        user = res.scalar_one_or_none()
        
        svc = PredictionService(session)
        print("Testing create_complete_assessment...")
        comp_res = await svc.create_complete_assessment(
            user=user,
            input_data=sample_input,
            model_name="tabicl"
        )
        print("Assessment ID:", comp_res["assessment_id"])
        print("Mode:", comp_res["assessment_mode"])
        print("Summary:", comp_res["summary"])
        print(f"Evaluated {len(comp_res['results'])} diseases:")
        for r in comp_res["results"]:
            print(f"  {r['disease_name']:25s}: {r['risk_percentage']}% ({r['risk_level']}) - status={r['status']}")

        print("\nTesting get_complete_assessment retrieval from DB...")
        retrieved = await svc.get_complete_assessment(uuid.UUID(comp_res["assessment_id"]))
        print(f"Retrieved {len(retrieved['results'])} disease records successfully from DB!")
        print("First disease attributions count:", len(retrieved['results'][0]['attributions']))
        print("First disease recommendations count:", len(retrieved['results'][0]['recommendations']))

asyncio.run(run_test())
