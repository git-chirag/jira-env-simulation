from dataclasses import dataclass, field
from typing import Any, List, Optional

from openenv.core.env_server import Environment

try:
    from ..models import JiraTaskAction, JiraTaskObservation, JiraTaskState
    from ..tasks.definitions import TASKS, TASK_NAMES
    from ..tasks.graders import grade_action
except ImportError:
    from models import JiraTaskAction, JiraTaskObservation, JiraTaskState
    from tasks.definitions import TASKS, TASK_NAMES
    from tasks.graders import grade_action


@dataclass
class Ticket:
    id: int
    title: str
    priority: str
    status: str
    assigned_to: Optional[str] = None
    comments: list[str] = field(default_factory=list)
    created_step: int = 0


class JiraTaskEnvironment(Environment[JiraTaskAction, JiraTaskObservation, JiraTaskState]):
    SUPPORTS_CONCURRENT_SESSIONS = True
    PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}
    SLA_THRESHOLDS = {"high": 3, "medium": 5, "low": 7}
    _http_task_id: Optional[str] = None
    _http_step_idx: int = 0
    _http_done: bool = False
    _http_rewards: List[float] = []
    _http_action_history: List[str] = []
    _http_commented_ticket_ids: List[int] = []
    _http_reprioritized_ticket_ids: List[int] = []
    _http_task_def: Any = None
    _http_tickets: List[Ticket] = []
    _http_dependencies: dict[int, list[int]] = {}

    def __init__(self):
        self._task_id: Optional[str] = None
        self._step_idx: int = 0
        self._done: bool = False
        self._rewards: List[float] = []
        self._action_history: List[str] = []
        self._commented_ticket_ids: set[int] = set()
        self._reprioritized_ticket_ids: set[int] = set()
        self._task_def: Any = None
        self._tickets: List[Ticket] = []
        self._dependencies: dict[int, list[int]] = {}

    def reset(self, seed: Optional[int] = None, episode_id: Optional[str] = None, **kwargs: Any) -> JiraTaskObservation:
        """Reset the environment to the start of a task."""
        del seed, episode_id
        self._task_id = kwargs.get("task_id") or kwargs.get("task") or TASK_NAMES[0]
        if self._task_id not in TASKS:
            self._task_id = TASK_NAMES[0]

        self._task_def = TASKS[self._task_id]
        self._step_idx = 0
        self._done = False
        self._rewards = []
        self._action_history = []
        self._commented_ticket_ids = set()
        self._reprioritized_ticket_ids = set()
        self._dependencies = {ticket_id: deps[:] for ticket_id, deps in self._task_def.get("dependencies", {}).items()}
        self._tickets = [self._ticket_from_dict(ticket_data) for ticket_data in self._task_def.get("initial_tickets", [])]
        self._persist_http_state()

        return JiraTaskObservation(
            text=self._build_observation(),
            task_id=self._task_id
        )

    def step(self, action: JiraTaskAction) -> JiraTaskObservation:
        """Apply an action and transition to the next state."""
        if self._task_id is None:
            self._restore_http_state()
        if self._task_id is None:
            self.reset(task_id=TASK_NAMES[0])
        if self._done:
            return JiraTaskObservation(
                text="",
                task_id=self._task_id or "",
                reward=0.01,
                done=True,
                metadata={
                    "step": self._step_idx,
                    "task_id": self._task_id,
                    "rewards_so_far": self._rewards,
                    "resolved_tickets": sum(1 for ticket in self._tickets if ticket.status == "resolved"),
                    "focus_ticket_id": None,
                    "focus_priority": None,
                    "blocked": False,
                    "action_effect": "no_op_episode_already_finished",
                    "reward_reason": "episode already finished; extra steps are safely ignored",
                    "warning": "episode_already_finished",
                },
            )

        self._step_idx += 1
        normalized_action = (action.action or "").strip().lower()
        target_ticket = self._select_focus_ticket()
        context = self._build_transition_context(normalized_action, target_ticket)
        self._apply_action(normalized_action, target_ticket, context)
        self._finalize_transition_context(normalized_action, context)
        reward = grade_action(self._task_id, normalized_action, context)
        reward = max(0.01, min(reward, 0.99))
        self._rewards.append(reward)
        self._action_history.append(normalized_action)
        self._done = self._all_resolved() or self._step_idx >= len(self._task_def["steps"])
        self._persist_http_state()

        info = {
            "step": self._step_idx,
            "task_id": self._task_id,
            "rewards_so_far": self._rewards,
            "resolved_tickets": sum(1 for ticket in self._tickets if ticket.status == "resolved"),
            "focus_ticket_id": target_ticket.id if target_ticket else None,
            "focus_priority": target_ticket.priority if target_ticket else None,
            "blocked": context["blocked"],
            "action_effect": self._describe_action_effect(normalized_action, context),
            "reward_reason": self._describe_reward_reason(normalized_action, context),
        }

        return JiraTaskObservation(
            text="" if self._done else self._build_observation(),
            task_id=self._task_id,
            reward=reward,
            done=self._done,
            metadata=info
        )

    @property
    def state(self) -> JiraTaskState:
        """Return the current comprehensive state."""
        if self._task_id is None:
            self._restore_http_state()
        return JiraTaskState(
            task_id=self._task_id or "",
            step=self._step_idx,
            max_steps=len(self._task_def["steps"]) if self._task_def else 0,
            history=[str(r) for r in self._rewards],
            done=self._done
        )

    def _persist_http_state(self) -> None:
        JiraTaskEnvironment._http_task_id = self._task_id
        JiraTaskEnvironment._http_step_idx = self._step_idx
        JiraTaskEnvironment._http_done = self._done
        JiraTaskEnvironment._http_rewards = list(self._rewards)
        JiraTaskEnvironment._http_action_history = list(self._action_history)
        JiraTaskEnvironment._http_commented_ticket_ids = sorted(self._commented_ticket_ids)
        JiraTaskEnvironment._http_reprioritized_ticket_ids = sorted(self._reprioritized_ticket_ids)
        JiraTaskEnvironment._http_task_def = self._task_def
        JiraTaskEnvironment._http_dependencies = {
            ticket_id: deps[:] for ticket_id, deps in self._dependencies.items()
        }
        JiraTaskEnvironment._http_tickets = [self._clone_ticket(ticket) for ticket in self._tickets]

    def _restore_http_state(self) -> None:
        self._task_id = JiraTaskEnvironment._http_task_id
        self._step_idx = JiraTaskEnvironment._http_step_idx
        self._done = JiraTaskEnvironment._http_done
        self._rewards = list(JiraTaskEnvironment._http_rewards)
        self._action_history = list(JiraTaskEnvironment._http_action_history)
        self._commented_ticket_ids = set(JiraTaskEnvironment._http_commented_ticket_ids)
        self._reprioritized_ticket_ids = set(JiraTaskEnvironment._http_reprioritized_ticket_ids)
        self._task_def = JiraTaskEnvironment._http_task_def
        self._dependencies = {
            ticket_id: deps[:] for ticket_id, deps in JiraTaskEnvironment._http_dependencies.items()
        }
        self._tickets = [self._clone_ticket(ticket) for ticket in JiraTaskEnvironment._http_tickets]

    @staticmethod
    def _ticket_from_dict(ticket_data: dict[str, Any]) -> Ticket:
        return Ticket(
            id=ticket_data["id"],
            title=ticket_data["title"],
            priority=ticket_data["priority"],
            status=ticket_data["status"],
            assigned_to=ticket_data.get("assigned_to"),
            comments=list(ticket_data.get("comments", [])),
            created_step=ticket_data.get("created_step", 0),
        )

    @staticmethod
    def _clone_ticket(ticket: Ticket) -> Ticket:
        return Ticket(
            id=ticket.id,
            title=ticket.title,
            priority=ticket.priority,
            status=ticket.status,
            assigned_to=ticket.assigned_to,
            comments=list(ticket.comments),
            created_step=ticket.created_step,
        )

    def _build_observation(self) -> str:
        focus_ticket = self._select_focus_ticket()
        lines = [
            "Jira Simulation Report:",
            f"Task: {self._task_id}",
            f"Current step: {self._step_idx + 1}/{len(self._task_def['steps'])}",
            self._task_def["description"],
            "",
            "Ticket summary:",
        ]

        for ticket in sorted(self._tickets, key=lambda item: item.id):
            if ticket.status == "resolved":
                state_line = f"Ticket #{ticket.id} '{ticket.title}' is {ticket.priority} priority and already resolved."
            elif self._is_blocked(ticket):
                blocking = ", ".join(f"#{dep}" for dep in self._dependencies.get(ticket.id, []))
                state_line = (
                    f"Ticket #{ticket.id} '{ticket.title}' is {ticket.priority} priority, assigned to {ticket.assigned_to}, "
                    f"but blocked until ticket(s) {blocking} are resolved."
                )
            elif not ticket.assigned_to:
                state_line = (
                    f"Ticket #{ticket.id} '{ticket.title}' is {ticket.priority} priority, {ticket.status}, and currently unassigned."
                )
            elif ticket.status != "in_progress":
                state_line = (
                    f"Ticket #{ticket.id} '{ticket.title}' is {ticket.priority} priority, assigned to {ticket.assigned_to}, "
                    f"status {ticket.status}, and needs active work before it can be resolved."
                )
            else:
                state_line = (
                    f"Ticket #{ticket.id} '{ticket.title}' is {ticket.priority} priority, assigned to {ticket.assigned_to}, "
                    f"status {ticket.status}, and ready to resolve."
                )
            lines.append(state_line)

        if focus_ticket is None:
            lines.append("")
            lines.append("All tickets are resolved.")
        elif self._is_blocked(focus_ticket):
            dependency_list = ", ".join(f"#{dep}" for dep in self._dependencies.get(focus_ticket.id, []))
            lines.append("")
            lines.append(
                f"Current focus: Ticket #{focus_ticket.id} remains blocked until dependency ticket(s) {dependency_list} are resolved."
            )
        elif not focus_ticket.assigned_to:
            lines.append("")
            lines.append(
                f"Current focus: Ticket #{focus_ticket.id} is the most urgent open item and is currently unassigned."
            )
            lines.append("The best next move starts progress on the current focus ticket.")
        elif focus_ticket.status != "in_progress":
            lines.append("")
            lines.append(
                f"Current focus: Ticket #{focus_ticket.id} is assigned but still marked {focus_ticket.status}."
            )
            lines.append("Move it into active work before trying to close it.")
        else:
            lines.append("")
            lines.append(
                f"Current focus: Ticket #{focus_ticket.id} is assigned and ready to close."
            )
            lines.append("The next move should complete the work cleanly.")

        lines.append("Choose one action type: assign_ticket, resolve_ticket, add_comment, update_status, or change_priority.")
        return "\n".join(lines)

    def _select_focus_ticket(self) -> Optional[Ticket]:
        unresolved = [ticket for ticket in self._tickets if ticket.status != "resolved"]
        if not unresolved:
            return None

        ready = [ticket for ticket in unresolved if not self._is_blocked(ticket)]
        candidates = ready if ready else unresolved
        return sorted(candidates, key=lambda ticket: (self.PRIORITY_RANK.get(ticket.priority, 3), ticket.id))[0]

    def _build_transition_context(self, action: str, target_ticket: Optional[Ticket]) -> dict[str, Any]:
        action_valid = action in {
            "assign_ticket",
            "resolve_ticket",
            "update_status",
            "change_priority",
            "add_comment",
        }
        blocked = self._is_blocked(target_ticket) if target_ticket else False
        unresolved_before = sum(1 for ticket in self._tickets if ticket.status != "resolved")
        return {
            "task_id": self._task_id,
            "step_idx": self._step_idx,
            "action_valid": action_valid,
            "target_exists": target_ticket is not None,
            "invalid_action": not action_valid,
            "blocked": blocked,
            "previous_action": self._action_history[-1] if self._action_history else None,
            "repeated_action": bool(self._action_history and self._action_history[-1] == action),
            "priority_before": target_ticket.priority if target_ticket else None,
            "status_before": target_ticket.status if target_ticket else None,
            "assigned_before": bool(target_ticket.assigned_to) if target_ticket else False,
            "ready_before": bool(target_ticket and target_ticket.assigned_to and target_ticket.status == "in_progress" and not blocked),
            "unresolved_before": unresolved_before,
            "higher_priority_ready_before": self._has_higher_priority_ready_ticket(target_ticket),
            "sla_risk": self._is_sla_risk(target_ticket),
            "assigned_now": False,
            "status_updated": False,
            "resolved_now": False,
            "priority_changed": False,
            "comment_added": False,
            "priority_change_first_time": False,
            "comment_first_time": False,
            "within_sla": False,
            "dependency_cleared_now": False,
            "action_success": False,
            "comment_useful": False,
            "priority_change_useful": False,
            "productive_action": False,
            "no_progress": False,
            "repeated_no_progress": False,
            "all_resolved_after": False,
            "episode_completed": False,
            "episode_truncated": False,
            "unresolved_after": unresolved_before,
        }

    def _finalize_transition_context(self, action: str, context: dict[str, Any]) -> None:
        # Reward shaping depends on whether the action moved the queue forward,
        # not just whether it was syntactically valid.
        unresolved_after = sum(1 for ticket in self._tickets if ticket.status != "resolved")
        context["unresolved_after"] = unresolved_after
        context["all_resolved_after"] = unresolved_after == 0
        context["episode_completed"] = context["all_resolved_after"]
        context["episode_truncated"] = unresolved_after > 0 and self._step_idx >= len(self._task_def["steps"])
        context["comment_useful"] = bool(
            context["comment_added"] and (context["blocked"] or context["sla_risk"])
        )
        context["priority_change_useful"] = bool(
            context["priority_changed"] and context["sla_risk"] and context["priority_before"] != "high"
        )
        context["productive_action"] = bool(
            context["assigned_now"]
            or context["status_updated"]
            or context["resolved_now"]
            or context["priority_change_useful"]
            or context["comment_useful"]
        )
        context["no_progress"] = not context["productive_action"]
        context["repeated_no_progress"] = bool(context["repeated_action"] and context["no_progress"])

    def _apply_action(self, action: str, target_ticket: Optional[Ticket], context: dict[str, Any]) -> None:
        if target_ticket is None or not context["action_valid"]:
            return

        if action == "assign_ticket":
            if not target_ticket.assigned_to:
                target_ticket.assigned_to = "agent"
                context["assigned_now"] = True
                context["action_success"] = True
            return

        if action == "resolve_ticket":
            if (
                target_ticket.status != "resolved"
                and target_ticket.assigned_to
                and target_ticket.status == "in_progress"
                and not context["blocked"]
            ):
                target_ticket.status = "resolved"
                context["resolved_now"] = True
                context["within_sla"] = self._resolved_within_sla(target_ticket)
                context["dependency_cleared_now"] = self._clears_dependency(target_ticket.id)
                context["action_success"] = True
            return

        if action == "update_status":
            if target_ticket.status not in {"in_progress", "resolved"}:
                target_ticket.status = "in_progress"
                context["status_updated"] = True
                context["action_success"] = True
            return

        if action == "change_priority":
            new_priority = self._next_priority(target_ticket.priority)
            if new_priority != target_ticket.priority:
                context["priority_change_first_time"] = target_ticket.id not in self._reprioritized_ticket_ids
                target_ticket.priority = new_priority
                self._reprioritized_ticket_ids.add(target_ticket.id)
                context["priority_changed"] = True
                context["action_success"] = True
            return

        if action == "add_comment":
            context["comment_first_time"] = target_ticket.id not in self._commented_ticket_ids
            target_ticket.comments.append(f"Step {self._step_idx}: investigating")
            self._commented_ticket_ids.add(target_ticket.id)
            context["comment_added"] = True
            context["action_success"] = True

    def _is_blocked(self, ticket: Optional[Ticket]) -> bool:
        if ticket is None:
            return False
        dependencies = self._dependencies.get(ticket.id, [])
        if not dependencies:
            return False
        return any(self._ticket_status(dep_id) != "resolved" for dep_id in dependencies)

    def _ticket_status(self, ticket_id: int) -> str:
        for ticket in self._tickets:
            if ticket.id == ticket_id:
                return ticket.status
        return "resolved"

    def _all_resolved(self) -> bool:
        return all(ticket.status == "resolved" for ticket in self._tickets)

    def _has_higher_priority_ready_ticket(self, ticket: Optional[Ticket]) -> bool:
        if ticket is None:
            return False
        ticket_rank = self.PRIORITY_RANK.get(ticket.priority, 3)
        for candidate in self._tickets:
            if candidate.id == ticket.id or candidate.status == "resolved" or self._is_blocked(candidate):
                continue
            if self.PRIORITY_RANK.get(candidate.priority, 3) < ticket_rank:
                return True
        return False

    def _is_sla_risk(self, ticket: Optional[Ticket]) -> bool:
        if ticket is None or ticket.status == "resolved":
            return False
        threshold = self.SLA_THRESHOLDS.get(ticket.priority, 5)
        age = self._step_idx - ticket.created_step
        return age >= max(1, threshold - 1)

    def _resolved_within_sla(self, ticket: Ticket) -> bool:
        threshold = self.SLA_THRESHOLDS.get(ticket.priority, 5)
        age = self._step_idx - ticket.created_step
        return age <= threshold

    def _clears_dependency(self, ticket_id: int) -> bool:
        for dependency_ids in self._dependencies.values():
            if ticket_id in dependency_ids:
                return True
        return False

    def _next_priority(self, priority: str) -> str:
        if priority == "low":
            return "medium"
        if priority == "medium":
            return "high"
        return "high"

    @staticmethod
    def _describe_action_effect(action: str, context: dict[str, Any]) -> str:
        if not context["target_exists"]:
            return "no_focus_ticket"
        if not context["action_valid"]:
            return "invalid_action"
        if action == "assign_ticket":
            return "ticket_assigned" if context["assigned_now"] else "assignment_no_effect"
        if action == "update_status":
            return "status_updated_to_in_progress" if context["status_updated"] else "status_update_no_effect"
        if action == "resolve_ticket":
            if context["resolved_now"]:
                return "ticket_resolved"
            if context["blocked"]:
                return "resolve_blocked_by_dependency"
            if not context["assigned_before"]:
                return "resolve_failed_unassigned"
            if context["status_before"] != "in_progress":
                return "resolve_failed_not_in_progress"
            return "resolve_no_effect"
        if action == "change_priority":
            return "priority_changed" if context["priority_changed"] else "priority_change_no_effect"
        if action == "add_comment":
            return "comment_added" if context["comment_added"] else "comment_no_effect"
        return "no_effect"

    @staticmethod
    def _describe_reward_reason(action: str, context: dict[str, Any]) -> str:
        if not context["target_exists"]:
            return "no focus ticket was available"
        if not context["action_valid"]:
            return "action name was not recognized"
        if action == "resolve_ticket" and context["blocked"]:
            return "focus ticket is blocked by unresolved dependencies"
        if action == "assign_ticket" and context["assigned_now"]:
            return f"assigned the {context['priority_before']} priority focus ticket"
        if action == "update_status" and context["status_updated"]:
            return "moved the assigned focus ticket into active work"
        if action == "resolve_ticket" and context["resolved_now"]:
            if context["within_sla"]:
                return "resolved the focus ticket within SLA"
            return "resolved the focus ticket after SLA pressure increased"
        if action == "change_priority" and context["priority_changed"]:
            if context["priority_change_useful"]:
                return "reprioritized a ticket that was approaching SLA risk"
            return "changed priority without strong operational need"
        if action == "add_comment" and context["comment_added"]:
            if context["comment_useful"]:
                return "documented blocked or SLA-risk work"
            return "added a low-value operational comment"
        if context["repeated_no_progress"]:
            return "repeated a no-progress action"
        if context["no_progress"]:
            return "action did not move the queue forward"
        return "reward reflects the action outcome and current workflow state"
