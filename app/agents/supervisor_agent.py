# import json

# from langchain_core.prompts import ChatPromptTemplate
# from langchain_groq import ChatGroq

# from app.core.config import settings
# from app.schemas.supervisor import SupervisionPlan
# from app.agents.authorization_state import AuthorizationState
# from app.ai.gateway.model_factory import get_chat_model

# from app.ai.gateway.fallback_manager import add_model_fallbacks
# from langchain_core.runnables import RunnableLambda

# from app.ai.gateway.model_registry import MODEL_REGISTRY
# from app.ai.gateway.provider_authorization import (
#     is_provider_authorized,
# )
# from app.security.classification import DataClassification
# from app.security.data_classifier import get_highest_classification
# from app.ai.gateway.provider_authorization import (
#     validate_task_provider_authorization,
# )

# from app.agents.authorization_state import AuthorizationState

# # --------------------------------------------------
# # 1. Initialize Supervisor LLM
# # --------------------------------------------------

# # supervisor_model = ChatGroq(
# #     model=settings.GROQ_MODEL,
# #     api_key=settings.GROQ_API_KEY,
# #     temperature=0
# # )

# supervisor_model = get_chat_model("supervisor")
# # --------------------------------------------------
# # 2. Supervisor Prompt
# # --------------------------------------------------

# supervisor_prompt = ChatPromptTemplate.from_messages(
#     [
#         (
#             "system",
#             """
# You are the workflow supervisor for HealthGuard AI.

# Your responsibility is to prepare a focused policy-search
# plan for a prior-authorization case.

# Rules:

# 1. Use only the supplied original policy question.
# 2. Do not invent procedure codes, diagnosis codes,
#    or policy rules.
# 3. If essential context is missing, identify it explicitly.
# 4. Keep the search query focused on finding applicable policy criteria.
# 5. Do not decide eligibility or clinical medical necessity.
# 6. Do not approve or reject an authorization.
# 7. Do not expose hidden chain-of-thought.
# 8. Return only the requested structured plan.

# The graph always invokes the required specialist stages
# and guardrails. Do not suggest skipping any of them.
# """
#         ),
#         (
#             "human",
#             """


# Original policy question:
# {policy_question}

# Are active policy versions available?
# {has_active_policy_versions}

# Number of extracted clinical pages:
# {clinical_page_count}
# """
#         )
#     ]
# )


# # --------------------------------------------------
# # 3. Structured-output Chain
# # --------------------------------------------------

# def validate_supervisor_input(inputs: dict) -> dict:
#     """
#     Validate input against the primary and fallback providers.
#     """

#     return validate_task_provider_authorization(
#         task_name="supervisor",
#         inputs=inputs,
#     )

# structured_supervisor_model = (
#     supervisor_model.with_structured_output(
#         SupervisionPlan
#     )
# )

# supervisor_chain = (
#     RunnableLambda(validate_supervisor_input)
#     | supervisor_prompt
#     | add_model_fallbacks(
#         structured_supervisor_model,
#         task_name="supervisor",
#         schema=SupervisionPlan,
#     )
# )

# # --------------------------------------------------
# # 4. Supervisor Graph Node
# # --------------------------------------------------

# def supervisor_node(state: AuthorizationState) -> dict:

#     policy_question = state.get("policy_question", "")

#     active_policy_version_ids = state.get(
#         "active_policy_version_ids", []
#     )

#     clinical_pages = state.get("clinical_pages", [])

#     plan: SupervisionPlan = supervisor_chain.invoke(
#         {
#             "policy_question": policy_question,
#             "has_active_policy_versions": bool(
#                 active_policy_version_ids
#             ),
#             "clinical_page_count": len(clinical_pages),
#         }
#     )

#     return {
#         "supervisor_summary": plan.case_summary,
#         "policy_search_query": plan.policy_search_query,
#         "supervisor_missing_information": (
#             plan.missing_information
#         ),
#         "current_node": "supervisor",
#     }




from app.agents.authorization_state import AuthorizationState


# --------------------------------------------------
# 1. Deterministic Supervisor Node
# --------------------------------------------------

def supervisor_node(state: AuthorizationState) -> dict:
    """
    Prepare a policy-search query using trusted application data.

    This supervisor does not call an external LLM.
    It does not make eligibility or clinical decisions.
    """

    # Get the original policy question.
    policy_question = state.get("policy_question", "").strip()

    # Get active policy versions.
    active_policy_version_ids = state.get(
        "active_policy_version_ids", []
    )

    # Get extracted clinical pages.
    clinical_pages = state.get("clinical_pages", [])

    # Collect missing information.
    missing_information = []

    if not policy_question:
        missing_information.append(
            "Original policy question is missing."
        )

    if not active_policy_version_ids:
        missing_information.append(
            "No active policy version is available."
        )

    if not clinical_pages:
        missing_information.append(
            "No extracted clinical pages are available."
        )

    # Use the original question as the policy-search query.
    # Do not invent or modify clinical information.
    policy_search_query = policy_question

    # Prepare supervisor summary.
    if missing_information:
        case_summary = (
            "Policy search preparation completed with "
            "missing information."
        )
    else:
        case_summary = (
            "Policy search preparation completed successfully."
        )

    return {
        "supervisor_summary": case_summary,
        "policy_search_query": policy_search_query,
        "supervisor_missing_information": missing_information,
        "current_node": "supervisor",
    }
