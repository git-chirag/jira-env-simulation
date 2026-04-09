---
title: Jira Env Simulation
emoji: 🎫
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
base_path: /web
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

One high-priority production issue is open and unassigned. The best policy is short and clean: assign the incident, then resolve it quickly.

### Medium

A mixed queue is present. The agent must still focus on the urgent unassigned incident first, then finish the already assigned follow-up work efficiently.

### Hard

The queue contains a blocking high-priority incident and a dependent medium-priority ticket. The agent must clear the blocker first, then finish the downstream work without wasting steps.

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

| Task | Mean Score |
| :--- | ---: |
| `easy` | `0.660` |
| `medium` | `0.657` |
| `hard` | `0.693` |

These are trajectory means over the current reward function and provide a stable local reference point for debugging and regression checks.

## Example Trajectory

For the `hard` task, a strong short trajectory is:

1. `assign_ticket` on the high-priority blocking incident
2. `resolve_ticket` on the blocker
3. `resolve_ticket` on the now-unblocked dependent ticket

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
