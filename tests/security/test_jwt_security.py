
from datetime import datetime, timedelta, timezone

from jose import jwt

from app.core.security import (
    create_access_token,
    validate_token,
)
from app.core.config import settings


def test_create_and_validate_access_token():
    token = create_access_token(
        user_id=1,
        organization_id=10,
        role="ADMIN",
    )

    payload = validate_token(token)

    assert payload is not None
    assert payload["sub"] == "1"
    assert payload["organization_id"] == 10
    assert payload["role"] == "ADMIN"


def test_expired_token_is_rejected():
    expired_time = datetime.now(timezone.utc) - timedelta(minutes=5)

    payload = {
        "sub": "1",
        "organization_id": 10,
        "role": "ADMIN",
        "exp": expired_time,
    }

    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    assert validate_token(token) is None


def test_tampered_token_is_rejected():
    token = create_access_token(
        user_id=1,
        organization_id=10,
        role="ADMIN",
    )

    tampered_token = token + "tampered"

    assert validate_token(tampered_token) is None
