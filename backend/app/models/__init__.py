# MediRisk 2.0 Database Models — Phase 3 + Phase 5
# Import all models so Alembic autogenerate detects them via Base.metadata

from app.models.models import (  # noqa: F401
    AuditLog,
    DiseasePrediction,
    HealthAssessment,
    PredictionAttribution,
    Profile,
    Recommendation,
    RefreshToken,
    Role,
    RiskLevel,
    User,
    UserRole,
)
