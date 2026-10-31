"""
MediRisk 2.0 — RefreshToken Repository
Phase 5: Authentication API
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import RefreshToken
from app.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(RefreshToken, session)

    async def get_by_jti(self, jti: str) -> Optional[RefreshToken]:
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.token_jti == jti)
        )
        return result.scalar_one_or_none()

    async def get_by_hash(self, token_hash: str) -> Optional[RefreshToken]:
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def revoke_by_jti(self, jti: str) -> bool:
        """Mark a refresh token as revoked. Returns True if found and revoked."""
        record = await self.get_by_jti(jti)
        if record is None:
            return False
        record.revoked_at = datetime.now(timezone.utc)
        await self.session.flush()
        return True

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> int:
        """Revoke all non-expired, non-revoked refresh tokens for a user."""
        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > now,
            )
        )
        tokens = result.scalars().all()
        for token in tokens:
            token.revoked_at = now
        await self.session.flush()
        return len(tokens)

    async def touch(self, record: RefreshToken) -> None:
        """Update last_used_at to now."""
        record.last_used_at = datetime.now(timezone.utc)
        await self.session.flush()
