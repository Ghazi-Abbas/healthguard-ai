
import pytest
from unittest.mock import MagicMock

from fastapi import HTTPException

from app.services.auth_service import AuthService


@pytest.fixture
def auth_service():
    db = MagicMock()
    user_repository = MagicMock()
    organization_repository = MagicMock()

    return AuthService(
        db=db,
        user_reposetory=user_repository,
        organ_reposetory=organization_repository,
    )


def test_valid_token_returns_active_user(auth_service, monkeypatch):
    user = MagicMock()
    user.id = 1
    user.is_active = True

    monkeypatch.setattr(
        "app.services.auth_service.validate_token",
        lambda token: {"sub": "1"},
    )

    auth_service.user_reposetory.get_by_id.return_value = user

    result = auth_service.get_current_user("valid-token")

    assert result == user


def test_invalid_token_is_rejected(auth_service, monkeypatch):
    monkeypatch.setattr(
        "app.services.auth_service.validate_token",
        lambda token: None,
    )

    with pytest.raises(HTTPException) as exc:
        auth_service.get_current_user("invalid-token")

    assert exc.value.status_code == 401


def test_malformed_user_id_is_rejected(auth_service, monkeypatch):
    monkeypatch.setattr(
        "app.services.auth_service.validate_token",
        lambda token: {"sub": "invalid-id"},
    )

    with pytest.raises(HTTPException) as exc:
        auth_service.get_current_user("malformed-token")

    assert exc.value.status_code == 401


def test_missing_user_is_rejected(auth_service, monkeypatch):
    monkeypatch.setattr(
        "app.services.auth_service.validate_token",
        lambda token: {"sub": "999"},
    )

    auth_service.user_reposetory.get_by_id.return_value = None

    with pytest.raises(HTTPException) as exc:
        auth_service.get_current_user("valid-token")

    assert exc.value.status_code == 401


def test_inactive_user_is_rejected(auth_service, monkeypatch):
    user = MagicMock()
    user.id = 1
    user.is_active = False

    monkeypatch.setattr(
        "app.services.auth_service.validate_token",
        lambda token: {"sub": "1"},
    )

    auth_service.user_reposetory.get_by_id.return_value = user

    with pytest.raises(HTTPException) as exc:
        auth_service.get_current_user("valid-token")

    assert exc.value.status_code == 401
