# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

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
