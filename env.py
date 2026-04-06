from __future__ import annotations

from models import Action, Observation, StepResult, Ticket


class JiraEnv:
    def __init__(self, max_steps: int = 10) -> None:
        self.max_steps = max_steps
        self.tickets: list[Ticket] = []
        self.current_step = 0
        self.sla_thresholds = {
            "high": 3,
            "medium": 5,
            "low": 7,
        }

    def reset(self) -> StepResult:
        self.current_step = 0
        self.tickets = [
            Ticket(
                id=1,
                title="Fix login error",
                priority="high",
                status="open",
                created_step=0,
            ),
            Ticket(
                id=2,
                title="Update onboarding copy",
                priority="medium",
                status="open",
                created_step=0,
            ),
            Ticket(
                id=3,
                title="Clean up unused CSS",
                priority="low",
                status="open",
                created_step=0,
            ),
        ]
        return StepResult(
            observation=self.state(),
            reward=0.0,
            done=False,
            info={},
        )

    def state(self) -> Observation:
        return Observation(
            tickets=[self._clone_ticket(ticket) for ticket in self.tickets],
            current_step=self.current_step,
        )

    def step(self, action: Action) -> StepResult:
        self.current_step += 1
        reward = -0.05

        ticket = self._get_ticket(action.ticket_id)
        if ticket is None:
            reward += -1.0
            return StepResult(
                observation=self.state(),
                reward=reward,
                done=self._is_done(),
                info={},
            )

        if action.action_type == "assign_ticket":
            if not action.user:
                reward += -1.0
            elif ticket.assigned_to:
                reward += -0.1
            else:
                ticket.assigned_to = action.user
                reward += 0.2

        elif action.action_type == "update_status":
            if action.status is None:
                reward += -1.0
            elif ticket.status == action.status:
                reward += -0.1
            else:
                ticket.status = action.status
                reward += 0.1

        elif action.action_type == "resolve_ticket":
            if ticket.status == "resolved":
                reward += -0.1
            elif not ticket.assigned_to:
                reward += -0.5
            else:
                ticket.status = "resolved"
                if ticket.priority == "high":
                    reward += 1.0
                elif ticket.priority == "medium":
                    reward += 0.7
                else:
                    reward += 0.4

                if self._resolved_within_sla(ticket):
                    reward += 0.1
                else:
                    reward += -0.3

        elif action.action_type == "change_priority":
            if action.priority is None:
                reward += -1.0
            elif ticket.priority == action.priority:
                reward += -0.1
            else:
                ticket.priority = action.priority
                reward += 0.05

        elif action.action_type == "add_comment":
            if not action.comment:
                reward += -1.0
            else:
                ticket.comments.append(action.comment)
                reward += 0.05

        done = self._is_done()
        return StepResult(
            observation=self.state(),
            reward=reward,
            done=done,
            info={},
        )

    def _get_ticket(self, ticket_id: int) -> Ticket | None:
        for ticket in self.tickets:
            if ticket.id == ticket_id:
                return ticket
        return None

    def _clone_ticket(self, ticket: Ticket) -> Ticket:
        if hasattr(ticket, "model_copy"):
            return ticket.model_copy(deep=True)
        return ticket.copy(deep=True)

    def _is_done(self) -> bool:
        all_resolved = all(ticket.status == "resolved" for ticket in self.tickets)
        return all_resolved or self.current_step >= self.max_steps

    def _resolved_within_sla(self, ticket: Ticket) -> bool:
        threshold = self.sla_thresholds.get(ticket.priority, 5)
        age = self.current_step - ticket.created_step
        return age <= threshold
