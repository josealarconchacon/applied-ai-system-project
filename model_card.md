# PawPal+ — Applied AI System Model Card

## Limitations or Biases

The agent can only fix what it's told about. `detect_conflicts()` only checks one pet's schedule and only catches exact matching times, not real overlap, so the agent inherits that same blind spot. It's not resolving every conflict that could exist, just the ones the base system actually flags. When three tasks land at once, `resolve()` can end up moving the same task more than once before it settles.

The order the agent uses to decide which task moves, priority, then preferred time, then alphabetical, is my own stand-in for "what matters most." It's consistent, but not something everyone would agree with.

## Could This Be Misused?

Not really, it's a pet scheduling agent. The one thing worth naming: it reschedules tasks on its own, no confirmation step. Every move gets logged so nothing happens quietly, but if this kind of agent were doing something with real stakes, I'd want it to ask before acting, not just log it after.

## What Surprised Me

The biggest surprise was the agent reporting "resolved" on something that wasn't actually fixed. An early version moved a conflicting task by a flat 15 minutes and called it done, but it still overlapped a longer task. No test caught that, I only found it by checking the math myself.

## AI Collaboration

**Helpful:** Before building the agent, Claude walked me through whether it should call an actual model to make decisions or just run on rule-based logic. The reliability point is what settled it, an LLM call would've added randomness into the exact part of the project meant to prove the agent works consistently. That's why `SchedulingAgent` ended up fully deterministic instead of model-driven.

**Flawed:** At one point Claude told me a file "already had the requested change, nothing to do" after I asked for an edit, but the file had clearly changed from the version before. The code itself turned out fine, it was just the explanation that was wrong. I only caught it because I compared the file against the previous version myself instead of taking Claude's summary at face value.
