
# import json
# from langgraph.types import interrupt

# from langgraph.graph import StateGraph, START, END

# from app.agents.authorization_state import AuthorizationState
# from app.agents.supervisor_agent import supervisor_node
# from app.agents.policy_crag_graph import policy_crag_graph
# from langchain_core.runnables import RunnableConfig
# from app.agents.eligibility_and_clinical_evidence_graph import (
#     authorization_analysis_graph
# )
# from app.agents.critaria_risk_agent import criteria_risk_chain

# from app.schemas.criteria_risk import Recommendation


# # =========================================================
# # 1. POLICY C-RAG ADAPTER
# # =========================================================

# def policy_crag_node(state: AuthorizationState) -> dict:

#     query = (
#         state.get("policy_search_query")
#         or state.get("policy_question", "")
#     )

#     organization_id = state.get("organization_id")
#     active_version_ids = state.get(
#         "active_policy_version_ids", []
#     )

#     # Do not run retrieval without the tenant context.
#     if not organization_id:
#         return {
#             "policy_answer": {},
#             "retrieved_policy_evidence": [],
#             "policy_criteria": [],
#             "policy_missing_information": [
#                 "Organization context is missing. Policy retrieval was not run."
#             ],
#             "needs_human_review": True
#         }

#     result = policy_crag_graph.invoke({
#         "query": query,
#         "search_query": query,
#         "organization_id": organization_id,
#         "active_policy_version_ids": active_version_ids,
#         "top_k": 6
#     })

#     draft = result.get("draft")
#     evaluation = result.get("evaluation")

#     policy_answer = {
#         "draft": (
#             draft.model_dump(mode="json")
#             if draft else {}
#         ),
#         "evaluation": (
#             evaluation.model_dump(mode="json")
#             if evaluation else {}
#         )
#     }

#     missing_information = []

#     if draft:
#         missing_information.extend(
#             draft.missing_information
#         )

#     missing_information.extend(
#         result.get("criteria_missing_information", [])
#     )

#     return {
#         "policy_reference": {
#             "policy_name": result.get("policy_name"),
#             "active_policy_version_ids": active_version_ids
#         },

#         "policy_answer": policy_answer,

#         "retrieved_policy_evidence": result.get(
#             "evidence", []
#         ),

#         "policy_criteria": result.get(
#             "policy_criteria", []
#         ),

#         "policy_missing_information": list(
#             dict.fromkeys(missing_information)
#         ),

#         "needs_human_review": result.get(
#             "needs_human_review", False
#         )
#     }


# # =========================================================
# # 2. ELIGIBILITY + CLINICAL EVIDENCE ADAPTER
# # =========================================================

# def authorization_analysis_node(state: AuthorizationState) -> dict:

#     result = authorization_analysis_graph.invoke(dict(state))

#     return {
#         "eligibility_result": result.get("eligibility_result", {}),
#         "clinical_evidence": result.get("clinical_evidence", []),
#         "clinical_missing_information": result.get(
#             "clinical_missing_information", []
#         )
#     }


# # =========================================================
# # 3. CRITERIA AND RISK AGENT
# # =========================================================

# def criteria_risk_node(
#     state: AuthorizationState
# ) -> dict:

#     policy_criteria = state.get("policy_criteria", [])
#     eligibility = state.get("eligibility_result", {})
#     clinical_evidence = state.get("clinical_evidence", [])

#     # Do not ask the LLM to assess an incomplete case.
#     if not policy_criteria or not eligibility:

#         return {
#             "criteria_result": {},
#             "recommendation": Recommendation.REQUEST_INFORMATION.value,
#             "needs_human_review": True,
#             "missing_information": [
#                 "Policy criteria or authoritative eligibility information is missing."
#             ]
#         }

#     result = criteria_risk_chain.invoke({


#         "eligibility_json": json.dumps(
#             eligibility,
#             ensure_ascii=False
#         ),

#         "policy_criteria_json": json.dumps(
#             policy_criteria,
#             ensure_ascii=False
#         ),

#         "clinical_evidence_json": json.dumps(
#             clinical_evidence,
#             ensure_ascii=False
#         ),

#         "clinical_missing_information_json": json.dumps(
#             state.get("clinical_missing_information", []),
#             ensure_ascii=False
#         )
#     })

#     guardrail_errors = list(
#         state.get("guardrail_errors", [])
#     )

