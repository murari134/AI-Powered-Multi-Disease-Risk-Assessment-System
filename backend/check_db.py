import asyncio
from app.db.session import engine
from sqlalchemy import text

async def update_schema():
    async with engine.begin() as conn:
        await conn.execute(text("ALTER TABLE health_assessments ALTER COLUMN profile_id DROP NOT NULL;"))
        print("Successfully made profile_id nullable in health_assessments!")

asyncio.run(update_schema())
