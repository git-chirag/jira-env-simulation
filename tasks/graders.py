# tasks/graders.py
# Reward functions for the Jira environment. All rewards are strictly in (0.0, 1.0).

__all__ = [
    "grade_action",
    "grade_easy",
    "grade_medium",
    "grade_hard",
    "TASK_GRADERS",
]


def grade_action(task_id: str, action: str, state: dict) -> float:
    """
    Score a single action for a given task and state transition context.
    Returns a float in (0.0, 1.0).
    """
    action = (action or "").lower().strip()
    valid_actions = (
        "assign_ticket",
        "resolve_ticket",
        "add_comment",
        "update_status",
        "change_priority",
    )

    if action not in valid_actions:
        for candidate in valid_actions:
            if candidate in action:
                action = candidate
                break
        else:
            return 0.10

    raw_score = 0.50
    if task_id == "easy":
        raw_score = grade_easy(action, state)
    elif task_id == "medium":
        raw_score = grade_medium(action, state)
    elif task_id == "hard":
        raw_score = grade_hard(action, state)
    return round(min(max(raw_score, 0.01), 0.99), 3)


def grade_easy(action: str, state: dict) -> float:
    return _grade_common(action, state, task_bonus=0.02)


def grade_medium(action: str, state: dict) -> float:
    return _grade_common(action, state, task_bonus=0.00)


def grade_hard(action: str, state: dict) -> float:
    bonus = 0.03 if state.get("dependency_cleared_now") else -0.02 if state.get("blocked") else 0.0
    if state.get("priority_before") == "high" and state.get("action_success"):
        bonus += 0.02
    return _grade_common(action, state, task_bonus=bonus)


def _grade_common(action: str, state: dict, task_bonus: float) -> float:
    reward = -0.05

    if not state.get("target_exists", False):
        return 0.01

    if not state.get("action_valid", True):
        return 0.01

    if state.get("blocked", False) and action == "resolve_ticket":
        return 0.01

    if state.get("invalid_action", False):
        reward += -1.0
    elif action == "assign_ticket":
        reward += 0.2 if state.get("assigned_now") else -0.1
    elif action == "update_status":
        reward += 0.1 if state.get("status_updated") else -0.1
    elif action == "resolve_ticket":
        if state.get("resolved_now"):
            priority = state.get("priority_before", "low")
            reward += {
                "high": 1.0,
                "medium": 0.7,
                "low": 0.4,
            }.get(priority, 0.4)
            reward += 0.1 if state.get("within_sla") else -0.3
        else:
            reward += -0.5
    elif action == "change_priority":
        reward += 0.05 if state.get("priority_changed") else -0.1
    elif action == "add_comment":
        reward += 0.05 if state.get("comment_added") else -0.1

    reward += task_bonus
    return reward


TASK_GRADERS = {
    "easy": grade_easy,
    "medium": grade_medium,
    "hard": grade_hard,
}
