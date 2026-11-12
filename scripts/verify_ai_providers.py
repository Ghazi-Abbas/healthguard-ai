
from app.ai.gateway.model_factory import create_model
from app.core.config import settings


def verify_provider(provider, model_name, api_key):
    print(f"\nChecking {provider}...")

    if not api_key:
        print(f"{provider}: API key is missing")
        return

    try:
        model = create_model(
            provider=provider,
            model_name=model_name,
            temperature=0,
        )

        response = model.invoke("Reply with exactly: OK")

        print(f"{provider}: SUCCESS")
        print(f"Response: {response.content}")


    except Exception as error:
        print(f"{provider}: FAILED")
        print(f"Error type: {type(error).__name__}")
        print(f"Error module: {type(error).__module__}")
        print(f"Error MRO: {type(error).__mro__}")
        print(f"Status code: {getattr(error, 'status_code', None)}")
        print(f"Error: {error}")


verify_provider(
    "groq",
    settings.GROQ_MODEL,
    settings.GROQ_API_KEY,
)

verify_provider(
    "gemini",
    settings.GEMINI_EVAL_MODEL,
    settings.GOOGLE_API_KEY,
)
