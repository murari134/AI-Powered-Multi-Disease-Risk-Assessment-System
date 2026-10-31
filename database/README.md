# MediRisk 2.0 — Database Module

## Overview

PostgreSQL 16.4 database foundation for MediRisk 2.0.

- **ORM**: SQLAlchemy 2.0.35 (async, Mapped[] typing)
- **Driver**: asyncpg 0.29.0
- **Migrations**: Alembic 1.13.3
- **DB**: PostgreSQL 16.4 (via Docker in development)

## Directory Structure

```
database/
├── README.md              # This file
├── migrations/            # Reserved for future raw SQL utilities
└── seeds/
    └── seed_roles.py      # Seeds initial roles (user, admin)

backend/
├── alembic.ini            # Alembic configuration
├── alembic/
│   ├── env.py             # Async engine env
│   ├── script.py.mako     # Migration template
│   └── versions/
│       └── 0001_initial_schema.py   # Initial migration
└── app/
    ├── db/
    │   ├── base.py        # DeclarativeBase
    │   └── session.py     # Async session factory
    └── models/
        ├── __init__.py    # Re-exports all models
        └── models.py      # All 9 ORM model classes
```

## Tables Created

| Table | Purpose |
|---|---|
| `users` | Authentication credentials |
| `roles` | Application roles |
| `user_roles` | M2M join: users ↔ roles |
| `profiles` | Clinical/demographic data |
| `health_assessments` | Assessment sessions with JSONB input |
| `disease_predictions` | ML inference results |
| `prediction_attributions` | SHAP/feature attribution values |
| `recommendations` | Risk-based recommendations |
| `audit_logs` | Append-only security event log |

## Running Migrations

Start PostgreSQL first (Docker Compose):

```bash
docker compose up -d postgres
```

Then apply migrations:

```bash
cd backend
.venv/Scripts/python -m alembic upgrade head
```

## Running Tests

```bash
cd backend
.venv/Scripts/python -m pytest tests/test_database.py -v
```

All 52 structural tests pass without a live database.
Tests marked `@pytest.mark.db` require PostgreSQL to be running.

## Full Schema Reference

See [docs/database-schema.md](../docs/database-schema.md).
