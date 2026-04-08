from typing import List

from pydantic import BaseModel

try:
    from openenv.core.env_server.types import Action as OpenEnvAction
    from openenv.core.env_server.types import Observation as OpenEnvObservation
    from openenv.core.env_server.types import State as OpenEnvState
except Exception:  # pragma: no cover
    OpenEnvAction = BaseModel
    OpenEnvObservation = BaseModel
    OpenEnvState = BaseModel


class JiraTaskAction(OpenEnvAction):
    action: str


class JiraTaskObservation(OpenEnvObservation):
    text: str
    task_id: str


class JiraTaskState(OpenEnvState):
    task_id: str
    step: int
    max_steps: int
    history: List[str]
    done: bool
