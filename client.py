from __future__ import annotations

from typing import Any, Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult

try:
    from .models import JiraTaskAction, JiraTaskObservation, JiraTaskState
except ImportError:
    from models import JiraTaskAction, JiraTaskObservation, JiraTaskState


class JiraClient(EnvClient[JiraTaskAction, JiraTaskObservation, JiraTaskState]):
    """
    Client for the Jira task environment.

    This mirrors the OpenEnv client pattern used by the reference project.
    """

    def _step_payload(self, action: JiraTaskAction) -> Dict[str, Any]:
        return action.model_dump()

    def _parse_result(self, payload: Dict[str, Any]) -> StepResult[JiraTaskObservation]:
        obs_data = payload.get("observation", {})
        observation = JiraTaskObservation(
            text=obs_data.get("text", payload.get("text", "")),
            task_id=obs_data.get("task_id", payload.get("task_id", "")),
            reward=payload.get("reward"),
            done=payload.get("done", False),
            metadata=payload.get("info", payload.get("metadata", {})),
        )

        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict[str, Any]) -> JiraTaskState:
        return JiraTaskState(
            task_id=payload.get("task_id", ""),
            step=payload.get("step", 0),
            max_steps=payload.get("max_steps", 0),
            history=payload.get("history", []),
            done=payload.get("done", False),
        )
