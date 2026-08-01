# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

> The section below is from the original PawPal+ (Module 2) project, kept here for history.

## Agent Workflow (SF7)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

I asked the agent to implement multi-pet support across three files simultaneously: adding a pet_name field to the Task dataclass in `pawpal_system.py`, fixing `filter_tasks()` to filter by each task's own pet_name instead of the schedule-wide pet, and wiring the full multi-pet UI into `app.py` including an active-pet selector, per-pet task tagging, and isolated schedule generation per pet.

**What did the agent do?**

It added pet_name: str = "" to Task, updated both recurrence branches in `mark_complete()` to carry the field forward, rewrote `filter_tasks()` to compare `task.pet_name` instead of self.pet.name, and rebuilt the UI to store multiple pets in `st.session_state["pets"]` and filter `owner.get_tasks()` by the active pet before calling generate().

**What did you have to verify or fix manually?**

The agent didn't flag that tasks added before a pet existed would get pet_name=None and silently never appear in any schedule, so I had to add a guard that blocks task creation until a pet is selected. I also caught that the app crashed with TypeError on first run because Streamlit had cached the old Task class in memory.The fix was a full process restart, not a code change.

---

## Prompt Comparison (SF11)

> Compare two different prompts (or two different models) on the same task.

|                       | Option A | Option B |
| --------------------- | -------- | -------- |
| **Model / tool used** |          |          |
| **Prompt**            |          |          |
| **Response summary**  |          |          |
| **What was useful**   |          |          |
| **Problems noticed**  |          |          |
| **Decision**          |          |          |

**Which approach did you use in your final implementation and why?**

<!-- Your conclusion -->

---

## Agentic Workflow Enhancement — Applied AI System (Project 4, Stretch)

This is the multi-step agent I built for the Applied AI System project (`agent.py`), separate from the Module 2 work above. The agent doesn't just run once and stop, it plans, builds a schedule, checks for conflicts, and if it finds any, fixes them and checks again before it's done.

Here's a real run, pulled straight from `main.py`, not something I made up for this doc:

```
=== Agentic Workflow Demo ===
Agent status: resolved
Agent log:
[plan] Planning to schedule 2 task(s) within 90 available minute(s). (ok)
[act] Generated schedule with 2 slot(s). (ok)
[check] Found 1 conflict(s). (conflict_found)
[resolve] Moved 'Nail Trim' from 09:00 to 09:20, clearing 'Bath''s 20-minute duration (lower priority than 'Bath'). (resolved)
[check] No conflicts detected. (ok)
[run] All conflicts resolved. (resolved)
Resulting schedule:
Schedule for Luna on 2026-07-25 (Owner: Alex Rivera):
09:00 — Bath [Hygiene] — 20 min [priority: high]
09:20 — Nail Trim [Hygiene] — 10 min [priority: low]
```

What I like about this trace is the `resolve` line actually says _why_ it moved Nail Trim instead of Bath, "lower priority than 'Bath'", not just that something moved. That reasoning shows up for every kind of tiebreak the agent uses, so if I ever needed to explain why the agent made a specific call, the log already has the answer.
