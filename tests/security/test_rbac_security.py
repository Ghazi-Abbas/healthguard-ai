
# import pytest

# from fastapi import HTTPException

# from app.api.dependencies import require_permission
# from app.core.permission import Permission


# def create_user(role):
#     class MockUser:
#         pass

#     user = MockUser()
#     user.role = role

#     return user


# def test_provider_can_create_authorization():
#     user = create_user("PROVIDER")

#     permission_checker = require_permission(
#         Permission.CREATE_AUTHORIZATION
#     )

#     result = permission_checker(current_user=user)

#     assert result == user


# def test_reviewer_can_approve_case():
#     user = create_user("REVIEWER")

#     permission_checker = require_permission(
#         Permission.APPROVE
#     )

#     result = permission_checker(current_user=user)

#     assert result == user


# def test_admin_can_manage_users():
#     user = create_user("ADMIN")

#     permission_checker = require_permission(
#         Permission.MANAGE_USERS
#     )

#     result = permission_checker(current_user=user)

#     assert result == user


# def test_provider_cannot_approve_case():
#     user = create_user("PROVIDER")

#     permission_checker = require_permission(
#         Permission.APPROVE
#     )

#     with pytest.raises(HTTPException) as exc:
#         permission_checker(current_user=user)

#     assert exc.value.status_code == 403


# def test_reviewer_cannot_manage_users():
#     user = create_user("REVIEWER")

#     permission_checker = require_permission(
#         Permission.MANAGE_USERS
#     )

#     with pytest.raises(HTTPException) as exc:
#         permission_checker(current_user=user)

#     assert exc.value.status_code == 403


# def test_invalid_role_is_rejected():
#     user = create_user("UNKNOWN_ROLE")

#     permission_checker = require_permission(
#         Permission.APPROVE
#     )

#     with pytest.raises(HTTPException) as exc:
#         permission_checker(current_user=user)

#     assert exc.value.status_code == 403



import pytest

from app.ai.gateway.provider_authorization import (
    validate_task_provider_authorization,
)


def test_groq_rejects_phi():

    inputs = {
        "clinical_pages_json": "Synthetic patient record"
    }

    with pytest.raises(PermissionError):
        validate_task_provider_authorization(
            "clinical_evidence",
            inputs,
        )


def test_groq_rejects_pii():

    inputs = {
        "patient_name": "Synthetic Patient"
    }

    with pytest.raises(PermissionError):
        validate_task_provider_authorization(
            "clinical_evidence",
            inputs,
        )


def test_groq_rejects_secret():

    inputs = {
        "api_key": "test-secret"
    }

    with pytest.raises(PermissionError):
        validate_task_provider_authorization(
            "clinical_evidence",
            inputs,
        )


def test_groq_allows_internal():

    inputs = {
        "criteria_json": "Synthetic policy criteria"
    }

    result = validate_task_provider_authorization(
        "clinical_evidence",
        inputs,
    )

    assert result == inputs