#     # -----------------------------------------------------
#     # Validate authoritative eligibility
#     # -----------------------------------------------------

#     authoritative_status = eligibility.get("status")

#     if result.eligibility_status.value != authoritative_status:
#         guardrail_errors.append(
#             "Criteria/Risk Agent eligibility does not match "
#             "the authoritative eligibility result."
#         )

#     # -----------------------------------------------------
#     # Build trusted criterion and evidence lookups
#     # -----------------------------------------------------

#     trusted_criteria_ids = {
#         item["criterion_id"]
#         for item in policy_criteria
#     }

#     trusted_sources = {}

#     for finding in clinical_evidence:
#         for source in finding.get("sources", []):
#             evidence_id = source.get("evidence_id")

#             if evidence_id:
#                 trusted_sources[evidence_id] = source

#     # -----------------------------------------------------
#     # Validate criterion IDs and source references
#     # -----------------------------------------------------

#     for criterion in result.criteria:

#         if criterion.criterion_id not in trusted_criteria_ids:
#             guardrail_errors.append(
#                 f"Unknown policy criterion ID: {criterion.criterion_id}"
#             )

#         for reference in criterion.evidence:

#             trusted_source = trusted_sources.get(
#                 reference.evidence_id
#             )

#             if trusted_source is None:
#                 guardrail_errors.append(
#                     f"Unknown clinical evidence ID: {reference.evidence_id}"
#                 )
#                 continue

#             if (
#                 reference.document_id != trusted_source.get("document_id")
#                 or reference.filename != trusted_source.get("filename")
#                 or reference.page_number != trusted_source.get("page_number")
#             ):
#                 guardrail_errors.append(
#                     f"Source metadata mismatch for evidence ID: "
#                     f"{reference.evidence_id}"
#                 )

#     # -----------------------------------------------------
#     # Apply conservative recommendation rules
#     # -----------------------------------------------------

#     recommendation = result.recommendation.value

#     if authoritative_status == "UNKNOWN":
#         recommendation = Recommendation.REQUEST_INFORMATION.value

#     if any(
#         item.status.value == "UNKNOWN"
#         for item in result.criteria
#     ):
#         recommendation = Recommendation.REQUEST_INFORMATION.value

#     # Any validation error prevents an automated recommendation
#     # from being treated as reliable.
#     if guardrail_errors:
#         recommendation = Recommendation.REQUEST_INFORMATION.value

#     missing_information = list(
#         dict.fromkeys(
#             result.missing_information
#             + state.get("supervisor_missing_information", [])
#             + state.get("policy_missing_information", [])
#             + state.get("clinical_missing_information", [])
#         )
#     )

#     criteria_result = result.model_dump(mode="json")
#     criteria_result["recommendation"] = recommendation

#     return {
#         "criteria_result": criteria_result,
#         "eligibility_result": eligibility,
#         "recommendation": recommendation,
#         "risk": result.risk.value,
#         "uncertainty": result.uncertainty,
#         "missing_information": missing_information,
#         "guardrail_errors": list(dict.fromkeys(guardrail_errors)),
#         "needs_human_review": True
#     }

# # =========================================================
# # 3. Human review node
# # =========================================================

# # =========================================================
# # 4. HUMAN REVIEW NODE
# # =========================================================

# def human_review_node(state: AuthorizationState) -> dict:

#     review_request = {
#         "authorization_id": state.get("authorization_id"),
#         "recommendation": state.get("recommendation"),
#         "risk": state.get("risk"),
#         "missing_information": state.get("missing_information", []),
#         "uncertainty": state.get("uncertainty", []),
#         "criteria_result": state.get("criteria_result", {}),
#         "message": (
#             "Human review is required before this "
#             "authorization can proceed."
#         )
#     }

#     reviewer_decision = interrupt(review_request)

#     decision = reviewer_decision.get("decision")

#     if decision not in ("APPROVE", "REJECT", "REQUEST_INFORMATION"):
#         raise ValueError("Invalid human review decision")

#     if decision == "REQUEST_INFORMATION":
#         workflow_status = "AWAITING_PROVIDER_INFORMATION"
#     else:
#         workflow_status = "REVIEW_COMPLETED"

#     return {
#         "human_decision": decision,
#         "reviewer_notes": reviewer_decision.get("notes"),
#         "workflow_status": workflow_status
#     }

# # =========================================================
# # 5. ROUTE AFTER HUMAN REVIEW
# # =========================================================

