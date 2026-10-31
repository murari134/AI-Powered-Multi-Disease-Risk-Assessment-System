"""
MediRisk 2.0 — Phase 3 Database Tests
Tests model imports, metadata, relationships, constraints, and JSONB/UUID.
These tests validate SQLAlchemy ORM structure without requiring a live DB.
Live DB tests (marked with @pytest.mark.db) require PostgreSQL 16 running.
"""

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import RelationshipProperty

from app.db.base import Base
from app.models.models import (
    AuditLog,
    DiseasePrediction,
    HealthAssessment,
    PredictionAttribution,
    Profile,
    Recommendation,
    RiskLevel,
    Role,
    User,
    UserRole,
)


# ---------------------------------------------------------------------------
# 1. Model imports and metadata detection
# ---------------------------------------------------------------------------

class TestModelImports:
    def test_all_models_importable(self):
        """All ORM model classes can be imported."""
        assert User is not None
        assert Role is not None
        assert UserRole is not None
        assert Profile is not None
        assert HealthAssessment is not None
        assert DiseasePrediction is not None
        assert PredictionAttribution is not None
        assert Recommendation is not None
        assert AuditLog is not None

    def test_all_tables_in_metadata(self):
        """All tables are registered in Base.metadata (9 Phase 3 tables + refresh_tokens)."""
        expected = {
            "users",
            "roles",
            "user_roles",
            "profiles",
            "health_assessments",
            "disease_predictions",
            "prediction_attributions",
            "recommendations",
            "audit_logs",
            "refresh_tokens",
        }
        actual = set(Base.metadata.tables.keys())
        assert expected == actual, f"Missing tables: {expected - actual}"

    def test_risk_level_enum_values(self):
        """RiskLevel enum contains the three expected values."""
        assert RiskLevel.LOW.value == "LOW"
        assert RiskLevel.MODERATE.value == "MODERATE"
        assert RiskLevel.HIGH.value == "HIGH"


# ---------------------------------------------------------------------------
# 2. Primary keys
# ---------------------------------------------------------------------------

class TestPrimaryKeys:
    @pytest.mark.parametrize("model,pk_name", [
        (User, "id"),
        (Role, "id"),
        (Profile, "id"),
        (HealthAssessment, "id"),
        (DiseasePrediction, "id"),
        (PredictionAttribution, "id"),
        (Recommendation, "id"),
        (AuditLog, "id"),
    ])
    def test_uuid_primary_key(self, model, pk_name):
        """Each model has a UUID primary key column named 'id'."""
        table = model.__table__
        pk_cols = [col.name for col in table.primary_key.columns]
        assert pk_name in pk_cols

    def test_user_role_composite_pk(self):
        """user_roles has composite PK of (user_id, role_id)."""
        table = UserRole.__table__
        pk_cols = {col.name for col in table.primary_key.columns}
        assert pk_cols == {"user_id", "role_id"}


# ---------------------------------------------------------------------------
# 3. Unique constraints
# ---------------------------------------------------------------------------

class TestUniqueConstraints:
    def test_user_email_unique(self):
        """users.email is unique (column-level unique=True or UniqueConstraint)."""
        table = User.__table__
        # Column-level unique
        if table.c.email.unique:
            return
        # Named UniqueConstraint
        unique_cols = {
            col.name
            for constraint in table.constraints
            if hasattr(constraint, "columns")
            and len(list(constraint.columns)) == 1
            and type(constraint).__name__ == "UniqueConstraint"
            for col in constraint.columns
        }
        assert "email" in unique_cols, "users.email is not marked as unique"

    def test_role_name_unique(self):
        """roles.name has a unique constraint."""
        table = Role.__table__
        unique_cols = {
            col.name
            for constraint in table.constraints
            if hasattr(constraint, "columns")
            and len(list(constraint.columns)) == 1
            and type(constraint).__name__ == "UniqueConstraint"
            for col in constraint.columns
        }
        assert "name" in unique_cols


