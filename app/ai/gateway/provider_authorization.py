
# from app.security.classification import DataClassification
# from app.ai.gateway.model_registry import MODEL_REGISTRY
# from app.security.data_classifier import get_highest_classification


# # Providers currently permitted to process each classification.
# # Keep PII and PHI blocked until the required approvals are verified.

# PROVIDER_DATA_POLICIES = {
#     "groq": {
#         DataClassification.PUBLIC,
#         DataClassification.INTERNAL,
#     },
#     "gemini": {
#         DataClassification.PUBLIC,
#         DataClassification.INTERNAL,
#     },
#     "google_embeddings": {
#         DataClassification.PUBLIC,
#         DataClassification.INTERNAL,
#     },
# }


# # Maps configured fallback names to their actual providers.
# FALLBACK_PROVIDER_MAP = {
#     "groq_fast": "groq",
#     "gemini": "gemini",
# }


# def is_provider_authorized(
#     provider: str,
#     classification: DataClassification,
# ) -> bool:
#     """Check whether a provider can process a classification."""

#     if not isinstance(provider, str):
#         return False

#     allowed_classifications = PROVIDER_DATA_POLICIES.get(
#         provider.lower()
#     )

#     if allowed_classifications is None:
#         return False

#     return classification in allowed_classifications


# def validate_task_provider_authorization(
#     task_name: str,
#     inputs: dict,
# ) -> dict:
#     """
#     Validate input classification against the primary provider
#     and every configured fallback provider.

#     Reject the request before model invocation if any provider
#     is not authorized.
#     """

#     if task_name not in MODEL_REGISTRY:
#         raise ValueError(f"Unknown AI task: {task_name}")

#     if not isinstance(inputs, dict):
#         raise ValueError("Model inputs must be a dictionary.")

#     classification = get_highest_classification(inputs)


#     task_config = MODEL_REGISTRY[task_name]

#     providers = [task_config["provider"]]

#     for fallback_name in task_config.get("fallbacks", []):

#         fallback_provider = FALLBACK_PROVIDER_MAP.get(
#             fallback_name
#         )

#         if fallback_provider is None:
#             raise PermissionError(
#                 f"Unknown fallback provider configuration: {fallback_name}"
#             )

#         providers.append(fallback_provider)

#     # Remove duplicate providers while preserving order.
#     providers = list(dict.fromkeys(providers))

#     for provider in providers:

#         if not is_provider_authorized(
#             provider=provider,
#             classification=classification,
#         ):
#             raise PermissionError(
#                 f"Provider '{provider}' is not authorized to process "
#                 f"{classification.value} data for task '{task_name}'."
#             )

#     return inputs

# def validate_embedding_authorization(data: dict) -> dict:
#     """
#     Validate data before sending it to the Google Embeddings provider.
#     """

#     classification = get_highest_classification(data)

#     if not is_provider_authorized(
#         provider="google_embeddings",
#         classification=classification,
#     ):
#         raise PermissionError(
#             "Google Embeddings is not authorized to process "
#             f"{classification.value} data."
#         )

#     return data



from app.security.classification import DataClassification
from app.security.data_classifier import get_highest_classification
from app.ai.gateway.model_registry import MODEL_REGISTRY



PROVIDER_DATA_POLICIES = {
    "groq": {
        DataClassification.PUBLIC,
        DataClassification.INTERNAL,
        DataClassification.PHI
    },

    "gemini": {
        DataClassification.PUBLIC,
        DataClassification.INTERNAL,
        DataClassification.PHI
    },

    "google_embeddings": {
        DataClassification.PUBLIC,
        DataClassification.INTERNAL,
        DataClassification.PHI
    },
}



FALLBACK_PROVIDER_MAP = {
    "groq_fast": "groq",
    "gemini": "gemini",
}


def is_provider_authorized(provider, classification):
    if not isinstance(provider, str):
        return False

    allowed = PROVIDER_DATA_POLICIES.get(provider.lower())

    if allowed is None:
        return False

    return classification in allowed


def validate_task_provider_authorization(task_name, inputs):

    if task_name not in MODEL_REGISTRY:
        raise ValueError(f"Unknown AI task: {task_name}")

    if not isinstance(inputs, dict):
        raise ValueError("Model inputs must be a dictionary.")

    classification = get_highest_classification(inputs)

    config = MODEL_REGISTRY[task_name]

    providers = [config["provider"]]

    for fallback in config.get("fallbacks", []):
        provider = FALLBACK_PROVIDER_MAP.get(fallback)

        if provider is None:
            raise PermissionError(
                f"Unknown fallback provider: {fallback}"
            )

        providers.append(provider)

    providers = list(dict.fromkeys(providers))

    for provider in providers:
        if not is_provider_authorized(provider, classification):
            raise PermissionError(
                f"Provider '{provider}' is not authorized to process "
                f"{classification.value} data for task '{task_name}'."
            )

    return inputs

def validate_embedding_authorization(data: dict) -> dict:
    """
    Validate data before sending it to Google Embeddings.

    Google Embeddings is permitted to process only
    PUBLIC and INTERNAL data under the current policy.
    """

    classification = get_highest_classification(data)

    if not is_provider_authorized(
        provider="google_embeddings",
        classification=classification,
    ):
        raise PermissionError(
            "Google Embeddings is not authorized to process "
            f"{classification.value} data."
        )

    return data
