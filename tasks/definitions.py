TASKS = {
    "easy": {
        "description": "Resolve a single high-priority ticket",
        "ideal_action": "resolve_ticket",
        "steps": [
            {
                "observation": (
                    "Jira Scenario Report:\n"
                    "One open ticket is present.\n"
                    "Priority: high\n"
                    "Status: open\n"
                    "Assigned: no\n"
                    "Goal: assign the ticket and resolve it efficiently."
                ),
                "signals": {
                    "ticket_count": 1,
                    "high_priority_count": 1,
                    "requires_assignment": True,
                    "ideal_action": "assign_ticket",
                },
            },
            {
                "observation": (
                    "Jira Scenario Report:\n"
                    "The urgent ticket is now assigned to an agent.\n"
                    "Priority: high\n"
                    "Status: open\n"
                    "Assigned: yes\n"
                    "Goal: resolve the urgent ticket."
                ),
                "signals": {
                    "ticket_count": 1,
                    "high_priority_count": 1,
                    "requires_assignment": False,
                    "ideal_action": "resolve_ticket",
                },
            },
        ],
    },
    "medium": {
        "description": "Resolve multiple tickets with mixed priorities",
        "ideal_action": "resolve_ticket",
        "steps": [
            {
                "observation": (
                    "Jira Scenario Report:\n"
                    "Three tickets are open with mixed priorities.\n"
                    "At least one ticket is high priority.\n"
                    "Goal: resolve all tickets while avoiding unnecessary actions."
                ),
                "signals": {
                    "ticket_count": 3,
                    "high_priority_count": 1,
                    "medium_priority_count": 1,
                    "low_priority_count": 1,
                    "ideal_action": "resolve_ticket",
                    "expected_completion": 1.0,
                },
            },
            {
                "observation": (
                    "Jira Scenario Report:\n"
                    "At least one ticket remains unresolved.\n"
                    "The agent should continue progressing toward full completion."
                ),
                "signals": {
                    "ticket_count": 3,
                    "high_priority_count": 1,
                    "ideal_action": "resolve_ticket",
                    "expected_completion": 1.0,
                },
            },
        ],
    },
    "hard": {
        "description": "Resolve tickets while optimizing priority and efficiency",
        "ideal_action": "resolve_ticket",
        "steps": [
            {
                "observation": (
                    "Jira Scenario Report:\n"
                    "Five tickets are open.\n"
                    "Two are high priority, two are medium priority, and one is low priority.\n"
                    "Goal: resolve all tickets, handle high priority work first, and stay efficient."
                ),
                "signals": {
                    "ticket_count": 5,
                    "high_priority_count": 2,
                    "medium_priority_count": 2,
                    "low_priority_count": 1,
                    "priority_order_required": True,
                    "ideal_action": "resolve_ticket",
                },
            },
            {
                "observation": (
                    "Jira Scenario Report:\n"
                    "Urgent work should be completed before medium or low priority cleanup.\n"
                    "Goal: maintain priority discipline and efficiency."
                ),
                "signals": {
                    "ticket_count": 5,
                    "high_priority_count": 2,
                    "priority_order_required": True,
                    "ideal_action": "resolve_ticket",
                },
            },
        ],
    },
}

TASK_NAMES = list(TASKS.keys())
