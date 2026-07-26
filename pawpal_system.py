from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List


@dataclass
class Pet:
    """Pet class with its profile information and special care requirements"""
    name: str
    species: str
    breed: str
    age: int
    special_needs: List = field(default_factory=list)

    def get_care_profile(self) -> dict:
        """Returns a dictionary summarizing the pet's profile, including species, breed, age, and special needs"""
        return {
            "name": self.name,
            "species": self.species,
            "breed": self.breed,
            "age": self.age,
            "special_needs": self.special_needs,
        }

    def has_special_needs(self) -> bool:
        """Returns True if the pet has any special needs, False otherwise"""
        return len(self.special_needs) > 0


@dataclass
class Task:
    """Represents a single care task (feeding, grooming) that can be scheduled for a pet"""
    name: str
    category: str
    duration_minutes: int
    priority: str  # "low", "medium", or "high"
    frequency: str
    preferred_time_of_day: str
    completed: bool = False
    scheduled_time: str = ""
    schedule_date: date = field(default_factory=date.today)
    pet_name: str = ""

    def mark_complete(self) -> "Task | None":
        """Mark this task complete and return the next occurrence if applicable.

        Sets self.completed to True. If this is the first time the task
        transitions from incomplete to complete and the frequency is "daily" or
        "weekly", creates and returns a new Task with the same fields but
        completed=False and schedule_date advanced by one day or one week
        respectively. Returns None for any other frequency, or if the task was
        already completed before this call.

        The caller is responsible for adding the returned task to any Owner or
        Schedule — this method only creates and returns it.

        Returns:
            Task | None: the next-occurrence task, or None.
        """
        if self.completed:
            return None
        self.completed = True
        if self.frequency == "daily":
            return Task(
                name=self.name,
                category=self.category,
                duration_minutes=self.duration_minutes,
                priority=self.priority,
                frequency=self.frequency,
                preferred_time_of_day=self.preferred_time_of_day,
                scheduled_time=self.scheduled_time,
                schedule_date=self.schedule_date + timedelta(days=1),
                pet_name=self.pet_name,
            )
        if self.frequency == "weekly":
            return Task(
                name=self.name,
                category=self.category,
                duration_minutes=self.duration_minutes,
                priority=self.priority,
                frequency=self.frequency,
                preferred_time_of_day=self.preferred_time_of_day,
                scheduled_time=self.scheduled_time,
                schedule_date=self.schedule_date + timedelta(weeks=1),
                pet_name=self.pet_name,
            )
        return None

    def is_due_today(self) -> bool:
        """Returns True if this task should be performed today based on its frequency"""
        today = date.today()
        freq = self.frequency.lower()
        if freq == "daily":
            return True
        elif freq == "weekly":
            return today.weekday() == 0  # Mondays
        elif freq == "bi-weekly":
            week_number = today.isocalendar()[1]
            return today.weekday() == 0 and week_number % 2 == 0
        elif freq == "monthly":
            return today.day == 1
        return False

    def get_priority_value(self) -> int:
        """Returns a numeric value for priority, used for sorting (low=3, medium=2, high=1)"""
        return {"high": 1, "medium": 2, "low": 3}.get(self.priority.lower(), 2)

    def get_display_label(self) -> str:
        """Returns a label for the task, combining name, category, and duration."""
        return f"{self.name} [{self.category}] — {self.duration_minutes} min [priority: {self.priority}]"


class Owner:
    """Pet owner with their daily availability and a list of care tasks they manage"""
    def __init__(self, name: str, available_minutes_per_day: int, preferences: dict):
        self.name = name
        self.available_minutes_per_day = available_minutes_per_day
        self.preferences = preferences
        self.tasks: List[Task] = []

    def add_task(self, task: Task):
        """Adds a Task to the owner's managed task list"""
        self.tasks.append(task)

    def remove_task(self, task: Task):
        """Removes a Task from the owner's managed task list"""
        if task in self.tasks:
            self.tasks.remove(task)

    def get_tasks(self) -> List[Task]:
        """Returns the full list of Tasks currently managed by this owner"""
        return self.tasks

    def set_availability(self, minutes: int):
        """Updates the owner's available time per day in minutes"""
        self.available_minutes_per_day = minutes


