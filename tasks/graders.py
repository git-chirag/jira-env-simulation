# tasks/graders.py
# Reward functions for the Jira environment. All rewards are strictly in (0.0, 1.0).

PRIORITY_REWARD = {
    "high": 0.82,
    "medium": 0.66,
    "low": 0.50,
}

ASSIGN_REWARD = {
    "high": 0.32,
    "medium": 0.26,
    "low": 0.20,
}

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
            return 0.08

    raw_score = 0.12
    if task_id == "easy":
        raw_score = grade_easy(action, state)
    elif task_id == "medium":
        raw_score = grade_medium(action, state)
    elif task_id == "hard":
        raw_score = grade_hard(action, state)
    return round(min(max(raw_score, 0.01), 0.99), 3)


def grade_easy(action: str, state: dict) -> float:
    return _grade_common(action, state, task_bonus=0.03)


def grade_medium(action: str, state: dict) -> float:
    bonus = 0.02 if state.get("resolved_now") and state.get("unresolved_after", 0) > 0 else 0.0
    return _grade_common(action, state, task_bonus=bonus)


def grade_hard(action: str, state: dict) -> float:
    bonus = 0.0
    if state.get("dependency_cleared_now"):
        bonus += 0.06
    if state.get("priority_before") == "high" and action in {"assign_ticket", "resolve_ticket"} and state.get("action_success"):
        bonus += 0.04
    if state.get("higher_priority_ready_before"):
        bonus -= 0.08
    return _grade_common(action, state, task_bonus=bonus)


def _grade_common(action: str, state: dict, task_bonus: float) -> float:
    if not state.get("target_exists", False):
        return 0.01

    if not state.get("action_valid", True):
        return 0.01

    if state.get("blocked", False) and action == "resolve_ticket":
        return 0.01

    priority = state.get("priority_before", "low")

    if action == "assign_ticket":
        reward = ASSIGN_REWARD.get(priority, 0.20) if state.get("assigned_now") else 0.04
    elif action == "update_status":
        if state.get("status_updated") and state.get("assigned_before"):
            reward = 0.22
        elif state.get("status_updated"):
            reward = 0.08
        else:
            reward = 0.04
    elif action == "resolve_ticket":
        if state.get("resolved_now"):
            reward = PRIORITY_REWARD.get(priority, 0.50)
            reward += 0.08 if state.get("within_sla") else -0.15
            if state.get("all_resolved_after"):
                reward += 0.04
        else:
            reward = 0.02
    elif action == "change_priority":
        reward = 0.18 if state.get("priority_change_useful") else 0.05
    elif action == "add_comment":
        reward = 0.16 if state.get("comment_useful") else 0.07
    else:
        reward = 0.03

    if state.get("repeated_action"):
        reward -= 0.05
    if state.get("repeated_no_progress"):
        reward -= 0.08
    elif state.get("no_progress") and action in {"assign_ticket", "resolve_ticket", "update_status"}:
        reward -= 0.06
    if state.get("higher_priority_ready_before") and action != "assign_ticket":
        reward -= 0.07

    reward += task_bonus
    return reward


TASK_GRADERS = {
    "easy": grade_easy,
    "medium": grade_medium,
    "hard": grade_hard,
}
