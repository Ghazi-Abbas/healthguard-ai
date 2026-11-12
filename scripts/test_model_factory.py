
import pytest

from app.ai.gateway.model_factory import create_model


def test_create_model_rejects_empty_model_name():
    with pytest.raises(ValueError, match="Model name is missing"):
        create_model(
            provider="groq",
            model_name="",
        )


def test_create_model_rejects_unsupported_provider():
    with pytest.raises(ValueError, match="Unsupported AI provider"):
        create_model(
            provider="unsupported",
            model_name="test-model",
        )
