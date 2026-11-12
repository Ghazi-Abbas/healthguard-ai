from enum import Enum

from pydantic import BaseModel, Field


class CriterionStatus(str, Enum):
    SATISFIED = "SATISFIED"
    NOT_SATISFIED = "NOT_SATISFIED"
    UNKNOWN = "UNKNOWN"

class EligibilityStatus(str, Enum):
    ELIGIBLE_FOR_REVIEW = "ELIGIBLE_FOR_REVIEW"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"
    UNKNOWN = "UNKNOWN"

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    UNKNOWN = "UNKNOWN"


class Recommendation(str, Enum):
    APPROVAL_RECOMMENDED = "APPROVAL_RECOMMENDED"
    DENIAL_RECOMMENDED = "DENIAL_RECOMMENDED"
    REQUEST_INFORMATION = "REQUEST_INFORMATION"


class EvidenceReference(BaseModel):
    evidence_id: str = Field(
        description="ID of evidence supplied by the Clinical Evidence Agent."
    )

    document_id: int = Field(
        description="Database ID of the source document."
    )

    filename: str = Field(
        description="Name of the source document."
    )

    page_number: int = Field(
        ge=1,
        description="One-based page number of the supporting evidence."
    )


class CriterionResult(BaseModel):
    criterion_id: str

    criterion: str

    status: CriterionStatus

    evidence: list[EvidenceReference] = Field(
        description=(
            "Source-backed evidence references supporting this criterion."
        )
    )

    rationale: str = Field(
        description="A concise, reviewer-facing explanation of the status."
    )


class CriteriaResult(BaseModel):
    eligibility_status: EligibilityStatus = Field(
        description=(
            "The authoritative eligibility status supplied to the agent."
        )
    )

    criteria: list[CriterionResult]

    missing_information: list[str]

    risk: RiskLevel

    uncertainty: list[str]

    recommendation: Recommendation

    concise_rationale: str = Field(
        description=(
            "A short explanation for the reviewer. Do not include "
            "hidden chain-of-thought."
        )
    )
