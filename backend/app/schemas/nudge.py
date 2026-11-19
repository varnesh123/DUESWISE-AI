"""Nudge schemas — CONTRACT.md §9."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class NudgeItem(BaseModel):
    id: str
    type: str
    priority: str
    title: str
    message: str
    created_at: datetime
    status: str


class NudgeList(BaseModel):
    items: List[NudgeItem]
    total: int


class NudgeActionResponse(BaseModel):
    id: str
    status: str
