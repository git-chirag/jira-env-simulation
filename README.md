---
title: Jira Env Simulation
emoji: 🎫
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
tags:
  - openenv
---

# Jira Env Simulation

Jira Env Simulation is an OpenEnv-compatible environment for evaluating AI agents on a real operational workflow: triaging, assigning, and resolving Jira-style tickets under priority pressure, SLA expectations, and dependency constraints.

## Why This Environment Exists

Many production agents look competent on one-shot benchmarks but fail on operational discipline. Real support and incident queues require the agent to:

- identify the most urgent unresolved work
- avoid resolving tickets before ownership is established
- respect blocked dependencies
- resolve important incidents quickly enough to satisfy SLA pressure
- avoid wasting time on administrative churn such as unnecessary reprioritization or repetitive no-op actions

This environment focuses on those behaviors rather than toy-game mechanics.

## OpenEnv Interface

The environment exposes the standard interaction loop:

- `POST /reset`
- `POST /step`
- `GET /state`

It also exposes:

- `GET /` for a simple API landing response
- `GET /health`
- `GET /docs`

Each episode returns a textual observation, a bounded reward, a `done` flag, and structured state history.

## Observation Space

Observations are natural-language Jira summaries. Each observation includes:

- active task name
- current step budget
- ticket summaries for all visible tickets
- assignment status
- blocking dependency status
- a short hint about the current focus ticket

The observation format is intentionally textual so that a general-purpose LLM agent must interpret workflow state rather than rely on a hand-engineered game board.

## Action Space

The action model supports five operational moves:

- `assign_ticket`
- `resolve_ticket`
- `update_status`
- `change_priority`
- `add_comment`

These are intentionally simple action labels, but their effect depends on the live environment state.

## Task Ladder

The published benchmark contains three deterministic tasks.

### Easy

An urgent production incident is open, while lower-priority background work is already complete. The agent should focus on the active incident, establish ownership, move it into active work, and close it cleanly.

### Medium

A larger mixed queue is present with several operational tickets already in flight. The agent must still prioritize the urgent incident first, then work through the remaining assigned follow-up tickets efficiently.

### Hard

The queue is crowded and dependency-sensitive. A high-priority blocking incident must be cleared before multiple medium-priority follow-up tickets can be completed, while low-priority backlog remains in view.

## Reward Design

The reward function is dense, bounded, and behavior-aware.

Positive signals:

- assigning the right ticket, especially high-priority work
- resolving tickets cleanly once they are assigned
- clearing dependency blockers in the hard task
- finishing work within SLA windows
- completing an episode without unnecessary detours

Negative signals:

- invalid actions
- trying to resolve blocked or unassigned work
- repeated no-op actions
- unnecessary administrative churn
- low-value comments
- reprioritization that is not justified by SLA risk

### Realism-Oriented Shaping

The current grading logic is designed to reward realistic operational behavior rather than raw endpoint exploitation:

- assignment and resolution are the highest-value actions when they actually advance the queue
- comments are only mildly rewarded when they document risk or blocked work; otherwise they are treated as churn
- priority changes are only useful when a ticket is approaching SLA pressure
- repeated actions that do not move the queue forward are penalized
- all step rewards are clipped into the validator-safe range `0.01` to `0.99`

### SLA Policy

Each ticket carries an implicit SLA window based on priority:

- high priority: 3 steps
- medium priority: 5 steps
- low priority: 7 steps

Resolving within SLA adds a bonus. Missing the window reduces the reward for the resolution step.

### Workflow Prerequisites

The environment intentionally models simple but realistic operational discipline:

- `assign_ticket` gives ownership to the agent but does not automatically start active work
- `update_status` is used to move an assigned ticket into `in_progress`
- `resolve_ticket` only succeeds when the focus ticket is:
  - assigned
  - already `in_progress`
  - not blocked by dependencies

This means the cleanest `easy` trajectory is now:

1. `assign_ticket`
2. `update_status`
3. `resolve_ticket`

### Exact Grading Rules

All rewards are clipped to the strict OpenEnv-safe range `0.01` to `0.99`.

Base reward maps:

- assignment reward by priority:
  - high: `0.32`
  - medium: `0.26`
  - low: `0.20`
- resolution reward by priority:
  - high: `0.82`
  - medium: `0.66`
  - low: `0.50`

Common action scoring:

- if no valid target ticket exists: `0.01`
- if the action is invalid: `0.01`
- if a blocked ticket is resolved: `0.01`
- `assign_ticket`:
  - successful assignment: reward by priority
  - otherwise: `0.04`
- `update_status`:
  - status updated on an already assigned ticket: `0.22`
  - status updated otherwise: `0.08`
  - no useful change: `0.04`
- `resolve_ticket`:
  - successful resolution:
    - reward by priority
    - `+0.08` if within SLA
    - `-0.15` if beyond SLA
    - `+0.04` if this closes the final remaining ticket
  - failed resolution: `0.02`
