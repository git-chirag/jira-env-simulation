"""
FastAPI application for the JiraEnv environment.

This module creates an HTTP server that exposes the JiraTaskEnvironment
over HTTP and WebSocket endpoints, compatible with EnvClient.
"""

try:
    from openenv.core.env_server.http_server import create_app
except Exception as e:  # pragma: no cover
    raise ImportError(
        "openenv is required for the web interface. Install dependencies with '\n    uv sync\n'"
    ) from e

try:
    from ..models import JiraTaskAction, JiraTaskObservation
    from .jira_environment import JiraTaskEnvironment
except (ModuleNotFoundError, ImportError):
    from models import JiraTaskAction, JiraTaskObservation
    from server.jira_environment import JiraTaskEnvironment


app = create_app(
    JiraTaskEnvironment,
    JiraTaskAction,
    JiraTaskObservation,
    env_name="jira-env",
    max_concurrent_envs=10,
)


def main():
    """
    Entry point for direct execution via uv run or python -m.
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
