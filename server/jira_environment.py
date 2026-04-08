from __future__ import annotations

from typing import Any, Optional

try:
    from openenv.core.env_server import Environment
except Exception as exc:  # pragma: no cover
    raise ImportError("openenv-core is required for the server environment.") from exc

try:
    from ..models import JiraTaskAction, JiraTaskObservation, JiraTaskState
    from ..tasks.definitions import TASKS
    from ..tasks.graders import grade_action
except (ImportError, ValueError):
    from models import JiraTaskAction, JiraTaskObservation, JiraTaskState
    from tasks.definitions import TASKS
    from tasks.graders import grade_action


class JiraTaskEnvironment(Environment[JiraTaskAction, JiraTaskObservation, JiraTaskState]):
    SUPPORTS_CONCURRENT_SESSIONS = True

    def __init__(self) -> None:
        self._task_id: Optional[str] = None
        self._task_def: dict[str, Any] | None = None
        self._step_idx = 0
        self._done = False
        self._rewards: list[float] = []

    def reset(
        self,
        seed: Optional[int] = None,
        episode_id: Optional[str] = None,
        **kwargs: Any,
    ) -> JiraTaskObservation:
        del seed, episode_id
        self._task_id = kwargs.get("task_id") or kwargs.get("task") or "easy"
        if self._task_id not in TASKS:
            self._task_id = "easy"

        self._task_def = TASKS[self._task_id]
        self._step_idx = 0
        self._done = False
        self._rewards = []

        first_step = self._task_def["steps"][0]
        return JiraTaskObservation(
            text=first_step["observation"],
            task_id=self._task_id,
        )

    def step(self, action: JiraTaskAction) -> JiraTaskObservation:
        if self._task_id is None or self._task_def is None:
            raise RuntimeError("Call reset() before step()")
        if self._done:
            raise RuntimeError("Episode is finished")

        step_data = self._task_def["steps"][self._step_idx]
        reward = grade_action(self._task_id, action.action, step_data["signals"])
        self._rewards.append(reward)
        self._step_idx += 1
        self._done = self._step_idx >= len(self._task_def["steps"])

        next_obs_text = ""
        if not self._done:
            next_obs_text = self._task_def["steps"][self._step_idx]["observation"]

        return JiraTaskObservation(
            text=next_obs_text,
            task_id=self._task_id,
            reward=reward,
            done=self._done,
            metadata={
                "step": self._step_idx,
                "task_id": self._task_id,
                "rewards_so_far": self._rewards,
            },
        )

    @property
    def state(self) -> JiraTaskState:
        return JiraTaskState(
            task_id=self._task_id or "",
            step=self._step_idx,
            max_steps=len(self._task_def["steps"]) if self._task_def else 0,
            history=[str(reward) for reward in self._rewards],
            done=self._done,
        )
