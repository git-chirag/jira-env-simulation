from __future__ import annotations

from env import JiraEnv
from tasks_runner import run_hard_task


def _resolve_env(*args, **kwargs) -> JiraEnv:
    env = kwargs.get("env")
    if isinstance(env, JiraEnv):
        return env
    for value in args:
        if isinstance(value, JiraEnv):
            return value
    return JiraEnv()


def grade(*args, **kwargs) -> float:
    working_env = _resolve_env(*args, **kwargs)
    score = float(run_hard_task(working_env))
    return round(max(0.001, min(0.999, score)), 4)


class HardGrader:
    def __call__(self, *args, **kwargs) -> float:
        return grade(*args, **kwargs)
