
from types import SimpleNamespace

import pytest

from app.agents import policy_rag_graph
from app.schemas.policy_rag import (
    PolicyAnswerDraft,
    PolicyAnswerEvaluation,
)


def make_draft(answer, citations):
    return PolicyAnswerDraft(
        answer=answer,
        citations=citations,
        criteria_support=[],
        missing_information=[],
        concise_rationale="Policy evidence supports the answer.",
    )


def make_evaluation(invalid_citations=None):
    return PolicyAnswerEvaluation(
        grounded=True,
        grounding_score=0.95,
        faithfulness_score=0.95,
        relevance_score=0.95,
        citation_valid=True,
        invalid_citations=invalid_citations or [],
        unsupported_claims=[],
        criteria_support=[],
        missing_information=[],
        concise_rationale="Evaluation completed.",
    )


def run_evaluation(monkeypatch, draft, evaluation=None):
    if evaluation is None:
        evaluation = make_evaluation()

    monkeypatch.setattr(
        policy_rag_graph,
        "evaluation_chain",
        SimpleNamespace(
            invoke=lambda inputs: evaluation
        ),
    )

    return policy_rag_graph.evaluate_answer({
        "draft": draft,
        "evidence": [
            {
                "evidence_id": "E1",
                "text": "The policy requires prior authorization.",
            }
        ],
        "query": "What does the policy require?",
    })


def test_valid_citations_are_accepted(monkeypatch):
    draft = make_draft(
        answer="Prior authorization is required [E1].",
        citations=["E1"],
    )

    result = run_evaluation(monkeypatch, draft)

    assert result["evaluation"].citation_valid is True
    assert result["evaluation"].invalid_citations == []


def test_unknown_evidence_id_is_rejected(monkeypatch):
    draft = make_draft(
        answer="The policy requires approval [E99].",
        citations=["E99"],
    )

    result = run_evaluation(monkeypatch, draft)

    assert result["evaluation"].citation_valid is False
    assert "E99" in result["evaluation"].invalid_citations


def test_missing_declared_citation_is_rejected(monkeypatch):
    draft = make_draft(
        answer="Prior authorization is required [E1].",
        citations=[],
    )

    result = run_evaluation(monkeypatch, draft)

    assert result["evaluation"].citation_valid is False
    assert "E1" in result["evaluation"].invalid_citations


def test_unused_declared_citation_is_rejected(monkeypatch):
    draft = make_draft(
        answer="Prior authorization is required.",
        citations=["E1"],
    )

    result = run_evaluation(monkeypatch, draft)

    assert result["evaluation"].citation_valid is False
    assert "E1" in result["evaluation"].invalid_citations


def test_evaluator_invalid_citation_is_rejected(monkeypatch):
    draft = make_draft(
        answer="Prior authorization is required [E1].",
        citations=["E1"],
    )

    evaluation = make_evaluation(
        invalid_citations=["E1"]
    )

    result = run_evaluation(
        monkeypatch,
        draft,
        evaluation,
    )

    assert result["evaluation"].citation_valid is False
    assert "E1" in result["evaluation"].invalid_citations
