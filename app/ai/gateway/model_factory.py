
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import settings
from app.ai.gateway.model_registry import MODEL_REGISTRY


def create_model(
    provider: str,
    model_name: str,
    temperature: float = 0,
):
    """Create a validated chat model using the selected provider."""

    timeout = settings.AI_MODEL_TIMEOUT
    max_retries = settings.AI_MODEL_MAX_RETRIES

    if not model_name or not model_name.strip():
        raise ValueError(
            f"Model name is missing for provider: {provider}"
        )

    if provider == "groq":
        api_key = settings.GROQ_API_KEY

        if not api_key:
            raise ValueError("GROQ_API_KEY is not configured")

        return ChatGroq(
            model=model_name,
            api_key=api_key,
            temperature=temperature,
            timeout=timeout,
            max_retries=max_retries,
        )

    if provider == "gemini":
        api_key = settings.GOOGLE_API_KEY

        if not api_key:
            raise ValueError("GOOGLE_API_KEY is not configured")

        return ChatGoogleGenerativeAI(
            model=model_name,
            api_key=api_key,
            temperature=temperature,
            timeout=timeout,
            max_retries=max_retries,
        )

    raise ValueError(f"Unsupported AI provider: {provider}")


def get_chat_model(task_name: str):
    """Create the primary model registered for an AI task."""

    if task_name not in MODEL_REGISTRY:
        raise ValueError(f"Unknown AI task: {task_name}")

    config = MODEL_REGISTRY[task_name]
    model_setting = config["model_setting"]

    if not hasattr(settings, model_setting):
        raise ValueError(
            f"Model setting '{model_setting}' is missing"
        )

    model_name = getattr(settings, model_setting)

    return create_model(
        provider=config["provider"],
        model_name=model_name,
        temperature=config["temperature"],
    )


def get_chat_model_for_fallback(
    provider: str,
    model_setting: str,
    temperature: float = 0,
):
    """Create a validated fallback model."""

    if not hasattr(settings, model_setting):
        raise ValueError(
            f"Fallback model setting '{model_setting}' is missing"
        )

    model_name = getattr(settings, model_setting)

    return create_model(
        provider=provider,
        model_name=model_name,
        temperature=temperature,
    )
