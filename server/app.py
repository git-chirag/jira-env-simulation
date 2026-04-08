from __future__ import annotations

from typing import Any

from fastapi import Body, FastAPI, HTTPException
from pydantic import ValidationError

from env import JiraEnv
from models import Action, TaskInfo
from server.grader import grade
from server.tasks import TASK_REGISTRY


app = FastAPI()
env = JiraEnv()


@app.post("/reset")
def reset(payload: dict[str, Any] | None = Body(default=None)) -> dict[str, Any]:
    task_id = None if payload is None else payload.get("task_id")
    result = env.reset(task_id=task_id)
    return result.model_dump()


@app.post("/step")
def step(action_data: dict[str, Any] = Body(...)) -> dict[str, Any]:
    try:
        action = Action.model_validate(action_data)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    result = env.step(action)
    return result.model_dump()


@app.get("/state")
def state() -> dict[str, Any]:
    return env.state().model_dump()


@app.get("/tasks")
def list_tasks() -> dict[str, list[dict[str, Any]]]:
    tasks = [
        TaskInfo(
            task_id=task_id,
            difficulty=task["difficulty"],
            description=task["description"],
            action_schema=Action.model_json_schema(),
        ).model_dump()
        for task_id, task in TASK_REGISTRY.items()
    ]
    return {"tasks": tasks}


@app.post("/grader")
def grader(task_id: str, action: Action) -> dict[str, Any]:
    if task_id not in TASK_REGISTRY:
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
    if task_id not in TASK_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Unknown task_id: {task_id}")

    local_env = JiraEnv()
    local_env.reset(task_id=task_id)
    score = grade({"action_type": "assign_ticket"}, task_id)
    return {
        "task_id": task_id,
        "score": score,
        "done": True,
    }


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
