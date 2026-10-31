# MediRisk 2.0 — Phase 4 Backend Core Implementation Report

**Project**: MediRisk 2.0 — AI-Powered Multi-Disease Risk Assessment System  
**Phase**: 4 — FastAPI Backend Core  
**Date Completed**: 2026-09-25  
**Python**: 3.11.9 (venv) / Target: 3.12.4  
**FastAPI**: 0.115.0  
**Pydantic**: 2.13.5  

---

## 1. Backend Architecture

Layered architecture with clear separation of concerns:

```
Request → Middleware → Router → Endpoint → Service → Repository → ORM Model → DB
```

No raw SQL in endpoints. No business logic in repositories. No ML in services.

---

## 2. Folder Structure

```
backend/
├── alembic.ini
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 0001_initial_schema.py
├── pyproject.toml
├── requirements.txt
└── app/
    ├── main.py                          ← Application entry point
    ├── middleware.py                    ← RequestID + Logging middleware
    ├── core/
    │   ├── config.py                    ← pydantic-settings
    │   ├── security.py                  ← Argon2id + JWT (pwdlib + PyJWT)
    │   ├── exceptions.py                ← Centralized error handling
    │   ├── logging.py                   ← Structured logging + context var
    │   └── redis_client.py              ← Lazy async Redis abstraction
    ├── api/
    │   └── v1/
    │       ├── router.py                ← Central APIRouter (/api/v1)
    │       └── endpoints/
    │           └── health.py            ← GET /api/v1/health, /health/ready
    ├── models/
    │   ├── __init__.py
    │   └── models.py                    ← 9 SQLAlchemy ORM models (Phase 3)
    ├── schemas/
    │   ├── __init__.py
    │   └── schemas.py                   ← Pydantic v2 request/response schemas
    ├── repositories/
    │   ├── __init__.py
    │   ├── base.py                      ← Generic async CRUD base
    │   └── repositories.py              ← 7 typed repository classes
    ├── services/
    │   ├── __init__.py
    │   └── services.py                  ← 5 service classes
    ├── db/
    │   ├── base.py                      ← DeclarativeBase
    │   └── session.py                   ← Async engine + get_db()
    └── dependencies/
        └── __init__.py                  ← JWT deps, RBAC factory, limiter
```

---

## 3. Configuration System

- **Tool**: `pydantic-settings==2.5.2`
- **Source**: Environment variables + optional `.env` file
- **Categories**: App, Database, Redis, Security (JWT), CORS

| Variable | Purpose |
|---|---|
| `APP_NAME` | Application display name |
| `APP_VERSION` | Semantic version |
| `ENVIRONMENT` | `development` / `production` / `staging` |
| `DATABASE_URL` | PostgreSQL async URL |
| `REDIS_URL` | Redis connection URL |
| `JWT_SECRET_KEY` | HS256 signing key |
| `JWT_ALGORITHM` | Default `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Default `15` |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins |

No secrets committed. `.env` is gitignored.

---

## 4. Database Session Architecture

- **Engine**: `create_async_engine` with `pool_pre_ping=True`, pool_size=10, max_overflow=20
- **Sessions**: `async_sessionmaker` → `AsyncSession`
- **Dependency**: `get_db()` — yields one `AsyncSession` per request; auto-rolls-back on exception, auto-closes

```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

---

## 5. API Versioning

All endpoints prefixed with `/api/v1`.  
Central `APIRouter` in `app/api/v1/router.py`.  
Endpoint routers are `include_router()`'d — no inline route definitions on app.

| Endpoint | Method | Status |
|---|---|---|
| `/health` | GET | ✅ Live |
| `/api/v1/health` | GET | ✅ Live |
| `/api/v1/health/ready` | GET | ✅ Live (503 when DB/Redis offline) |

---

## 6. Error Handling

`app/core/exceptions.py` defines:

- `MediRiskException` hierarchy: `NotFoundError`, `ConflictError`, `AuthenticationError`, `AuthorizationError`, `ValidationError`, `ServiceUnavailableError`
- Registered FastAPI exception handlers
- Consistent JSON envelope: `{ code, message, request_id, details? }`

