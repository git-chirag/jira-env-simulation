TASKS = {
    "easy": {
        "description": "Assign and resolve a single high-priority ticket with minimal wasted motion.",
        "ideal_action": "assign_ticket",
        "steps": [
            {
                "observation": (
                    "Jira Simulation Report:\n"
                    "Task: easy\n"
                    "Ticket #1 is high priority, open, and currently unassigned.\n"
                    "A correct next move prepares the urgent ticket for resolution.\n"
                    "Choose one action type: assign_ticket, resolve_ticket, add_comment, update_status, or change_priority."
                ),
                "signals": {
                    "priority": "high",
                    "assigned": False,
                    "status": "open",
                    "ideal_action": "assign_ticket",
                },
            },
            {
                "observation": (
                    "Jira Simulation Report:\n"
                    "Task: easy\n"
                    "Ticket #1 is high priority, assigned, and still open.\n"
                    "The next move should complete the work cleanly.\n"
                    "Choose one action type: assign_ticket, resolve_ticket, add_comment, update_status, or change_priority."
                ),
                "signals": {
                    "priority": "high",
                    "assigned": True,
                    "status": "open",
                    "ideal_action": "resolve_ticket",
                },
            },
        ],
    },
    "medium": {
        "description": "Work through multiple tickets with mixed priorities while staying reasonably efficient.",
        "ideal_action": "assign_ticket",
        "steps": [
            {
                "observation": (
                    "Jira Simulation Report:\n"
                    "Task: medium\n"
                    "Three tickets are open: one high, one medium, and one low priority.\n"
                    "None are assigned yet.\n"
                    "The best next move starts progress on the highest-priority ticket.\n"
                    "Choose one action type: assign_ticket, resolve_ticket, add_comment, update_status, or change_priority."
                ),
                "signals": {
                    "priority": "high",
                    "assigned": False,
                    "status": "open",
                    "ideal_action": "assign_ticket",
                },
            },
            {
                "observation": (
                    "Jira Simulation Report:\n"
                    "Task: medium\n"
                    "The high-priority ticket is assigned and ready to close.\n"
                    "Two lower-priority tickets remain open.\n"
                    "Choose one action type: assign_ticket, resolve_ticket, add_comment, update_status, or change_priority."
                ),
                "signals": {
                    "priority": "high",
                    "assigned": True,
                    "status": "open",
                    "ideal_action": "resolve_ticket",
                },
            },
            {
                "observation": (
                    "Jira Simulation Report:\n"
                    "Task: medium\n"
                    "The urgent ticket is resolved.\n"
                    "A medium-priority ticket is now the best work item and is still unassigned.\n"
                    "Choose one action type: assign_ticket, resolve_ticket, add_comment, update_status, or change_priority."
                ),
                "signals": {
                    "priority": "medium",
                    "assigned": False,
                    "status": "open",
                    "ideal_action": "assign_ticket",
                },
            },
        ],
    },
    "hard": {
        "description": "Prioritize urgent work correctly, avoid useless actions, and finish efficiently.",
        "ideal_action": "assign_ticket",
        "steps": [
            {
                "observation": (
                    "Jira Simulation Report:\n"
                    "Task: hard\n"
                    "Five tickets are open. Two are high priority, two are medium, and one is low.\n"
                    "No ticket is assigned yet.\n"
                    "The best move starts execution on a high-priority ticket first.\n"
                    "Choose one action type: assign_ticket, resolve_ticket, add_comment, update_status, or change_priority."
                ),
                "signals": {
                    "priority": "high",
                    "assigned": False,
                    "status": "open",
                    "priority_discipline": True,
                    "ideal_action": "assign_ticket",
                },
            },
            {
                "observation": (
                    "Jira Simulation Report:\n"
                    "Task: hard\n"
                    "A high-priority ticket is assigned and ready to resolve.\n"
                    "Lower-priority tickets are still untouched.\n"
                    "Choose one action type: assign_ticket, resolve_ticket, add_comment, update_status, or change_priority."
                ),
                "signals": {
                    "priority": "high",
                    "assigned": True,
                    "status": "open",
                    "priority_discipline": True,
                    "ideal_action": "resolve_ticket",
                },
            },
            {
                "observation": (
                    "Jira Simulation Report:\n"
                    "Task: hard\n"
                    "One high-priority ticket remains open and unassigned.\n"
                    "Medium and low tickets should still wait.\n"
                    "Choose one action type: assign_ticket, resolve_ticket, add_comment, update_status, or change_priority."
                ),
                "signals": {
                    "priority": "high",
                    "assigned": False,
                    "status": "open",
                    "priority_discipline": True,
                    "ideal_action": "assign_ticket",
                },
            },
        ],
    },
}

TASK_NAMES = ["easy", "medium", "hard"]
