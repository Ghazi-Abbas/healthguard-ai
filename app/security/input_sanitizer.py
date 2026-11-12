
import json
from typing import Any


# Maximum serialized input sizes (characters).
MAX_AUTHORIZATION_SIZE = 20_000
MAX_CRITERIA_SIZE = 30_000
MAX_CLINICAL_PAGES_SIZE = 200_000


def serialize_untrusted_input(
    data: Any,
    max_size: int,
    field_name: str,
) -> str:
    """
    Validate and serialize application data before
    sending it to an LLM.

    Original policy and medical content is preserved.
    """

    if not isinstance(data, (dict, list)):
        raise ValueError(
            f"{field_name} must be a dictionary or list."
        )

    if not isinstance(max_size, int) or isinstance(max_size, bool):
        raise ValueError("max_size must be a positive integer.")

    if max_size <= 0:
        raise ValueError("max_size must be a positive integer.")

    try:
        serialized = json.dumps(
            data,
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{field_name} contains unsupported data."
        ) from exc

    if len(serialized) > max_size:
        raise ValueError(
            f"{field_name} exceeds the maximum allowed size."
        )

    return serialized
