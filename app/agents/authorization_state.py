
from typing import Any, TypedDict


class AuthorizationState(TypedDict, total=False):

    # --------------------------------------------------
    # Workflow identity
    # --------------------------------------------------

    authorization_id: int
    thread_id: str
    organization_id: int
    current_node: str
    workflow_status: str

    # --------------------------------------------------
    # Trusted application input
    # --------------------------------------------------

    authorization: dict[str, Any]
    service_date: str | None
    policy_question: str
    case_context: str

    active_policy_version_ids: list[int]
    clinical_pages: list[dict[str, Any]]
    coverage_records: list[dict[str, Any]]

    # --------------------------------------------------
    # Supervisor output
    # --------------------------------------------------

    supervisor_summary: str
    supervisor_missing_information: list[str]
    policy_search_query: str

    # --------------------------------------------------
    # Eligibility Agent output
    # --------------------------------------------------

    eligibility_result: dict[str, Any]

    # --------------------------------------------------
    # Policy RAG / C-RAG output
    # --------------------------------------------------

    policy_reference: dict[str, Any]
    policy_answer: dict[str, Any]
    retrieved_policy_evidence: list[dict[str, Any]]
    policy_criteria: list[dict[str, Any]]
    policy_missing_information: list[str]

    # --------------------------------------------------
    # Clinical Evidence Agent output
    # --------------------------------------------------

    clinical_evidence: list[dict[str, Any]]
    clinical_missing_information: list[str]

    # --------------------------------------------------
    # Criteria and Risk Agent output
    # --------------------------------------------------

    criteria_result: dict[str, Any]
    missing_information: list[str]
    risk: str
    uncertainty: list[str]
    recommendation: str

    # --------------------------------------------------
    # Validation and retry information
    # --------------------------------------------------

    guardrail_errors: list[str]
    retry_metadata: dict[str, Any]

    # --------------------------------------------------
    # Human-in-the-loop
    # --------------------------------------------------

    needs_human_review: bool
    human_decision: str | None
    reviewer_notes: str | None

    # --------------------------------------------------
    # Provider document upload and reanalysis
    # --------------------------------------------------

    provider_upload_event: dict[str, Any]
    reanalysis_count: int
