from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field, ConfigDict


class BaseAgentResponse(BaseModel):
    type: Literal["response", "tool_call"]
    content: Optional[str] = None
    query: Optional[str] = None
    engine: str = "duck-duck-go"
    max_value: Optional[int] = None


class CalendarAgentResponse(BaseModel):
    type: Literal["response", "tool_call"]
    content: Optional[str] = None
    command: Optional[
        Literal["new-event", "event-list", "event-details", "delete-event"]
    ] = None
    name: Optional[str] = None
    description: Optional[str] = None
    date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    freq: Optional[Literal["daily", "weekly", "monthly", "yearly"]] = None


class EmailAgentResponse(BaseModel):
    type: Literal["response", "tool_call"]
    content: Optional[str] = None
    command: Optional[
        Literal["new-email", "email-list", "email-details", "delete-email"]
    ] = None
    to: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    query: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    max_value: Optional[int] = None


class ClassificationResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    type: Literal["classification"]
    class_name: str = Field(alias="class")
