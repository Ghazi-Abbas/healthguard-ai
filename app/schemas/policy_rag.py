
from typing import Literal

from pydantic import BaseModel, Field


# --------------------------------------------------
# 1. Policy Criteria Support
# --------------------------------------------------

class CriteriaSupport(BaseModel):

    criterion: str = Field(
        description="A policy criterion being discussed."
    )

    status: Literal[
        "supported_by_policy",
        "not_found_in_policy",
        "conflicting_policy_evidence",
        "insufficient_information"
    ] = Field(
        description=(
            "How the retrieved policy evidence addresses this criterion. "
            "This does not represent the patient's approval decision."
        )
    )

    note: str = Field(
        description="A concise, evidence-based explanation."
    )


# --------------------------------------------------
# 2. Policy Answer Draft
# --------------------------------------------------

class PolicyAnswerDraft(BaseModel):

    answer: str = Field(
        description=(
            "A concise answer based only on retrieved policy evidence. "
            "Use inline references such as [E1] for factual claims."
        )
    )

    citations: list[str] = Field(
        description=(
            "Exact evidence IDs cited in the answer, without brackets."
        )
    )

    criteria_support: list[CriteriaSupport] = Field(
        description="Policy-level support for the discussed criteria."
    )

    missing_information: list[str] = Field(
        description="Information needed but absent from the evidence."
    )

    concise_rationale: str = Field(
        description="A short, user-facing explanation."
    )


# --------------------------------------------------
# 3. Policy Answer Evaluation
# --------------------------------------------------

class PolicyAnswerEvaluation(BaseModel):

    grounded: bool = Field(
        description=(
            "True when material factual claims are supported by the "
            "supplied evidence, or insufficient evidence is acknowledged."
        )
    )

    grounding_score: float = Field(
        ge=0,
        le=1,
        description=(
            "Estimated degree to which the answer is supported "
            "by retrieved evidence."
        )
    )

    faithfulness_score: float = Field(
        ge=0,
        le=1,
        description=(
            "Estimated consistency of the answer with the meaning "
            "of the supplied policy evidence."
        )
    )

    relevance_score: float = Field(
        ge=0,
        le=1,
        description=(
            "Estimated degree to which the answer addresses the question."
        )
    )

    citation_valid: bool = Field(
        description=(
            "Whether cited sources exist and support the claims "
            "for which they are cited."
        )
    )

    invalid_citations: list[str] = Field(
        default_factory=list,
        description="Evidence references that are invalid."
    )

    unsupported_claims: list[str] = Field(
        default_factory=list,
        description="Claims not supported by the supplied evidence."
    )

    criteria_support: list[CriteriaSupport] = Field(
        default_factory=list,
        description="Evaluation of policy support for each criterion."
    )

    missing_information: list[str] = Field(
        default_factory=list,
        description="Information needed but absent from the evidence."
    )

    concise_rationale: str = Field(
        description="A brief, user-facing explanation of the evaluation."
    )


# --------------------------------------------------
# 4. Policy RAG Request
# --------------------------------------------------

class PolicyRAGRequest(BaseModel):

    query: str = Field(
        min_length=2,
        max_length=1500
    )

    top_k: int = Field(
        default=6,
        ge=1,
        le=10
    )

    policy_version_id: int | None = Field(
        default=None,
        gt=0
    )


# --------------------------------------------------
# 5. Retrieved Policy Evidence
# --------------------------------------------------

class RetrievedEvidence(BaseModel):

    evidence_id: str

    text: str

    policy_version_id: int | None = None

    document_id: int | None = None

    page_number: int | None = Field(
        default=None,
        ge=1
    )

    section: str | None = None

    source: str | None = None


# --------------------------------------------------
# 6. Policy Citation
# --------------------------------------------------

class PolicyCitation(BaseModel):

    evidence_id: str

    policy_version_id: int | None = None

    document_id: int | None = None

    page_number: int | None = Field(
        default=None,
        ge=1
    )

    source: str | None = None


# --------------------------------------------------
# 7. Final Policy RAG Response
# --------------------------------------------------

class PolicyRAGResponse(BaseModel):

    answer: str

    evidence: list[RetrievedEvidence]

    citations: list[PolicyCitation]

    grounded: bool

    grounding_score: float = Field(
        ge=0,
        le=1
    )

    faithfulness_score: float = Field(
        ge=0,
        le=1
    )

    relevance_score: float = Field(
        ge=0,
        le=1
    )

    citation_valid: bool

    criteria_support: list[CriteriaSupport]

    missing_information: list[str]

    concise_rationale: str

    generation_attempts: int = Field(
        ge=1
    )
