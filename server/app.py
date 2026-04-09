"""FastAPI application for the Jira environment."""

from fastapi import APIRouter

try:
    from openenv.core.env_server.http_server import create_app
except Exception as e:  # pragma: no cover
    raise ImportError(
        "openenv is required for the web interface. Install dependencies with '\n    uv sync\n'"
    ) from e

try:
    from ..models import JiraTaskAction, JiraTaskObservation, JiraTaskState
    from .jira_environment import JiraTaskEnvironment
except (ModuleNotFoundError, ImportError):
    from models import JiraTaskAction, JiraTaskObservation, JiraTaskState
    from server.jira_environment import JiraTaskEnvironment


app = create_app(
    JiraTaskEnvironment,
    JiraTaskAction,
    JiraTaskObservation,
    env_name="jira-env",
    max_concurrent_envs=10,
)


def _remove_generated_route(path: str) -> None:
    app.router.routes = [
        route for route in app.router.routes
        if getattr(route, "path", None) != path
    ]


_remove_generated_route("/state")
_remove_generated_route("/ws")

router = APIRouter()


@router.get("/")
def root() -> dict[str, object]:
    return {
        "status": "running",
        "project": "Jira Env Simulation",
        "message": "API is live",
        "available_endpoints": {
            "reset": "/reset (POST)",
            "step": "/step (POST)",
            "state": "/state (GET)",
            "docs": "/docs",
        },
    }


@router.get("/state", response_model=JiraTaskState)
def get_state() -> JiraTaskState:
    env = JiraTaskEnvironment()
    return env.state


app.include_router(router)


def main():
    """
    Entry point for direct execution via uv run or python -m.

    This function enables running the server without Docker:
        uv run --project . server
        python -m jira_env_simulation.server.app

    For production deployments, consider using uvicorn directly with
    multiple workers:
        uvicorn jira_env_simulation.server.app:app --workers 4
    """
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=7860)
    args = parser.parse_args()

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
