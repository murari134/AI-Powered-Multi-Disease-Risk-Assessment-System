"""
MediRisk 2.0 — Pydantic Schemas
Phase 4: Backend Core

Foundational request/response schemas.
password_hash is NEVER included in any response schema.
"""

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ---------------------------------------------------------------------------
# Shared base
# ---------------------------------------------------------------------------

class MediRiskBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ---------------------------------------------------------------------------
# Role schemas
# ---------------------------------------------------------------------------

class RoleRead(MediRiskBase):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    created_at: datetime


# ---------------------------------------------------------------------------
# User schemas
# ---------------------------------------------------------------------------

class UserCreate(MediRiskBase):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class UserUpdate(MediRiskBase):
    email: Optional[EmailStr] = None


class UserRead(MediRiskBase):
    """Public user representation — password_hash is EXCLUDED."""
    id: uuid.UUID
    email: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    # password_hash intentionally omitted


# ---------------------------------------------------------------------------
# Profile schemas (Phase 6)
# ---------------------------------------------------------------------------

VALID_SEXES = {"male", "female", "other", "prefer_not_to_say", "intersex"}


class ProfileCreate(MediRiskBase):
    """
    Schema for creating a clinical/demographic profile.
    Note: Validation boundaries for height and weight are application-level
    data-quality constraints only, not clinical validity ranges.
    """
    display_name: Optional[str] = Field(None, max_length=128)
    date_of_birth: Optional[datetime] = None
    sex: Optional[str] = Field(None, max_length=32)
    height: Optional[float] = Field(
        None, ge=20.0, le=300.0, description="Height in cm (data-quality bound: 20-300)"
    )
    weight: Optional[float] = Field(
        None, ge=1.0, le=650.0, description="Weight in kg (data-quality bound: 1-650)"
    )

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v_stripped = v.strip()
        if not v_stripped:
            raise ValueError("display_name cannot be empty or whitespace only")
        return v_stripped

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is None:
            return v
        from datetime import timezone
        now = datetime.now(timezone.utc)
        v_aware = v if v.tzinfo else v.replace(tzinfo=timezone.utc)
        if v_aware > now:
            raise ValueError("date_of_birth cannot be in the future")
        if v_aware.year < 1900:
            raise ValueError("date_of_birth must be in or after the year 1900")
        return v

    @field_validator("sex")
    @classmethod
    def validate_sex(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        normalized = v.strip().lower()
        if normalized not in VALID_SEXES:
            raise ValueError(
                f"Invalid sex '{v}'. Allowed options: {', '.join(sorted(VALID_SEXES))}"
            )
        return normalized


class ProfileUpdate(MediRiskBase):
    """Schema for updating an existing profile."""
    display_name: Optional[str] = Field(None, max_length=128)
    date_of_birth: Optional[datetime] = None
    sex: Optional[str] = Field(None, max_length=32)
    height: Optional[float] = Field(
        None, ge=20.0, le=300.0, description="Height in cm (data-quality bound: 20-300)"
    )
    weight: Optional[float] = Field(
        None, ge=1.0, le=650.0, description="Weight in kg (data-quality bound: 1-650)"
    )

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v_stripped = v.strip()
        if not v_stripped:
            raise ValueError("display_name cannot be empty or whitespace only")
        return v_stripped

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is None:
            return v
        from datetime import timezone
        now = datetime.now(timezone.utc)
        v_aware = v if v.tzinfo else v.replace(tzinfo=timezone.utc)
        if v_aware > now:
            raise ValueError("date_of_birth cannot be in the future")
        if v_aware.year < 1900:
            raise ValueError("date_of_birth must be in or after the year 1900")
        return v

    @field_validator("sex")
    @classmethod
    def validate_sex(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        normalized = v.strip().lower()
        if normalized not in VALID_SEXES:
            raise ValueError(
                f"Invalid sex '{v}'. Allowed options: {', '.join(sorted(VALID_SEXES))}"
            )
        return normalized


class ProfileRead(MediRiskBase):
    id: uuid.UUID
    user_id: uuid.UUID
    display_name: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    sex: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    created_at: datetime
    updated_at: datetime


ProfileResponse = ProfileRead


# ---------------------------------------------------------------------------
# Health Assessment schemas (Phase 6)
# ---------------------------------------------------------------------------

SUPPORTED_ASSESSMENT_VERSIONS = {"1.0"}
MAX_ASSESSMENT_PAYLOAD_BYTES = 65536  # 64 KB


class HealthAssessmentCreate(MediRiskBase):
    """
    Health assessment submission envelope.
    Immutability rule: assessments cannot be updated once created.
    """
    profile_id: Optional[uuid.UUID] = None
    assessment_version: str = Field(
        "1.0", description="Assessment schema version, e.g. '1.0'"
    )
    input_data: dict[str, Any] = Field(
        ..., description="Clinical feature payload JSON object"
    )

    @field_validator("assessment_version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        v_clean = v.strip()
        if not v_clean:
            raise ValueError("assessment_version cannot be empty")
        if v_clean not in SUPPORTED_ASSESSMENT_VERSIONS:
            raise ValueError(
                f"Unsupported assessment_version '{v_clean}'. Supported versions: {', '.join(sorted(SUPPORTED_ASSESSMENT_VERSIONS))}"
            )
        return v_clean

    @field_validator("input_data")
    @classmethod
    def validate_input_data(cls, v: Any) -> dict[str, Any]:
        import json as _json
        if v is None:
            raise ValueError("input_data cannot be null")
        if not isinstance(v, dict):
            raise ValueError("input_data must be a JSON object (dictionary)")
        if len(v) == 0:
            raise ValueError("input_data cannot be an empty object")
        try:
            encoded = _json.dumps(v)
        except (TypeError, ValueError) as err:
            raise ValueError(f"input_data must be JSON-serializable: {err}")
        if len(encoded.encode("utf-8")) > MAX_ASSESSMENT_PAYLOAD_BYTES:
            raise ValueError(
                f"input_data payload exceeds maximum allowed size of {MAX_ASSESSMENT_PAYLOAD_BYTES} bytes"
            )
        return v


class HealthAssessmentRead(MediRiskBase):
    id: uuid.UUID
    profile_id: uuid.UUID
    assessment_version: str
    input_data: dict[str, Any]
    created_at: datetime


HealthAssessmentResponse = HealthAssessmentRead


class HealthAssessmentListResponse(MediRiskBase):
    items: list[HealthAssessmentResponse]
    total: int
    limit: int
    offset: int


# ---------------------------------------------------------------------------
# Disease Prediction schemas
# ---------------------------------------------------------------------------

class DiseasePredictionRead(MediRiskBase):
    id: uuid.UUID
    assessment_id: uuid.UUID
    disease_code: str
    model_name: str
    model_version: str
    raw_probability: float
    calibrated_probability: Optional[float] = None
    risk_level: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Recommendation schemas
# ---------------------------------------------------------------------------

class RecommendationRead(MediRiskBase):
    id: uuid.UUID
    prediction_id: uuid.UUID
    recommendation_code: Optional[str] = None
    title: str
    description: str
    priority: int
    created_at: datetime


# ---------------------------------------------------------------------------
# JWT / Token schemas
# ---------------------------------------------------------------------------

class TokenResponse(MediRiskBase):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Seconds until expiry")


# ---------------------------------------------------------------------------
# Standard API envelope
# ---------------------------------------------------------------------------

class ErrorDetail(MediRiskBase):
    field: Optional[str] = None
    message: str


class ErrorResponse(MediRiskBase):
    code: str
    message: str
    request_id: str
    details: Optional[list[ErrorDetail]] = None
