"""
MediRisk 2.0 — Alembic env.py
Configured for SQLAlchemy 2.x async engine with asyncpg.
"""

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# This is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# -----------------------------------------------------------------------
# Import Base and all models so autogenerate can detect them
# -----------------------------------------------------------------------
# Import Base first
from app.db.base import Base  # noqa: E402

# Import all models — this registers them against Base.metadata
import app.models  # noqa: E402, F401

target_metadata = Base.metadata

# -----------------------------------------------------------------------
# Override sqlalchemy.url from environment variable if present
# -----------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    # asyncpg driver URL
    config.set_main_option("sqlalchemy.url", DATABASE_URL)


# -----------------------------------------------------------------------
# Offline mode (generate SQL without live DB connection)
# -----------------------------------------------------------------------
def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


# -----------------------------------------------------------------------
# Online mode (async SQLAlchemy engine with asyncpg)
# -----------------------------------------------------------------------
def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
