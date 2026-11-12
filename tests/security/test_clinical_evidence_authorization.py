
from langchain_core.runnables import RunnableLambda

from app.agents import clinical_evidence_agent as agent
from app.security.classification import DataClassification
from app.ai.gateway import provider_authorization

def test_phi_is_blocked_before_primary_and_fallback(monkeypatch):
    calls = {
        "primary": 0,
        "fallback": 0,
    }

    def primary_model(inputs):
        calls["primary"] += 1
        return "Primary response"

    def fallback_model(inputs):
        calls["fallback"] += 1
        return "Fallback response"

    model_with_fallback = RunnableLambda(
        primary_model
    ).with_fallbacks([
        RunnableLambda(fallback_model)
    ])

    test_chain = (
        RunnableLambda(agent.validate_clinical_evidence_input)
        | agent.clinical_evidence_prompt
        | model_with_fallback
    )

    inputs = {
        "authorization_json": '{"member_id": "SYNTHETIC123"}',
        "criteria_json": '{"criteria": []}',
        "clinical_pages_json": "Synthetic clinical information",
    }

    try:
        test_chain.invoke(inputs)
        assert False, "Expected PHI authorization to fail"
    except PermissionError:
        pass

    assert calls["primary"] == 0
    assert calls["fallback"] == 0


def test_authorized_data_reaches_primary_model(monkeypatch):
    calls = {
        "primary": 0,
        "fallback": 0,
    }

    def primary_model(inputs):
        calls["primary"] += 1
        return "Primary response"

    def fallback_model(inputs):
        calls["fallback"] += 1
        return "Fallback response"

    monkeypatch.setattr(
        provider_authorization,
        "get_highest_classification",
        lambda data: DataClassification.PUBLIC,
    )

    model_with_fallback = RunnableLambda(
        primary_model
    ).with_fallbacks([
        RunnableLambda(fallback_model)
    ])

    test_chain = (
        RunnableLambda(agent.validate_clinical_evidence_input)
        | agent.clinical_evidence_prompt
        | model_with_fallback
    )

    inputs = {
        "authorization_json": '{"public_description": "Example"}',
        "criteria_json": '{"public_description": "Example"}',
        "clinical_pages_json": "Public example",
    }

    result = test_chain.invoke(inputs)

    assert result == "Primary response"
    assert calls["primary"] == 1
    assert calls["fallback"] == 0
