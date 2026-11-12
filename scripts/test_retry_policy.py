from google.genai.errors import ServerError, APIError
from app.ai.gateway.fallback_manager import add_model_fallbacks
from app.ai.gateway.retry_policy import is_retryable_error


def test_gemini_server_error_is_retryable():
    error = ServerError(
        503,
        {"message": "Service unavailable"},
    )

    assert is_retryable_error(error) is True


def test_gemini_api_error_is_not_automatically_retryable():
    error = APIError(
        400,
        {"message": "Invalid request"},
    )

    assert is_retryable_error(error) is False


def test_gemini_server_error_triggers_fallback(monkeypatch):
    from google.genai.errors import ServerError
    from langchain_core.runnables import RunnableLambda

    fallback = RunnableLambda(lambda data: "Fallback success")

    def simulate_gemini_error(data):
        raise ServerError(
            503,
            {"message": "Service unavailable"},
        )

    primary = RunnableLambda(simulate_gemini_error)

    monkeypatch.setattr(
        "app.ai.gateway.fallback_manager.get_fallback_models",
        lambda **kwargs: [fallback],
    )

    chain = add_model_fallbacks(
        primary,
        "policy_query_rewriting",
    )

    result = chain.invoke({"query": "test"})

    assert result == "Fallback success"
