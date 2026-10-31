from fastapi import APIRouter

from app.api.v1.endpoints.assessments import router as assessments_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.profiles import router as profiles_router

from app.api.v1.endpoints.predictions import router as predictions_router

api_v1_router = APIRouter(prefix="/api/v1")

# Health
api_v1_router.include_router(health_router)

# Authentication (Phase 5)
api_v1_router.include_router(auth_router)

# Profiles & Health Assessments (Phase 6)
api_v1_router.include_router(profiles_router)
api_v1_router.include_router(assessments_router)

# Predictions, Diseases & Clinical Intelligence (Phase 8)
api_v1_router.include_router(predictions_router)