**Never exposed**: stack traces, DB passwords, JWT secrets, filesystem paths.

---

## 7. Request ID System

`RequestIDMiddleware` (Starlette `BaseHTTPMiddleware`):
- Accepts `X-Request-ID` or `X-Correlation-ID` from client
- Generates `uuid4()` if absent
- Sets `request.state.request_id`
- Sets `request_id_ctx_var` (ContextVar for logging)
- Returns `X-Request-ID` in every response header

Validated live: request ID echoed in both body and header simultaneously.

---

## 8. Logging

`app/core/logging.py`:
- `configure_logging()` — stdlib StreamHandler, ISO timestamp format
- `request_id_ctx_var` — `ContextVar[str]` propagated per-request
- `LoggingMiddleware` — logs `METHOD PATH → STATUS | Xms | req=ID`

**Not logged**: passwords, password hashes, JWT tokens, clinical assessment values.

---

## 9. CORS

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,   # from env, never ["*"]
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)
```

Disallowed origins are not echoed back (tested and validated).

---

## 10. Security Foundation

`app/core/security.py`:

| Function | Library | Description |
|---|---|---|
| `hash_password(plain)` | `pwdlib[argon2]` | Argon2id hash |
| `verify_password(plain, hash)` | `pwdlib[argon2]` | Constant-time compare |
| `create_access_token(sub)` | `PyJWT` | Signed JWT with `sub`, `iat`, `exp`, `jti`, `type` |
| `create_refresh_token(sub)` | `PyJWT` | Signed refresh JWT |
| `decode_access_token(token)` | `PyJWT` | Validates signature, expiry, type claim |
| `decode_refresh_token(token)` | `PyJWT` | Validates refresh token |

**No passlib. No python-jose.**

---

## 11. JWT Foundation

- Algorithm: `HS256`
- Claims: `sub`, `iat`, `exp`, `jti` (UUID4), `type` (`access` / `refresh`)
- Refresh token type is rejected by access-token decoder
- Expired tokens raise `jwt.ExpiredSignatureError`
- Invalid tokens raise `jwt.InvalidTokenError`

---

## 12. RBAC Foundation

`app/dependencies/__init__.py`:

```python
def require_role(*required_roles: str):
    """Dependency factory for endpoint-level role guards."""
    async def _check_roles(current_user=Depends(get_current_active_user)):
        user_role_names = {ur.role.name for ur in current_user.user_roles}
        if not user_role_names.intersection(set(required_roles)):
            raise AuthorizationError(...)
    return _check_roles
```

Roles: `user`, `admin`. Admin panel and business operations deferred to later phases.

---

## 13. Repository Layer

`app/repositories/repositories.py`:

| Class | Model | Extra Methods |
|---|---|---|
| `UserRepository` | `User` | `get_by_email`, `email_exists` |
| `RoleRepository` | `Role` | `get_by_name` |
| `ProfileRepository` | `Profile` | `get_by_user_id` |
| `HealthAssessmentRepository` | `HealthAssessment` | `get_by_profile_id` |
| `DiseasePredictionRepository` | `DiseasePrediction` | `get_by_assessment_id` |
| `RecommendationRepository` | `Recommendation` | `get_by_prediction_id` |
| `AuditLogRepository` | `AuditLog` | `get_by_user_id` |

All extend `BaseRepository[T]` with generic `get_by_id`, `get_all`, `create`, `delete`.

---

## 14. Service Layer

`app/services/services.py`:

| Service | Responsibility |
|---|---|
| `UserService` | Create user, authenticate, lookup |
| `ProfileService` | Create / update / list profiles |
| `AssessmentService` | Persist assessment sessions (no ML) |
| `PredictionService` | Read predictions (no inference) |
| `AuditService` | Append-only audit event recording |

No TabPFN, no TabICLv2, no SHAP, no training.

---

## 15. Redis Abstraction

`app/core/redis_client.py`:
- Lazy initialization — client created on first use
- `get_redis_client()` returns `None` safely if Redis is offline
- `ping_redis()` returns `bool` — never raises
- `close_redis()` called on application shutdown
- Structured to support caching, rate limiting, sessions in later phases

---

## 16. Tests Created

| File | Tests | Coverage |
|---|---|---|
| `tests/test_security.py` | 24 | Hashing, verification, JWT, schema safety |
| `tests/test_api.py` | 21 | Health, readiness, request ID, CORS, errors |
| `tests/test_database.py` | 52 | Phase 3 ORM structure (unchanged) |

---

## 17. Test Results

```
============================= 97 passed in 26.29s =============================

