from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


ActionType = Literal[
    "assign_ticket",
    "update_status",
    "resolve_ticket",
    "change_priority",
    "add_comment",
]
Priority = Literal["low", "medium", "high"]
Status = Literal["open", "in_progress", "resolved"]


class Action(BaseModel):
    action_type: ActionType
    ticket_id: int
    user: str | None = None
    status: Status | None = None
    priority: Priority | None = None
    comment: str | None = None


class Ticket(BaseModel):
    id: int
    title: str
    priority: Priority
    status: Status
    assigned_to: str | None = None
    comments: list[str] = Field(default_factory=list)
    created_step: int


class Observation(BaseModel):
    tickets: list[Ticket]
    current_step: int


class StepResult(BaseModel):
    observation: Observation
    reward: float
    done: bool
    info: dict[str, Any] = Field(default_factory=dict)
