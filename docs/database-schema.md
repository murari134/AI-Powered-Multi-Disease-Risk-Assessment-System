# MediRisk 2.0 — Database Schema Reference

## Overview

PostgreSQL 16.4 · SQLAlchemy 2.0.35 · asyncpg 0.29.0 · Alembic 1.13.3

The database persists all user-generated clinical data, ML inference results,
recommendation outputs, and security audit events for MediRisk 2.0.

---

## Entity Relationship Summary

```
users ──┬── user_roles ─── roles
        │
        └── profiles ── health_assessments
                              │
                              └── disease_predictions
                                        │
                                        ├── prediction_attributions
                                        └── recommendations

users ──── audit_logs
```

---

## Table Reference

### `users`

Stores application credentials. No PII beyond email.

| Column | Type | Constraints |
|---|---|---|
| `id` | `UUID` | PK, `gen_random_uuid()` default |
| `email` | `VARCHAR(320)` | NOT NULL, UNIQUE, indexed |
| `password_hash` | `VARCHAR(512)` | NOT NULL |
| `is_active` | `BOOLEAN` | NOT NULL, default `true` |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, `now()` |

---

### `roles`

Application roles: `user`, `admin`.

| Column | Type | Constraints |
|---|---|---|
| `id` | `UUID` | PK |
| `name` | `VARCHAR(64)` | NOT NULL, UNIQUE |
| `description` | `TEXT` | nullable |
| `created_at` | `TIMESTAMPTZ` | NOT NULL |

---

### `user_roles`

Many-to-many join between `users` and `roles`.

| Column | Type | Constraints |
|---|---|---|
| `user_id` | `UUID` | PK, FK → `users.id` CASCADE DELETE |
| `role_id` | `UUID` | PK, FK → `roles.id` CASCADE DELETE |

---

### `profiles`

Clinical/demographic profile. One user → many profiles.

| Column | Type | Constraints |
|---|---|---|
| `id` | `UUID` | PK |
| `user_id` | `UUID` | NOT NULL, FK → `users.id` CASCADE DELETE, indexed |
| `display_name` | `VARCHAR(128)` | nullable |
| `date_of_birth` | `TIMESTAMPTZ` | nullable |
| `sex` | `VARCHAR(32)` | nullable |
| `height` | `FLOAT` | nullable (cm) |
| `weight` | `FLOAT` | nullable (kg) |
| `created_at` | `TIMESTAMPTZ` | NOT NULL |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL |

---

### `health_assessments`

Assessment session. `input_data` holds full feature payload (JSONB).

| Column | Type | Constraints |
|---|---|---|
| `id` | `UUID` | PK |
| `profile_id` | `UUID` | NOT NULL, FK → `profiles.id` RESTRICT, indexed |
| `assessment_version` | `VARCHAR(32)` | NOT NULL, default `'1.0'` |
| `input_data` | `JSONB` | NOT NULL |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, indexed |

---

### `disease_predictions`

ML inference result. One assessment → N predictions (one per disease).

| Column | Type | Constraints |
|---|---|---|
| `id` | `UUID` | PK |
| `assessment_id` | `UUID` | NOT NULL, FK → `health_assessments.id` RESTRICT, indexed |
| `disease_code` | `VARCHAR(64)` | NOT NULL, indexed |
| `model_name` | `VARCHAR(64)` | NOT NULL |
| `model_version` | `VARCHAR(32)` | NOT NULL |
| `raw_probability` | `NUMERIC(10,8)` | NOT NULL |
| `calibrated_probability` | `NUMERIC(10,8)` | nullable |
| `risk_level` | `risk_level_enum` | NOT NULL (LOW / MODERATE / HIGH) |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, indexed |

---

### `prediction_attributions`

Per-feature SHAP/attribution values from explainability layer.

