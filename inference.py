#!/usr/bin/env python3
"""
inference.py — Jira OpenEnv Agent
=================================
Runs an LLM agent through all Jira tasks and emits structured stdout logs.

Required environment variables:
    API_BASE_URL      LLM API endpoint
    HF_TOKEN          Hugging Face / API key
    MODEL_NAME        Model identifier
    LOCAL_IMAGE_NAME  (optional) Docker image to launch as env server

Stdout format (must not deviate):
    [START] task=<task> env=<benchmark> model=<model>
    [STEP]  step=<n> action=<action> reward=<0.00> done=<true|false> error=<msg|null>
    [END]   success=<true|false> steps=<n> score=<0.000> rewards=<r1,r2,...>
"""

import os
import random
import re
import textwrap
from typing import Any, Dict, List, Optional, Tuple

import requests
from openai import OpenAI

from tasks.definitions import TASKS


IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
API_KEY = os.getenv("API_KEY") or os.getenv("HF_TOKEN") or os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4o-mini")
ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://localhost:7860")
BENCHMARK = "jira-env"
SUCCESS_SCORE_THRESHOLD = 0.5
TEMPERATURE = 0.0
MAX_TOKENS = 128
HTTP_TIMEOUT = 30
TASK_ORDER = ["easy", "medium", "hard"]
ACTION_NAMES = (
    "assign_ticket",
    "resolve_ticket",
    "update_status",
    "change_priority",
    "add_comment",
)

