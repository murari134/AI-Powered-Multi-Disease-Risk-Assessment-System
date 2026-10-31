"""
MediRisk 2.0 — Service Layer
Phase 4: Backend Core

Services coordinate repository calls and business logic.
No raw SQL, no ML inference, no TabPFN, no dataset generation.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import hash_password, verify_password
from app.models.models import AuditLog, HealthAssessment, Profile, User
from app.repositories.repositories import (
    AuditLogRepository,
    DiseasePredictionRepository,
    HealthAssessmentRepository,
    ProfileRepository,
    UserRepository,
)
from app.schemas.schemas import (
    HealthAssessmentCreate,
    ProfileCreate,
    ProfileUpdate,
    UserCreate,
)


# ---------------------------------------------------------------------------
# UserService
# ---------------------------------------------------------------------------

class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = UserRepository(session)
        self.session = session

    async def create_user(self, data: UserCreate) -> User:
        if await self.repo.email_exists(data.email):
            raise ConflictError(f"An account with email '{data.email}' already exists.")
        user = User(
            id=uuid.uuid4(),
            email=data.email,
            password_hash=hash_password(data.password),
            is_active=True,
        )
        created = await self.repo.create(user)
        await self.session.commit()
        return created

    async def get_user_by_id(self, user_id: uuid.UUID) -> User:
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User")
        return user

    async def authenticate(self, email: str, password: str) -> Optional[User]:
        """Verify credentials — returns User on success, None on failure."""
        user = await self.repo.get_by_email(email)
        if user is None or not user.is_active:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user


# ---------------------------------------------------------------------------
# ProfileService
# ---------------------------------------------------------------------------

class ProfileService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = ProfileRepository(session)
        self.audit = AuditService(session)
        self.session = session

    async def create_profile(
        self,
        user_id: uuid.UUID,
        data: ProfileCreate,
        *,
        request_id: str = "-",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Profile:
        profile = Profile(
            id=uuid.uuid4(),
            user_id=user_id,
            display_name=data.display_name,
            date_of_birth=data.date_of_birth,
            sex=data.sex,
            height=data.height,
            weight=data.weight,
        )
        created = await self.repo.create(profile)
        await self.session.commit()
        await self.session.refresh(created)

        await self.audit.log_event(
            "PROFILE_CREATED",
            user_id=user_id,
            resource_type="profile",
            resource_id=str(created.id),
            event_metadata={"profile_id": str(created.id), "request_id": request_id},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return created

    async def get_profile(
        self,
        profile_id: uuid.UUID,
        *,
        user_id: Optional[uuid.UUID] = None,
    ) -> Profile:
        if user_id is not None:
            profile = await self.repo.get_by_id_and_user_id(profile_id, user_id)
        else:
            profile = await self.repo.get_by_id(profile_id)
        if profile is None:
            raise NotFoundError("Profile")
        return profile

    async def list_profiles(self, user_id: uuid.UUID) -> Sequence[Profile]:
        return await self.repo.get_by_user_id(user_id)

    async def update_profile(
        self,
        profile_id: uuid.UUID,
        data: ProfileUpdate,
        *,
        user_id: Optional[uuid.UUID] = None,
        request_id: str = "-",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Profile:
        profile = await self.get_profile(profile_id, user_id=user_id)
        updates = data.model_dump(exclude_unset=True)
        for field, value in updates.items():
            setattr(profile, field, value)
        await self.session.commit()
        await self.session.refresh(profile)

        await self.audit.log_event(
            "PROFILE_UPDATED",
            user_id=profile.user_id,
            resource_type="profile",
            resource_id=str(profile.id),
            event_metadata={
                "profile_id": str(profile.id),
                "updated_fields": list(updates.keys()),
                "request_id": request_id,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return profile

    async def delete_profile(
        self,
        profile_id: uuid.UUID,
        *,
        user_id: Optional[uuid.UUID] = None,
        request_id: str = "-",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        profile = await self.get_profile(profile_id, user_id=user_id)
        owner_id = profile.user_id
        await self.repo.delete(profile)
        await self.session.commit()

        await self.audit.log_event(
            "PROFILE_DELETED",
            user_id=owner_id,
            resource_type="profile",
            resource_id=str(profile_id),
            event_metadata={"profile_id": str(profile_id), "request_id": request_id},
            ip_address=ip_address,
            user_agent=user_agent,
        )


# ---------------------------------------------------------------------------
# AssessmentService
# ---------------------------------------------------------------------------

class AssessmentService:
    """
    Manages HealthAssessment persistence only.
    ML inference is NOT performed here — belongs to later phases.
    Immutability: Assessments cannot be modified after submission.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.profile_repo = ProfileRepository(session)
        self.repo = HealthAssessmentRepository(session)
        self.audit = AuditService(session)
        self.session = session

    async def create_assessment(
        self,
        profile_id: uuid.UUID,
        data: HealthAssessmentCreate,
        *,
        user_id: Optional[uuid.UUID] = None,
        request_id: str = "-",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> HealthAssessment:
        if user_id is not None:
            profile = await self.profile_repo.get_by_id_and_user_id(profile_id, user_id)
            if profile is None:
                raise NotFoundError("Profile")
        else:
            profile = await self.profile_repo.get_by_id(profile_id)
            if profile is None:
                raise NotFoundError("Profile")

        assessment = HealthAssessment(
            id=uuid.uuid4(),
            profile_id=profile_id,
            assessment_version=data.assessment_version,
            input_data=data.input_data,
            created_at=datetime.now(timezone.utc),
        )
        created = await self.repo.create(assessment)
        await self.session.commit()
        await self.session.refresh(created)

        # Audit event: sensitive input_data is NEVER stored in audit metadata
        await self.audit.log_event(
            "ASSESSMENT_CREATED",
            user_id=profile.user_id,
            resource_type="health_assessment",
            resource_id=str(created.id),
            event_metadata={
                "profile_id": str(profile_id),
                "assessment_id": str(created.id),
                "assessment_version": created.assessment_version,
                "request_id": request_id,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return created

    async def get_assessment(
        self,
        assessment_id: uuid.UUID,
        *,
        profile_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        request_id: str = "-",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> HealthAssessment:
        if user_id is not None:
            if profile_id is None:
                raise NotFoundError("Profile")
            profile = await self.profile_repo.get_by_id_and_user_id(profile_id, user_id)
            if profile is None:
                raise NotFoundError("Profile")

        if profile_id is not None:
            assessment = await self.repo.get_by_id_and_profile_id(assessment_id, profile_id)
        else:
            assessment = await self.repo.get_by_id(assessment_id)

        if assessment is None:
            raise NotFoundError("HealthAssessment")

        await self.audit.log_event(
            "ASSESSMENT_VIEWED",
            user_id=user_id,
            resource_type="health_assessment",
            resource_id=str(assessment.id),
            event_metadata={
                "profile_id": str(assessment.profile_id),
                "assessment_id": str(assessment.id),
                "request_id": request_id,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return assessment

    async def list_assessments(
        self,
        profile_id: uuid.UUID,
        *,
        user_id: Optional[uuid.UUID] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[HealthAssessment], int]:
        if user_id is not None:
            profile = await self.profile_repo.get_by_id_and_user_id(profile_id, user_id)
            if profile is None:
                raise NotFoundError("Profile")

        items = await self.repo.get_by_profile_id(profile_id, limit=limit, offset=offset)
        total = await self.repo.count_by_profile_id(profile_id)
        return items, total


# ---------------------------------------------------------------------------
# PredictionService
# ---------------------------------------------------------------------------

class PredictionService:
    """
    Persistence abstraction for DiseasePrediction records.
    ML inference (TabPFN, TabICLv2, SHAP) will be added in Phase 6/7.
    This service MUST NOT invoke any model inference.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.repo = DiseasePredictionRepository(session)

    async def get_predictions_for_assessment(
        self, assessment_id: uuid.UUID
    ) -> Sequence[Any]:
        return await self.repo.get_by_assessment_id(assessment_id)


# ---------------------------------------------------------------------------
# AuditService
# ---------------------------------------------------------------------------

class AuditService:
    """Records security and application audit events."""

    def __init__(self, session: AsyncSession) -> None:
        self.repo = AuditLogRepository(session)
        self.session = session

    async def log_event(
        self,
        action: str,
        *,
        user_id: Optional[uuid.UUID] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        event_metadata: Optional[dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """
        Append an audit event.
        IMPORTANT: Never log passwords, password hashes, JWT tokens,
        or raw clinical assessment values.
        """
        log = AuditLog(
            id=uuid.uuid4(),
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            event_metadata=event_metadata,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        created = await self.repo.create(log)
        await self.session.commit()
        return created
