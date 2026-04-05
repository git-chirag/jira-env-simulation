from __future__ import annotations

from env import JiraEnv
from models import Action, Ticket


def clamp_score(value: float) -> float:
    return max(0.0, min(1.0, value))


def count_resolved_tickets(env: JiraEnv) -> int:
    return sum(1 for ticket in env.tickets if ticket.status == "resolved")


def get_priority_order(env: JiraEnv, resolved_order: list[int]) -> list[str]:
    priority_by_ticket_id = {ticket.id: ticket.priority for ticket in env.tickets}
    return [priority_by_ticket_id[ticket_id] for ticket_id in resolved_order if ticket_id in priority_by_ticket_id]


def compute_efficiency_score(env: JiraEnv) -> float:
    if env.max_steps <= 0:
        return 0.0
    return clamp_score(1.0 - (env.current_step / env.max_steps))


def grade_easy_task(env: JiraEnv) -> float:
    if len(env.tickets) != 1:
        return 0.0
    return 1.0 if env.tickets[0].status == "resolved" else 0.0


def grade_medium_task(env: JiraEnv) -> float:
    total_tickets = len(env.tickets)
    if total_tickets == 0:
        return 0.0
    completion_score = count_resolved_tickets(env) / total_tickets
    efficiency_score = compute_efficiency_score(env)
    return clamp_score(completion_score * efficiency_score)


def grade_hard_task(env: JiraEnv, resolved_order: list[int]) -> float:
    total_tickets = len(env.tickets)
    if total_tickets == 0:
        return 0.0

    completion_score = count_resolved_tickets(env) / total_tickets

    priorities = get_priority_order(env, resolved_order)
    high_ticket_count = sum(1 for ticket in env.tickets if ticket.priority == "high")
    if high_ticket_count == 0:
        priority_score = 1.0
    else:
        high_indices = [index for index, priority in enumerate(priorities) if priority == "high"]
        lower_indices = [index for index, priority in enumerate(priorities) if priority != "high"]
        if not lower_indices:
            priority_score = 1.0
        elif high_indices and max(high_indices) < min(lower_indices):
            priority_score = 1.0
        else:
            priority_score = 0.2

    efficiency_score = compute_efficiency_score(env)

    score = (
        0.5 * completion_score
        + 0.3 * priority_score
        + 0.2 * efficiency_score
    )
    return clamp_score(score)


def _resolve_ticket(env: JiraEnv, ticket_id: int, user: str, resolved_order: list[int] | None = None) -> None:
    env.step(Action(action_type="assign_ticket", ticket_id=ticket_id, user=user))
    result = env.step(Action(action_type="resolve_ticket", ticket_id=ticket_id))
    if result.observation.tickets:
        for ticket in result.observation.tickets:
            if ticket.id == ticket_id and ticket.status == "resolved" and resolved_order is not None:
                resolved_order.append(ticket_id)
                break


def run_easy_task(env: JiraEnv) -> float:
    env.reset()
    env.tickets = [
        Ticket(
            id=1,
            title="Fix login error",
            priority="high",
            status="open",
            created_step=env.current_step,
        )
    ]

    _resolve_ticket(env, ticket_id=1, user="alice")
    return grade_easy_task(env)


def run_medium_task(env: JiraEnv) -> float:
    env.reset()
    env.max_steps = 10
    env.tickets = [
        Ticket(
            id=1,
            title="Fix login error",
            priority="high",
            status="open",
            created_step=env.current_step,
        ),
        Ticket(
            id=2,
            title="Refresh help text",
            priority="medium",
            status="open",
            created_step=env.current_step,
        ),
        Ticket(
            id=3,
            title="Remove dead CSS",
            priority="low",
            status="open",
            created_step=env.current_step,
        ),
    ]

    _resolve_ticket(env, ticket_id=1, user="alice")
    env.step(Action(action_type="add_comment", ticket_id=2, comment="Need follow-up"))
    _resolve_ticket(env, ticket_id=2, user="bob")
    _resolve_ticket(env, ticket_id=3, user="carol")
    return grade_medium_task(env)


def run_hard_task(env: JiraEnv) -> float:
    env.reset()
    env.max_steps = 20
    env.tickets = [
        Ticket(
            id=1,
            title="Payment gateway outage",
            priority="high",
            status="open",
            created_step=env.current_step,
        ),
        Ticket(
            id=2,
            title="Search results lag",
            priority="medium",
            status="open",
            created_step=env.current_step,
        ),
        Ticket(
            id=3,
            title="Security alert triage",
            priority="high",
            status="open",
            created_step=env.current_step,
        ),
        Ticket(
            id=4,
            title="Broken footer link",
            priority="low",
            status="open",
            created_step=env.current_step,
        ),
        Ticket(
            id=5,
            title="Dashboard query cleanup",
            priority="medium",
            status="open",
            created_step=env.current_step,
        ),
    ]

    resolved_order: list[int] = []
    for ticket_id, user in [
        (2, "carol"),
        (1, "alice"),
        (3, "bob"),
        (5, "dave"),
        (4, "erin"),
    ]:
        _resolve_ticket(env, ticket_id=ticket_id, user=user, resolved_order=resolved_order)
        if ticket_id == 1:
            env.step(Action(action_type="add_comment", ticket_id=4, comment="Queue after urgent work"))
        if env.state().current_step >= env.max_steps:
            break

    return grade_hard_task(env, resolved_order)


if __name__ == "__main__":
    env = JiraEnv()
    print("Easy:", run_easy_task(env))
    print("Medium:", run_medium_task(env))
    print("Hard:", run_hard_task(env))
