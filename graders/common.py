from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from env import JiraEnv
from tasks.definitions import TASKS
from tasks.graders import grade_action
from tasks_runner import run_easy_task, run_hard_task, run_medium_task


def strict_score(value: float) -> float:
    return round(max(0.01, min(0.99, float(value))), 2)


def extract_rewards(*args, **kwargs) -> list[float]:
    rewards: list[float] = []

    def _append_values(value: Any) -> None:
        if isinstance(value, (int, float)):
            rewards.append(float(value))
            return

        if isinstance(value, str):
            try:
                rewards.append(float(value))
            except ValueError:
                return
            return

        if isinstance(value, dict):
            for key in ("rewards", "step_rewards", "history", "trajectory"):
                if key in value:
                    _append_values(value[key])
            return

        if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
            for item in value:
                _append_values(item)

    for arg in args:
        _append_values(arg)
    for value in kwargs.values():
        _append_values(value)

    return rewards


def trajectory_score(step_rewards: list[float]) -> float:
    if not step_rewards:
        return 0.01

    rewards = [max(0.01, min(0.99, float(value))) for value in step_rewards]
    base_score = sum(rewards) / len(rewards)

    strong_steps = sum(1 for reward in rewards if reward >= 0.8)
    weak_steps = sum(1 for reward in rewards if reward <= 0.1)
    catastrophic_failures = sum(1 for reward in rewards if reward <= 0.05)

    consistency_bonus = 0.05 * (strong_steps / len(rewards))
    behavior_penalty = 0.06 * weak_steps + 0.18 * catastrophic_failures

    volatility = 0.0
    if len(rewards) > 1:
        deltas = [abs(current - previous) for previous, current in zip(rewards, rewards[1:])]
        volatility = sum(deltas) / len(deltas)

    stability_bonus = 0.03 if volatility < 0.20 else 0.0
    final_score = base_score + consistency_bonus + stability_bonus - behavior_penalty
    return strict_score(final_score)


def ideal_trajectory(task_id: str) -> list[float]:
    task = TASKS.get(task_id, {})
    rewards: list[float] = []
    for step in task.get("steps", []):
        signals = step.get("signals", {})
        rewards.append(grade_action(task_id, signals.get("ideal_action", ""), signals))
    return rewards


def fallback_env_score(task_id: str, env: JiraEnv) -> float:
    if task_id == "easy":
        return strict_score(run_easy_task(env))
    if task_id == "medium":
        return strict_score(run_medium_task(env))
    if task_id == "hard":
        return strict_score(run_hard_task(env))
    return strict_score(trajectory_score(ideal_trajectory(task_id)))
