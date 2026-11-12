
import pytest
from langchain_core.runnables import RunnableLambda

from app.agents import critaria_risk_agent as agent


def test_criteria_risk_blocks_phi_before_models():
    calls = {
        "primary": 0,
        "fallback": 0,
    }

    def primary(inputs):
        calls["primary"] += 1
        return "Primary response"

    def fallback(inputs):
        calls["fallback"] += 1
        return "Fallback response"

    test_chain = (
        RunnableLambda(agent.validate_criteria_risk_input)
        | agent.criteria_risk_prompt
        | RunnableLambda(primary).with_fallbacks([
            RunnableLambda(fallback)
        ])
    )

    inputs = {
        "authorization_json": '{"member_id": "SYNTHETIC123"}',
        "eligibility_json": '{"status": "ELIGIBLE_FOR_REVIEW"}',
        "policy_criteria_json": '{"criteria": []}',
        "clinical_evidence_json": '{"evidence": []}',
        "clinical_missing_information_json": "[]",
    }

    with pytest.raises(PermissionError):
        test_chain.invoke(inputs)

    assert calls["primary"] == 0
    assert calls["fallback"] == 0


def test_criteria_risk_validator_rejects_phi():
    inputs = {
        "authorization_json": '{"member_id": "SYNTHETIC123"}',
        "eligibility_json": '{"status": "ELIGIBLE_FOR_REVIEW"}',
        "policy_criteria_json": '{"criteria": []}',
        "clinical_evidence_json": '{"evidence": []}',
        "clinical_missing_information_json": "[]",
    }

    with pytest.raises(PermissionError):
        agent.validate_criteria_risk_input(inputs)
