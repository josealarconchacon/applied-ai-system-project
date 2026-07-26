import re
from datetime import datetime, timedelta

from pawpal_system import Schedule, Task


class SchedulingAgent:
    """Plan/act/check/resolve loop that drives a Schedule to a conflict-free state."""

    def __init__(self, schedule: Schedule, max_resolution_attempts: int = 3):
        self.schedule = schedule
        self.max_resolution_attempts = max_resolution_attempts
        self.log = []

    def _log(self, step: str, detail: str, result: str) -> None:
        self.log.append({
            "step": step,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "detail": detail,
            "result": result,
        })

    def plan(self, tasks, available_minutes) -> None:
        self._log(
            "plan",
            f"Planning to schedule {len(tasks)} task(s) within {available_minutes} available minute(s).",
            "ok",
        )

    def act(self, tasks, available_minutes) -> bool:
        try:
            self.schedule.generate(tasks=tasks, available_minutes=available_minutes)
        except Exception as exc:
            self._log("act", str(exc), "error")
            return False
        self._log("act", f"Generated schedule with {len(self.schedule.slots)} slot(s).", "ok")
        return True

    def check(self) -> list:
        conflicts = self.schedule.detect_conflicts()
        if conflicts:
            self._log("check", f"Found {len(conflicts)} conflict(s).", "conflict_found")
        else:
            self._log("check", "No conflicts detected.", "ok")
        return conflicts

    def resolve(self, conflicts: list) -> None:
        preferred_time_of_day = self.schedule.owner.preferences.get("preferred_time_of_day")
        pattern = re.compile(r"Conflict: '(.+)' and '(.+)' both scheduled at (\S+)")

        for warning in conflicts:
            match = pattern.match(warning)
            if not match:
                continue
            name_a, name_b, _time = match.groups()

            task_a = next((t for _, t in self.schedule.slots if t.name == name_a), None)
            task_b = next((t for _, t in self.schedule.slots if t.name == name_b), None)
            if task_a is None or task_b is None:
                continue

            mover, reason = self._pick_mover(task_a, task_b, preferred_time_of_day)
            stayer = task_a if mover is task_b else task_b

            old_time = mover.scheduled_time
            new_time = self._shift_after(stayer)
            mover.scheduled_time = new_time

            self._log(
                "resolve",
                f"Moved '{mover.name}' from {old_time} to {new_time}, clearing '{stayer.name}''s {stayer.duration_minutes}-minute duration ({reason}).",
                "resolved",
            )

    def _pick_mover(self, task_a: Task, task_b: Task, preferred_time_of_day):
        if task_a.get_priority_value() != task_b.get_priority_value():
            mover, stayer = (task_a, task_b) if task_a.get_priority_value() > task_b.get_priority_value() else (task_b, task_a)
            return mover, f"lower priority than '{stayer.name}'"

        a_matches = task_a.preferred_time_of_day == preferred_time_of_day
        b_matches = task_b.preferred_time_of_day == preferred_time_of_day
        if a_matches != b_matches:
            mover, stayer = (task_a, task_b) if not a_matches else (task_b, task_a)
            return mover, f"preferred_time_of_day mismatch vs '{stayer.name}'"

        mover, stayer = (task_a, task_b) if task_a.name > task_b.name else (task_b, task_a)
        return mover, f"alphabetically later than '{stayer.name}'"

    def _shift_after(self, anchor_task: Task) -> str:
        base = datetime.strptime(anchor_task.scheduled_time, "%H:%M")
        shifted = base + timedelta(minutes=anchor_task.duration_minutes)
        return shifted.strftime("%H:%M")

    def run(self, tasks, available_minutes) -> dict:
        self.plan(tasks, available_minutes)

        if not self.act(tasks, available_minutes):
            self._log("run", "Aborting after act() error.", "error")
            return {"status": "error", "log": self.log}

        conflicts = self.check()

        attempts = 0
        while conflicts and attempts < self.max_resolution_attempts:
            self.resolve(conflicts)
            conflicts = self.check()
            attempts += 1

        if not conflicts:
            self._log("run", "All conflicts resolved.", "resolved")
            status = "resolved"
        else:
            self._log("run", f"{len(conflicts)} conflict(s) remain after {self.max_resolution_attempts} attempt(s).", "unresolved")
            status = "unresolved"

        return {"status": status, "log": self.log}
