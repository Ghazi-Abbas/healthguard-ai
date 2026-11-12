
import pytest

from app.agents.clinical_evidence_agent import (
    build_mock_clinical_evidence_chain,
)
from app.schemas.clinical_evidence import ClinicalEvidenceResult


def test_clinical_evidence_mock_with_phi():

    response = {
        "finding": [
            {
                "criterion_id": "C001",
                "criterion": "Clinical documentation",
                "eviedence_status": "FOUND",
                "evodence_summatry": "Synthetic test evidence.",
                "supporting_evidence_ids": ["DOC001"],
                "missing_information": [],
            }
        ],
        "overall_missing_information": [],
    }

    inputs = {
        "authorization_json": "Synthetic authorization",
        "criteria_json": "Synthetic policy criteria",
        "clinical_pages_json": "Synthetic clinical document",
    }

    chain = build_mock_clinical_evidence_chain(response)

    result = chain.invoke(inputs)

    assert isinstance(result, ClinicalEvidenceResult)
    assert result.finding[0].criterion_id == "C001"


def test_clinical_evidence_mock_rejects_secret():

    response = {
        "finding": [],
        "overall_missing_information": [],
    }

    inputs = {
        "authorization_json": "Synthetic authorization",
        "criteria_json": "Synthetic policy criteria",
        "clinical_pages_json": "Synthetic clinical document",
        "api_key": "test-secret",
    }

    chain = build_mock_clinical_evidence_chain(response)

    with pytest.raises(PermissionError):
        chain.invoke(inputs)
