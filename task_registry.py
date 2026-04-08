from tasks.definitions import TASK_NAMES, TASKS
from tasks.graders import TASK_GRADERS, grade_easy, grade_hard, grade_medium


TASK_REGISTRY = {
    "easy": {
        "definition": TASKS["easy"],
        "grader": grade_easy,
    },
    "medium": {
        "definition": TASKS["medium"],
        "grader": grade_medium,
    },
    "hard": {
        "definition": TASKS["hard"],
        "grader": grade_hard,
    },
}


__all__ = [
    "TASK_NAMES",
    "TASKS",
    "TASK_GRADERS",
    "TASK_REGISTRY",
    "grade_easy",
    "grade_medium",
    "grade_hard",
]
