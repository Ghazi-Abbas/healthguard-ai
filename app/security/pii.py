import re


EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

PHONE_PATTERN = re.compile(
    r"(?<!\w)\+?\d[\d ().-]{7,}\d(?!\w)"
)


def detect_pii_types(text: str) -> set[str]:
    """
    Return detected PII categories, not actual values.
    """

    detected: set[str] = set()

    if EMAIL_PATTERN.search(text):
        detected.add("EMAIL")

    if PHONE_PATTERN.search(text):
        detected.add("PHONE")

    return detected
