
import pytest

from app.agents import policy_crag_graph
from app.security.input_sanitizer import MAX_CRITERIA_SIZE


def test_grade_relevant_ignores_unknown_evidence_ids():

    state = {
        "query": "MRI documentation requirements",
        "search_query": "MRI documentation requirements",
        "evidence": [
            {
                "evidence_id": "E1",
                "text": "MRI documentation requirements must be met.",
            },
            {
                "evidence_id": "E2",
                "text": "Unrelated administrative information.",
            },
        ],
    }

    result = policy_crag_graph.grade_relevant(state)

    ids = result["retrieval_assessment"].relevant_evidence_ids

    assert ids == ["E1"]
    assert "E999" not in ids


def test_grade_relevant_rejects_oversized_evidence():

    state = {
        "query": "policy requirements",
        "evidence": [
            {
                "evidence_id": "E1",
                "text": "A" * MAX_CRITERIA_SIZE,
            }
        ],
    }

    with pytest.raises(ValueError, match="maximum allowed size"):
        policy_crag_graph.grade_relevant(state)


def test_rewrite_query_rejects_oversized_input():

    state = {
        "query": "A" * (
            policy_crag_graph.MAX_AUTHORIZATION_SIZE + 1
        ),
        "search_query": "MRI criteria",
        "query_history": ["MRI criteria"],
    }

    with pytest.raises(ValueError, match="maximum allowed size"):
        policy_crag_graph.rewrite_query(state)


def test_rewrite_query_handles_previously_used_query():

    state = {
        "query": "MRI criteria",
        "search_query": "MRI criteria",
        "query_history": [
            "MRI criteria",
            "magnetic resonance imaging criteria",
        ],
    }

    result = policy_crag_graph.rewrite_query(state)

    # The function must return a valid graph-state update.
    assert isinstance(result, dict)

    # It must not generate an unbounded sequence of repeated queries.
    assert result.get("fallback_reason") or result.get("search_query") != (
        "magnetic resonance imaging criteria"
    )
