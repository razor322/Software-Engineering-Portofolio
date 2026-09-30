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


class AppError(Exception):
    """A failure the client is allowed to understand, with a domain-specific code.

    An HTTPException always maps to a generic code (409 -> CONFLICT); the API
    contract needs codes like BOOKING_CONFLICT, so domain failures raise this
    instead.
    """

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


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
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError):
        return error_response(
            exc.status_code, exc.code, exc.message, getattr(request.state, "request_id", None)
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException):
        request_id = getattr(request.state, "request_id", None)
        code = STATUS_CODES_BY_NAME.get(exc.status_code, f"HTTP_{exc.status_code}")
        message = exc.detail if isinstance(exc.detail, str) else "Request failed."
        return error_response(exc.status_code, code, message, request_id)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        request_id = getattr(request.state, "request_id", None)
        # ponytail: pick loc/msg/type only — safe to expose, no internals
        details = [
            {"loc": list(item.get("loc", ())), "msg": item.get("msg"), "type": item.get("type")}
            for item in exc.errors()
        ]
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