test_api.py          — 21 passed  ✅
test_database.py     — 52 passed  ✅  (Phase 3 — unchanged)
test_security.py     — 24 passed  ✅
```

Phase 3's 52 tests remain 100% passing.

---

## 18. PostgreSQL Live Validation — Pending Docker

PostgreSQL is not running in this environment.

| Validation | Status |
|---|---|
| ORM model structure | ✅ Validated (52 tests) |
| Alembic migration files | ✅ Created and syntactically valid |
| Live migration (`alembic upgrade head`) | ⏳ Pending Docker |
| Seed roles | ⏳ Pending Docker |
| Referential integrity live test | ⏳ Pending Docker |

**To run live validation when Docker is available:**
```bash
docker compose up -d postgres redis
cd backend
.venv/Scripts/python -m alembic upgrade head
.venv/Scripts/python ..\database\seeds\seed_roles.py
.venv/Scripts/python -m pytest tests/ -v
```

---

## 19. Commands Used

```bash
# Package installation
pip install "pwdlib[argon2]==0.2.0" "PyJWT[crypto]==2.9.0" "slowapi==0.1.9" "redis==5.0.8"
pip install "pydantic[email]"

# Tests
python -m pytest tests/ -v

# Live server validation
uvicorn app.main:app --host 127.0.0.1 --port 8001 --no-access-log

# Live endpoint tests
GET http://127.0.0.1:8001/health              → 200 {"status":"ok"}
GET http://127.0.0.1:8001/api/v1/health       → 200 {"status":"ok","request_id":"..."}
GET http://127.0.0.1:8001/api/v1/health/ready → 503 {"status":"degraded"}  (no Docker)
```

---

## 20. Warnings & Notes

| Item | Note |
|---|---|
| `asyncio_default_fixture_loop_scope` | Set to `"function"` in `pyproject.toml` — suppresses pytest-asyncio deprecation |
| Python version | venv uses 3.11.9 (installed); target spec is 3.12.4 — all packages compatible |
| `on_event("startup/shutdown")` | FastAPI deprecation warning for these decorators — will migrate to `lifespan` in Phase 5 |
| Redis 503 | Expected without Docker — application does NOT crash |
| PostgreSQL 503 | Expected without Docker — application does NOT crash |

---

## Phase 4 Compliance Checklist

| Requirement | Status |
|---|---|
| No old project (`Multi disease`) references | ✅ |
| No secrets committed | ✅ |
| No plaintext passwords | ✅ |
| No passlib | ✅ |
| No python-jose | ✅ |
| No SQLite | ✅ |
| No ML training | ✅ |
| No dataset generation | ✅ |
| No prediction implementation | ✅ |
| No frontend feature work | ✅ |
| Phase 3 tests still passing | ✅ 52/52 |
| FastAPI starts cleanly | ✅ |
| API versioning works | ✅ |
| Configuration works | ✅ |
| Security foundation works | ✅ |
| JWT utilities work | ✅ |
| Argon2 password hashing works | ✅ |
| Error handling works | ✅ |
| Request IDs work | ✅ |
| Logging foundation works | ✅ |
| Redis abstraction exists (no crash) | ✅ |
| Repository / service architecture exists | ✅ |
| 97 total tests passing | ✅ |

---

## Phase 4 Complete ✅

**Next Phase**: Phase 5 — Authentication API (login, register, token refresh, logout).
