from __future__ import annotations

import threading
from typing import Any

from fastapi import Body, FastAPI, HTTPException
from pydantic import ValidationError

from env import JiraEnv
from models import Action, Observation
from server.grader import grade
from graders.easy_grader import EasyGrader
from graders.hard_grader import HardGrader
from graders.medium_grader import MediumGrader


app = FastAPI()
_env: JiraEnv | None = None
_env_lock = threading.Lock()

TASK_GRADERS = {
    "easy": EasyGrader,
    "medium": MediumGrader,
    "hard": HardGrader,
}


def _get_env() -> JiraEnv:
    global _env
    if _env is None:
        _env = JiraEnv()
    return _env


@app.get("/")
def root() -> dict[str, str]:
    return {
        "status": "ok",
        "environment": "jira-env",
        "health": "/health",
        "tasks": "/tasks",
        "grader": "/grader",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "jira-env-api"}


@app.post("/reset")
def reset(payload: dict[str, Any] | None = Body(default=None)) -> dict[str, Any]:
    task_id = None if payload is None else payload.get("task_id")
    with _env_lock:
        env = _get_env()
        result = env.reset(task_id=task_id)
        return result.model_dump()


@app.post("/step")
def step(action_data: dict[str, Any] = Body(...)) -> dict[str, Any]:
    try:
        action = Action.model_validate(action_data)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    with _env_lock:
        env = _get_env()
        result = env.step(action)
        return result.model_dump()


@app.get("/state")
def state() -> dict[str, Any]:
    with _env_lock:
        env = _get_env()
        return env.state().model_dump()


@app.get("/tasks")
def list_tasks() -> dict[str, list[dict[str, Any]]]:
    tasks = [
        {
            "id": task_id,
            "difficulty": task["difficulty"],
            "description": task["description"],
            "max_steps": task["max_steps"],
            "score_range": [0.0, 1.0],
        }
        for task_id, task in JiraEnv.TASK_CONFIGS.items()
    ]
    return {"tasks": tasks}


@app.post("/grader")
def grader(task_id: str, action: Action) -> dict[str, Any]:
    if task_id not in JiraEnv.TASK_CONFIGS:
        raise HTTPException(status_code=404, detail=f"Unknown task_id: {task_id}")

    score = grade(action.model_dump(), task_id)
    return {
        "task_id": task_id,
        "score": score,
        "passed": 1 if score > 0.5 else 0,
        "total": 1,
        "metric": "jira_task_alignment",
    }


@app.get("/grader")
def grader_score(task_id: str = "easy") -> dict[str, Any]:
    if task_id not in JiraEnv.TASK_CONFIGS:
        raise HTTPException(status_code=404, detail=f"Unknown task_id: {task_id}")

    grader_cls = TASK_GRADERS[task_id]
    score = grader_cls()()
    return {
        "task_id": task_id,
        "score": score,
        "done": True,
    }


@app.get("/schema")
def schema() -> dict[str, Any]:
    return {
        "action_schema": Action.model_json_schema(),
        "observation_schema": Observation.model_json_schema(),
    }


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
