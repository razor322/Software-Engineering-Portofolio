from pydantic import BaseModel

from app.auth.schemas import UserOut


class UserListResponse(BaseModel):
    data: list[UserOut]


class UserResponse(BaseModel):
    data: UserOut
