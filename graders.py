from __future__ import annotations

from env import JiraEnv
from tasks import run_easy_task, run_hard_task, run_medium_task


def grade_easy_task(env: JiraEnv) -> float:
    return float(run_easy_task(env))


def grade_medium_task(env: JiraEnv) -> float:
    return float(run_medium_task(env))


def grade_hard_task(env: JiraEnv) -> float:
    return float(run_hard_task(env))


# Extra aliases help simple validators that scan for either "grader" or "grade_*"
# naming patterns without changing the underlying task logic.
easy_grader = grade_easy_task
medium_grader = grade_medium_task
hard_grader = grade_hard_task


__all__ = [
    "grade_easy_task",
    "grade_medium_task",
    "grade_hard_task",
    "easy_grader",
    "medium_grader",
    "hard_grader",
]