SYSTEM_PROMPT = textwrap.dedent(
    """
    You are a disciplined Jira workflow assistant.
    You will receive Jira ticket-management observations with assignment,
    status, and priority cues.

    Reason briefly to yourself before answering:
    1. Identify the current focus ticket.
    2. Check whether the focus ticket is blocked, unassigned, or ready to resolve.
    3. Choose the single best next workflow action.

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


def reset_env(task_name: str) -> dict:
    response = requests.post(
        f"{ENV_BASE_URL}/reset",
        json={"task_id": task_name},
        timeout=HTTP_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def step_env(action: str) -> dict:
    response = requests.post(
        f"{ENV_BASE_URL}/step",
        json={"action": {"action": action}},
        timeout=HTTP_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def extract_focus_context(observation: str) -> Dict[str, Any]:
    focus_context: Dict[str, Any] = {
        "focus_ticket_id": None,
        "priority": None,
        "blocked": False,
        "unassigned": False,
        "ready_to_resolve": False,
        "reasoning_summary": "default workflow fallback",
    }
    text = observation or ""
    focus_match = re.search(r"Current focus:\s*Ticket #(\d+)(.*)", text, re.IGNORECASE | re.DOTALL)
    if not focus_match:
        return focus_context

    focus_ticket_id = int(focus_match.group(1))
    focus_context["focus_ticket_id"] = focus_ticket_id
    focus_tail = focus_match.group(2).lower()
    focus_context["blocked"] = "blocked until" in focus_tail
    focus_context["unassigned"] = "currently unassigned" in focus_tail
    focus_context["ready_to_resolve"] = "ready to close" in focus_tail or "ready to resolve" in focus_tail

    ticket_match = re.search(
        rf"Ticket #{focus_ticket_id} .*? is (\w+) priority",
        text,
        re.IGNORECASE,
    )
    if ticket_match:
        focus_context["priority"] = ticket_match.group(1).lower()

    if focus_context["blocked"]:
        focus_context["reasoning_summary"] = f"focus #{focus_ticket_id} is blocked"
    elif focus_context["unassigned"]:
        focus_context["reasoning_summary"] = f"focus #{focus_ticket_id} is unassigned"
    elif focus_context["ready_to_resolve"]:
        focus_context["reasoning_summary"] = f"focus #{focus_ticket_id} is ready to resolve"
    else:
        focus_context["reasoning_summary"] = f"focus #{focus_ticket_id} needs workflow progress"

    return focus_context


def choose_rule_based_action(observation: str) -> str:
    text = observation.lower()
    focus_text = text.split("current focus:", 1)[1] if "current focus:" in text else text

    if "unassigned" in focus_text or "none are assigned yet" in text or "no ticket is assigned yet" in text:
        return "assign_ticket"
    if "ready to resolve" in focus_text or "ready to close" in focus_text or "can be resolved safely" in focus_text:
        return "resolve_ticket"
    if "complete the work cleanly" in text:
        return "resolve_ticket"
    if "best next move starts progress" in text or "best move starts execution" in text:
        return "assign_ticket"
    if "blocked until" in focus_text:
        return "add_comment"

    return "assign_ticket"


def normalize_action(text: str) -> Optional[str]:
    candidate = (text or "").strip().lower()
    for action in ACTION_NAMES:
        if action in candidate:
            return action
        if action.upper() in (text or ""):
            return action
    return None


def allowed_actions_for_observation(observation: str) -> tuple[str, ...]:
    text = observation.lower()
    focus_text = text.split("current focus:", 1)[1] if "current focus:" in text else text
    if "currently unassigned" in focus_text:
        return ("assign_ticket", "add_comment")
    if "ready to resolve" in focus_text or "ready to close" in focus_text or "complete the work cleanly" in focus_text:
        return ("resolve_ticket", "add_comment")
    if "blocked until" in focus_text:
        return ("add_comment", "change_priority", "assign_ticket")
    return ACTION_NAMES


def choose_random_action(observation: str, rng: random.Random) -> str:
    allowed_actions = allowed_actions_for_observation(observation)
    return rng.choice(list(allowed_actions))


def get_model_suggestion(client: OpenAI, observation: str, history: List[str]) -> Optional[str]:
    focus_context = extract_focus_context(observation)
    history_block = "\n".join(history[-3:]) if history else "None"
    user_prompt = (
        f"Current Jira observation:\n{observation}\n\n"
        f"Focus analysis:\n"
        f"- focus_ticket_id: {focus_context['focus_ticket_id']}\n"
        f"- priority: {focus_context['priority']}\n"
        f"- blocked: {focus_context['blocked']}\n"
        f"- unassigned: {focus_context['unassigned']}\n"
        f"- ready_to_resolve: {focus_context['ready_to_resolve']}\n\n"
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

        return normalize_action(completion.choices[0].message.content or "")
    except Exception:
        return None


def choose_action(client: OpenAI, observation: str, history: List[str]) -> str:
    allowed_actions = allowed_actions_for_observation(observation)
    rule_action = choose_rule_based_action(observation)
    model_action = get_model_suggestion(client, observation, history)

    if model_action in allowed_actions:
        return model_action
    if rule_action in allowed_actions:
        return rule_action
    return allowed_actions[0]


def choose_action_with_context(
    client: OpenAI,
    observation: str,
    history: List[str],
    policy: str,
    rng: Optional[random.Random] = None,
) -> Tuple[str, Dict[str, Any]]:
    context = extract_focus_context(observation)
    if policy == "random":
        action = choose_random_action(observation, rng or random.Random(42))
        context["reasoning_summary"] = f"{context['reasoning_summary']}; random policy selected {action}"
        return action, context

    action = choose_action(client, observation, history)
    context["reasoning_summary"] = f"{context['reasoning_summary']}; safe policy selected {action}"
    return action, context


def run_task(
    client: OpenAI,
    task_name: str,
    policy: str = "safe_llm",
    rng: Optional[random.Random] = None,
) -> Dict[str, Any]:
    rewards: List[float] = []
    history: List[str] = []
    resolved_order: List[int] = []
    steps_taken = 0
    score = 0.01
    success = False
    max_steps = len(TASKS[task_name]["steps"])

    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)

    try:
        result = reset_env(task_name)

        for step in range(1, max_steps + 1):
            if bool(result.get("done", False)):
                break

            observation_text = result.get("observation", {}).get("text", "")
            action_str, focus_context = choose_action_with_context(client, observation_text, history, policy, rng=rng)
            error: Optional[str] = None

            try:
                result = step_env(action_str)
                reward = float(result.get("reward")) if result.get("reward") is not None else 0.01
                done = bool(result.get("done", False))
            except Exception as exc:
                error = str(exc)
                reward = 0.01
                done = True

            rewards.append(reward)
            steps_taken = step
            log_step(step=step, action=action_str, reward=reward, done=done, error=error)
            if action_str == "resolve_ticket" and reward >= 0.5 and focus_context.get("focus_ticket_id") is not None:
                resolved_order.append(int(focus_context["focus_ticket_id"]))
            history.append(
                f"Step {step}: {focus_context.get('reasoning_summary', 'n/a')} -> {action_str} -> reward {reward:.2f}"
            )

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

    return {
        "task": task_name,
        "policy": policy,
        "success": success,
        "score": score,
        "steps": steps_taken,
        "max_steps": max_steps,
        "total_reward": round(sum(rewards), 3),
        "rewards": rewards,
        "resolved_order": resolved_order,
        "efficiency": round(steps_taken / max_steps, 3) if max_steps else 0.0,
    }


def run_llm_agent(client: OpenAI) -> List[Dict[str, Any]]:
    return [run_task(client, task_name, policy="safe_llm") for task_name in TASK_ORDER]


def run_random_agent(seed: int = 42) -> List[Dict[str, Any]]:
    rng = random.Random(seed)
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    try:
        return [run_task(client, task_name, policy="random", rng=rng) for task_name in TASK_ORDER]
    finally:
        client.close()


def compare_agents(seed: int = 42) -> Dict[str, List[Dict[str, Any]]]:
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    try:
        llm_results = run_llm_agent(client)
    finally:
        client.close()
    random_results = run_random_agent(seed=seed)
    return {
        "safe_llm": llm_results,
        "random": random_results,
    }


def main() -> None:
    if not API_KEY:
        raise RuntimeError("Set API_KEY, HF_TOKEN, or OPENAI_API_KEY before running inference.py")

    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    try:
        for task_name in TASK_ORDER:
            run_task(client, task_name, policy="safe_llm")
    finally:
        client.close()


if __name__ == "__main__":
    main()