# def route_after_human_review(state: AuthorizationState) -> str:

#     decision = state.get("human_decision")

#     if decision == "REQUEST_INFORMATION":
#         return "provider_information"

#     return "end"


# # =========================================================
# # 6. PROVIDER INFORMATION NODE
# # =========================================================

# def provider_information_node(state: AuthorizationState) -> dict:

#     upload_event = interrupt({
#         "authorization_id": state.get("authorization_id"),
#         "message": (
#             "Additional clinical information is required. "
#             "Waiting for the provider to submit documents."
#         )
#     })

#     if upload_event.get("event") != "DOCUMENTS_SUBMITTED":
#         raise ValueError("Invalid provider information event")

#     clinical_pages = upload_event.get("clinical_pages")

#     if not isinstance(clinical_pages, list) or not clinical_pages:
#         raise ValueError("No processed clinical pages were provided")

#     return {
#         "provider_upload_event": upload_event,
#         "clinical_pages": clinical_pages,
#         "reanalysis_count": state.get("reanalysis_count", 0) + 1,
#         "workflow_status": "REANALYSIS"
#     }


# # =========================================================
# # 7. BUILD CENTRAL AUTHORIZATION GRAPH
# # =========================================================

# def create_authorization_supervisor_graph(checkpointer):

#     builder = StateGraph(AuthorizationState)

#     builder.add_node("supervisor", supervisor_node)
#     builder.add_node("policy_crag", policy_crag_node)

#     builder.add_node(
#         "authorization_analysis",
#         authorization_analysis_node
#     )

#     builder.add_node("criteria_risk", criteria_risk_node)
#     builder.add_node("human_review", human_review_node)

#     builder.add_node(
#         "provider_information",
#         provider_information_node
#     )

#     # Initial analysis
#     builder.add_edge(START, "supervisor")
#     builder.add_edge("supervisor", "policy_crag")
#     builder.add_edge("policy_crag", "authorization_analysis")
#     builder.add_edge("authorization_analysis", "criteria_risk")
#     builder.add_edge("criteria_risk", "human_review")

#     # Conditional routing after human review
#     builder.add_conditional_edges(
#         "human_review",
#         route_after_human_review,
#         {
#             "provider_information": "provider_information",
#             "end": END
#         }
#     )

#     # Resume analysis after provider submits information
#     builder.add_edge("provider_information", "supervisor")

#     return builder.compile(checkpointer=checkpointer)


import json

from langgraph.types import interrupt
from langgraph.graph import StateGraph, START, END
from langchain_core.runnables import RunnableConfig

from app.agents.authorization_state import AuthorizationState
from app.agents.supervisor_agent import supervisor_node
from app.agents.policy_crag_graph import policy_crag_graph
from app.agents.eligibility_and_clinical_evidence_graph import (
    authorization_analysis_graph
)
from app.agents.critaria_risk_agent import criteria_risk_chain

from app.schemas.criteria_risk import Recommendation


# =========================================================
# 1. POLICY C-RAG ADAPTER
# =========================================================

def policy_crag_node(
    state: AuthorizationState,
    config: RunnableConfig
) -> dict:

    query = (
        state.get("policy_search_query")
        or state.get("policy_question", "")
    )

    organization_id = state.get("organization_id")

    active_version_ids = state.get(
        "active_policy_version_ids", []
    )

    # Do not run retrieval without the tenant context.
    if not organization_id:
        return {
            "policy_answer": {},
            "retrieved_policy_evidence": [],
            "policy_criteria": [],
            "policy_missing_information": [
                "Organization context is missing. Policy retrieval was not run."
            ],
            "needs_human_review": True
        }

    # Pass the parent configuration to the nested graph.
    result = policy_crag_graph.invoke(
        {
            "query": query,
            "search_query": query,
            "organization_id": organization_id,
            "active_policy_version_ids": active_version_ids,
            "top_k": 6
        },
        config=config
    )

    draft = result.get("draft")
    evaluation = result.get("evaluation")

    policy_answer = {
        "draft": (
            draft.model_dump(mode="json")
            if draft else {}
        ),
        "evaluation": (
            evaluation.model_dump(mode="json")
            if evaluation else {}
        )
    }

    missing_information = []

    if draft:
        missing_information.extend(
            draft.missing_information
        )

    missing_information.extend(
        result.get("criteria_missing_information", [])
    )

    return {
        "policy_reference": {
            "policy_name": result.get("policy_name"),
            "active_policy_version_ids": active_version_ids
        },

        "policy_answer": policy_answer,

        "retrieved_policy_evidence": result.get(
            "evidence", []
        ),

        "policy_criteria": result.get(
            "policy_criteria", []
        ),

        "policy_missing_information": list(
            dict.fromkeys(missing_information)
        ),

        "needs_human_review": result.get(
            "needs_human_review", False
        )
    }


