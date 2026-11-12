
import logging

from app.core.logging_filter import SensitiveDataFilter

import io
def test_email_is_redacted():

    record = logging.LogRecord(
        "test",
        logging.INFO,
        "",
        0,
        "Email: patient@example.com",
        (),
        None,
    )

    sensitive_filter = SensitiveDataFilter()
    sensitive_filter.filter(record)

    assert "patient@example.com" not in record.getMessage()
    assert "[EMAIL_REDACTED]" in record.getMessage()


def test_bearer_token_is_redacted():

    record = logging.LogRecord(
        "test",
        logging.INFO,
        "",
        0,
        "Authorization: Bearer abc123456789",
        (),
        None,
    )

    SensitiveDataFilter().filter(record)

    assert "abc123456789" not in record.getMessage()
    assert "[TOKEN_REDACTED]" in record.getMessage()


def test_password_is_redacted():

    record = logging.LogRecord(
        "test",
        logging.INFO,
        "",
        0,
        "password=MySecret123",
        (),
        None,
    )

    SensitiveDataFilter().filter(record)

    assert "MySecret123" not in record.getMessage()
    assert "[SECRET_REDACTED]" in record.getMessage()



def test_jwt_token_is_redacted():

    jwt_token = (
        "eyJhbGciOiJIUzI1NiJ9."
        "eyJzdWIiOiIxMjM0NTYifQ."
        "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    )

    record = logging.LogRecord(
        "test",
        logging.INFO,
        "",
        0,
        f"Token: {jwt_token}",
        (),
        None,
    )

    SensitiveDataFilter().filter(record)

    assert jwt_token not in record.getMessage()
    assert "[JWT_REDACTED]" in record.getMessage()


def test_phone_number_is_redacted():

    phone_number = "+91 98765 43210"

    record = logging.LogRecord(
        "test",
        logging.INFO,
        "",
        0,
        f"Patient phone: {phone_number}",
        (),
        None,
    )

    SensitiveDataFilter().filter(record)

    assert phone_number not in record.getMessage()
    assert "[PHONE_REDACTED]" in record.getMessage()




def test_exception_information_is_redacted():

    try:
        raise ValueError(
            "Failed for patient@example.com"
        )

    except ValueError:
        record = logging.LogRecord(
            "test",
            logging.ERROR,
            "",
            0,
            "Document processing failed",
            (),
            __import__("sys").exc_info(),
        )

    SensitiveDataFilter().filter(record)

    assert record.exc_info is None

    assert record.exc_text is not None

    assert "patient@example.com" not in record.exc_text

    assert "[EMAIL_REDACTED]" in record.exc_text






def test_exception_traceback_is_redacted_in_actual_log_output():

    output = io.StringIO()

    handler = logging.StreamHandler(output)
    handler.addFilter(SensitiveDataFilter())

    logger = logging.getLogger("security_test_logger")
    logger.setLevel(logging.ERROR)
    logger.propagate = False
    logger.addHandler(handler)

    try:
        try:
            raise ValueError(
                "Failed for patient@example.com"
            )
        except ValueError:
            logger.exception("Document processing failed")

        log_output = output.getvalue()

        assert "patient@example.com" not in log_output
        assert "[EMAIL_REDACTED]" in log_output

    finally:
        logger.removeHandler(handler)
        handler.close()
