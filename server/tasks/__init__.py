from .task_easy import EASY_TASK
from .task_hard import HARD_TASK
from .task_medium import MEDIUM_TASK


TASK_REGISTRY = {
    "easy": EASY_TASK,
    "medium": MEDIUM_TASK,
    "hard": HARD_TASK,
}

TASK_IDS = tuple(TASK_REGISTRY.keys())

__all__ = ["EASY_TASK", "MEDIUM_TASK", "HARD_TASK", "TASK_REGISTRY", "TASK_IDS"]
