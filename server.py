from __future__ import annotations

from typing import Any

from fastapi import Body, FastAPI, HTTPException
from pydantic import ValidationError

from env import JiraEnv
from models import Action


app = FastAPI()
env = JiraEnv()


@app.post("/reset")
def reset() -> dict[str, Any]:
    result = env.reset()
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7860)
