"""
MediRisk 2.0 — Predictions, Diseases & Hospital Locator API
Phase 8: Production Endpoints
"""

import json
import logging
import urllib.parse
import uuid
from typing import Annotated, Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, Depends, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.token_service import validate_access_token
from app.db.session import get_db
from app.dependencies import get_current_active_user, limiter
from app.models.models import User
from app.services.ml_engine import ml_engine
from app.services.prediction_service import PredictionService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Predictions & Clinical Intelligence"])


class PredictionRequest(BaseModel):
    disease_id: str = Field(..., description="Disease identifier e.g. 'diabetes', 'heart_disease'")
    input_data: Dict[str, Any] = Field(..., description="Patient clinical & lifestyle feature map")
    model_name: str = Field("tabicl", description="Model architecture: 'tabicl' or 'tabpfn'")
    profile_id: Optional[uuid.UUID] = Field(None, description="Optional target profile UUID")


class CompleteAssessmentRequest(BaseModel):
    input_data: Dict[str, Any] = Field(..., description="Unified multi-disease clinical and lifestyle features")
    model_name: str = Field("tabicl", description="Model architecture: 'tabicl' or 'tabpfn'")
    profile_id: Optional[uuid.UUID] = Field(None, description="Optional target profile UUID")


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _get_user_agent(request: Request) -> str:
    return request.headers.get("User-Agent", "unknown")


def _get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "-")


