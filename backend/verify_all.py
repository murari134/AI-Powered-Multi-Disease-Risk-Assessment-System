import asyncio
import uuid
import httpx

BASE_URL = "http://127.0.0.1:8000"

SUPPORTED_DISEASES = [
    "diabetes",
    "heart_disease",
    "stroke",
    "asthma",
    "chronic_kidney_disease",
    "liver_disease",
    "parkinsons",
    "breast_cancer",
    "lung_cancer",
    "hypertension",
]

async def test_full_system():
    print("=================================================================")
    print("MediRisk 2.0 Full System Verification Test Suite")
    print("=================================================================\n")

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=90.0) as client:
        # 1. Health check
        health_resp = await client.get("/health")
        assert health_resp.status_code == 200, f"Health check failed: {health_resp.text}"
        print("[PASS] 1. Backend Health Check: OK")

        # 2. Diseases Specs Endpoint
        diseases_resp = await client.get("/api/v1/diseases")
        assert diseases_resp.status_code == 200, f"Diseases endpoint failed: {diseases_resp.text}"
        data = diseases_resp.json()
        assert data["count"] == 10, f"Expected 10 diseases, got {data['count']}"
        print(f"[PASS] 2. Verified all {data['count']} disease specifications in catalog")

        # 3. Test Individual Disease Assessment (Mode B) for each of the 10 diseases
        print("\n--- Testing Mode B: Individual Disease Assessments (All 10) ---")
        individual_results = {}
        for disease_id in SUPPORTED_DISEASES:
            spec_resp = await client.get(f"/api/v1/diseases/{disease_id}")
            assert spec_resp.status_code == 200
            spec = spec_resp.json()

            # Build valid input according to spec
            test_input = {}
            for f in spec["features"]:
                fn = f["name"]
                ft = f.get("type", "numerical")
                dom = f.get("domain")
                if ft == "numerical":
                    if dom and len(dom) == 2:
                        test_input[fn] = (dom[0] + dom[1]) / 2.0
                    else:
                        test_input[fn] = 50.0
                elif ft == "binary":
                    test_input[fn] = 0
                else: # categorical
                    test_input[fn] = dom[0] if dom else "normal"

            # Execute individual prediction
            pred_resp = await client.post(
                "/api/v1/predictions",
                json={
                    "disease_id": disease_id,
                    "input_data": test_input,
                    "model_name": "tabicl",
                },
            )
            assert pred_resp.status_code in (200, 201), f"Prediction failed for {disease_id}: {pred_resp.text}"
            res = pred_resp.json()
            pred_id = res["prediction_id"]

            # Test retrieval of prediction detail from PostgreSQL
            detail_resp = await client.get(f"/api/v1/predictions/{pred_id}")
            assert detail_resp.status_code == 200, f"Failed retrieving detail for {pred_id}: {detail_resp.text}"
            detail = detail_resp.json()

            individual_results[disease_id] = {
                "probability": res["raw_probability"],
                "risk_level": res["risk_level"],
                "attributions": len(res.get("attributions", [])),
                "recommendations": len(res.get("recommendations", [])),
                "model": f"{res['model_name']} {res['model_version']}",
                "retrieved_from_db": detail["prediction_id"] == pred_id,
            }
            print(f"  [PASS] {disease_id:25s} -> Prob: {res['raw_probability']:.4f} ({res['risk_level']:8s}), Attributions: {len(res.get('attributions', []))}, DB Persisted: OK")

        # 4. Test Complete Multi-Disease Assessment (Mode A)
        print("\n--- Testing Mode A: Complete Health Assessment (All 10 in 1 Workflow) ---")
        unified_sample = {
            "age": 56,
            "sex": "male",
            "bmi": 29.5,
            "smoking_status": "current",
            "physical_activity": "sedentary",
            "alcohol_consumption": "moderate",
            "blood_pressure_systolic": 145,
            "blood_pressure_diastolic": 92,
            "glucose_level": 140,
            "cholesterol_total": 235,
            "heart_rate_resting": 80,
            "hypertension_flag": 1,
            "diabetes_flag": 1,
            "family_history_heart_disease": 1,
            "family_history_diabetes": 1,
            "blood_urea": 38,
            "serum_creatinine": 1.25,
            "total_bilirubin": 1.1,
            "alt": 35,
            "fev1_fvc_ratio": 0.78,
        }

        complete_resp = await client.post(
            "/api/v1/predictions/complete",
            json={
                "input_data": unified_sample,
                "model_name": "tabicl",
            },
        )
        assert complete_resp.status_code in (200, 201), f"Complete assessment failed: {complete_resp.text}"
        comp = complete_resp.json()
        assessment_id = comp["assessment_id"]

        print(f"[PASS] Complete Assessment Created: ID={assessment_id}")
        print(f"       Evaluated Diseases Count: {comp['diseases_evaluated']}")
        print(f"       Summary Breakdown: High={comp['summary']['high_risk_count']}, Moderate={comp['summary']['moderate_risk_count']}, Low={comp['summary']['low_risk_count']}")
        print(f"       Highest Flagged Condition: {comp['summary']['highest_risk_disease']} ({comp['summary']['highest_risk_percentage']}%)")

        # Test retrieval of the complete assessment from PostgreSQL
        get_comp_resp = await client.get(f"/api/v1/assessments/complete/{assessment_id}")
        assert get_comp_resp.status_code == 200, f"Retrieving complete assessment failed: {get_comp_resp.text}"
        retrieved_comp = get_comp_resp.json()
        assert retrieved_comp["assessment_id"] == assessment_id
        assert len(retrieved_comp["results"]) == 10
        print(f"[PASS] Complete Assessment Retrieved from DB with all {len(retrieved_comp['results'])} disease prediction records!")

        # 5. Test Hospital & Facility Locator
        print("\n--- Testing Healthcare Facility Locator ---")
        hosp_boston = await client.get("/api/v1/hospitals/search?query=Boston")
        assert hosp_boston.status_code == 200
        hb_data = hosp_boston.json()
        assert hb_data["count"] > 0, "Expected Boston hospital results"
        print(f"[PASS] Hospital Query 'Boston': Found {hb_data['count']} verified facilities")

        hosp_cardio = await client.get("/api/v1/hospitals/search?specialty=Cardiology")
        assert hosp_cardio.status_code == 200
        hc_data = hosp_cardio.json()
        assert hc_data["count"] > 0, "Expected Cardiology specialty results"
        print(f"[PASS] Specialty Filter 'Cardiology': Found {hc_data['count']} verified facilities")

        # Proximity search
        hosp_geo = await client.get("/api/v1/hospitals/search?lat=42.36&lon=-71.06")
        assert hosp_geo.status_code == 200
        print(f"[PASS] Proximity Location Search: Responded with HTTP 200")

        # 6. Test Analytics Endpoint
        print("\n--- Testing Analytics & Benchmark Summary ---")
        ana_resp = await client.get("/api/v1/analytics/overview")
        assert ana_resp.status_code == 200
        ana_data = ana_resp.json()
        print(f"[PASS] Analytics Overview: Total DB Assessments={ana_data['total_assessments']}, Risk Tier Distribution={ana_data['risk_tier_distribution']}")

    print("\n=================================================================")
    print("ALL TESTS PASSED SUCCESSFULLY! Both Mode A & Mode B are fully verified!")
    print("=================================================================")

if __name__ == "__main__":
    asyncio.run(test_full_system())
