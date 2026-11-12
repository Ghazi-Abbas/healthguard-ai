from app.security.classification import (
    DataClassification,
    classify_field,
)
import pytest

from app.security.phi import is_phi_field


def test_member_id_is_phi():
    assert is_phi_field("member_id") is True


def test_clinical_pages_are_phi():
    assert is_phi_field("clinical_pages") is True


def test_email_is_pii():
    assert classify_field("email") == DataClassification.PII


def test_password_is_secret():
    assert classify_field("password") == DataClassification.SECRET


def test_organization_id_is_internal():
    assert classify_field("organization_id") == DataClassification.INTERNAL


def test_unknown_field_is_rejected():
    with pytest.raises(ValueError, match="Unknown data classification"):
        classify_field("unknown_field")

def test_policy_question_is_phi():
    assert is_phi_field("policy_question") is True


def test_field_names_are_case_insensitive():
    assert classify_field("EMAIL") == DataClassification.PII