# =========================================================
# 2. ELIGIBILITY + CLINICAL EVIDENCE ADAPTER
# =========================================================

def authorization_analysis_node(
    state: AuthorizationState,
    config: RunnableConfig
) -> dict:

    # Pass the parent configuration to the nested graph.
    result = authorization_analysis_graph.invoke(
        dict(state),
        config=config
    )

    return {
        "eligibility_result": result.get(
            "eligibility_result", {}
        ),

        "clinical_evidence": result.get(
            "clinical_evidence", []
        ),

        "clinical_missing_information": result.get(
            "clinical_missing_information", []
        )
    }


# =========================================================
# 3. CRITERIA AND RISK AGENT
# =========================================================

def criteria_risk_node(
    state: AuthorizationState,
    config: RunnableConfig
) -> dict:

    policy_criteria = state.get("policy_criteria", [])
    eligibility = state.get("eligibility_result", {})
    clinical_evidence = state.get("clinical_evidence", [])

    # Do not ask the LLM to assess an incomplete case.
    if not policy_criteria or not eligibility:

        return {
            "criteria_result": {},
            "recommendation": Recommendation.REQUEST_INFORMATION.value,
            "needs_human_review": True,
            "missing_information": [
                "Policy criteria or authoritative eligibility information is missing."
            ]
        }

    # Pass the parent configuration to the chain.
    result = criteria_risk_chain.invoke(
        {
            "eligibility_json": json.dumps(
                eligibility,
                ensure_ascii=False
            ),

            "policy_criteria_json": json.dumps(
                policy_criteria,
                ensure_ascii=False
            ),

            "clinical_evidence_json": json.dumps(
                clinical_evidence,
                ensure_ascii=False
            ),

            "clinical_missing_information_json": json.dumps(
                state.get("clinical_missing_information", []),
                ensure_ascii=False
            )
        },
        config=config
    )

    guardrail_errors = list(
        state.get("guardrail_errors", [])
    )

    # -----------------------------------------------------
    # Validate authoritative eligibility
    # -----------------------------------------------------

    authoritative_status = eligibility.get("status")

    if result.eligibility_status.value != authoritative_status:
        guardrail_errors.append(
            "Criteria/Risk Agent eligibility does not match "
            "the authoritative eligibility result."
        )

    # -----------------------------------------------------
    # Build trusted criterion and evidence lookups
    # -----------------------------------------------------

    trusted_criteria_ids = {
        item["criterion_id"]
        for item in policy_criteria
    }

    trusted_sources = {}

    for finding in clinical_evidence:
        for source in finding.get("sources", []):

            evidence_id = source.get("evidence_id")

            if evidence_id:
                trusted_sources[evidence_id] = source

    # -----------------------------------------------------
    # Validate criterion IDs and source references
    # -----------------------------------------------------

    for criterion in result.criteria:

        if criterion.criterion_id not in trusted_criteria_ids:
            guardrail_errors.append(
                f"Unknown policy criterion ID: {criterion.criterion_id}"
            )

        for reference in criterion.evidence:

            trusted_source = trusted_sources.get(
                reference.evidence_id
            )

            if trusted_source is None:
                guardrail_errors.append(
                    f"Unknown clinical evidence ID: {reference.evidence_id}"
                )
                continue

            if (
                reference.document_id != trusted_source.get("document_id")
                or reference.filename != trusted_source.get("filename")
                or reference.page_number != trusted_source.get("page_number")
            ):
                guardrail_errors.append(
                    f"Source metadata mismatch for evidence ID: "
                    f"{reference.evidence_id}"
                )

    # -----------------------------------------------------
    # Apply conservative recommendation rules
    # -----------------------------------------------------

    recommendation = result.recommendation.value

    if authoritative_status == "UNKNOWN":
        recommendation = Recommendation.REQUEST_INFORMATION.value

    if any(
        item.status.value == "UNKNOWN"
        for item in result.criteria
    ):
        recommendation = Recommendation.REQUEST_INFORMATION.value

    # Any validation error prevents an automated recommendation
    # from being treated as reliable.
    if guardrail_errors:
        recommendation = Recommendation.REQUEST_INFORMATION.value

    missing_information = list(
        dict.fromkeys(
            result.missing_information
            + state.get("supervisor_missing_information", [])
            + state.get("policy_missing_information", [])
            + state.get("clinical_missing_information", [])
        )
    )

    criteria_result = result.model_dump(mode="json")
    criteria_result["recommendation"] = recommendation

    return {
        "criteria_result": criteria_result,
        "eligibility_result": eligibility,
        "recommendation": recommendation,
        "risk": result.risk.value,
        "uncertainty": result.uncertainty,
        "missing_information": missing_information,
        "guardrail_errors": list(dict.fromkeys(guardrail_errors)),
        "needs_human_review": True
    }


