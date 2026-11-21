"""Authentication schemas — CONTRACT.md §3.

Two authentication paths coexist:

- Real accounts: ``/auth/register`` and ``/auth/login`` return an opaque,
  server-stored session token.
- Demo personas: ``/auth/demo`` returns a deterministic synthetic user token.
  Demo mode is explicit and never used for normal login.
"""

from pydantic import BaseModel, Field

from app.security.passwords import MAX_PASSWORD_LENGTH, MIN_PASSWORD_LENGTH


class DemoRequest(BaseModel):
    persona: str = Field(..., description="One of: salaried, young_professional, shopkeeper")


class AuthUser(BaseModel):
    id: str
    name: str
    email: str | None = None
    persona: str
    currency: str = "INR"
    is_demo: bool = False


class DemoUser(BaseModel):
    id: str
    name: str
    email: str | None = None
    persona: str
    currency: str = "INR"
    is_demo: bool = True


class DemoResponse(BaseModel):
    user: DemoUser
    user_id: str
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int = 30


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(
        ...,
        min_length=MIN_PASSWORD_LENGTH,
        max_length=MAX_PASSWORD_LENGTH,
        description="At least 8 characters",
    )
    currency: str = Field("INR", min_length=3, max_length=3)


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=1, max_length=MAX_PASSWORD_LENGTH)


class AuthResponse(BaseModel):
    user: AuthUser
    user_id: str
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int


class UserResponse(BaseModel):
    id: str
    name: str
    email: str | None = None
    persona: str
    currency: str = "INR"
    is_demo: bool = False
