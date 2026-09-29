from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.database import database_available

router = APIRouter(tags=["health"])


@router.get("/health/live")
async def live():
    return {"status": "ok"}


@router.get("/health/ready")
async def ready():
    db_ok = await database_available()
    body = {
        "status": "ready" if db_ok else "unavailable",
        "dependencies": {"database": "ok" if db_ok else "error"},
    }
    if not db_ok:
        return JSONResponse(status_code=503, content=body)
    return body
