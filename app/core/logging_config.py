
import logging

from app.core.logging_filter import SensitiveDataFilter


def add_sensitive_filter(handler):

    already_added = any(
        isinstance(log_filter, SensitiveDataFilter)
        for log_filter in handler.filters
    )

    if not already_added:
        handler.addFilter(SensitiveDataFilter())


def setup_logging():

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Protect root logging handlers.
    root_logger = logging.getLogger()

    for handler in root_logger.handlers:
        add_sensitive_filter(handler)

    # Protect Uvicorn's independent handlers.
    uvicorn_loggers = [
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
    ]

    for logger_name in uvicorn_loggers:

        logger = logging.getLogger(logger_name)

        for handler in logger.handlers:
            add_sensitive_filter(handler)



"""
Understanding the code:
- level=logging.INFO: displays INFO, WARNING, ERROR and CRITICAL messages.
- asctime: records the timestamp.
- levelname: shows the severity.
- name: identifies the module that generated the log.
- message: contains the actual log message.
"""
