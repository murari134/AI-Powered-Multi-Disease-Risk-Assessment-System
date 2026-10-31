"""
MediRisk 2.0 — Seed Script Phase 3
Seeds only structural roles: user, admin.
No patient data, no assessments, no predictions.
"""

import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.models.models import Role

INITIAL_ROLES = [
    {
        "name": "user",
        "description": "Standard platform user with access to their own assessments.",
    },
    {
        "name": "admin",
        "description": "Administrator with access to monitoring, users, and audit logs.",
    },
]


async def seed_roles(session: AsyncSession) -> None:
    from sqlalchemy import select
    for role_data in INITIAL_ROLES:
        result = await session.execute(
            select(Role).where(Role.name == role_data["name"])
        )
        existing = result.scalar_one_or_none()
        if not existing:
            role = Role(
                id=uuid.uuid4(),
                name=role_data["name"],
                description=role_data["description"],
            )
            session.add(role)
            print(f"  [SEED] Created role: {role_data['name']}")
        else:
            print(f"  [SEED] Role already exists: {role_data['name']}")
    await session.commit()


async def main() -> None:
    print("[SEED] Seeding structural roles...")
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        await seed_roles(session)
    await engine.dispose()
    print("[SEED] Done.")


if __name__ == "__main__":
    asyncio.run(main())
