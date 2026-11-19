"""System status and health schemas."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str = "ok"


class SystemStatus(BaseModel):
    name: str
    version: str
    environment: str
    database: str
