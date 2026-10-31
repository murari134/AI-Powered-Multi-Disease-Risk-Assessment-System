"""
MediRisk 2.0 — Health Assessment Endpoints
Phase 6: User Profile & Health Assessment API

Endpoints:
  POST /api/v1/profiles/{profile_id}/assessments
  GET  /api/v1/profiles/{profile_id}/assessments
  GET  /api/v1/profiles/{profile_id}/assessments/{assessment_id}

Strict Immutability Rule:
  Assessments cannot be updated once created. No PATCH/PUT endpoint exists.

Ownership Hierarchy:
  authenticated_user -> profile_id -> assessment_id
  Access to profiles or assessments belonging to other users returns 404 Not Found.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_active_user
from app.models.models import User
from app.schemas.schemas import (
    HealthAssessmentCreate,
    HealthAssessmentListResponse,
    HealthAssessmentResponse,
)
from app.services.services import AssessmentService

router = APIRouter(prefix="/profiles/{profile_id}/assessments", tags=["Health Assessments"])


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _get_user_agent(request: Request) -> str:
    return request.headers.get("User-Agent", "unknown")


def _get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "-")


@router.post(
    "",
    response_model=HealthAssessmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new health assessment for a profile",
)
async def create_assessment(
    request: Request,
    profile_id: uuid.UUID,
    body: HealthAssessmentCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
) -> HealthAssessmentResponse:
    svc = AssessmentService(db)
    assessment = await svc.create_assessment(
        profile_id,
        body,
        user_id=current_user.id,
        request_id=_get_request_id(request),
        ip_address=_get_client_ip(request),
        user_agent=_get_user_agent(request),
    )
    return HealthAssessmentResponse.model_validate(assessment)


@router.get(
    "",
    response_model=HealthAssessmentListResponse,
    summary="List health assessments for a profile (paginated, newest first)",
)
async def list_assessments(
    profile_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    limit: int = Query(default=20, ge=1, le=100, description="Number of assessments to return"),
    offset: int = Query(default=0, ge=0, description="Number of assessments to skip"),
    db: AsyncSession = Depends(get_db),
) -> HealthAssessmentListResponse:
    svc = AssessmentService(db)
    items, total = await svc.list_assessments(
        profile_id,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )
    return HealthAssessmentListResponse(
        items=[HealthAssessmentResponse.model_validate(a) for a in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{assessment_id}",
    response_model=HealthAssessmentResponse,
    summary="Retrieve a single health assessment record by ID",
)
async def get_assessment(
    request: Request,
    profile_id: uuid.UUID,
    assessment_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
) -> HealthAssessmentResponse:
    svc = AssessmentService(db)
    assessment = await svc.get_assessment(
        assessment_id,
        profile_id=profile_id,
        user_id=current_user.id,
        request_id=_get_request_id(request),
        ip_address=_get_client_ip(request),
        user_agent=_get_user_agent(request),
    )
    return HealthAssessmentResponse.model_validate(assessment)
