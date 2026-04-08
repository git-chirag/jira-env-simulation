from tasks_runner import run_easy_task, run_hard_task, run_medium_task


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


def grade_action(task_id: str, env) -> float:
    # Alias mirrors the reference project style while still grading via env state.
    return float(grade_task(task_id, env))


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
