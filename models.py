from typing import List

from openenv.core.env_server.types import Action, Observation, State
from pydantic import BaseModel


class JiraTaskAction(Action):
    action: str


class JiraStepRequest(BaseModel):
    action: JiraTaskAction


class JiraTaskObservation(Observation):
    text: str
    task_id: str


class JiraTaskState(State):
    task_id: str
    step: int
    max_steps: int
    history: List[str]
    done: bool
