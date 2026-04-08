from __future__ import annotations

from tasks_runner import run_easy_task, run_hard_task, run_medium_task


def _strict_score(value: float) -> float:
    return max(0.01, min(float(value), 0.99))


def grade_easy(env) -> float:
    score = float(run_easy_task(env))
    return _strict_score(score)


def grade_medium(env) -> float:
    score = float(run_medium_task(env))
    return _strict_score(score)


def grade_hard(env) -> float:
    score = float(run_hard_task(env))
    return _strict_score(score)


__all__ = ["grade_easy", "grade_medium", "grade_hard"]
