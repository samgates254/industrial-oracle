import secrets
import uuid

import pytest
from pydantic import ValidationError

from industrial_oracle.core.config import Settings, settings
from industrial_oracle.core.security import create_access_token, decode_access_token


def test_production_requires_jwt_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("JWT_SECRET", raising=False)
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        Settings(ENVIRONMENT="production", _env_file=None)


@pytest.mark.parametrize(
    "secret",
    [
        "weak",
        "a" * 48,
        "industrial-oracle-change-in-production-placeholder",
    ],
)
def test_production_rejects_weak_or_known_jwt_secret(secret: str) -> None:
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        Settings(ENVIRONMENT="production", JWT_SECRET=secret, _env_file=None)


def test_production_accepts_strong_jwt_secret() -> None:
    secret = secrets.token_urlsafe(48)

    configured = Settings(ENVIRONMENT="production", JWT_SECRET=secret, _env_file=None)

    assert configured.JWT_SECRET == secret


def test_development_without_secret_uses_ephemeral_key() -> None:
    first = Settings(ENVIRONMENT="development", JWT_SECRET="", _env_file=None)
    second = Settings(ENVIRONMENT="development", JWT_SECRET="", _env_file=None)

    assert len(first.JWT_SECRET.encode("utf-8")) >= 32
    assert first.JWT_SECRET != second.JWT_SECRET


def test_access_token_creation_and_verification(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "JWT_SECRET", secrets.token_urlsafe(48))
    user_id = uuid.uuid4()

    claims = decode_access_token(create_access_token(user_id, "user@example.test"))

    assert claims["sub"] == str(user_id)
    assert claims["email"] == "user@example.test"
    assert claims["exp"] > claims["iat"]
