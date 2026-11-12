
# import json

# from langgraph.graph import StateGraph, START, END

# from app.agents.authorization_state import AuthorizationState

# from app.agents.clinical_evidence_agent import (
#     clinical_evidence_chain
# )

# from app.security.input_sanitizer import (
#     serialize_untrusted_input,
#     MAX_AUTHORIZATION_SIZE,
#     MAX_CRITERIA_SIZE,
#     MAX_CLINICAL_PAGES_SIZE,
# )

# from app.schemas.clinical_evidence import ClinicalEvidenceResult

# from app.services.eligibility_service import EligibilityService


# # =========================================================
# # 1. CLINICAL EVIDENCE AGENT
# # =========================================================

# def clinical_evidence_node(
#     state: AuthorizationState
# ) -> dict:

#     authorization = state.get("authorization", {})
#     criteria = state.get("policy_criteria", [])
#     pages = state.get("clinical_pages", [])

#     # No policy criteria means there is nothing to evaluate.
#     if not criteria:

#         return {
#             "clinical_evidence": [],

#             "clinical_missing_information": [
#                 "No applicable policy criteria were supplied."
#             ]
#         }

#     # No clinical pages means evidence cannot be found.
#     if not pages:

#         findings = []

#         for item in criteria:

#             findings.append({
#                 "criterion_id": item["criterion_id"],

#                 "criterion": item["description"],

#                 "evidence_status": "NOT_FOUND",

#                 "evidence_summary": (
#                     "No clinical document pages were available to inspect."
#                 ),

#                 "supporting_evidence_ids": [],

#                 "sources": [],

#                 "missing_information": [
#                     "Supporting clinical documentation is missing."
#                 ]
#             })

#         return {
#             "clinical_evidence": findings,

#             "clinical_missing_information": [
#                 "No clinical document pages were available."
#             ]
#         }

#     # Prepare only the information the LLM needs.
#     pages_for_model = [
#         {
#             "evidence_id": page["evidence_id"],
#             "filename": page.get("filename"),
#             "page_number": page.get("page_number"),
#             "text": page.get("text", ""),
#         }
#         for page in pages
#     ]

#     # Invoke the structured-output chain.
#     result: ClinicalEvidenceResult = clinical_evidence_chain.invoke(
#         {
#             "authorization_json": serialize_untrusted_input(
#                 authorization,
#                 MAX_AUTHORIZATION_SIZE,
#                 "authorization"
#             ),

#             "criteria_json": serialize_untrusted_input(
#                 criteria,
#                 MAX_CRITERIA_SIZE,
#                 "policy criteria"
#             ),

#             "clinical_pages_json": serialize_untrusted_input(
#                 pages_for_model,
#                 MAX_CLINICAL_PAGES_SIZE,
#                 "clinical pages"
#             )
#         }
#     )

#     # Build trusted lookups from application-supplied data.
#     pages_by_id = {
#         page["evidence_id"]: page
#         for page in pages
#     }

#     criteria_by_id = {
#         item["criterion_id"]: item
#         for item in criteria
#     }

#     findings_by_id = {}

#     # Validate every finding returned by the LLM.
#     for finding in result.finding:

#         criterion_id = finding.criterion_id

#         # Ignore criteria that were not supplied by the application.
#         if criterion_id not in criteria_by_id:
#             continue

#         # Ignore duplicate findings for the same criterion.
#         if criterion_id in findings_by_id:
#             continue

#         # Keep only evidence IDs that exist in trusted application data.
#         valid_ids = list(
#             dict.fromkeys(
#                 evidence_id
#                 for evidence_id in finding.supporting_evidence_ids
#                 if evidence_id in pages_by_id
#             )
#         )

#         status = finding.evidence_status

#         # A FOUND result without a valid source is not verifiable.
#         if status == "FOUND" and not valid_ids:
#             status = "AMBIGUOUS"

#         # NOT_FOUND must not contain supporting evidence references.
#         if status == "NOT_FOUND":
#             valid_ids = []

#         # Resolve source metadata from trusted application data.
#         sources = [
#             {
#                 "evidence_id": evidence_id,

#                 "document_id": pages_by_id[evidence_id].get(
#                     "document_id"
#                 ),

#                 "filename": pages_by_id[evidence_id].get(
#                     "filename"
#                 ),

#                 "page_number": pages_by_id[evidence_id].get(
#                     "page_number"
#                 )
#             }
#             for evidence_id in valid_ids
#         ]

#         findings_by_id[criterion_id] = {
#             "criterion_id": criterion_id,

#             # Use the original policy criterion, not LLM-generated text.
#             "criterion": criteria_by_id[criterion_id]["description"],

#             "evidence_status": status,

#             "evidence_summary": finding.evidence_summary,

#             "supporting_evidence_ids": valid_ids,

#             "sources": sources,

#             "missing_information": list(
#                 finding.missing_information
#             )
#         }

