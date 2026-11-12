import pytest

from app.security.classification import DataClassification
from app.ai.gateway.provider_authorization import (
    is_provider_authorized,
)


@pytest.mark.parametrize(
    "provider",
    ["groq", "gemini", "google_embeddings"],
)
def test_providers_allow_public_data(provider):
    assert is_provider_authorized(
        provider,
        DataClassification.PUBLIC
    )


@pytest.mark.parametrize(
    "provider",
    ["groq", "gemini", "google_embeddings"],
)
def test_providers_allow_internal_data(provider):
    assert is_provider_authorized(
        provider,
        DataClassification.INTERNAL
    )


@pytest.mark.parametrize(
    "classification",
    [
        DataClassification.PII,
        DataClassification.PHI,
        DataClassification.SECRET,
    ],
)
def test_groq_blocks_sensitive_data(classification):
    assert not is_provider_authorized(
        "groq",
        classification
    )


def test_unknown_provider_is_rejected():
    assert not is_provider_authorized(
        "unknown_provider",
        DataClassification.PUBLIC
    )


def test_provider_name_is_case_insensitive():
    assert is_provider_authorized(
        "GROQ",
        DataClassification.PUBLIC
    )
