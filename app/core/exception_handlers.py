
import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse


logger = logging.getLogger(__name__)


def get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def create_error_response(
    request: Request,
    status_code: int,
    error_code: str,
    message: str,
    headers: dict[str, str] | None = None
) -> JSONResponse:

    return JSONResponse(
        status_code=status_code,
        headers=headers,
        content={
            "success": False,
            "error": {
                "code": error_code,
                "message": message
            },
            "request_id": get_request_id(request)
        }
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
):
    error_messages = {
        400: ("BAD_REQUEST", "Bad request."),
        401: ("UNAUTHORIZED", "Authentication required."),
        403: (
            "FORBIDDEN",
            "You do not have permission to perform this action."
        ),
        404: ("NOT_FOUND", "Resource not found."),
        409: (
            "CONFLICT",
            "The request conflicts with the current resource state."
        ),
        413: ("FILE_TOO_LARGE", "The uploaded file is too large."),
        422: (
            "UNPROCESSABLE_ENTITY",
            "The request could not be processed."
        ),
        429: ("TOO_MANY_REQUESTS", "Too many requests."),
        503: (
            "SERVICE_UNAVAILABLE",
            "The service is temporarily unavailable."
        )
    }

    error_code, message = error_messages.get(
        exc.status_code,
        ("HTTP_ERROR", "The request could not be completed.")
    )

    return create_error_response(
        request=request,
        status_code=exc.status_code,
        error_code=error_code,
        message=message,
        headers=exc.headers
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    return create_error_response(
        request=request,
        status_code=422,
        error_code="VALIDATION_ERROR",
        message="Request validation failed. Check your input."
    )


async def unexpected_exception_handler(
    request: Request,
    exc: Exception
):
    request_id = get_request_id(request)

    # Log the traceback for debugging.
    # SensitiveDataFilter protects sensitive values in the logs.
    logger.error(
        "Unhandled application exception | request_id=%s",
        request_id,
        exc_info=(
            type(exc),
            exc,
            exc.__traceback__
        )
    )

    return create_error_response(
        request=request,
        status_code=500,
        error_code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred."
    )
