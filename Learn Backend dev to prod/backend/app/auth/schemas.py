from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: str
    roles: list[str]


class LoginResponse(BaseModel):
    user: UserOut


class UserResponse(BaseModel):
    data: UserOut


class CsrfToken(BaseModel):
    token: str


class CsrfTokenResponse(BaseModel):
    data: CsrfToken