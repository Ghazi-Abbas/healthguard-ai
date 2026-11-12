
import logging

from app.ai.gateway.model_factory import get_chat_model_for_fallback
from app.ai.gateway.model_registry import MODEL_REGISTRY
from app.ai.gateway.retry_policy import RETRYABLE_ERRORS


logger = logging.getLogger(__name__)


def get_fallback_models(
    task_name: str,
    schema=None,
    structured_output_kwargs=None,
):
    """
    Create fallback models for a task.

    Every fallback uses the same structured-output
    schema and options as the primary model.
    """

    if task_name not in MODEL_REGISTRY:
        raise ValueError(f"Unknown AI task: {task_name}")

    task_config = MODEL_REGISTRY[task_name]
    fallback_models = []

    for fallback_name in task_config.get("fallbacks", []):

        if fallback_name == "groq_fast":
            model = get_chat_model_for_fallback(
                provider="groq",
                model_setting="GROQ_FAST_MODEL",
            )
            provider = "groq"

        elif fallback_name == "gemini":
            model = get_chat_model_for_fallback(
                provider="gemini",
                model_setting="GEMINI_EVAL_MODEL",
            )
            provider = "gemini"

        else:
            raise ValueError(f"Unknown fallback: {fallback_name}")

        if schema is not None:
            model = model.with_structured_output(
                schema,
                **(structured_output_kwargs or {}),
            )

        logger.debug(
            "Fallback model configured | task=%s | provider=%s | fallback=%s",
            task_name,
            provider,
            fallback_name,
        )

        # This listener runs only when this fallback starts executing.
        def log_fallback_start(
            run,
            current_task=task_name,
            current_fallback=fallback_name,
            current_provider=provider,
        ):
            logger.warning(
                "AI fallback activated | task=%s | provider=%s | fallback=%s",
                current_task,
                current_provider,
                current_fallback,
            )

        model = model.with_listeners(
            on_start=log_fallback_start,
        )

        fallback_models.append(model)

    return fallback_models


def add_model_fallbacks(
    runnable,
    task_name: str,
    schema=None,
    structured_output_kwargs=None,
):
    """
    Attach fallback runnables to the primary runnable.

    Runtime logging records when a fallback actually starts.
    """

    fallback_models = get_fallback_models(
        task_name=task_name,
        schema=schema,
        structured_output_kwargs=structured_output_kwargs,
    )

    if not fallback_models:
        logger.debug(
            "No fallback models configured | task=%s",
            task_name,
        )
        return runnable

    logger.info(
        "AI fallback chain configured | task=%s | fallback_count=%d",
        task_name,
        len(fallback_models),
    )

    return runnable.with_fallbacks(
        fallback_models,
        exceptions_to_handle=RETRYABLE_ERRORS,
    )
