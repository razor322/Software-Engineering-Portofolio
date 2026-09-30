from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.audit.router import router as audit_router
from app.auth.router import router as auth_router
from app.bookings.router import router as bookings_router
from app.core.config import get_settings
from app.core.database import engine
from app.core.errors import register_error_handlers
from app.core.middleware import CSRFMiddleware, RequestIDMiddleware
from app.health.router import router as health_router
from app.rooms.router import router as rooms_router
from app.users.router import router as users_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )
    # registration order = outermost first, so CSRF rejections still get a request id
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        # explicit list, not "*": with credentials the browser does not honour the wildcard
        allow_headers=["Content-Type", "X-CSRF-Token", "X-Request-ID"],
    )
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(CSRFMiddleware)
    register_error_handlers(app)
    app.include_router(health_router, prefix=settings.api_v1_prefix)
    app.include_router(auth_router, prefix=settings.api_v1_prefix)
    app.include_router(users_router, prefix=settings.api_v1_prefix)
    app.include_router(rooms_router, prefix=settings.api_v1_prefix)
    app.include_router(bookings_router, prefix=settings.api_v1_prefix)
    app.include_router(audit_router, prefix=settings.api_v1_prefix)

    # root only reports that the service is up; Swagger UI lives at /docs
    @app.get("/", include_in_schema=False)
    def root() -> dict[str, str]:
        return {"status": "running"}

    return app


app = create_app()
