from __future__ import annotations

from env import JiraEnv
from graders.common import extract_rewards, ideal_trajectory, strict_score, trajectory_score


def grade(*args, **kwargs) -> float:
    rewards = extract_rewards(*args, **kwargs)
    if rewards:
        return trajectory_score(rewards)

    for value in list(args) + list(kwargs.values()):
        if isinstance(value, JiraEnv):
            # Dedicated workflow-discipline task; use its ideal trajectory if only a raw env is passed.
            return trajectory_score(ideal_trajectory("assignment_guard"))

    return trajectory_score(ideal_trajectory("assignment_guard"))


class AssignmentGuardGrader:
    def __call__(self, *args, **kwargs) -> float:
        return strict_score(grade(*args, **kwargs))
