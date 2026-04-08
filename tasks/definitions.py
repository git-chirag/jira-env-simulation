TASKS = {
    "easy": {
        "description": "Resolve a single high-priority ticket",
        "ideal_outcome": "resolve_assigned_high_priority_ticket",
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
                    "ideal_action_sequence": ["assign_ticket", "resolve_ticket"],
                },
            }
        ],
    },
    "medium": {
        "description": "Resolve multiple tickets with mixed priorities",
        "ideal_outcome": "resolve_all_tickets_with_reasonable_efficiency",
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
                    "expected_completion": 1.0,
                },
            }
        ],
    },
    "hard": {
        "description": "Resolve tickets while optimizing priority and efficiency",
        "ideal_outcome": "resolve_all_tickets_with_high_priority_first",
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
                },
            }
        ],
    },
}

TASK_NAMES = list(TASKS.keys())
