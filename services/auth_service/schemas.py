from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserProfile(BaseModel):
    id: int
    username: str
    role: str
    employee_name: str
    manager_id: int | None = None


class ValidateTokenResponse(BaseModel):
    valid: bool
    user: UserProfile | None = None