- `change_priority`:
  - useful reprioritization: `0.18`
  - unnecessary reprioritization: `0.05`
- `add_comment`:
  - useful documentation on blocked or SLA-risk work: `0.16`
  - low-value comment: `0.07`

Global penalties applied after the action reward:

- repeated action: `-0.05`
- repeated no-progress action: `-0.08`
- no-progress `assign_ticket`, `resolve_ticket`, or `update_status`: `-0.06`
- ignoring a higher-priority ready ticket with a non-assignment action: `-0.07`

Task-specific bonuses:

- `easy`:
  - base bonus: `+0.08`
  - additional `+0.04` for correctly assigning the high-priority focus ticket
  - additional `+0.22` for correctly moving the assigned high-priority ticket into active work
  - additional `+0.04` for resolving the final remaining ticket
- `medium`:
  - `+0.02` when a successful resolution happens and unresolved tickets still remain
- `hard`:
  - `+0.06` when an action clears a dependency
  - `+0.04` for a successful high-priority `assign_ticket` or `resolve_ticket`
  - `-0.08` if a higher-priority ready ticket was available before the action

### Why The Scores Separate By Difficulty

The three published tasks are intentionally different in both queue size and workflow burden:

- `easy` is a short, clean incident workflow with a visible backlog but only one active urgent ticket
- `medium` requires resolving several operational tickets in sequence across a fuller mixed queue
- `hard` combines a larger queue, more medium-priority work, and dependency clearing before follow-up work can be finished

This keeps the benchmark realistic while still deterministic enough for reproducible evaluation.

## Baseline Agent

`inference.py` provides a validator-compatible baseline agent.

Key properties:

- uses the OpenAI client with `API_BASE_URL`, `MODEL_NAME`, and `API_KEY` / `HF_TOKEN`
- emits strict `[START]`, `[STEP]`, and `[END]` logs
- makes the required LLM proxy call on every decision step
- applies a deterministic safety layer on top of the model output
- falls back to a rule-based Jira policy if the model output is unusable

The baseline does not blindly trust the model. It accepts model suggestions only when they fit the currently visible workflow state. This keeps the trajectory reproducible and avoids obvious mistakes such as trying to resolve an unassigned focus ticket.

### Deterministic Safe-Policy Scores

The current deterministic safe policy achieves the following local scores over the published tasks:

| Task | Latest Local Baseline |
| :--- | ---: |
| `easy` | `0.650` |
| `medium` | `0.461` |
| `hard` | `0.394` |

These are trajectory means over the current reward function and provide a stable local reference point for debugging and regression checks.

## Failure Modes

Weak agents in this environment usually fail in a few predictable ways:

- they try to resolve work before ownership is established
- they skip the `update_status` transition and attempt to close tickets that are not yet actively in progress
- they spend steps on comments or reprioritization when the queue needs operational work instead
- they ignore dependency blockers and attempt follow-up work too early
- they waste steps on low-priority items while higher-priority ready work is still available

## Strong Agent Behavior

Stronger agents are distinguished by disciplined workflow sequencing:

- they identify the highest-priority ready ticket first
- they assign the focus ticket before attempting execution
- they move assigned work into `in_progress` before resolving it
- they clear blockers before working dependent tickets
- they minimize administrative churn and keep the queue moving forward

## Example Trajectory

For the `hard` task, a strong short trajectory is:

1. `assign_ticket` on the high-priority blocking incident
2. `update_status` on the blocker
3. `resolve_ticket` on the blocker
4. continue activating and resolving the newly unblocked follow-up tickets in priority order

This sequence clears the dependency chain without wasting steps and yields a strong score.

## Running Locally

### Docker

```bash
docker build -t jira-env .
docker run -p 7860:7860 jira-env
```

### Direct Python

```powershell
python server.py
```

### Baseline Inference

Windows PowerShell:

```powershell
$env:API_BASE_URL="https://router.huggingface.co/v1"
$env:MODEL_NAME="gpt-4o-mini"
$env:HF_TOKEN="your_token_here"
$env:ENV_BASE_URL="http://127.0.0.1:7860"
python inference.py
```

POSIX shell:

```bash
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=gpt-4o-mini
export HF_TOKEN=your_token_here
export ENV_BASE_URL=http://127.0.0.1:7860
python inference.py
```

## Validation and Development Notes

- `openenv.yaml` declares the benchmark metadata and task list
- `tasks/definitions.py` defines the published task scenarios
- `tasks/graders.py` contains the reward shaping logic
- `server/jira_environment.py` contains the stateful Jira workflow simulation
- `server/app.py` exposes the HTTP app used by Docker and Hugging Face Spaces

To run a local validation pass:

```bash
openenv validate
```

<!-- noop: trigger rebuild -->
