
import pytest

from app.agents import policy_crag_graph as agent


def test_query_rewriting_rejects_phi():
    inputs = {
        "original_query": "Find applicable criteria",
        "current_query": "Search for procedure criteria",
        "case_context": '{"clinical_summary": "Synthetic data"}',
        "feedback_json": "{}",
    }

    with pytest.raises(PermissionError):
        agent.validate_query_rewriting_input(inputs)


def test_keyword_retrieval_does_not_call_external_embedding_provider(
    monkeypatch,
):
    calls = {"keyword": 0}

    def fake_keyword_retriever(**kwargs):
        calls["keyword"] += 1

        assert kwargs["search_query"] == "Find applicable criteria"
        assert kwargs["organization_id"] == 1
        assert kwargs["active_policy_version_ids"] == [1]

        return []

    monkeypatch.setattr(
        agent,
        "get_keyword_retriever",
        fake_keyword_retriever,
    )

    state = {
        "organization_id": 1,
        "active_policy_version_ids": [1],
        "query": "Find applicable criteria",
    }

    result = agent.retrieve_evidence(state)

    assert calls["keyword"] == 1
    assert result["evidence"] == []
