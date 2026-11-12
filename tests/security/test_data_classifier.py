
from app.security.data_classifier import get_highest_classification
from app.security.classification import DataClassification

import pytest

from app.security.classification import (
    DataClassification,
    classify_field,
)

from app.security.data_classifier import (
    get_highest_classification,
)


def test_public_data():
    data = {"public_description": "Public information"}

    assert get_highest_classification(data) == DataClassification.PUBLIC


def test_internal_data():
    data = {"organization_id": 10}

    assert get_highest_classification(data) == DataClassification.INTERNAL


def test_pii_data():
    data = {"email": "test@example.com"}

    assert get_highest_classification(data) == DataClassification.PII


def test_phi_data():
    data = {"member_id": "MEMBER123"}

    assert get_highest_classification(data) == DataClassification.PHI


def test_secret_data():
    data = {"password": "secret"}

    assert get_highest_classification(data) == DataClassification.SECRET


def test_nested_phi_data():
    data = {
        "organization_id": 10,
        "authorization": {
            "member_id": "MEMBER123",
            "clinical_summary": "Patient information"
        }
    }

    assert get_highest_classification(data) == DataClassification.PHI


def test_nested_list_with_phi():
    data = {
        "clinical_pages": [
            {"page_text": "Clinical information"}
        ]
    }

    assert get_highest_classification(data) == DataClassification.PHI


def test_empty_data_is_rejected():
    with pytest.raises(ValueError, match="non-empty dictionary"):
        get_highest_classification({})
