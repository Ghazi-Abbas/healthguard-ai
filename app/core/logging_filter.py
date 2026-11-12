
import logging
import re
import traceback
import copy


class SensitiveDataFilter(logging.Filter):

    PATTERNS = [
        # Email addresses
        (
            re.compile(
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
            ),
            "[EMAIL_REDACTED]",
        ),

        # JWT tokens
        (
            re.compile(
                r"\beyJ[A-Za-z0-9_-]+\."
                r"[A-Za-z0-9_-]+\."
                r"[A-Za-z0-9_-]+\b"
            ),
            "[JWT_REDACTED]",
        ),

        # Bearer tokens
        (
            re.compile(
                r"(?i)(Bearer\s+)[A-Za-z0-9._~+/-]+=*"
            ),
            r"\1[TOKEN_REDACTED]",
        ),

        # Common secret assignments
        (
            re.compile(
                r"""(?i)\b(password|api_key|secret_key|access_key|aws_secret_access_key)\s*[:=]\s*['"]?[^'"\s,}]+"""
            ),
            r"\1=[SECRET_REDACTED]",
        ),

        # Phone numbers
        (
            re.compile(
                r"(?<!\w)(?:\+\d{1,3}[\s.-]?)?"
                r"(?:\d[\s().-]?){9,12}\d(?!\w)"
            ),
            "[PHONE_REDACTED]",
        ),
    ]

    def redact(self, text: str) -> str:
        """Redact sensitive values from text."""

        for pattern, replacement in self.PATTERNS:
            text = pattern.sub(replacement, text)

        return text

    def filter(self, record: logging.LogRecord):
        """
        Redact sensitive log messages and exception tracebacks.

        Preserve Uvicorn access-log arguments because its
        formatter requires exactly five arguments.
        """

        # --------------------------------------------------
        # 1. Special handling for Uvicorn access logs
        # --------------------------------------------------

        if record.name == "uvicorn.access":

            safe_record = copy.copy(record)

            if isinstance(safe_record.args, tuple):

                args = list(safe_record.args)

                # Uvicorn access-log argument positions:
                # 0 = client address
                # 1 = HTTP method
                # 2 = requested path
                # 3 = HTTP version
                # 4 = status code

                if len(args) == 5 and isinstance(args[2], str):
                    args[2] = self.redact(args[2])

                safe_record.args = tuple(args)

            return safe_record

        # --------------------------------------------------
        # 2. Redact normal application log messages
        # --------------------------------------------------

        message = record.getMessage()

        record.msg = self.redact(message)
        record.args = ()

        # --------------------------------------------------
        # 3. Redact exception tracebacks
        # --------------------------------------------------

        if record.exc_info:

            exception_text = "".join(
                traceback.format_exception(*record.exc_info)
            )

            record.exc_text = self.redact(exception_text)
            record.exc_info = None

        elif record.exc_text:

            record.exc_text = self.redact(record.exc_text)

        return True
