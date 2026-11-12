
import pytest
from langchain_core.runnables import RunnableLambda

from app.agents import policy_rag_agent as agent


def test_policy_criteria_extraction_blocks_phi_before_models():
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
        RunnableLambda(agent.validate_criteria_extraction_input)
        | agent.criteria_extraction_prompt
        | RunnableLambda(primary).with_fallbacks([
            RunnableLambda(fallback)
        ])
    )

    inputs = {
        "authorization_facts_json": '{"member_id": "SYNTHETIC123"}',
        "policy_evidence_json": '{"policy": "Synthetic policy evidence"}',
    }

    with pytest.raises(PermissionError):
        test_chain.invoke(inputs)

    assert calls["primary"] == 0
    assert calls["fallback"] == 0


def test_policy_criteria_extraction_validator_rejects_phi():
    inputs = {
        "authorization_facts_json": '{"member_id": "SYNTHETIC123"}',
        "policy_evidence_json": '{"policy": "Synthetic policy evidence"}',
    }

    with pytest.raises(PermissionError):
        agent.validate_criteria_extraction_input(inputs)
