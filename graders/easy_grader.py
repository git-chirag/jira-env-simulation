from __future__ import annotations

from env import JiraEnv
from graders.common import extract_rewards, fallback_env_score, ideal_trajectory, trajectory_score


def _resolve_env(*args, **kwargs) -> JiraEnv:
    env = kwargs.get("env")
    if isinstance(env, JiraEnv):
        return env
    for value in args:
        if isinstance(value, JiraEnv):
            return value
    return JiraEnv()


def grade(*args, **kwargs) -> float:
    for value in list(args) + list(kwargs.values()):
        if isinstance(value, JiraEnv):
            return fallback_env_score("easy", value)

    rewards = extract_rewards(*args, **kwargs)
    if rewards:
        return trajectory_score(rewards)
    return trajectory_score(ideal_trajectory("easy"))


class EasyGrader:
    def __call__(self, *args, **kwargs) -> float:
        return grade(*args, **kwargs)
