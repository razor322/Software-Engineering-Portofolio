import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("officehub")

STATUS_CODES_BY_NAME = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    429: "TOO_MANY_REQUESTS",
    500: "INTERNAL_ERROR",
    503: "SERVICE_UNAVAILABLE",
}


def error_response(
    status_code: int,
    code: str,
    message: str,
    request_id: str | None,
    details: object | None = None,
) -> JSONResponse:
    error: dict = {"code": code, "message": message, "request_id": request_id}
    if details is not None:
        error["details"] = details
    return JSONResponse(status_code=status_code, content={"error": error})


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException):
        request_id = getattr(request.state, "request_id", None)
        code = STATUS_CODES_BY_NAME.get(exc.status_code, f"HTTP_{exc.status_code}")
        message = exc.detail if isinstance(exc.detail, str) else "Request failed."
        return error_response(exc.status_code, code, message, request_id)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        request_id = getattr(request.state, "request_id", None)
        # ponytail: errors() keeps only loc/msg/type — safe to expose, no internals
        details = exc.errors(include_url=False, include_context=False, include_input=False)
        return error_response(
            422,
            "VALIDATION_ERROR",
            "Request validation failed.",
            request_id,
            details=details,
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", None)
        logger.exception("unhandled error request_id=%s path=%s", request_id, request.url.path)
        # ponytail: never leak internals to the client (PRD 4.2)
        return error_response(500, "INTERNAL_ERROR", "Internal server error.", request_id)