# ---------------------------------------------------------------------------
# 4. Foreign keys
# ---------------------------------------------------------------------------

class TestForeignKeys:
    def test_user_role_user_fk(self):
        """user_roles.user_id references users.id."""
        fks = {fk.target_fullname for fk in UserRole.__table__.foreign_keys}
        assert "users.id" in fks

    def test_user_role_role_fk(self):
        """user_roles.role_id references roles.id."""
        fks = {fk.target_fullname for fk in UserRole.__table__.foreign_keys}
        assert "roles.id" in fks

    def test_profile_user_fk(self):
        """profiles.user_id references users.id."""
        fks = {fk.target_fullname for fk in Profile.__table__.foreign_keys}
        assert "users.id" in fks

    def test_assessment_profile_fk(self):
        """health_assessments.profile_id references profiles.id."""
        fks = {fk.target_fullname for fk in HealthAssessment.__table__.foreign_keys}
        assert "profiles.id" in fks

    def test_prediction_assessment_fk(self):
        """disease_predictions.assessment_id references health_assessments.id."""
        fks = {fk.target_fullname for fk in DiseasePrediction.__table__.foreign_keys}
        assert "health_assessments.id" in fks

    def test_attribution_prediction_fk(self):
        """prediction_attributions.prediction_id references disease_predictions.id."""
        fks = {fk.target_fullname for fk in PredictionAttribution.__table__.foreign_keys}
        assert "disease_predictions.id" in fks

    def test_recommendation_prediction_fk(self):
        """recommendations.prediction_id references disease_predictions.id."""
        fks = {fk.target_fullname for fk in Recommendation.__table__.foreign_keys}
        assert "disease_predictions.id" in fks

    def test_audit_log_user_fk(self):
        """audit_logs.user_id references users.id (nullable FK)."""
        fks = {fk.target_fullname for fk in AuditLog.__table__.foreign_keys}
        assert "users.id" in fks


# ---------------------------------------------------------------------------
# 5. Indexes
# ---------------------------------------------------------------------------

class TestIndexes:
    @pytest.mark.parametrize("model,index_name", [
        (User, "ix_users_email"),
        (Profile, "ix_profiles_user_id"),
        (HealthAssessment, "ix_health_assessments_profile_id"),
        (HealthAssessment, "ix_health_assessments_created_at"),
        (DiseasePrediction, "ix_disease_predictions_assessment_id"),
        (DiseasePrediction, "ix_disease_predictions_disease_code"),
        (DiseasePrediction, "ix_disease_predictions_created_at"),
        (AuditLog, "ix_audit_logs_user_id"),
        (AuditLog, "ix_audit_logs_created_at"),
    ])
    def test_index_exists(self, model, index_name):
        """Each expected index is defined on the table."""
        table = model.__table__
        index_names = {idx.name for idx in table.indexes}
        assert index_name in index_names, f"{index_name} not found in {model.__tablename__}"


# ---------------------------------------------------------------------------
# 6. Column nullability and JSONB
# ---------------------------------------------------------------------------

class TestColumns:
    def test_user_email_not_nullable(self):
        assert not User.__table__.c.email.nullable

    def test_user_password_hash_not_nullable(self):
        assert not User.__table__.c.password_hash.nullable

    def test_audit_log_user_id_nullable(self):
        """audit_logs.user_id is nullable (anonymous events allowed)."""
        assert AuditLog.__table__.c.user_id.nullable

    def test_health_assessment_input_data_jsonb(self):
        """health_assessments.input_data is JSONB."""
        from sqlalchemy.dialects.postgresql import JSONB
        col_type = type(HealthAssessment.__table__.c.input_data.type)
        assert col_type is JSONB

    def test_audit_log_metadata_jsonb(self):
        """audit_logs.metadata column (mapped as event_metadata) is JSONB."""
        from sqlalchemy.dialects.postgresql import JSONB
        col = AuditLog.__table__.c.get("metadata")
        assert col is not None, "Column 'metadata' not found in audit_logs table"
        assert type(col.type) is JSONB


