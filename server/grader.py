from __future__ import annotations

from typing import Any

from server.tasks import TASK_REGISTRY


def _clamp_score(value: float) -> float:
    return round(max(0.01, min(0.99, float(value))), 2)


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
            return _clamp_score(0.95)
        if task_id == "medium":
            return _clamp_score(0.85)
        return _clamp_score(0.75)

    if action_type == "add_comment":
        return _clamp_score(0.25 if task_id != "hard" else 0.15)

    if action_type == "change_priority":
        return _clamp_score(0.20 if task_id != "hard" else 0.10)

    if action_type == "update_status":
        return _clamp_score(0.40)

    return _clamp_score(0.05)


__all__ = ["grade"]
