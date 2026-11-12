
from unittest.mock import Mock

from groq import APITimeoutError
from langchain_core.runnables import RunnableLambda

from app.ai.gateway.fallback_manager import add_model_fallbacks


def test_fallback_manager_attaches_configured_fallback(monkeypatch):
    fallback = RunnableLambda(lambda data: "Fallback success")

    monkeypatch.setattr(
        "app.ai.gateway.fallback_manager.get_fallback_models",
        lambda task_name, schema=None, structured_output_kwargs=None: [
            fallback
        ],
    )

    primary = RunnableLambda(lambda data: "Primary success")

    chain = add_model_fallbacks(
        primary,
        "clinical_evidence",
    )

    assert chain.invoke({"test": "data"}) == "Primary success"

    assert APITimeoutError in chain.exceptions_to_handle


def test_fallback_manager_executes_fallback_on_timeout(monkeypatch):
    import httpx

    def simulate_timeout(data):
        request = httpx.Request(
            "POST",
            "https://api.groq.com/test",
        )

        raise APITimeoutError(request=request)

    primary = RunnableLambda(simulate_timeout)

    fallback = RunnableLambda(
        lambda data: "Fallback success"
    )

    monkeypatch.setattr(
        "app.ai.gateway.fallback_manager.get_fallback_models",
        lambda task_name, schema=None, structured_output_kwargs=None: [
            fallback
        ],
    )

    chain = add_model_fallbacks(
        primary,
        "clinical_evidence",
    )

    result = chain.invoke({"test": "data"})

    assert result == "Fallback success"


def test_non_retryable_error_does_not_trigger_fallback(monkeypatch):
    primary = RunnableLambda(
        lambda data: (_ for _ in ()).throw(
            ValueError("Invalid input")
        )
    )

    fallback_called = Mock()

    fallback = RunnableLambda(
        lambda data: fallback_called()
    )

    monkeypatch.setattr(
        "app.ai.gateway.fallback_manager.get_fallback_models",
        lambda task_name, schema=None, structured_output_kwargs=None: [
            fallback
        ],
    )

    chain = add_model_fallbacks(
        primary,
        "clinical_evidence",
    )

    try:
        chain.invoke({"test": "data"})
        assert False, "Expected ValueError"
    except ValueError:
        pass

    fallback_called.assert_not_called()


def test_fallback_activation_is_logged(monkeypatch, caplog):
    import logging
    import httpx

    from groq import APITimeoutError

    fallback = RunnableLambda(
        lambda data: "Fallback success"
    )

    def simulate_timeout(data):
        request = httpx.Request(
            "POST",
            "https://api.groq.com/test",
        )
        raise APITimeoutError(request=request)

    primary = RunnableLambda(simulate_timeout)

    # Mock only the model factory.
    # Keep the real get_fallback_models() function running
    # so it can attach the logging listener.
    monkeypatch.setattr(
        "app.ai.gateway.fallback_manager.get_chat_model_for_fallback",
        lambda **kwargs: fallback,
    )

    with caplog.at_level(
        logging.WARNING,
        logger="app.ai.gateway.fallback_manager",
    ):
        chain = add_model_fallbacks(
            primary,
            "clinical_evidence",
        )

        result = chain.invoke({"test": "data"})

    assert result == "Fallback success"

    assert any(
        "AI fallback activated" in record.message
        for record in caplog.records
    )
