import pytest

from app.agents import policy_rag_graph as agent


def test_answer_generation_rejects_phi():
    inputs = {
        "query": "Find applicable policy criteria",
        "evidence_json": '{"evidence": []}',
        "feedback_json": "{}",
    }

    with pytest.raises(PermissionError):
        agent.validate_answer_generation_input(inputs)


def test_answer_evaluation_rejects_phi():
    inputs = {
        "query": "Find applicable policy criteria",
        "evidence_json": '{"evidence": []}',
        "draft_json": '{"answer": "Synthetic answer"}',
    }

    with pytest.raises(PermissionError):
        agent.validate_answer_evaluation_input(inputs)


def test_embedding_provider_rejects_phi_before_retrieval(monkeypatch):
    calls = {"invoke": 0}

    class FakeRetriever:
        def invoke(self, query):
            calls["invoke"] += 1
            return []

    monkeypatch.setattr(
        agent,
        "get_hybrid_retriever",
        lambda **kwargs: FakeRetriever(),
    )

    state = {
        "organization_id": 1,
        "active_policy_version_ids": [1],
        "query": "Find applicable criteria",
    }

    with pytest.raises(PermissionError):
        agent.retrieve_evidence(state)

    assert calls["invoke"] == 0