#     # Ensure every supplied policy criterion has a finding.
#     final_findings = []

#     for item in criteria:

#         criterion_id = item["criterion_id"]

#         finding = findings_by_id.get(criterion_id)

#         if finding is None:

#             finding = {
#                 "criterion_id": criterion_id,

#                 "criterion": item["description"],

#                 "evidence_status": "AMBIGUOUS",

#                 "evidence_summary": (
#                     "The clinical evidence agent did not return "
#                     "a valid finding for this criterion."
#                 ),

#                 "supporting_evidence_ids": [],

#                 "sources": [],

#                 "missing_information": [
#                     "Clinical evidence assessment is incomplete."
#                 ]
#             }

#         final_findings.append(finding)

#     # Include missing information from individual findings as well
#     # as the overall LLM response.
#     all_missing_information = list(
#         result.overall_missing_information
#     )

#     for finding in final_findings:
#         all_missing_information.extend(
#             finding["missing_information"]
#         )

#     return {
#         "clinical_evidence": final_findings,

#         "clinical_missing_information": list(
#             dict.fromkeys(all_missing_information)
#         )
#     }


# # =========================================================
# # 2. ELIGIBILITY AGENT
# # =========================================================

# eligibility_service = EligibilityService()


# def eligibility_node(
#     state: AuthorizationState
# ) -> dict:

#     authorization = state.get("authorization", {})

#     result = eligibility_service.evaluate(
#         member_id=str(
#             authorization.get("member_id") or ""
#         ),

#         service_date=state.get("service_date"),

#         coverage_records=state.get("coverage_records", [])
#     )

#     return {
#         "eligibility_result": result.model_dump(mode="json")
#     }


# # =========================================================
# # 3. BUILD ELIGIBILITY AND CLINICAL GRAPH
# # =========================================================

# builder = StateGraph(AuthorizationState)

# builder.add_node(
#     "clinical_evidence",
#     clinical_evidence_node
# )

# builder.add_node(
#     "eligibility",
#     eligibility_node
# )

# # Both agents start from the same shared state.
# builder.add_edge(
#     START,
#     "clinical_evidence"
# )

# builder.add_edge(
#     START,
#     "eligibility"
# )

# # Both agents finish independently.
# builder.add_edge(
#     "clinical_evidence",
#     END
# )

# builder.add_edge(
#     "eligibility",
#     END
# )

# authorization_analysis_graph = builder.compile()



from langgraph.graph import StateGraph, START, END

from app.agents.authorization_state import AuthorizationState

from app.agents.clinical_evidence_agent import (
    clinical_evidence_chain
)

from app.security.input_sanitizer import (
    serialize_untrusted_input,
    MAX_AUTHORIZATION_SIZE,
    MAX_CRITERIA_SIZE,
    MAX_CLINICAL_PAGES_SIZE,
)

from app.schemas.clinical_evidence import ClinicalEvidenceResult

from app.services.eligibility_service import EligibilityService


# =========================================================
# 1. CLINICAL EVIDENCE NODE FACTORY
# =========================================================

