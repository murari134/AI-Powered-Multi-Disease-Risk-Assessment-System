"""
MediRisk 2.0 — Phase 4 Security Tests
Tests: password hashing, verification, JWT creation/decoding, expiry, roles.
"""

import time
import uuid
from datetime import timedelta

import jwt
import pytest

from app.core.security import (
    TOKEN_TYPE_ACCESS,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.schemas.schemas import UserRead


# ---------------------------------------------------------------------------
# 1. Password hashing
# ---------------------------------------------------------------------------

class TestPasswordHashing:
    def test_hash_password_returns_string(self):
        hashed = hash_password("supersecret123")
        assert isinstance(hashed, str)

    def test_hash_is_not_plaintext(self):
        plain = "mysecretpassword"
        hashed = hash_password(plain)
        assert plain not in hashed

    def test_hashes_are_unique(self):
        """Argon2id salts are random — two hashes of same input differ."""
        hashed1 = hash_password("same_password")
        hashed2 = hash_password("same_password")
        assert hashed1 != hashed2

    def test_hash_contains_argon2_identifier(self):
        hashed = hash_password("anypassword")
        assert "$argon2" in hashed


# ---------------------------------------------------------------------------
# 2. Password verification
# ---------------------------------------------------------------------------

class TestPasswordVerification:
    def test_correct_password_verifies(self):
        plain = "correct_horse_battery_staple"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True

    def test_wrong_password_rejected(self):
        hashed = hash_password("right_password")
        assert verify_password("wrong_password", hashed) is False

    def test_empty_string_rejected(self):
        hashed = hash_password("correct")
        assert verify_password("", hashed) is False

    def test_gibberish_hash_returns_false(self):
        """verify_password must not raise on malformed hash input."""
        result = verify_password("any_password", "not_a_valid_hash_at_all")
        assert result is False


# ---------------------------------------------------------------------------
# 3. JWT creation
# ---------------------------------------------------------------------------

class TestJWTCreation:
    def test_create_access_token_returns_string(self):
        token = create_access_token(str(uuid.uuid4()))
        assert isinstance(token, str)
        assert len(token) > 0

    def test_access_token_has_three_parts(self):
        """JWT format: header.payload.signature"""
        token = create_access_token(str(uuid.uuid4()))
        assert token.count(".") == 2

    def test_access_token_encodes_subject(self):
        subject = str(uuid.uuid4())
        token = create_access_token(subject)
        payload = decode_access_token(token)
        assert payload["sub"] == subject

    def test_access_token_type_claim(self):
        token = create_access_token(str(uuid.uuid4()))
        payload = decode_access_token(token)
        assert payload["type"] == TOKEN_TYPE_ACCESS

    def test_access_token_has_jti(self):
        token = create_access_token(str(uuid.uuid4()))
        payload = decode_access_token(token)
        assert "jti" in payload
        assert len(payload["jti"]) > 0

    def test_extra_claims_embedded(self):
        token = create_access_token(
            str(uuid.uuid4()), extra_claims={"roles": ["user"]}
        )
        payload = decode_access_token(token)
        assert payload["roles"] == ["user"]

    def test_create_refresh_token_returns_string(self):
        token = create_refresh_token(str(uuid.uuid4()))
        assert isinstance(token, str)


# ---------------------------------------------------------------------------
# 4. JWT decoding
# ---------------------------------------------------------------------------

class TestJWTDecoding:
    def test_valid_token_decodes(self):
        subject = str(uuid.uuid4())
        token = create_access_token(subject)
        payload = decode_access_token(token)
        assert payload["sub"] == subject

    def test_expired_token_raises(self):
        token = create_access_token(
            str(uuid.uuid4()), expires_delta=timedelta(seconds=-1)
        )
        with pytest.raises(jwt.ExpiredSignatureError):
            decode_access_token(token)

    def test_invalid_signature_raises(self):
        token = create_access_token(str(uuid.uuid4()))
        tampered = token[:-4] + "XXXX"
        with pytest.raises(jwt.InvalidTokenError):
            decode_access_token(tampered)

    def test_garbage_token_raises(self):
        with pytest.raises(jwt.InvalidTokenError):
            decode_access_token("not.a.token")

    def test_empty_token_raises(self):
        with pytest.raises(jwt.InvalidTokenError):
            decode_access_token("")

    def test_refresh_token_not_accepted_as_access(self):
        """A refresh token must not pass the access-token decoder."""
        refresh_token = create_refresh_token(str(uuid.uuid4()))
        with pytest.raises(jwt.InvalidTokenError):
            decode_access_token(refresh_token)


# ---------------------------------------------------------------------------
# 5. Schema: password_hash not exposed
# ---------------------------------------------------------------------------

class TestUserReadSchemaDoesNotExposePasswordHash:
    def test_user_read_has_no_password_hash_field(self):
        """UserRead schema must NOT contain a password_hash field."""
        fields = UserRead.model_fields
        assert "password_hash" not in fields

    def test_user_read_has_no_password_field(self):
        """UserRead schema must NOT contain a raw password field."""
        fields = UserRead.model_fields
        assert "password" not in fields

    def test_user_read_contains_expected_fields(self):
        fields = set(UserRead.model_fields.keys())
        expected = {"id", "email", "is_active", "created_at", "updated_at"}
        assert expected.issubset(fields)
