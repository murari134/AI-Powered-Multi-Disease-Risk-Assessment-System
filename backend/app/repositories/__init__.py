# MediRisk 2.0 — repositories package
from app.repositories.base import BaseRepository  # noqa: F401
from app.repositories.repositories import (  # noqa: F401
    AuditLogRepository,
    DiseasePredictionRepository,
    HealthAssessmentRepository,
    ProfileRepository,
    RecommendationRepository,
    RoleRepository,
    UserRepository,
)
