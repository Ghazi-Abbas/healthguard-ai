from enum import Enum

class DataClassification(str,Enum):
    PUBLIC="PUBLIC"
    INTERNAL="INTERNAL"
    PII="PII"
    PHI="PHI"
    SECRET="SECRET"

FIELD_CLASSIFICATION={
    # PUBLIC
    "public_description": DataClassification.PUBLIC,

    # Internal
    "organization_id": DataClassification.INTERNAL,
    "role": DataClassification.INTERNAL,

    # Personal identifiers
    "email": DataClassification.PII,
    "phone": DataClassification.PII,
    "full_name": DataClassification.PII,
    "date_of_birth": DataClassification.PII,
    "address": DataClassification.PII,

    # Patient/authorization information
    "member_id": DataClassification.PHI,
    "diagnosis_code": DataClassification.PHI,
    "procedure_code": DataClassification.PHI,
    "clinical_summary": DataClassification.PHI,
    "medical_history": DataClassification.PHI,
    "document_text": DataClassification.PHI,
    "authorization_id": DataClassification.PHI,

    # Credentials and secrets
    "password": DataClassification.SECRET,
    "password_hash": DataClassification.SECRET,
    "jwt_secret_key": DataClassification.SECRET,
    "aws_secret_access_key": DataClassification.SECRET,
    "api_key": DataClassification.SECRET,

    # Additional patient and authorization information
    "clinical_pages": DataClassification.PHI,
    "coverage_records": DataClassification.PHI,
    "authorization": DataClassification.PHI,
    "case_context": DataClassification.PHI,
    "reviewer_notes": DataClassification.PHI,
    "policy_question": DataClassification.PHI,
    "page_text": DataClassification.PHI,
    "filename": DataClassification.INTERNAL,
    "patient_name": DataClassification.PII,
    "authorization_json": DataClassification.PHI,
    "clinical_pages_json": DataClassification.PHI,
    "criteria_json": DataClassification.INTERNAL,
    "authorization_facts_json": DataClassification.PHI,
    "eligibility_json": DataClassification.PHI,
    "policy_criteria_json": DataClassification.INTERNAL,
    "clinical_evidence_json": DataClassification.PHI,
    "clinical_missing_information_json": DataClassification.PHI,
    "authorization_facts_json": DataClassification.PHI,
    "policy_evidence_json": DataClassification.INTERNAL,
    "original_query": DataClassification.PHI,
    "current_query": DataClassification.PHI,
    "query": DataClassification.PHI,
    "search_query": DataClassification.PHI,
    "feedback_json": DataClassification.PHI,
    "evidence_json": DataClassification.PHI,
    "evidence_json": DataClassification.PHI,
    "draft_json": DataClassification.PHI,
    "feedback_json": DataClassification.PHI,
    "policy_document_text": DataClassification.INTERNAL,
    "has_active_policy_versions": DataClassification.INTERNAL,
    "clinical_page_count": DataClassification.INTERNAL,
}

def classify_field(field_name: str) -> DataClassification:
    """
    Return the configured classification for a fiel

    Unknown fields are rejected instead of defaulting
    to INTERNAL.
    """

    if not isinstance(field_name, str) or not field_name.strip():
        raise ValueError("Field name must be a non-empty string.")

    normalized_name = field_name.strip().lower()

    classification = FIELD_CLASSIFICATION.get(normalized_name)

    if classification is None:
        raise ValueError(
            f"Unknown data classification field: {normalized_name}"
        )

    return classification
