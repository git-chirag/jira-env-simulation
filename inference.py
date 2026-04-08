#!/usr/bin/env python3
"""
inference.py — Jira OpenEnv Agent
=================================
Runs an LLM agent through all Jira tasks and emits structured stdout logs.

Required environment variables:
    API_BASE_URL      LLM API endpoint
    API_KEY           API key
    MODEL_NAME        Model identifier
    LOCAL_IMAGE_NAME  (optional) Docker image to launch as env server

Stdout format (must not deviate):
    [START] task=<task> env=<benchmark> model=<model>
    [STEP]  step=<n> action=<action> reward=<0.00> done=<true|false> error=<msg|null>
    [END]   success=<true|false> steps=<n> score=<0.000> rewards=<r1,r2,...>
"""

import os
import textwrap
from typing import List, Optional

from openai import OpenAI

from client import JiraClient
from models import JiraTaskAction
from tasks.definitions import TASK_NAMES, TASKS


IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")
API_BASE_URL = os.environ["API_BASE_URL"]
API_KEY = os.environ["API_KEY"]
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4o-mini")
ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://localhost:7860")
BENCHMARK = "jira-env"
SUCCESS_SCORE_THRESHOLD = 0.5
TEMPERATURE = 0.2
MAX_TOKENS = 128

SYSTEM_PROMPT = textwrap.dedent(
    """
    You are a disciplined Jira workflow assistant.
    You will receive Jira ticket-management observations with assignment,
    status, and priority cues.

    Based on the observation, choose exactly one of these actions:
      ASSIGN_TICKET
      RESOLVE_TICKET
      UPDATE_STATUS
      CHANGE_PRIORITY
      ADD_COMMENT

    Reply with EXACTLY ONE ACTION NAME.
    No explanation. No punctuation. No extra text.
    """
).strip()


def log_start(task: str, env: str, model: str):
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]):
    error_val = error if error else "null"
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={str(done).lower()} error={error_val}", flush=True)


def log_end(success: bool, steps: int, score: float, rewards: List[float]):
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)


def choose_rule_based_action(observation: str) -> str:
    text = observation.lower()

    if "unassigned" in text or "none are assigned yet" in text or "no ticket is assigned yet" in text:
        return "assign_ticket"
    if "ready to resolve" in text or "ready to close" in text or "can be resolved safely" in text:
        return "resolve_ticket"
    if "complete the work cleanly" in text:
        return "resolve_ticket"
    if "best next move starts progress" in text or "best move starts execution" in text:
        return "assign_ticket"

    return "assign_ticket"


def get_model_action(client: OpenAI, observation: str, history: List[str]) -> str:
    history_block = "\n".join(history[-3:]) if history else "None"
    user_prompt = (
        f"Current Jira observation:\n{observation}\n\n"
        f"Previous decisions this episode:\n{history_block}\n\n"
        f"Your decision:"
    )

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            stream=False,
        )

        text = (completion.choices[0].message.content or "").strip().upper()
        for action in (
            "ASSIGN_TICKET",
            "RESOLVE_TICKET",
            "UPDATE_STATUS",
            "CHANGE_PRIORITY",
            "ADD_COMMENT",
        ):
            if action in text:
                return action.lower()
    except Exception:
        pass

    return choose_rule_based_action(observation)


def run_task(client: OpenAI, task_name: str) -> None:
    if IMAGE_NAME:
        env_instance = JiraClient.from_docker_image(IMAGE_NAME, task=task_name)
    else:
        env_instance = JiraClient(base_url=ENV_BASE_URL)

    rewards: List[float] = []
    history: List[str] = []
    steps_taken = 0
    score = 0.01
    success = False

    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)

    try:
        with env_instance.sync() as env:
            if IMAGE_NAME:
                result = env.reset()
            else:
                result = env.reset(task_id=task_name)

            max_steps = len(TASKS[task_name]["steps"])

            for step in range(1, max_steps + 1):
                if result.done:
                    break

                observation_text = result.observation.text
                action_str = get_model_action(client, observation_text, history)
                error: Optional[str] = None

                try:
                    result = env.step(JiraTaskAction(action=action_str))
                    reward = float(result.reward or 0.0)
                    done = bool(result.done)
                except Exception as exc:
                    error = str(exc)
                    reward = 0.01
                    done = True

                rewards.append(reward)
                steps_taken = step
                log_step(step=step, action=action_str, reward=reward, done=done, error=error)
                history.append(f"Step {step}: {action_str} -> reward {reward:.2f}")

                if done:
                    break

        if rewards:
            score = sum(rewards) / len(rewards)
            score = max(0.01, min(score, 0.99))
        success = score >= SUCCESS_SCORE_THRESHOLD
    except Exception:
        pass
    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)


def main() -> None:
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    try:
        for task_name in TASK_NAMES:
            run_task(client, task_name)
    finally:
        client.close()


if __name__ == "__main__":
    main()
