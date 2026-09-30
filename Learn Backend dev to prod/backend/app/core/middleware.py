import re
import secrets
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.config import get_settings
from app.core.errors import error_response
from app.core.security import CSRF_COOKIE, CSRF_HEADER

_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a request id to every request and echo it back as X-Request-ID."""

    async def dispatch(self, request: Request, call_next):
        incoming = request.headers.get("X-Request-ID", "")
        # ponytail: only accept well-formed client ids, otherwise mint our own
        request_id = incoming if _REQUEST_ID_RE.match(incoming) else f"req_{uuid.uuid4().hex}"
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class CSRFMiddleware(BaseHTTPMiddleware):
    """Double-submit cookie check for cookie-authenticated requests.

    SameSite=Lax already blocks cross-site form posts from carrying the session
    cookie, but it is not a complete defence and it degrades with future
    same-site subdomains. The client must echo the readable CSRF cookie in the
    X-CSRF-Token header; an attacker on another origin can trigger the request but
    cannot read the cookie to copy it into the header.

    The login and CSRF-token endpoints are exempt: no session exists yet.
    """

    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        exempt = {
            f"{settings.api_v1_prefix}/auth/login",
            f"{settings.api_v1_prefix}/auth/csrf",
        }
        if request.method in _UNSAFE_METHODS and request.url.path not in exempt:
            cookie_token = request.cookies.get(CSRF_COOKIE, "")
            header_token = request.headers.get(CSRF_HEADER, "")
            if not cookie_token or not secrets.compare_digest(cookie_token, header_token):
                return error_response(
                    403,
                    "CSRF_TOKEN_INVALID",
                    "Missing or invalid CSRF token.",
                    getattr(request.state, "request_id", None),
                )
        return await call_next(request)