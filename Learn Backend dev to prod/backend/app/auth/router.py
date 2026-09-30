from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import service
from app.auth.models import User
from app.auth.schemas import CsrfTokenResponse, LoginRequest, UserOut, UserResponse
from app.core.config import get_settings
from app.core.database import get_session
from app.core.security import CSRF_COOKIE, SESSION_COOKIE, new_csrf_token

router = APIRouter(prefix="/auth", tags=["auth"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def _to_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        name=user.name,
        email=user.email,
        roles=[role.name.value for role in user.roles],
    )


def _set_cookies(response: Response, session_token: str, csrf_token: str) -> None:
    settings = get_settings()
    max_age = settings.session_ttl_hours * 3600
    response.set_cookie(
        SESSION_COOKIE,
        session_token,
        max_age=max_age,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        path="/",
    )
    # readable by JS on purpose — the client echoes it back in the CSRF header
    response.set_cookie(
        CSRF_COOKIE,
        csrf_token,
        max_age=max_age,
        httponly=False,
        secure=settings.is_production,
        samesite="lax",
        path="/",
    )


async def get_current_user(
    session: SessionDep,
    session_token: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> User:
    user = await service.resolve_session(session, session_token)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post("/login", response_model=UserResponse)
async def login(payload: LoginRequest, response: Response, session: SessionDep):
    user = await service.authenticate(session, payload.email, payload.password)
    session_token = await service.start_session(session, user)
    _set_cookies(response, session_token, new_csrf_token())
    return UserResponse(data=_to_out(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    session: SessionDep,
    session_token: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> Response:
    await service.end_session(session, session_token)
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(SESSION_COOKIE, path="/")
    response.delete_cookie(CSRF_COOKIE, path="/")
    return response


@router.get("/me", response_model=UserResponse)
async def me(user: CurrentUser):
    return UserResponse(data=_to_out(user))


@router.get("/csrf", response_model=CsrfTokenResponse)
async def csrf(response: Response):
    token = new_csrf_token()
    settings = get_settings()
    response.set_cookie(
        CSRF_COOKIE,
        token,
        max_age=settings.session_ttl_hours * 3600,
        httponly=False,
        secure=settings.is_production,
        samesite="lax",
        path="/",
    )
    return CsrfTokenResponse(data={"token": token})