def create_clinical_evidence_node(clinical_chain):

    def clinical_evidence_node(
        state: AuthorizationState
    ) -> dict:

        authorization = state.get("authorization", {})
        criteria = state.get("policy_criteria", [])
        pages = state.get("clinical_pages", [])

        # No policy criteria means there is nothing to evaluate.
        if not criteria:
            return {
                "clinical_evidence": [],
                "clinical_missing_information": [
                    "No applicable policy criteria were supplied."
                ]
            }

        # No clinical pages means evidence cannot be found.
        if not pages:

            findings = []

            for item in criteria:
                findings.append({
                    "criterion_id": item["criterion_id"],
                    "criterion": item["description"],
                    "evidence_status": "NOT_FOUND",
                    "evidence_summary": (
                        "No clinical document pages were available to inspect."
                    ),
                    "supporting_evidence_ids": [],
                    "sources": [],
                    "missing_information": [
                        "Supporting clinical documentation is missing."
                    ]
                })

            return {
                "clinical_evidence": findings,
                "clinical_missing_information": [
                    "No clinical document pages were available."
                ]
            }

        # Prepare only the information the LLM needs.
        pages_for_model = [
            {
                "evidence_id": page["evidence_id"],
                "filename": page.get("filename"),
                "page_number": page.get("page_number"),
                "text": page.get("text", ""),
            }
            for page in pages
        ]

        # Serialize untrusted inputs before sending them to the chain.
        result: ClinicalEvidenceResult = clinical_chain.invoke(
            {
                "authorization_json": serialize_untrusted_input(
                    authorization,
                    MAX_AUTHORIZATION_SIZE,
                    "authorization"
                ),

                "criteria_json": serialize_untrusted_input(
                    criteria,
                    MAX_CRITERIA_SIZE,
                    "policy criteria"
                ),

                "clinical_pages_json": serialize_untrusted_input(
                    pages_for_model,
                    MAX_CLINICAL_PAGES_SIZE,
                    "clinical pages"
                )
            }
        )

        # Build trusted lookups from application-supplied data.
        pages_by_id = {
            page["evidence_id"]: page
            for page in pages
        }

        criteria_by_id = {
            item["criterion_id"]: item
            for item in criteria
        }

        findings_by_id = {}

        # Validate every finding returned by the LLM.
        for finding in result.finding:

            criterion_id = finding.criterion_id

            # Ignore criteria not supplied by the application.
            if criterion_id not in criteria_by_id:
                continue

            # Ignore duplicate findings for the same criterion.
            if criterion_id in findings_by_id:
                continue

            # Keep only evidence IDs from trusted application data.
            valid_ids = list(
                dict.fromkeys(
                    evidence_id
                    for evidence_id in finding.supporting_evidence_ids
                    if evidence_id in pages_by_id
                )
            )

            # Use the actual schema field names.
            status = finding.eviedence_status

            # FOUND without a valid source cannot be verified.
            if status == "FOUND" and not valid_ids:
                status = "AMBIGUOUS"

            # NOT_FOUND must not contain evidence references.
            if status == "NOT_FOUND":
                valid_ids = []

            # Resolve source metadata from trusted application data.
            sources = [
                {
                    "evidence_id": evidence_id,
                    "document_id": pages_by_id[evidence_id].get(
                        "document_id"
                    ),
                    "filename": pages_by_id[evidence_id].get(
                        "filename"
                    ),
                    "page_number": pages_by_id[evidence_id].get(
                        "page_number"
                    )
                }
                for evidence_id in valid_ids
            ]

            findings_by_id[criterion_id] = {
                "criterion_id": criterion_id,

                # Use the original policy criterion.
                "criterion": criteria_by_id[criterion_id]["description"],

                "evidence_status": status,

                # Use the actual schema field name.
                "evidence_summary": finding.evodence_summatry,

                "supporting_evidence_ids": valid_ids,

                "sources": sources,

                "missing_information": list(
                    finding.missing_information
                )
            }

        # Ensure every supplied criterion has a finding.
        final_findings = []

        for item in criteria:

            criterion_id = item["criterion_id"]

            finding = findings_by_id.get(criterion_id)

            if finding is None:

                finding = {
                    "criterion_id": criterion_id,
                    "criterion": item["description"],
                    "evidence_status": "AMBIGUOUS",
                    "evidence_summary": (
                        "The clinical evidence agent did not return "
                        "a valid finding for this criterion."
                    ),
                    "supporting_evidence_ids": [],
                    "sources": [],
                    "missing_information": [
                        "Clinical evidence assessment is incomplete."
                    ]
                }

            final_findings.append(finding)

        # Collect missing information from all findings.
        all_missing_information = list(
            result.overall_missing_information
        )

        for finding in final_findings:
            all_missing_information.extend(
                finding["missing_information"]
            )

        return {
            "clinical_evidence": final_findings,
            "clinical_missing_information": list(
                dict.fromkeys(all_missing_information)
            )
        }

    return clinical_evidence_node


# =========================================================
# 2. ELIGIBILITY NODE
# =========================================================

eligibility_service = EligibilityService()


def eligibility_node(
    state: AuthorizationState
) -> dict:

    authorization = state.get("authorization", {})

    result = eligibility_service.evaluate(
        member_id=str(
            authorization.get("member_id") or ""
        ),

        service_date=state.get("service_date"),

        coverage_records=state.get("coverage_records", [])
    )

    return {
        "eligibility_result": result.model_dump(mode="json")
    }


# =========================================================
# 3. BUILD AUTHORIZATION ANALYSIS GRAPH
# =========================================================

def build_authorization_analysis_graph(
    clinical_chain=None
):
    """
    Build the authorization analysis graph.

    Production:
        Uses the real clinical evidence chain.

    Testing:
        Accepts an injected mock clinical chain.
    """

    # Production chain is used by default.
    if clinical_chain is None:
        clinical_chain = clinical_evidence_chain

    builder = StateGraph(AuthorizationState)

    # Create the clinical node with the selected chain.
    builder.add_node(
        "clinical_evidence",
        create_clinical_evidence_node(clinical_chain)
    )

    builder.add_node(
        "eligibility",
        eligibility_node
    )

    # Both agents start from the same shared state.
    builder.add_edge(
        START,
        "clinical_evidence"
    )

    builder.add_edge(
        START,
        "eligibility"
    )

    # Both agents finish independently.
    builder.add_edge(
        "clinical_evidence",
        END
    )

    builder.add_edge(
        "eligibility",
        END
    )

    return builder.compile()


# =========================================================
# 4. PRODUCTION GRAPH
# =========================================================

# This graph always uses the production clinical evidence chain.
authorization_analysis_graph = build_authorization_analysis_graph()
