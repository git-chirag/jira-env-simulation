from tasks_runner import run_easy_task, run_hard_task, run_medium_task


def grade_action(task_id: str, action: str, signals: dict) -> float:
    """
    Score a single action for a given task and signal state.
    Returns a float in [0.0, 1.0].
    """
    action = (action or "").lower().strip()
    valid_actions = (
        "assign_ticket",
        "update_status",
        "resolve_ticket",
        "change_priority",
        "add_comment",
    )

    if action not in valid_actions:
        for candidate in valid_actions:
            if candidate in action:
                action = candidate
                break
        else:
            return 0.1

    raw_score = 0.5
    if task_id == "easy":
        raw_score = _grade_easy_action(action, signals)
    elif task_id == "medium":
        raw_score = _grade_medium_action(action, signals)
    elif task_id == "hard":
        raw_score = _grade_hard_action(action, signals)

    return round(min(max(raw_score, 0.01), 0.99), 3)


def _grade_easy_action(action: str, signals: dict) -> float:
    if signals.get("requires_assignment", False):
        if action == "assign_ticket":
            return 0.95
        if action == "resolve_ticket":
            return 0.35
        if action == "add_comment":
            return 0.15
        return 0.10

    if action == "resolve_ticket":
        return 0.99
    if action == "assign_ticket":
        return 0.20
    if action == "add_comment":
        return 0.10
    return 0.05


def _grade_medium_action(action: str, signals: dict) -> float:
    if action == "resolve_ticket":
        return 0.90
    if action == "assign_ticket":
        return 0.75
    if action == "update_status":
        return 0.55
    if action == "add_comment":
        return 0.25
    if action == "change_priority":
        return 0.20
    return 0.10


def _grade_hard_action(action: str, signals: dict) -> float:
    if signals.get("priority_order_required", False):
        if action == "resolve_ticket":
            return 0.95
        if action == "assign_ticket":
            return 0.80
        if action == "update_status":
            return 0.45
        if action == "add_comment":
            return 0.20
        if action == "change_priority":
            return 0.15
        return 0.10

    return _grade_medium_action(action, signals)


def grade_easy(env) -> float:
    return float(run_easy_task(env))


def grade_medium(env) -> float:
    return float(run_medium_task(env))


def grade_hard(env) -> float:
    return float(run_hard_task(env))


def grade_task(task_id: str, env) -> float:
    if task_id == "easy":
        return grade_easy(env)
    if task_id == "medium":
        return grade_medium(env)
    if task_id == "hard":
        return grade_hard(env)
    return 0.0


TASK_GRADERS = {
    "easy": grade_easy,
    "medium": grade_medium,
    "hard": grade_hard,
}


__all__ = [
    "grade_easy",
    "grade_medium",
    "grade_hard",
    "grade_task",
    "grade_action",
    "TASK_GRADERS",
]