# ---------------------------------------------------------------------------
# 7. ORM relationships
# ---------------------------------------------------------------------------

class TestRelationships:
    def _get_relationship_names(self, model):
        mapper = sa_inspect(model)
        return {rel.key for rel in mapper.relationships}

    def test_user_has_profiles_relationship(self):
        rels = self._get_relationship_names(User)
        assert "profiles" in rels

    def test_user_has_user_roles_relationship(self):
        rels = self._get_relationship_names(User)
        assert "user_roles" in rels

    def test_user_has_audit_logs_relationship(self):
        rels = self._get_relationship_names(User)
        assert "audit_logs" in rels

    def test_profile_has_assessments_relationship(self):
        rels = self._get_relationship_names(Profile)
        assert "assessments" in rels

    def test_assessment_has_predictions_relationship(self):
        rels = self._get_relationship_names(HealthAssessment)
        assert "predictions" in rels

    def test_prediction_has_attributions_relationship(self):
        rels = self._get_relationship_names(DiseasePrediction)
        assert "attributions" in rels

    def test_prediction_has_recommendations_relationship(self):
        rels = self._get_relationship_names(DiseasePrediction)
        assert "recommendations" in rels


# ---------------------------------------------------------------------------
# 8. UUID generation (Python-side)
# ---------------------------------------------------------------------------

class TestUUIDGeneration:
    def test_uuid4_generates_valid_uuid(self):
        new_id = uuid.uuid4()
        assert isinstance(new_id, uuid.UUID)
        assert new_id.version == 4

    def test_two_uuids_are_unique(self):
        id1 = uuid.uuid4()
        id2 = uuid.uuid4()
        assert id1 != id2


# ---------------------------------------------------------------------------
# 9. Model instantiation (no DB required)
# ---------------------------------------------------------------------------

class TestModelInstantiation:
    def test_user_can_be_instantiated(self):
        u = User(
            id=uuid.uuid4(),
            email="test@medirisk.test",
            password_hash="$argon2id$...",
            is_active=True,
        )
        assert u.email == "test@medirisk.test"
        assert u.is_active is True

    def test_role_can_be_instantiated(self):
        r = Role(id=uuid.uuid4(), name="user", description="Standard user.")
        assert r.name == "user"

    def test_profile_can_be_instantiated(self):
        uid = uuid.uuid4()
        p = Profile(id=uuid.uuid4(), user_id=uid, display_name="Test Profile")
        assert p.display_name == "Test Profile"
        assert p.user_id == uid

    def test_health_assessment_accepts_jsonb(self):
        payload = {
            "diabetes": {"glucose": 120, "bmi": 27.5},
            "hypertension": {"systolic_bp": 135, "diastolic_bp": 88},
        }
        a = HealthAssessment(
            id=uuid.uuid4(),
            profile_id=uuid.uuid4(),
            assessment_version="1.0",
            input_data=payload,
        )
        assert a.input_data["diabetes"]["glucose"] == 120

    def test_disease_prediction_risk_levels(self):
        for level in [RiskLevel.LOW, RiskLevel.MODERATE, RiskLevel.HIGH]:
            dp = DiseasePrediction(
                id=uuid.uuid4(),
                assessment_id=uuid.uuid4(),
                disease_code="DIABETES",
                model_name="TabPFN",
                model_version="9.0.0",
                raw_probability=0.45,
                risk_level=level,
            )
            assert dp.risk_level == level

    def test_audit_log_nullable_user_id(self):
        log = AuditLog(
            id=uuid.uuid4(),
            user_id=None,  # anonymous event
            action="SYSTEM_STARTUP",
            resource_type="system",
        )
        assert log.user_id is None

    def test_audit_log_accepts_jsonb_metadata(self):
        log = AuditLog(
            id=uuid.uuid4(),
            action="USER_LOGIN",
            event_metadata={"browser": "Chrome", "os": "Windows 11"},
        )
        assert log.event_metadata["browser"] == "Chrome"
