from __future__ import annotations

import os

from openai import OpenAI

from env import JiraEnv
from models import Action, Ticket


DEFAULT_API_BASE_URL = "https://router.huggingface.co/v1"
DEFAULT_MODEL_NAME = "gpt-4o-mini"
DEFAULT_HF_TOKEN = "hf_demo_token"
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
    api_base_url = os.getenv("API_BASE_URL", DEFAULT_API_BASE_URL)
    model_name = os.getenv("MODEL_NAME", DEFAULT_MODEL_NAME)
    hf_token = os.getenv("HF_TOKEN", DEFAULT_HF_TOKEN)

    # The client is initialized for future model-backed inference, even though
    # this baseline uses deterministic rule-based actions only.
    _client = OpenAI(
        base_url=api_base_url,
        api_key=hf_token,
    )

    env = JiraEnv()
    reset_result = env.reset()
    env.max_steps = MAX_STEPS
    max_possible_reward = compute_max_possible_reward(reset_result.observation.tickets)

    print(f"[START] task={TASK_NAME} env={ENV_NAME} model={model_name}")

    rewards: list[float] = []
    steps_taken = 0
    success = False
    score = 0.0
    attempted_resolve_unassigned: set[int] = set()
    reprioritized_tickets: set[int] = set()
    comment_added = False

    for step_number in range(1, MAX_STEPS + 1):
        action = choose_action(
            env.state().tickets,
            attempted_resolve_unassigned,
            reprioritized_tickets,
            comment_added,
        )
        if action is None:
            break

        if action.action_type == "add_comment":
            comment_added = True

        error = "null"
        try:
            result = env.step(action)
            reward = result.reward
            done = result.done
        except Exception as exc:
            reward = 0.0
            done = False
            error = str(exc)
            print(
                f"[STEP] step={step_number} action={format_action(action)} "
                f"reward={reward:.2f} done={format_bool(done)} error={error}"
            )
            steps_taken = step_number
            break

        rewards.append(reward)
        steps_taken = step_number
        print(
            f"[STEP] step={step_number} action={format_action(action)} "
            f"reward={reward:.2f} done={format_bool(done)} error={error}"
        )

        if done:
            break

    total_reward = sum(rewards)
    score = clamp_score(total_reward / max_possible_reward)
    success = score > 0.5
    rewards_str = ",".join(f"{reward:.2f}" for reward in rewards)

    print(
        f"[END] success={format_bool(success)} steps={steps_taken} "
        f"score={score:.2f} rewards={rewards_str}"
    )


if __name__ == "__main__":
    main()