class Schedule:
    """Builds and holds a daily care schedule for a specific owner and pet"""
    def __init__(self, schedule_date: date, owner: Owner, pet: Pet):
        self.date = schedule_date
        self.owner = owner
        self.pet = pet
        self.slots: List = []
        self.total_minutes_used: int = 0
        self.skipped_tasks: List[Task] = []

    def generate(self, tasks: List[Task], available_minutes: int):
        """Populates slots by fitting tasks into the available time budget in priority order.

        Tasks are sorted by (priority_value, time_of_day_match), so when two tasks share the
        same priority, the one matching the owner's preferred_time_of_day comes first (key 0)
        and the non-matching one comes second (key 1). If the owner has no preferred_time_of_day
        set, the secondary key has no effect since no task will match None.
        """
        due_tasks = [t for t in tasks if t.is_due_today()]
        sorted_tasks = sorted(
            due_tasks,
            key=lambda t: (
                t.get_priority_value(),
                0 if t.preferred_time_of_day == self.owner.preferences.get("preferred_time_of_day") else 1,
            ),
        )

        current_minute = 0
        time_remaining = available_minutes

        for task in sorted_tasks:
            if self.fits_in_budget(task, time_remaining):
                self.add_slot(current_minute, task)
                current_minute += task.duration_minutes
                time_remaining -= task.duration_minutes
            else:
                self.skipped_tasks.append(task)

    def add_slot(self, start_time: int, task: Task):
        """Appends a (start_time, task) entry to the schedule's slot list and updates total_minutes_used"""
        self.slots.append((start_time, task))
        self.total_minutes_used += task.duration_minutes

    def fits_in_budget(self, task: Task, time_remaining: int) -> bool:
        """Returns True if the task's duration fits within the remaining available minutes"""
        return task.duration_minutes <= time_remaining

    def sort_by_time(self) -> list:
        """Return slots sorted ascending by scheduled_time, empty strings sort last."""
        return sorted(self.slots, key=lambda t: t[1].scheduled_time if t[1].scheduled_time else "99:99")

    def filter_tasks(self, completed: bool = None, pet_name: str = None) -> list:
        """Return Task objects from slots matching the given completion status and/or each task's own pet_name."""
        return [
            task for _, task in self.slots
            if (completed is None or task.completed == completed)
            and (pet_name is None or task.pet_name == pet_name)
        ]

    def get_summary(self) -> str:
        """Returns a formatted string listing all scheduled slots and total minutes used"""
        if not self.slots:
            return "No tasks scheduled."
        lines = [f"Schedule for {self.pet.name} on {self.date} (Owner: {self.owner.name}):"]
        base_hour, base_minute = 8, 0
        for offset_minutes, task in self.slots:
            if task.scheduled_time:
                lines.append(f"  {task.scheduled_time} — {task.get_display_label()}")
            else:
                total = base_hour * 60 + base_minute + offset_minutes
                h, m = divmod(total, 60)
                lines.append(f"  {h:02d}:{m:02d} — {task.get_display_label()}")
        lines.append(f"Total time used: {self.total_minutes_used} min")
        return "\n".join(lines)

    def get_skipped_summary(self) -> str:
        """Returns a formatted string listing all tasks that were skipped due to time constraints"""
        if not self.skipped_tasks:
            return "No tasks skipped."
        lines = ["Skipped tasks (insufficient time):"]
        for task in self.skipped_tasks:
            lines.append(f"  - {task.get_display_label()}")
        return "\n".join(lines)

    def detect_conflicts(self) -> List[str]:
        """Returns warning messages for any two tasks sharing the same non-empty scheduled_time."""
        time_map = defaultdict(list)
        for _, task in self.slots:
            if task.scheduled_time:
                time_map[task.scheduled_time].append(task.name)
        warnings = []
        for time, names in time_map.items():
            for i in range(len(names)):
                for j in range(i + 1, len(names)):
                    warnings.append(f"Conflict: '{names[i]}' and '{names[j]}' both scheduled at {time}")
        return warnings
