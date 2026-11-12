
from groq import (
    APIConnectionError,
    APITimeoutError,
    RateLimitError,
    InternalServerError,
)

from google.genai.errors import (
    APIError,
    ServerError,
)


# Temporary failures that may recover on retry or fallback.
RETRYABLE_ERRORS = (
    # Groq errors
    APIConnectionError,
    APITimeoutError,
    RateLimitError,
    InternalServerError,

    # Gemini errors
    ServerError,
)


def is_retryable_error(error: Exception) -> bool:
    """
    Check whether an AI provider error is temporary
    and may be worth retrying or triggering fallback.
    """
    return isinstance(error, RETRYABLE_ERRORS)
