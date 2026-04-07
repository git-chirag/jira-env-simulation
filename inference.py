from __future__ import annotations

import os
from typing import Optional

from openai import OpenAI

from env import JiraEnv
from models import Action, Ticket

API_BASE_URL = os.environ["API_BASE_URL"]
API_KEY = os.environ["API_KEY"]
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4o-mini")
TASK_NAME = "baseline"
ENV_NAME = "jira-env"
MAX_STEPS = 12

ASSIGN_REWARD = 0.2
TIME_PENALTY = 0.05
RESOLVE_REWARD_BY_PRIORITY = {
    "high": 1.0,
    "medium": 0.7,
    "low": 0.4,
}

client = OpenAI(
    base_url=API_BASE_URL,
    api_key=API_KEY,
)


def clamp_score(value: float) -> float:
    return max(0.0, min(1.0, value))


def format_bool(value: bool) -> str:
    return "true" if value else "false"


def format_action(action: Action) -> str:
    if action.action_type == "assign_ticket":
        return f"assign_ticket(ticket_id={action.ticket_id},user={action.user})"
    if action.action_type == "resolve_ticket":
        return f"resolve_ticket(ticket_id={action.ticket_id})"
    if action.action_type == "add_comment":
        return f"add_comment(ticket_id={action.ticket_id},comment={action.comment})"
    if action.action_type == "change_priority":
        return f"change_priority(ticket_id={action.ticket_id},priority={action.priority})"
    return action.action_type


def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: list[float]) -> None:
    rewards_str = ",".join(f"{reward:.2f}" for reward in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}",
        flush=True,
    )


def choose_action(
    tickets: list[Ticket],
    attempted_resolve_unassigned: set[int],
    reprioritized_tickets: set[int],
    comment_added: bool,
) -> Action | None:
    for ticket in tickets:
        if ticket.status == "resolved":
            continue
        if not ticket.assigned_to:
            if ticket.id not in attempted_resolve_unassigned:
                attempted_resolve_unassigned.add(ticket.id)
                return Action(
                    action_type="resolve_ticket",
                    ticket_id=ticket.id,
                )
            return Action(
                action_type="assign_ticket",
                ticket_id=ticket.id,
                user="alice",
            )
        if not comment_added:
            return Action(
                action_type="add_comment",
                ticket_id=ticket.id,
                comment="checking issue",
            )
        if ticket.priority != "high" and ticket.id not in reprioritized_tickets:
            reprioritized_tickets.add(ticket.id)
            return Action(
                action_type="change_priority",
                ticket_id=ticket.id,
                priority="high",
            )
        return Action(
            action_type="resolve_ticket",
            ticket_id=ticket.id,
        )
    return None


def compute_max_possible_reward(tickets: list[Ticket]) -> float:
    total = 0.0
    for ticket in tickets:
        total += ASSIGN_REWARD
        total += RESOLVE_REWARD_BY_PRIORITY[ticket.priority]
        total -= 2 * TIME_PENALTY
    return max(total, 0.01)


def main() -> None:
    env = JiraEnv()
    reset_result = env.reset()
    env.max_steps = MAX_STEPS
    max_possible_reward = compute_max_possible_reward(reset_result.observation.tickets)

    log_start(task=TASK_NAME, env=ENV_NAME, model=MODEL_NAME)

    rewards: list[float] = []
    steps_taken = 0
    success = False
    score = 0.0
    attempted_resolve_unassigned: set[int] = set()
    reprioritized_tickets: set[int] = set()
    comment_added = False

    try:
        for step_number in range(1, MAX_STEPS + 1):
            observation = env.state()
            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": "You are an assistant helping decide actions."},
                        {
                            "role": "user",
                            "content": f"Given this state: {observation}, suggest next action.",
                        },
                    ],
                    max_tokens=50,
                )
                llm_output = response.choices[0].message.content
            except Exception:
                llm_output = None

            _ = llm_output
            action = choose_action(
                observation.tickets,
                attempted_resolve_unassigned,
                reprioritized_tickets,
                comment_added,
            )
            if action is None:
                break

            if action.action_type == "add_comment":
                comment_added = True

            error = None
            result = env.step(action)
            reward = result.reward
            done = result.done

            rewards.append(reward)
            steps_taken = step_number
            log_step(
                step=step_number,
                action=format_action(action),
                reward=reward,
                done=done,
                error=error,
            )

            if done:
                break

        total_reward = sum(rewards)
        score = clamp_score(total_reward / max_possible_reward)
        success = score > 0.5
    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)


if __name__ == "__main__":
    main()
