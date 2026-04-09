# tasks/graders.py
# Reward functions for the Jira environment. All rewards are strictly in (0.0, 1.0).

RESOLUTION_REWARD_BY_PRIORITY = {
    "high": 0.82,
    "medium": 0.66,
    "low": 0.50,
}

ASSIGNMENT_REWARD_BY_PRIORITY = {
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


def _clamp_reward(value: float) -> float:
    return round(min(max(value, 0.01), 0.99), 3)


def grade_action(task_id: str, action: str, transition: dict) -> float:
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
        raw_score = grade_easy(action, transition)
    elif task_id == "medium":
        raw_score = grade_medium(action, transition)
    elif task_id == "hard":
        raw_score = grade_hard(action, transition)
    return _clamp_reward(raw_score)


def grade_easy(action: str, transition: dict) -> float:
    bonus = 0.08
    if action == "assign_ticket" and transition.get("assigned_now") and transition.get("priority_before") == "high":
        bonus += 0.04
    if (
        action == "update_status"
        and transition.get("status_updated")
        and transition.get("assigned_before")
        and transition.get("priority_before") == "high"
    ):
        bonus += 0.22
    if action == "resolve_ticket" and transition.get("resolved_now") and transition.get("all_resolved_after"):
        bonus += 0.04
    return _grade_common(action, transition, task_bonus=bonus)


def grade_medium(action: str, transition: dict) -> float:
    bonus = 0.02 if transition.get("resolved_now") and transition.get("unresolved_after", 0) > 0 else 0.0
    return _grade_common(action, transition, task_bonus=bonus)


def grade_hard(action: str, transition: dict) -> float:
    bonus = 0.0
    if transition.get("dependency_cleared_now"):
        bonus += 0.06
    if transition.get("priority_before") == "high" and action in {"assign_ticket", "resolve_ticket"} and transition.get("action_success"):
        bonus += 0.04
    if transition.get("higher_priority_ready_before"):
        bonus -= 0.08
    return _grade_common(action, transition, task_bonus=bonus)


def _grade_common(action: str, transition: dict, task_bonus: float) -> float:
    if not transition.get("target_exists", False):
        return 0.01

    if not transition.get("action_valid", True):
        return 0.01

    if transition.get("blocked", False) and action == "resolve_ticket":
        return 0.01

    priority = transition.get("priority_before", "low")

    if action == "assign_ticket":
        reward = ASSIGNMENT_REWARD_BY_PRIORITY.get(priority, 0.20) if transition.get("assigned_now") else 0.04
    elif action == "update_status":
        if transition.get("status_updated") and transition.get("assigned_before"):
            reward = 0.22
        elif transition.get("status_updated"):
            reward = 0.08
        else:
            reward = 0.04
    elif action == "resolve_ticket":
        if transition.get("resolved_now"):
            reward = RESOLUTION_REWARD_BY_PRIORITY.get(priority, 0.50)
            reward += 0.08 if transition.get("within_sla") else -0.15
            if transition.get("all_resolved_after"):
                reward += 0.04
        else:
            reward = 0.02
    elif action == "change_priority":
        reward = 0.18 if transition.get("priority_change_useful") else 0.05
    elif action == "add_comment":
        reward = 0.16 if transition.get("comment_useful") else 0.07
    else:
        reward = 0.03

    if transition.get("repeated_action"):
        reward -= 0.05
    if transition.get("repeated_no_progress"):
        reward -= 0.08
    elif transition.get("no_progress") and action in {"assign_ticket", "resolve_ticket", "update_status"}:
        reward -= 0.06
    if transition.get("higher_priority_ready_before") and action != "assign_ticket":
        reward -= 0.07

    reward += task_bonus
    return reward


TASK_GRADERS = {
    "easy": grade_easy,
    "medium": grade_medium,
    "hard": grade_hard,
}
