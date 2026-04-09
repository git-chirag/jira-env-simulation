import os
from typing import Any

import requests


BASE_URL = os.getenv("ENV_BASE_URL", "http://127.0.0.1:7860")
TASKS = ("easy", "medium", "hard")


def _print_response(label: str, payload: Any) -> None:
    print(f"{label}: {payload}")


def check_server() -> None:
    health = requests.get(f"{BASE_URL}/health", timeout=10)
    root = requests.get(f"{BASE_URL}/", timeout=10)
    _print_response("health", health.status_code)
    _print_response("root", root.status_code)


def run_baseline() -> None:
    os.environ.setdefault("API_BASE_URL", "http://127.0.0.1:9/v1")
    os.environ.setdefault("API_KEY", "dummy-key")
    os.environ["ENV_BASE_URL"] = BASE_URL
    os.environ.setdefault("MODEL_NAME", "gpt-4o-mini")

    import inference

    inference.main()


def inspect_tasks() -> None:
    for task_name in TASKS:
        reset_response = requests.post(f"{BASE_URL}/reset", json={"task_id": task_name}, timeout=10)
        reset_payload = reset_response.json()
        _print_response(f"{task_name}_task", reset_payload["observation"]["task_id"])
        _print_response(f"{task_name}_observation_length", len(reset_payload["observation"]["text"]))


if __name__ == "__main__":
    check_server()
    inspect_tasks()
    run_baseline()
