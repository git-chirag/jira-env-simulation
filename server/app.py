"""FastAPI application for the Jira environment."""

from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

try:
    from openenv.core.env_server.http_server import create_app
except Exception as e:  # pragma: no cover
    raise ImportError(
        "openenv is required for the web interface. Install dependencies with '\n    uv sync\n'"
    ) from e

try:
    from ..models import JiraTaskAction, JiraTaskObservation, JiraTaskState
    from ..tasks.definitions import TASKS
    from .jira_environment import JiraTaskEnvironment
except (ModuleNotFoundError, ImportError):
    from models import JiraTaskAction, JiraTaskObservation, JiraTaskState
    from tasks.definitions import TASKS
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
_remove_generated_route("/step")

router = APIRouter()


def _render_task_cards() -> str:
    cards: list[str] = []
    reference_scores = {
        "easy": "0.650",
        "medium": "0.461",
        "hard": "0.394",
    }
    for task_id, definition in TASKS.items():
        cards.append(
            f"""
            <article class="task-card">
              <div class="task-header">
                <h3>{task_id.title()}</h3>
                <span>{len(definition["steps"])} step budget</span>
              </div>
              <p>{definition["description"]}</p>
              <div class="task-metric">
                <strong>Latest local baseline</strong>
                <span>{reference_scores.get(task_id, "n/a")}</span>
              </div>
            </article>
            """
        )
    return "\n".join(cards)


@router.get("/", response_class=HTMLResponse)
def root() -> HTMLResponse:
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <title>Jira Env Simulation</title>
      <style>
        :root {{
          --bg: #f4f1e8;
          --panel: #fffaf1;
          --ink: #1d2a33;
          --muted: #5f6b72;
          --accent: #0b6e4f;
          --accent-soft: #dff3ea;
          --line: #d9d2c5;
        }}
        * {{ box-sizing: border-box; }}
        body {{
          margin: 0;
          font-family: Georgia, "Times New Roman", serif;
          color: var(--ink);
          background:
            radial-gradient(circle at top left, #fff4cf 0, transparent 28%),
            linear-gradient(135deg, #f7f2e7 0%, #eef3ea 100%);
        }}
        .shell {{
          max-width: 1080px;
          margin: 0 auto;
          padding: 32px 20px 48px;
        }}
        .hero {{
          background: var(--panel);
          border: 1px solid var(--line);
          border-radius: 24px;
          padding: 28px;
          box-shadow: 0 18px 40px rgba(35, 46, 56, 0.08);
        }}
        .eyebrow {{
          display: inline-block;
          margin-bottom: 12px;
          padding: 6px 12px;
          border-radius: 999px;
          background: var(--accent-soft);
          color: var(--accent);
          font-size: 13px;
          letter-spacing: 0.04em;
          text-transform: uppercase;
        }}
        h1 {{
          margin: 0;
          font-size: clamp(32px, 6vw, 58px);
          line-height: 0.95;
        }}
        .lede {{
          max-width: 720px;
          margin: 16px 0 0;
          font-size: 18px;
          line-height: 1.5;
          color: var(--muted);
        }}
        .metrics, .task-grid, .endpoint-grid {{
          display: grid;
          gap: 16px;
          margin-top: 24px;
        }}
        .metrics {{
          grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        }}
        .metric, .task-card, .endpoint {{
          background: rgba(255, 255, 255, 0.82);
          border: 1px solid var(--line);
          border-radius: 18px;
          padding: 18px;
        }}
        .metric strong, .task-header h3 {{
          display: block;
          font-size: 18px;
        }}
        .metric span, .task-card p, .endpoint p {{
          color: var(--muted);
          line-height: 1.45;
        }}
        .task-grid {{
          grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        }}
        .task-header {{
          display: flex;
          align-items: baseline;
          justify-content: space-between;
          gap: 12px;
        }}
        .task-metric {{
          display: flex;
          justify-content: space-between;
          margin-top: 16px;
          padding-top: 12px;
          border-top: 1px solid var(--line);
        }}
        .endpoint-grid {{
          grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        }}
        code {{
          font-family: "Courier New", monospace;
          font-size: 14px;
          color: var(--accent);
        }}
        a {{
          color: var(--accent);
          text-decoration: none;
        }}
      </style>
    </head>
    <body>
      <main class="shell">
        <section class="hero">
          <div class="eyebrow">OpenEnv Space</div>
          <h1>Jira Env Simulation</h1>
          <p class="lede">
            A read-only Hugging Face Space dashboard for an OpenEnv-compatible Jira workflow benchmark.
            Agents must prioritize urgent tickets, respect dependencies, and resolve work efficiently under SLA pressure.
          </p>

          <div class="metrics">
            <div class="metric">
              <strong>Status</strong>
              <span>Running and ready for evaluation</span>
            </div>
            <div class="metric">
              <strong>Supported actions</strong>
              <span><code>assign_ticket</code>, <code>resolve_ticket</code>, <code>update_status</code>, <code>change_priority</code>, <code>add_comment</code></span>
            </div>
            <div class="metric">
              <strong>API</strong>
              <span><a href="/docs">Interactive docs</a> and standard <code>/reset</code>, <code>/step</code>, <code>/state</code> endpoints</span>
            </div>
          </div>

          <div class="task-grid">
            {_render_task_cards()}
          </div>

          <div class="endpoint-grid">
            <section class="endpoint">
              <strong><code>POST /reset</code></strong>
              <p>Starts a task episode and returns the first Jira observation.</p>
            </section>
            <section class="endpoint">
              <strong><code>POST /step</code></strong>
              <p>Applies one workflow action and returns reward, observation, and done state.</p>
            </section>
            <section class="endpoint">
              <strong><code>GET /state</code></strong>
              <p>Returns the current task id, step count, reward history, and completion state.</p>
            </section>
            <section class="endpoint">
              <strong><code>GET /docs</code></strong>
              <p>FastAPI documentation for manual testing and quick API inspection.</p>
            </section>
          </div>
        </section>
      </main>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@router.get("/state", response_model=JiraTaskState)
def get_state() -> JiraTaskState:
    env = JiraTaskEnvironment()
    return env.state


@router.post("/step")
def step(payload: dict[str, Any]) -> dict[str, Any]:
    action_payload = payload.get("action")
    if not isinstance(action_payload, dict):
        raise HTTPException(status_code=422, detail="Expected payload shape: {'action': {'action': '<action_name>'}}")

    action_name = action_payload.get("action")
    if not isinstance(action_name, str):
        raise HTTPException(status_code=422, detail="Missing action.action string")

    env = JiraTaskEnvironment()
    result = env.step(JiraTaskAction(action=action_name))
    return {
        "observation": {
            "text": result.text,
            "task_id": result.task_id,
        },
        "reward": result.reward,
        "done": result.done,
        "info": result.metadata or {},
    }


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