# =========================================================
# 4. HUMAN REVIEW NODE
# =========================================================

def human_review_node(state: AuthorizationState) -> dict:

    review_request = {
        "authorization_id": state.get("authorization_id"),
        "recommendation": state.get("recommendation"),
        "risk": state.get("risk"),
        "missing_information": state.get("missing_information", []),
        "uncertainty": state.get("uncertainty", []),
        "criteria_result": state.get("criteria_result", {}),
        "message": (
            "Human review is required before this "
            "authorization can proceed."
        )
    }

    reviewer_decision = interrupt(review_request)

    decision = reviewer_decision.get("decision")

    if decision not in (
        "APPROVE",
        "REJECT",
        "REQUEST_INFORMATION"
    ):
        raise ValueError("Invalid human review decision")

    if decision == "REQUEST_INFORMATION":
        workflow_status = "AWAITING_PROVIDER_INFORMATION"
    else:
        workflow_status = "REVIEW_COMPLETED"

    return {
        "human_decision": decision,
        "reviewer_notes": reviewer_decision.get("notes"),
        "workflow_status": workflow_status
    }


# =========================================================
# 5. ROUTE AFTER HUMAN REVIEW
# =========================================================

def route_after_human_review(state: AuthorizationState) -> str:

    decision = state.get("human_decision")

    if decision == "REQUEST_INFORMATION":
        return "provider_information"

    return "end"


# =========================================================
# 6. PROVIDER INFORMATION NODE
# =========================================================

def provider_information_node(state: AuthorizationState) -> dict:

    upload_event = interrupt({
        "authorization_id": state.get("authorization_id"),
        "message": (
            "Additional clinical information is required. "
            "Waiting for the provider to submit documents."
        )
    })

    if upload_event.get("event") != "DOCUMENTS_SUBMITTED":
        raise ValueError("Invalid provider information event")

    clinical_pages = upload_event.get("clinical_pages")

    if not isinstance(clinical_pages, list) or not clinical_pages:
        raise ValueError("No processed clinical pages were provided")

    return {
        "provider_upload_event": upload_event,
        "clinical_pages": clinical_pages,
        "reanalysis_count": state.get("reanalysis_count", 0) + 1,
        "workflow_status": "REANALYSIS"
    }


# =========================================================
# 7. BUILD CENTRAL AUTHORIZATION GRAPH
# =========================================================

def create_authorization_supervisor_graph(checkpointer):

    builder = StateGraph(AuthorizationState)

    builder.add_node("supervisor", supervisor_node)
    builder.add_node("policy_crag", policy_crag_node)

    builder.add_node(
        "authorization_analysis",
        authorization_analysis_node
    )

    builder.add_node("criteria_risk", criteria_risk_node)
    builder.add_node("human_review", human_review_node)

    builder.add_node(
        "provider_information",
        provider_information_node
    )

    # Initial analysis
    builder.add_edge(START, "supervisor")
    builder.add_edge("supervisor", "policy_crag")
    builder.add_edge("policy_crag", "authorization_analysis")
    builder.add_edge("authorization_analysis", "criteria_risk")
    builder.add_edge("criteria_risk", "human_review")

    # Conditional routing after human review
    builder.add_conditional_edges(
        "human_review",
        route_after_human_review,
        {
            "provider_information": "provider_information",
            "end": END
        }
    )

    # Resume analysis after provider submits information
    builder.add_edge("provider_information", "supervisor")

    return builder.compile(checkpointer=checkpointer)
