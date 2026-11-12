import re
from collections.abc import Iterable

from app.security.pii import (
    EMAIL_PATTERN,
    PHONE_PATTERN,
)


def redact_sensitive_text(
    text: str,
    known_identifiers: Iterable[str] = (),
) -> str:
    """
    Redact common personal identifiers and explicitly
    supplied values.

    This is a basic utility, not a PHI de-identification
    guarantee.
    """

    # Replace known identifiers first.
    identifiers = sorted(
        {
            item
            for item in known_identifiers
            if item
        },
        key=len,
        reverse=True,
    )

    for identifier in identifiers:
        text = re.sub(
            re.escape(identifier),
            "[REDACTED]",
            text,
            flags=re.IGNORECASE,
        )

    # Replace emails.
    text = EMAIL_PATTERN.sub(
        "[REDACTED_EMAIL]",
        text,
    )

    # Replace common phone-number patterns.
    text = PHONE_PATTERN.sub(
        "[REDACTED_PHONE]",
        text,
    )

    return text
