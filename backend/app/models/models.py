"""
MediRisk 2.0 — SQLAlchemy ORM Models
Phase 3: Database Foundation

All models use:
- UUID primary keys (server-default via gen_random_uuid())
- UTC timestamps
- asyncpg-compatible PostgreSQL types
- SQLAlchemy 2.x Mapped[] typed columns
"""

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"


# ---------------------------------------------------------------------------
# Association table: user_roles
# ---------------------------------------------------------------------------


class UserRole(Base):
    """Many-to-many join table between users and roles."""

    __tablename__ = "user_roles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="user_roles")
    role: Mapped["Role"] = relationship("Role", back_populates="user_roles")


# ---------------------------------------------------------------------------
# users
# ---------------------------------------------------------------------------


class User(Base):
    """Application user account. Stores credentials only — no PII beyond email."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(
        String(320), nullable=False, unique=True, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    user_roles: Mapped[list["UserRole"]] = relationship(
        "UserRole", back_populates="user", cascade="all, delete-orphan"
    )
    profiles: Mapped[list["Profile"]] = relationship(
        "Profile", back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="user"
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"


# ---------------------------------------------------------------------------
# roles
# ---------------------------------------------------------------------------


class Role(Base):
    """Application roles (user, admin)."""

    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    user_roles: Mapped[list["UserRole"]] = relationship(
        "UserRole", back_populates="role", cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("name", name="uq_roles_name"),)

    def __repr__(self) -> str:
        return f"<Role name={self.name}>"


# ---------------------------------------------------------------------------
# profiles
# ---------------------------------------------------------------------------


class Profile(Base):
    """
    Clinical/demographic profile.
    A user may have multiple profiles (e.g., family members in a shared account).
    """

    __tablename__ = "profiles"
    __table_args__ = (Index("ix_profiles_user_id", "user_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    display_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    date_of_birth: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sex: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    height: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # cm
    weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # kg
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="profiles")
    assessments: Mapped[list["HealthAssessment"]] = relationship(
        "HealthAssessment", back_populates="profile", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Profile id={self.id} user_id={self.user_id}>"


# ---------------------------------------------------------------------------
# health_assessments
# ---------------------------------------------------------------------------


class HealthAssessment(Base):
    """
    A single multi-disease assessment session.
    input_data (JSONB) stores all submitted clinical/lifestyle features.
    Extensible: different disease schemas can be nested inside.
    """

    __tablename__ = "health_assessments"
    __table_args__ = (
        Index("ix_health_assessments_profile_id", "profile_id"),
        Index("ix_health_assessments_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
        default=uuid.uuid4,
    )
    profile_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="SET NULL"),
        nullable=True,
    )
    assessment_version: Mapped[str] = mapped_column(
        String(32), nullable=False, default="1.0"
    )
    assessment_mode: Mapped[str] = mapped_column(
        String(32), nullable=False, default="individual", server_default="individual"
    )
    input_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    profile: Mapped["Profile"] = relationship("Profile", back_populates="assessments")
    predictions: Mapped[list["DiseasePrediction"]] = relationship(
        "DiseasePrediction",
        back_populates="assessment",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<HealthAssessment id={self.id} profile_id={self.profile_id}>"


# ---------------------------------------------------------------------------
# disease_predictions
# ---------------------------------------------------------------------------


class DiseasePrediction(Base):
    """
    A single disease risk prediction result produced by the ML inference layer.
    One HealthAssessment produces N DiseasePredictions (one per disease evaluated).
    """

    __tablename__ = "disease_predictions"
    __table_args__ = (
        Index("ix_disease_predictions_assessment_id", "assessment_id"),
        Index("ix_disease_predictions_disease_code", "disease_code"),
        Index("ix_disease_predictions_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
        default=uuid.uuid4,
    )
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("health_assessments.id", ondelete="RESTRICT"),
        nullable=False,
    )
    disease_code: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # e.g. DIABETES, HEART_DISEASE
    model_name: Mapped[str] = mapped_column(String(64), nullable=False)
    model_version: Mapped[str] = mapped_column(String(32), nullable=False)
    raw_probability: Mapped[float] = mapped_column(Numeric(10, 8), nullable=False)
    calibrated_probability: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 8), nullable=True
    )
    risk_level: Mapped[str] = mapped_column(
        SAEnum(RiskLevel, name="risk_level_enum", create_type=True),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    assessment: Mapped["HealthAssessment"] = relationship(
        "HealthAssessment", back_populates="predictions"
    )
    attributions: Mapped[list["PredictionAttribution"]] = relationship(
        "PredictionAttribution",
        back_populates="prediction",
        cascade="all, delete-orphan",
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(
        "Recommendation",
        back_populates="prediction",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<DiseasePrediction id={self.id} disease={self.disease_code} risk={self.risk_level}>"


# ---------------------------------------------------------------------------
# prediction_attributions
# ---------------------------------------------------------------------------


class PredictionAttribution(Base):
    """
    Per-feature attribution values from the ML explainability layer (e.g., SHAP).
    Created after inference in Phase 7.
    """

    __tablename__ = "prediction_attributions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
        default=uuid.uuid4,
    )
    prediction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("disease_predictions.id", ondelete="CASCADE"),
        nullable=False,
    )
    feature_name: Mapped[str] = mapped_column(String(128), nullable=False)
    feature_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attribution_value: Mapped[float] = mapped_column(Numeric(12, 8), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationship
    prediction: Mapped["DiseasePrediction"] = relationship(
        "DiseasePrediction", back_populates="attributions"
    )

    def __repr__(self) -> str:
        return f"<PredictionAttribution feature={self.feature_name} value={self.attribution_value}>"


# ---------------------------------------------------------------------------
# recommendations
# ---------------------------------------------------------------------------


class Recommendation(Base):
    """Risk-aware recommendations linked to a specific disease prediction."""

    __tablename__ = "recommendations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
        default=uuid.uuid4,
    )
    prediction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("disease_predictions.id", ondelete="CASCADE"),
        nullable=False,
    )
    recommendation_code: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationship
    prediction: Mapped["DiseasePrediction"] = relationship(
        "DiseasePrediction", back_populates="recommendations"
    )

    def __repr__(self) -> str:
        return f"<Recommendation title={self.title} priority={self.priority}>"


# ---------------------------------------------------------------------------
# audit_logs
# ---------------------------------------------------------------------------


class AuditLog(Base):
    """
    Append-only audit event log.
    Tracks user actions for security monitoring and research accountability.
    """

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_user_id", "user_id"),
        Index("ix_audit_logs_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
        default=uuid.uuid4,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    resource_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    event_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationship
    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog action={self.action} user_id={self.user_id}>"


# ---------------------------------------------------------------------------
# refresh_tokens  (Phase 5 — Authentication)
# ---------------------------------------------------------------------------


class RefreshToken(Base):
    """
    Stores a revocable record for each issued refresh token.

    Design:
      - raw_token is NEVER stored.
      - token_hash: SHA-256 hex digest of the raw refresh JWT.
      - token_jti: the 'jti' claim from the JWT (UUID4 string).
      - revoked_at: set on logout or rotation; None = still valid.
      - Rotation: on every /refresh, old row is revoked and a new row created.
    """

    __tablename__ = "refresh_tokens"
    __table_args__ = (
        Index("ix_refresh_tokens_user_id", "user_id"),
        Index("ix_refresh_tokens_token_jti", "token_jti", unique=True),
        Index("ix_refresh_tokens_expires_at", "expires_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    token_jti: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")

    @property
    def is_revoked(self) -> bool:
        return self.revoked_at is not None

    @property
    def is_expired(self) -> bool:
        from datetime import timezone
        if self.expires_at is None:
            return False
        now = datetime.now(timezone.utc)
        expires_at = self.expires_at
        if expires_at.tzinfo is None:
            now = now.replace(tzinfo=None)
        return now > expires_at

    @property
    def is_valid(self) -> bool:
        return not self.is_revoked and not self.is_expired

    def __repr__(self) -> str:
        return f"<RefreshToken jti={self.token_jti} revoked={self.is_revoked}>"
