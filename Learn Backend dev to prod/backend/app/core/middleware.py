import re
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


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
