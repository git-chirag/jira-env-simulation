TASKS = {
    "easy": {
        "description": "Resolve a single urgent production issue by assigning it and then closing it quickly.",
        "ideal_action": "assign_ticket",
        "steps": [
            {"milestone": "assign urgent ticket"},
            {"milestone": "resolve urgent ticket"},
        ],
        "initial_tickets": [
            {
                "id": 1,
                "title": "Fix login outage",
                "priority": "high",
                "status": "open",
                "assigned_to": None,
            }
        ],
        "dependencies": {},
    },
    "medium": {
        "description": "Handle a mixed queue where the urgent ticket must be assigned and resolved before closing lower-priority work.",
        "ideal_action": "assign_ticket",
        "steps": [
            {"milestone": "assign urgent ticket"},
            {"milestone": "resolve urgent ticket"},
            {"milestone": "resolve assigned follow-up"},
        ],
        "initial_tickets": [
            {
                "id": 1,
                "title": "Restore checkout flow",
                "priority": "high",
                "status": "open",
                "assigned_to": None,
            },
            {
                "id": 2,
                "title": "Update onboarding copy",
                "priority": "medium",
                "status": "in_progress",
                "assigned_to": "alice",
            },
            {
                "id": 3,
                "title": "Refresh support FAQ",
                "priority": "low",
                "status": "resolved",
                "assigned_to": "ops-bot",
            },
        ],
        "dependencies": {},
    },
    "hard": {
        "description": "Resolve a realistic queue with priority discipline and a dependency that blocks follow-up work until the incident is closed.",
        "ideal_action": "assign_ticket",
        "steps": [
            {"milestone": "assign blocking incident"},
            {"milestone": "resolve blocking incident"},
            {"milestone": "resolve dependent follow-up"},
        ],
        "initial_tickets": [
            {
                "id": 1,
                "title": "Payment outage investigation",
                "priority": "high",
                "status": "open",
                "assigned_to": None,
            },
            {
                "id": 2,
                "title": "Checkout monitoring regression",
                "priority": "medium",
                "status": "in_progress",
                "assigned_to": "alice",
            },
            {
                "id": 3,
                "title": "Low-priority cleanup follow-up",
                "priority": "low",
                "status": "resolved",
                "assigned_to": "ops-bot",
            },
        ],
        "dependencies": {
            2: [1],
        },
    },
}

TASK_NAMES = ["easy", "medium", "hard"]
