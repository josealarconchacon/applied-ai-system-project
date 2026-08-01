from datetime import date

from pawpal_system import Owner, Pet, Schedule, Task
from agent import SchedulingAgent


def _fresh_agent():
    """Builds a fresh Owner, Pet, Schedule, and SchedulingAgent for a scenario."""
    owner = Owner(
        name="Alex",
        available_minutes_per_day=90,
        preferences={"preferred_time_of_day": "morning"},
    )
    pet = Pet(name="Luna", species="Dog", breed="Golden Retriever", age=3, special_needs=[])
    schedule = Schedule(schedule_date=date.today(), owner=owner, pet=pet)
    agent = SchedulingAgent(schedule)
    return agent


def _scenario_1():
    agent = _fresh_agent()
    task_a = Task(
        name="Feed Luna",
        category="feeding",
        duration_minutes=15,
        priority="medium",
        frequency="daily",
        preferred_time_of_day="morning",
        scheduled_time="08:00",
        pet_name="Luna",
    )
    task_b = Task(
        name="Evening Walk",
        category="exercise",
        duration_minutes=15,
        priority="medium",
        frequency="daily",
        preferred_time_of_day="morning",
        scheduled_time="18:00",
        pet_name="Luna",
    )
    result = agent.run(tasks=[task_a, task_b], available_minutes=90)

    had_conflict = any(entry["result"] == "conflict_found" for entry in result["log"])
    if result["status"] == "resolved" and not had_conflict:
        print("Scenario 1 (No Conflict): PASS")
    else:
        reason = f"status={result['status']}, conflict_found={had_conflict}"
        print(f"Scenario 1 (No Conflict): FAIL — {reason}")
        return False
    return True


def _scenario_2():
    agent = _fresh_agent()
    high_task = Task(
        name="Vet Medication",
        category="health",
        duration_minutes=15,
        priority="high",
        frequency="daily",
        preferred_time_of_day="morning",
        scheduled_time="10:00",
        pet_name="Luna",
    )
    low_task = Task(
        name="Brushing",
        category="grooming",
        duration_minutes=15,
        priority="low",
        frequency="daily",
        preferred_time_of_day="morning",
        scheduled_time="10:00",
        pet_name="Luna",
    )
    agent.run(tasks=[high_task, low_task], available_minutes=90)

    if low_task.scheduled_time != "10:00" and high_task.scheduled_time == "10:00":
        print("Scenario 2 (Priority Tiebreak): PASS")
    else:
        reason = f"high={high_task.scheduled_time}, low={low_task.scheduled_time}"
        print(f"Scenario 2 (Priority Tiebreak): FAIL — {reason}")
        return False
    return True


def _scenario_3():
    agent = _fresh_agent()
    zebra_task = Task(
        name="Zebra Task",
        category="misc",
        duration_minutes=15,
        priority="medium",
        frequency="daily",
        preferred_time_of_day="evening",
        scheduled_time="11:00",
        pet_name="Luna",
    )
    apple_task = Task(
        name="Apple Task",
        category="misc",
        duration_minutes=15,
        priority="medium",
        frequency="daily",
        preferred_time_of_day="evening",
        scheduled_time="11:00",
        pet_name="Luna",
    )
    agent.run(tasks=[zebra_task, apple_task], available_minutes=90)

    if zebra_task.scheduled_time != "11:00" and apple_task.scheduled_time == "11:00":
        print("Scenario 3 (Alphabetical Tiebreak): PASS")
    else:
        reason = f"apple={apple_task.scheduled_time}, zebra={zebra_task.scheduled_time}"
        print(f"Scenario 3 (Alphabetical Tiebreak): FAIL — {reason}")
        return False
    return True


def _scenario_4():
    agent = _fresh_agent()
    result = agent.run(tasks=[None], available_minutes=90)

    if result["status"] == "error":
        print("Scenario 4 (Invalid Input Handling): PASS")
    else:
        print(f"Scenario 4 (Invalid Input Handling): FAIL — status={result['status']}")
        return False
    return True


def _scenario_5():
    agent = _fresh_agent()
    vet_visit = Task(
        name="Vet Visit",
        category="health",
        duration_minutes=30,
        priority="high",
        frequency="daily",
        preferred_time_of_day="morning",
        scheduled_time="09:00",
        pet_name="Luna",
    )
    brushing = Task(
        name="Brushing",
        category="grooming",
        duration_minutes=15,
        priority="low",
        frequency="daily",
        preferred_time_of_day="morning",
        scheduled_time="09:00",
        pet_name="Luna",
    )
    agent.run(tasks=[vet_visit, brushing], available_minutes=90)

    if brushing.scheduled_time == "09:30" and vet_visit.scheduled_time == "09:00":
        print("Scenario 5 (Duration-Aware Shift): PASS")
    else:
        reason = f"vet_visit={vet_visit.scheduled_time}, brushing={brushing.scheduled_time}"
        print(f"Scenario 5 (Duration-Aware Shift): FAIL — {reason}")
        return False
    return True


def run_evaluation():
    scenarios = [_scenario_1, _scenario_2, _scenario_3, _scenario_4, _scenario_5]
    passed = sum(1 for scenario in scenarios if scenario())

    print()
    print(f"Summary: {passed}/5 scenarios passed")


if __name__ == "__main__":
    run_evaluation()
