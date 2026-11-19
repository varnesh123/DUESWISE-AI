"""Authentication / demo-session schemas — CONTRACT.md §3."""

from pydantic import BaseModel, Field


class DemoRequest(BaseModel):
    persona: str = Field(..., description="One of: salaried, young_professional, shopkeeper")


class DemoUser(BaseModel):
    id: str
    name: str
    persona: str
    currency: str = "INR"


class DemoResponse(BaseModel):
    user: DemoUser
    user_id: str
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int = 30


class UserResponse(BaseModel):
    id: str
    name: str
    persona: str
    currency: str = "INR"
