
import pytest

from app.ai.gateway.provider_authorization import (
    validate_task_provider_authorization,
)


def test_central_authorization_rejects_phi():
    inputs = {
        "authorization_json": '{"member_id": "SYNTHETIC123"}',
    }

    with pytest.raises(PermissionError):
        validate_task_provider_authorization(
            task_name="supervisor",
            inputs=inputs,
        )


def test_central_authorization_rejects_unknown_task():
    with pytest.raises(ValueError):
        validate_task_provider_authorization(
            task_name="unknown_task",
            inputs={},
        )


def test_central_authorization_rejects_unknown_fallback(
    monkeypatch,
):
    from app.ai.gateway import provider_authorization as auth

    monkeypatch.setitem(
        auth.MODEL_REGISTRY,
        "test_task",
        {
            "provider": "groq",
            "fallbacks": ["unknown_provider"],
        },
    )

    with pytest.raises(PermissionError):
        auth.validate_task_provider_authorization(
            task_name="test_task",
            inputs={"public_description": "Test"},
        )


def test_central_authorization_allows_public_data():
    inputs = {
        "public_description": "General policy information",
    }

    result = validate_task_provider_authorization(
        task_name="supervisor",
        inputs=inputs,
    )

    assert result == inputs
