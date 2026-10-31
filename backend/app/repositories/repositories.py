"""
MediRisk 2.0 — Repository Implementations
Phase 4: Backend Core
"""

import uuid
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    AuditLog,
    DiseasePrediction,
    HealthAssessment,
    Profile,
    Recommendation,
    Role,
    User,
)
from app.repositories.base import BaseRepository


# ---------------------------------------------------------------------------
# UserRepository
# ---------------------------------------------------------------------------

class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        return await self.get_by_email(email) is not None


# ---------------------------------------------------------------------------
# RoleRepository
# ---------------------------------------------------------------------------

class RoleRepository(BaseRepository[Role]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Role, session)

    async def get_by_name(self, name: str) -> Optional[Role]:
        result = await self.session.execute(
            select(Role).where(Role.name == name)
        )
        return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# ProfileRepository
# ---------------------------------------------------------------------------

class ProfileRepository(BaseRepository[Profile]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Profile, session)

    async def get_by_user_id(self, user_id: uuid.UUID) -> Sequence[Profile]:
        result = await self.session.execute(
            select(Profile).where(Profile.user_id == user_id).order_by(Profile.created_at.asc())
        )
        return result.scalars().all()

    async def get_by_id_and_user_id(
        self, profile_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[Profile]:
        result = await self.session.execute(
            select(Profile).where(
                Profile.id == profile_id,
                Profile.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# HealthAssessmentRepository
# ---------------------------------------------------------------------------

class HealthAssessmentRepository(BaseRepository[HealthAssessment]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(HealthAssessment, session)

    async def get_by_id_and_profile_id(
        self, assessment_id: uuid.UUID, profile_id: uuid.UUID
    ) -> Optional[HealthAssessment]:
        result = await self.session.execute(
            select(HealthAssessment).where(
                HealthAssessment.id == assessment_id,
                HealthAssessment.profile_id == profile_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_profile_id(
        self, profile_id: uuid.UUID, *, limit: int = 50, offset: int = 0
    ) -> Sequence[HealthAssessment]:
        result = await self.session.execute(
            select(HealthAssessment)
            .where(HealthAssessment.profile_id == profile_id)
            .order_by(HealthAssessment.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def count_by_profile_id(self, profile_id: uuid.UUID) -> int:
        from sqlalchemy import func
        result = await self.session.execute(
            select(func.count(HealthAssessment.id)).where(
                HealthAssessment.profile_id == profile_id
            )
        )
        return result.scalar_one() or 0


# ---------------------------------------------------------------------------
# DiseasePredictionRepository
# ---------------------------------------------------------------------------

class DiseasePredictionRepository(BaseRepository[DiseasePrediction]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(DiseasePrediction, session)

    async def get_by_assessment_id(
        self, assessment_id: uuid.UUID
    ) -> Sequence[DiseasePrediction]:
        result = await self.session.execute(
            select(DiseasePrediction).where(
                DiseasePrediction.assessment_id == assessment_id
            )
        )
        return result.scalars().all()


# ---------------------------------------------------------------------------
# RecommendationRepository
# ---------------------------------------------------------------------------

class RecommendationRepository(BaseRepository[Recommendation]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Recommendation, session)

    async def get_by_prediction_id(
        self, prediction_id: uuid.UUID
    ) -> Sequence[Recommendation]:
        result = await self.session.execute(
            select(Recommendation)
            .where(Recommendation.prediction_id == prediction_id)
            .order_by(Recommendation.priority.asc())
        )
        return result.scalars().all()


# ---------------------------------------------------------------------------
# AuditLogRepository
# ---------------------------------------------------------------------------

class AuditLogRepository(BaseRepository[AuditLog]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(AuditLog, session)

    async def get_by_user_id(
        self, user_id: uuid.UUID, *, limit: int = 100
    ) -> Sequence[AuditLog]:
        result = await self.session.execute(
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
