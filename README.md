---
title: Jira Env Simulation
emoji: 🎫
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# 🎫 Jira Env Simulation

A **Jira-like OpenEnv environment** for evaluating AI agents on real-world ticket management workflows such as prioritization, assignment, and resolution.

---

## 🧠 Motivation

Modern AI agents are increasingly used to automate **operational workflows** — from customer support to incident management.

However, evaluating such agents requires:
- structured environments  
- measurable outcomes  
- realistic constraints  

This project simulates a **ticket management system (inspired by Jira/Atlassian)** where agents must:
- interpret state  
- take meaningful actions  
- optimize for correctness and efficiency  

---

## ⚙️ Environment Overview

The environment follows a reinforcement-learning style interaction:

- `reset()` → initializes tickets  
- `step(action)` → applies an action and returns:
  - observation  
  - reward  
  - done  
- `state()` → returns current system state  

---

## 🧩 Entities

Each ticket contains:

- `id`  
- `title`  
- `priority` (low / medium / high)  
- `status` (open / in_progress / resolved)  
- `assigned_to`  
- `comments`  
- `created_step`  

---

## 🎯 Action Space

Agents can perform:

- `assign_ticket(ticket_id, user)`  
- `resolve_ticket(ticket_id)`  
- `update_status(ticket_id, status)`  
- `change_priority(ticket_id, priority)`  
- `add_comment(ticket_id, text)`  

---

## 📊 Reward Design

The reward function is **dense and structured**:

### ✅ Positive signals
- Correct assignment  
- Resolving tickets  
- Handling high-priority tickets  
- Fast resolution within SLA windows

### ❌ Negative signals
- Invalid actions  
- Resolving without assignment  
- Inefficient behavior  
- Time penalties per step  
- Delayed resolution beyond ticket SLA  
- Unnecessary priority changes

👉 This ensures agents are rewarded for **both correctness and efficiency**

### Reward Design Notes

- High-priority tickets are expected to be resolved within 3 steps, medium within 5, and low within 7. Missing those SLAs adds a small penalty.  
- Resolving within SLA gives a small efficiency bonus, which makes early correct handling more valuable than late cleanup.  
- Hard-task scoring now strongly rewards resolving urgent tickets before lower-priority work and penalizes inefficient action sequences.

---

## 🧪 Tasks & Evaluation

The environment includes **3 graded tasks**:

### 🟢 Easy
- Resolve a single high-priority ticket  
- Score: binary (0 or 1)

---

### 🟡 Medium
- Resolve multiple tickets  
- Score: completion × efficiency  

---

### 🔴 Hard
- Resolve tickets with:
  - correct prioritization  
  - efficient action sequence  

Score is computed as:

- completion score  
- priority correctness  
- efficiency score  

👉 Produces a normalized score between **0.0 – 1.0**

---

## 🤖 Baseline Agent

A deterministic baseline agent is included (`inference.py`):

- follows simple rules  
- intentionally imperfect  
- achieves ~**0.7 score**

This ensures meaningful comparison with stronger agents.

---

## 🚀 API Endpoints

The environment is exposed via FastAPI:

- `POST /reset`  
- `POST /step`  
- `GET /state`  

---

## 🐳 Running Locally

```bash
docker build -t jira-env .
docker run -p 7860:7860 jira-env