| Column | Type | Constraints |
|---|---|---|
| `id` | `UUID` | PK |
| `prediction_id` | `UUID` | NOT NULL, FK → `disease_predictions.id` CASCADE DELETE |
| `feature_name` | `VARCHAR(128)` | NOT NULL |
| `feature_value` | `TEXT` | nullable |
| `attribution_value` | `NUMERIC(12,8)` | NOT NULL |
| `created_at` | `TIMESTAMPTZ` | NOT NULL |

---

### `recommendations`

Risk-aware recommendations linked to a prediction.

| Column | Type | Constraints |
|---|---|---|
| `id` | `UUID` | PK |
| `prediction_id` | `UUID` | NOT NULL, FK → `disease_predictions.id` CASCADE DELETE |
| `recommendation_code` | `VARCHAR(64)` | nullable |
| `title` | `VARCHAR(255)` | NOT NULL |
| `description` | `TEXT` | NOT NULL |
| `priority` | `INTEGER` | NOT NULL, default `5` |
| `created_at` | `TIMESTAMPTZ` | NOT NULL |

---

### `audit_logs`

Append-only security event log. `user_id` nullable for anonymous events.

| Column | Type | Constraints |
|---|---|---|
| `id` | `UUID` | PK |
| `user_id` | `UUID` | nullable, FK → `users.id` SET NULL, indexed |
| `action` | `VARCHAR(128)` | NOT NULL |
| `resource_type` | `VARCHAR(64)` | nullable |
| `resource_id` | `VARCHAR(128)` | nullable |
| `metadata` | `JSONB` | nullable (Python attr: `event_metadata`) |
| `ip_address` | `VARCHAR(45)` | nullable |
| `user_agent` | `VARCHAR(512)` | nullable |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, indexed |

---

## Indexes

| Table | Index Name | Columns |
|---|---|---|
| `users` | `ix_users_email` | `email` (unique) |
| `profiles` | `ix_profiles_user_id` | `user_id` |
| `health_assessments` | `ix_health_assessments_profile_id` | `profile_id` |
| `health_assessments` | `ix_health_assessments_created_at` | `created_at` |
| `disease_predictions` | `ix_disease_predictions_assessment_id` | `assessment_id` |
| `disease_predictions` | `ix_disease_predictions_disease_code` | `disease_code` |
| `disease_predictions` | `ix_disease_predictions_created_at` | `created_at` |
| `audit_logs` | `ix_audit_logs_user_id` | `user_id` |
| `audit_logs` | `ix_audit_logs_created_at` | `created_at` |

---

## Custom PostgreSQL Types

| Type | Kind | Values |
|---|---|---|
| `risk_level_enum` | ENUM | `LOW`, `MODERATE`, `HIGH` |

---

## Cascade / Delete Rules

| Relationship | Rule |
|---|---|
| `user_roles.user_id` → `users.id` | CASCADE DELETE |
| `user_roles.role_id` → `roles.id` | CASCADE DELETE |
| `profiles.user_id` → `users.id` | CASCADE DELETE |
| `health_assessments.profile_id` → `profiles.id` | RESTRICT |
| `disease_predictions.assessment_id` → `health_assessments.id` | RESTRICT |
| `prediction_attributions.prediction_id` → `disease_predictions.id` | CASCADE DELETE |
| `recommendations.prediction_id` → `disease_predictions.id` | CASCADE DELETE |
| `audit_logs.user_id` → `users.id` | SET NULL |

RESTRICT prevents accidental data loss of assessments and predictions.
CASCADE is used for child rows that are logically inseparable from the parent.

---

## Migration: Running Alembic

```bash
# Apply all migrations (requires PostgreSQL to be running)
cd backend
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/medirisk_db \
  .venv/Scripts/python -m alembic upgrade head

# Generate a new migration after ORM changes
.venv/Scripts/python -m alembic revision --autogenerate -m "describe_your_change"

# Rollback
.venv/Scripts/python -m alembic downgrade -1
```

## Seed Roles

```bash
cd backend
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/medirisk_db \
  .venv/Scripts/python ../database/seeds/seed_roles.py
```
