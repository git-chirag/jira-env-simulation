from tasks_runner import run_easy_task, run_hard_task, run_medium_task


def grade_easy(env) -> float:
    return float(run_easy_task(env))


def grade_medium(env) -> float:
    return float(run_medium_task(env))


def grade_hard(env) -> float:
    return float(run_hard_task(env))
