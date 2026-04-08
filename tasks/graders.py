# tasks/graders.py
# Reward functions for each task. All rewards are strictly in (0.0, 1.0).


def grade_action(task_id: str, action: str, signals: dict) -> float:
    """
    Score a single action for a given task and signal state.
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
        raw_score = _grade_easy(action, signals)
    elif task_id == "medium":
        raw_score = _grade_medium(action, signals)
    elif task_id == "hard":
        raw_score = _grade_hard(action, signals)
    return round(min(max(raw_score, 0.01), 0.99), 3)


def _grade_easy(action: str, signals: dict) -> float:
    if not signals.get("assigned", False):
        if action == "assign_ticket":
            return 0.99
        if action == "resolve_ticket":
            return 0.20
        if action == "add_comment":
            return 0.12
        return 0.08

    if action == "resolve_ticket":
        return 0.99
    if action == "update_status":
        return 0.30
    if action == "add_comment":
        return 0.12
    return 0.08


def _grade_medium(action: str, signals: dict) -> float:
    priority = signals.get("priority", "medium")
    assigned = signals.get("assigned", False)

    if not assigned:
        if action == "assign_ticket":
            return 0.95 if priority == "high" else 0.85
        if action == "resolve_ticket":
            return 0.18
        if action == "add_comment":
            return 0.15
        return 0.10

    if action == "resolve_ticket":
        return 0.92 if priority == "high" else 0.82
    if action == "update_status":
        return 0.35
    if action == "add_comment":
        return 0.18
    return 0.10


def _grade_hard(action: str, signals: dict) -> float:
    priority = signals.get("priority", "medium")
    assigned = signals.get("assigned", False)

    if not assigned:
        if action == "assign_ticket":
            return 0.97 if priority == "high" else 0.70
        if action == "resolve_ticket":
            return 0.10
        if action == "add_comment":
            return 0.08
        if action == "change_priority":
            return 0.05
        return 0.06

    if action == "resolve_ticket":
        return 0.97 if priority == "high" else 0.80
    if action == "update_status":
        return 0.28
    if action == "add_comment":
        return 0.08
    return 0.05
