import pytest
from datetime import date
from pawpal_system import Owner, Pet, Schedule, Task
from agent import SchedulingAgent


@pytest.fixture
def sample_owner():
    return Owner(name="Alex", available_minutes_per_day=90, preferences={"preferred_time_of_day": "morning"})


@pytest.fixture
def sample_pet():
    return Pet(name="Luna", species="Dog", breed="Golden Retriever", age=3, special_needs=[])


@pytest.fixture
def sample_schedule(sample_owner, sample_pet):
    return Schedule(schedule_date=date.today(), owner=sample_owner, pet=sample_pet)


@pytest.fixture
def agent(sample_schedule):
    return SchedulingAgent(sample_schedule)


def test_run_no_conflicts_returns_resolved_status(agent):
    """Two tasks at different scheduled_time must resolve without ever hitting a conflict."""
    # 1. Arrange: two same-priority daily tasks with distinct scheduled_time values
    task_a = Task(
        name="Morning Walk",
        category="Exercise",
        duration_minutes=20,
        priority="medium",
        frequency="daily",
        preferred_time_of_day="morning",
        scheduled_time="08:00",
    )
    task_b = Task(
        name="Evening Walk",
        category="Exercise",
        duration_minutes=20,
        priority="medium",
        frequency="daily",
        preferred_time_of_day="evening",
        scheduled_time="18:00",
    )
    # 2. Act: run the agent's plan/act/check/resolve loop
    result = agent.run(tasks=[task_a, task_b], available_minutes=90)
    # 3. Assert: resolved status and no conflict was ever logged
    assert result["status"] == "resolved"
    assert all(entry["result"] != "conflict_found" for entry in result["log"])


def test_run_resolves_conflict_by_priority(agent):
    """A conflict between tasks of different priority must move only the lower-priority task."""
    # 1. Arrange: two tasks at the same scheduled_time, differing only in priority
    high_task = Task(
        name="Vet Check",
        category="Health",
        duration_minutes=15,
        priority="high",
        frequency="daily",
        preferred_time_of_day="morning",
        scheduled_time="10:00",
    )
    low_task = Task(
        name="Play Time",
        category="Exercise",
        duration_minutes=15,
        priority="low",
        frequency="daily",
        preferred_time_of_day="morning",
        scheduled_time="10:00",
    )
    original_high_time = high_task.scheduled_time
    original_low_time = low_task.scheduled_time
    # 2. Act: run the agent's loop
    result = agent.run(tasks=[high_task, low_task], available_minutes=90)
    # 3. Assert: resolved, low-priority task moved, high-priority task untouched
    assert result["status"] == "resolved"
    assert low_task.scheduled_time != original_low_time
    assert high_task.scheduled_time == original_high_time


def test_run_resolves_conflict_by_alphabetical_tiebreak(agent):
    """When priority and preferred_time_of_day both tie, the alphabetically later task must move."""
    # 1. Arrange: same scheduled_time, same priority, same non-matching preferred_time_of_day
    task_bravo = Task(
        name="Bravo Groom",
        category="Hygiene",
        duration_minutes=15,
        priority="medium",
        frequency="daily",
        preferred_time_of_day="afternoon",
        scheduled_time="11:00",
    )
    task_alpha = Task(
        name="Alpha Groom",
        category="Hygiene",
        duration_minutes=15,
        priority="medium",
        frequency="daily",
        preferred_time_of_day="afternoon",
        scheduled_time="11:00",
    )
    original_bravo_time = task_bravo.scheduled_time
    original_alpha_time = task_alpha.scheduled_time
    # 2. Act: run the agent's loop
    agent.run(tasks=[task_bravo, task_alpha], available_minutes=90)
    # 3. Assert: alphabetically later task ("Bravo Groom") moved, earlier ("Alpha Groom") did not
    assert task_bravo.scheduled_time != original_bravo_time
    assert task_alpha.scheduled_time == original_alpha_time


