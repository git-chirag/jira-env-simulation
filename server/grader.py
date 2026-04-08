from __future__ import annotations

from typing import Any

from server.tasks import TASK_REGISTRY


def _clamp_score(value: float) -> float:
    return max(0.01, min(0.99, float(value)))


def grade(action_dict: dict[str, Any], task_id: str, temperature: float = 0.0, seed: int = 42) -> float:
    del temperature, seed
    task = TASK_REGISTRY.get(task_id)
    if not task:
        return 0.01

    action_type = str(action_dict.get("action_type") or "").strip().lower()
    if not action_type:
        return 0.01

    if action_type in task.get("ideal_actions", []):
        if task_id == "easy":
            return 0.95
        if task_id == "medium":
            return 0.85
        return 0.75

    if action_type == "add_comment":
        return 0.25 if task_id != "hard" else 0.15

    if action_type == "change_priority":
        return 0.20 if task_id != "hard" else 0.10

    if action_type == "update_status":
        return 0.40

    return 0.05


__all__ = ["grade"]
