"""
MediRisk 2.0 — User Profile Endpoints
Phase 6: User Profile & Health Assessment API

Endpoints:
  POST   /api/v1/profiles
  GET    /api/v1/profiles
  GET    /api/v1/profiles/{profile_id}
  PATCH  /api/v1/profiles/{profile_id}
  DELETE /api/v1/profiles/{profile_id}

All endpoints require authentication and enforce strict ownership:
authenticated_user.id == profile.user_id
"""

import uuid
from typing import Annotated, Sequence

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_active_user
from app.models.models import User
from app.schemas.schemas import (
    ProfileCreate,
    ProfileResponse,
    ProfileUpdate,
)
from app.services.services import ProfileService

router = APIRouter(prefix="/profiles", tags=["Profiles"])


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
    response_model=ProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new profile for the authenticated user",
)
async def create_profile(
    request: Request,
    body: ProfileCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    svc = ProfileService(db)
    profile = await svc.create_profile(
        current_user.id,
        body,
        request_id=_get_request_id(request),
        ip_address=_get_client_ip(request),
        user_agent=_get_user_agent(request),
    )
    return ProfileResponse.model_validate(profile)


@router.get(
    "",
    response_model=list[ProfileResponse],
    summary="List all profiles owned by the authenticated user",
)
async def list_profiles(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
) -> list[ProfileResponse]:
    svc = ProfileService(db)
    profiles = await svc.list_profiles(current_user.id)
    return [ProfileResponse.model_validate(p) for p in profiles]


@router.get(
    "/{profile_id}",
    response_model=ProfileResponse,
    summary="Retrieve a specific profile owned by the authenticated user",
)
async def get_profile(
    profile_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    svc = ProfileService(db)
    profile = await svc.get_profile(profile_id, user_id=current_user.id)
    return ProfileResponse.model_validate(profile)


@router.patch(
    "/{profile_id}",
    response_model=ProfileResponse,
    summary="Update a profile owned by the authenticated user",
)
async def update_profile(
    request: Request,
    profile_id: uuid.UUID,
    body: ProfileUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    svc = ProfileService(db)
    profile = await svc.update_profile(
        profile_id,
        body,
        user_id=current_user.id,
        request_id=_get_request_id(request),
        ip_address=_get_client_ip(request),
        user_agent=_get_user_agent(request),
    )
    return ProfileResponse.model_validate(profile)


@router.delete(
    "/{profile_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a profile owned by the authenticated user",
)
async def delete_profile(
    request: Request,
    profile_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
) -> None:
    svc = ProfileService(db)
    await svc.delete_profile(
        profile_id,
        user_id=current_user.id,
        request_id=_get_request_id(request),
        ip_address=_get_client_ip(request),
        user_agent=_get_user_agent(request),
    )