def test_run_logs_every_step_type(agent):
    """run() must log at least one entry for each step type in the plan/act/check/resolve/run loop."""
    # 1. Arrange: reuse the priority-conflict scenario, which is guaranteed to trigger a resolve step
    high_task = Task(
        name="Vet Check",
        category="Health",
        duration_minutes=15,
        priority="high",
        frequency="daily",
        preferred_time_of_day="morning",
        scheduled_time="10:00",
    )
    low_task = Task(
        name="Play Time",
        category="Exercise",
        duration_minutes=15,
        priority="low",
        frequency="daily",
        preferred_time_of_day="morning",
        scheduled_time="10:00",
    )
    # 2. Act: run the agent's loop
    result = agent.run(tasks=[high_task, low_task], available_minutes=90)
    # 3. Assert: every expected step type appears at least once in the log
    steps_logged = {entry["step"] for entry in result["log"]}
    for expected_step in ("plan", "act", "check", "resolve", "run"):
        assert expected_step in steps_logged


def test_act_failure_returns_error_status(agent):
    """An exception inside Schedule.generate() must be caught and reported as an error status."""
    # 1. Act: call run() with a task list containing a non-Task element, so plan()'s len()
    #    succeeds but generate()'s call to t.is_due_today() raises inside act()
    result = agent.run(tasks=[None], available_minutes=90)
    # 2. Assert: error status and the final log entry records the error
    assert result["status"] == "error"
    assert result["log"][-1]["result"] == "error"


def test_run_stops_after_max_resolution_attempts(sample_schedule, monkeypatch):
    """run() must give up and return 'unresolved' once max_resolution_attempts is exhausted."""
    # 1. Arrange: two tasks in the schedule, and a detect_conflicts that never clears
    task_a = Task(
        name="Bath",
        category="Hygiene",
        duration_minutes=15,
        priority="medium",
        frequency="daily",
        preferred_time_of_day="morning",
        scheduled_time="10:00",
    )
    task_b = Task(
        name="Feeding",
        category="Nutrition",
        duration_minutes=15,
        priority="medium",
        frequency="daily",
        preferred_time_of_day="morning",
        scheduled_time="10:00",
    )
    agent = SchedulingAgent(sample_schedule, max_resolution_attempts=2)
    always_conflicting = ["Conflict: 'Bath' and 'Feeding' both scheduled at 10:00"]
    monkeypatch.setattr(sample_schedule, "detect_conflicts", lambda: always_conflicting)
    # 2. Act: run the agent, which can never converge because conflicts never clear
    result = agent.run(tasks=[task_a, task_b], available_minutes=90)
    # 3. Assert: unresolved status, and the number of check steps respects the attempt cap
    assert result["status"] == "unresolved"
    check_entries = [entry for entry in result["log"] if entry["step"] == "check"]
    assert len(check_entries) <= agent.max_resolution_attempts + 1


def test_run_resolves_conflict_with_no_actual_overlap(agent):
    """The lower-priority task must be shifted to start exactly when the higher-priority task ends."""
    # 1. Arrange: two tasks at the same scheduled_time, differing in priority and duration
    vet_visit = Task(
        name="Vet Visit",
        category="Health",
        duration_minutes=30,
        priority="high",
        frequency="daily",
        preferred_time_of_day="morning",
        scheduled_time="09:00",
    )
    brushing = Task(
        name="Brushing",
        category="Hygiene",
        duration_minutes=15,
        priority="low",
        frequency="daily",
        preferred_time_of_day="morning",
        scheduled_time="09:00",
    )
    # 2. Act: run the agent's loop
    result = agent.run(tasks=[vet_visit, brushing], available_minutes=90)
    # 3. Assert: resolved, Brushing shifted to exactly 09:30, Vet Visit untouched
    assert result["status"] == "resolved"
    assert brushing.scheduled_time == "09:30"
    assert vet_visit.scheduled_time == "09:00"