async def _get_optional_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> Optional[User]:
    """Extract authenticated user if Authorization Bearer header is provided."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ")[1]
    try:
        payload = validate_access_token(token)
        user_id = uuid.UUID(payload["sub"])
        from app.repositories.repositories import UserRepository
        repo = UserRepository(db)
        return await repo.get_by_id(user_id)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Diseases Specifications & Benchmark Metadata
# ---------------------------------------------------------------------------

@router.get("/diseases", summary="List all 10 supported disease specifications and model benchmarks")
async def list_diseases():
    return {
        "count": len(ml_engine.specs),
        "diseases": ml_engine.get_all_diseases_metadata(),
    }


@router.get("/diseases/{disease_id}", summary="Get detailed YAML schema and features for a disease")
async def get_disease_detail(disease_id: str):
    return ml_engine.get_disease_spec(disease_id)


# ---------------------------------------------------------------------------
# Prediction Execution
# ---------------------------------------------------------------------------

@router.post(
    "/predictions",
    status_code=status.HTTP_201_CREATED,
    summary="Execute multi-disease risk assessment using Tabular Foundation Models",
)
@limiter.limit("30/minute")
async def create_prediction(
    request: Request,
    body: PredictionRequest,
    current_user: Optional[User] = Depends(_get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = PredictionService(db)
    result = await svc.create_prediction(
        user=current_user,
        disease_id=body.disease_id,
        input_data=body.input_data,
        model_name=body.model_name,
        profile_id=body.profile_id,
        ip_address=_get_client_ip(request),
        user_agent=_get_user_agent(request),
        request_id=_get_request_id(request),
    )
    return result


@router.post(
    "/predictions/complete",
    status_code=status.HTTP_201_CREATED,
    summary="Mode A: Execute unified multi-disease health assessment across all 10 diseases",
)
@limiter.limit("20/minute")
async def create_complete_assessment(
    request: Request,
    body: CompleteAssessmentRequest,
    current_user: Optional[User] = Depends(_get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = PredictionService(db)
    result = await svc.create_complete_assessment(
        user=current_user,
        input_data=body.input_data,
        model_name=body.model_name,
        profile_id=body.profile_id,
        ip_address=_get_client_ip(request),
        user_agent=_get_user_agent(request),
        request_id=_get_request_id(request),
    )
    return result


@router.get(
    "/assessments/complete/{assessment_id}",
    summary="Get combined multi-disease assessment results for all 10 diseases",
)
async def get_complete_assessment_detail(
    assessment_id: uuid.UUID,
    current_user: Optional[User] = Depends(_get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = PredictionService(db)
    return await svc.get_complete_assessment(
        assessment_id=assessment_id,
        user_id=current_user.id if current_user else None,
    )


@router.get(
    "/predictions/history",
    summary="Get authenticated user's prediction history",
)
async def get_prediction_history(
    current_user: Annotated[User, Depends(get_current_active_user)],
    disease_filter: Optional[str] = Query(None, description="Filter by disease code"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    svc = PredictionService(db)
    return await svc.get_user_history(
        user_id=current_user.id,
        disease_filter=disease_filter,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/predictions/{prediction_id}",
    summary="Get single prediction details with attributions and recommendations",
)
async def get_prediction_detail(
    prediction_id: uuid.UUID,
    current_user: Optional[User] = Depends(_get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = PredictionService(db)
    return await svc.get_prediction_detail(
        prediction_id=prediction_id,
        user_id=current_user.id if current_user else None,
    )


# ---------------------------------------------------------------------------
# Analytics Overview
# ---------------------------------------------------------------------------

@router.get("/analytics/overview", summary="Get disease statistics, risk tier breakdown, and benchmark comparisons")
async def get_analytics_overview(
    current_user: Optional[User] = Depends(_get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = PredictionService(db)
    return await svc.get_analytics_overview(user_id=current_user.id if current_user else None)


# ---------------------------------------------------------------------------
# Real Hospital Locator (OpenStreetMap Overpass API + Fallback Directory)
# ---------------------------------------------------------------------------

VERIFIED_GLOBAL_HOSPITALS = [
    {
        "id": "hosp-1",
        "name": "Massachusetts General Hospital",
        "city": "Boston",
        "country": "United States",
        "address": "55 Fruit St, Boston, MA 02114",
        "type": "General Hospital & Research Center",
        "emergency": True,
        "phone": "+1 617-726-2000",
        "specialties": ["Cardiology", "Oncology", "Neurology", "Endocrinology"],
        "lat": 42.3628,
        "lon": -71.0694,
        "website": "https://www.massgeneral.org",
    },
    {
        "id": "hosp-2",
        "name": "Cleveland Clinic Main Campus",
        "city": "Cleveland",
        "country": "United States",
        "address": "9500 Euclid Ave, Cleveland, OH 44195",
        "type": "Specialized Medical Center",
        "emergency": True,
        "phone": "+1 216-444-2200",
        "specialties": ["Heart Disease", "Cardiovascular Surgery", "Nephrology"],
        "lat": 41.5034,
        "lon": -81.6214,
        "website": "https://my.clevelandclinic.org",
    },
    {
        "id": "hosp-3",
        "name": "Johns Hopkins Hospital",
        "city": "Baltimore",
        "country": "United States",
        "address": "1800 Orleans St, Baltimore, MD 21287",
        "type": "Academic Medical Center",
        "emergency": True,
        "phone": "+1 410-955-5000",
        "specialties": ["Oncology", "Neurology", "Pediatrics", "Internal Medicine"],
        "lat": 39.2970,
        "lon": -76.5925,
        "website": "https://www.hopkinsmedicine.org",
    },
    {
        "id": "hosp-4",
        "name": "Mayo Clinic Rochester",
        "city": "Rochester",
        "country": "United States",
        "address": "200 1st St SW, Rochester, MN 55905",
        "type": "Specialized Diagnostic & Care Center",
        "emergency": True,
        "phone": "+1 507-284-2511",
        "specialties": ["Endocrinology", "Cardiology", "Pulmonology", "Neurology"],
        "lat": 44.0225,
        "lon": -92.4665,
        "website": "https://www.mayoclinic.org",
    },
    {
        "id": "hosp-5",
        "name": "St Thomas' Hospital (NHS)",
        "city": "London",
        "country": "United Kingdom",
        "address": "Westminster Bridge Rd, London SE1 7EH",
        "type": "Major NHS Trust & Emergency Center",
        "emergency": True,
        "phone": "+44 20 7188 7188",
        "specialties": ["Cardiovascular", "Respiratory", "Kidney Care", "Stroke"],
        "lat": 51.4988,
        "lon": -0.1189,
        "website": "https://www.guysandstthomas.nhs.uk",
    },
    {
        "id": "hosp-6",
        "name": "All India Institute of Medical Sciences (AIIMS)",
        "city": "New Delhi",
        "country": "India",
        "address": "Sri Aurobindo Marg, Ansari Nagar, New Delhi 110029",
        "type": "Apex Public Medical Institute",
        "emergency": True,
        "phone": "+91 11 2658 8500",
        "specialties": ["Cardiology", "Neurology", "Nephrology", "Oncology", "Endocrinology"],
        "lat": 28.5672,
        "lon": 77.2100,
        "website": "https://www.aiims.edu",
    },
    {
        "id": "hosp-7",
        "name": "Apollo Hospitals Greams Road",
        "city": "Chennai",
        "country": "India",
        "address": "21 Greams Lane, Thousand Lights, Chennai 600006",
        "type": "Super Specialty Tertiary Care",
        "emergency": True,
        "phone": "+91 44 2829 0200",
        "specialties": ["Cardiology", "Liver Care", "Oncology", "Organ Transplants"],
        "lat": 13.0594,
        "lon": 80.2505,
        "website": "https://www.apollohospitals.com",
    },
    {
        "id": "hosp-8",
        "name": "Toronto General Hospital (UHN)",
        "city": "Toronto",
        "country": "Canada",
        "address": "200 Elizabeth St, Toronto, ON M5G 2C4",
        "type": "Teaching & Research Hospital",
        "emergency": True,
        "phone": "+1 416-340-4800",
        "specialties": ["Cardiac Care", "Organ Transplant", "Stroke Center"],
        "lat": 43.6591,
        "lon": -79.3879,
        "website": "https://www.uhn.ca",
    },
    {
        "id": "hosp-9",
        "name": "Charité – Universitätsmedizin Berlin",
        "city": "Berlin",
        "country": "Germany",
        "address": "Charitépl. 1, 10117 Berlin",
        "type": "University Hospital",
        "emergency": True,
        "phone": "+49 30 45050",
        "specialties": ["Neurology", "Pulmonology", "Oncology", "Cardiology"],
        "lat": 52.5256,
        "lon": 13.3789,
        "website": "https://www.charite.de",
    },
    {
        "id": "hosp-10",
        "name": "Singapore General Hospital (SGH)",
        "city": "Singapore",
        "country": "Singapore",
        "address": "Outram Rd, Singapore 169608",
        "type": "Tertiary Referral Hospital",
        "emergency": True,
        "phone": "+65 6222 3322",
        "specialties": ["Endocrinology", "Cardiology", "Nephrology", "Respiratory"],
        "lat": 1.2789,
        "lon": 103.8344,
        "website": "https://www.sgh.com.sg",
    },
]


@router.get("/hospitals/search", summary="Search real verified hospitals and healthcare facilities")
async def search_hospitals(
    query: Optional[str] = Query(None, description="City, hospital name, or condition e.g. 'Boston', 'AIIMS', 'Cardiology'"),
    lat: Optional[float] = Query(None, description="Optional latitude for proximity search"),
    lon: Optional[float] = Query(None, description="Optional longitude for proximity search"),
    specialty: Optional[str] = Query(None, description="Filter by clinical specialty"),
):
    """
    Search verified real hospitals.
    First tries live OpenStreetMap Overpass query if coordinates or city are given,
    then combines with verified global hospital registry.
    """
    results = []

    # Filter verified registry
    for h in VERIFIED_GLOBAL_HOSPITALS:
        matches = True
        if query:
            q_lower = query.lower().strip()
            text_corpus = f"{h['name']} {h['city']} {h['country']} {h['address']} {' '.join(h['specialties'])}".lower()
            if q_lower not in text_corpus:
                matches = False

        if matches and specialty:
            spec_lower = specialty.lower().strip()
            if not any(spec_lower in s.lower() for s in h["specialties"]):
                matches = False

        if matches:
            results.append(h)

    # If coordinates given and Overpass API query is desired:
    if lat and lon and len(results) < 5:
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                overpass_query = f"""
                [out:json][timeout:3];
                (
                  node["amenity"="hospital"](around:25000,{lat},{lon});
                  way["amenity"="hospital"](around:25000,{lat},{lon});
                );
                out center 10;
                """
                resp = await client.post(
                    "https://overpass-api.de/api/interpreter",
                    data={"data": overpass_query},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for elem in data.get("elements", []):
                        tags = elem.get("tags", {})
                        name = tags.get("name")
                        if not name:
                            continue
                        elem_lat = elem.get("lat") or elem.get("center", {}).get("lat")
                        elem_lon = elem.get("lon") or elem.get("center", {}).get("lon")
                        results.append({
                            "id": f"osm-{elem.get('id')}",
                            "name": name,
                            "city": tags.get("addr:city", "Local Area"),
                            "country": tags.get("addr:country", ""),
                            "address": tags.get("addr:street", tags.get("address", "Local Medical Facility")),
                            "type": tags.get("healthcare", "Hospital"),
                            "emergency": tags.get("emergency") == "yes",
                            "phone": tags.get("phone", tags.get("contact:phone", "Consult local directory")),
                            "specialties": ["Emergency Care", "General Medicine"],
                            "lat": elem_lat,
                            "lon": elem_lon,
                            "website": tags.get("website", ""),
                        })
        except Exception as e:
            logger.info("Overpass API query skipped or timed out: %s", e)

    return {
        "count": len(results),
        "query": query,
        "results": results,
    }
