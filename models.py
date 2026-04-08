from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

try:
    from openenv.core.env_server.types import Action as OpenEnvAction
    from openenv.core.env_server.types import Observation as OpenEnvObservation
    from openenv.core.env_server.types import State as OpenEnvState
except Exception:  # pragma: no cover
    OpenEnvAction = BaseModel
    OpenEnvObservation = BaseModel
    OpenEnvState = BaseModel


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


class TaskInfo(BaseModel):
    task_id: str
    difficulty: str
    description: str
    action_schema: dict[str, Any] = Field(default_factory=dict)


class JiraTaskAction(OpenEnvAction):
    action: str


class JiraTaskObservation(OpenEnvObservation):
    text: str
    task_id: str


class JiraTaskState(OpenEnvState):
    task_id: str
    step: int
    max_steps: int
    history: list[str]
    done: bool
