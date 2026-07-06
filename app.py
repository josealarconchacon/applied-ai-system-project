import re
import streamlit as st
from datetime import date, timedelta
from pawpal_system import Owner, Pet, Task, Schedule

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Quick Demo Inputs (UI only)")

row1_col1, row1_col2 = st.columns([1, 1])
with row1_col1:
    owner_name = st.text_input("Owner name", value="Jordan")
with row1_col2:
    available_minutes_per_day = st.number_input(
        "Available minutes per day", min_value=15, max_value=600, value=90
    )

row2_col1, row2_col2 = st.columns([1, 1])
with row2_col1:
    owner_preferred_time = st.selectbox("Preferred time of day", ["morning", "afternoon", "evening"], index=0, key="owner_preferred_time")
with row2_col2:
    pet_name = st.text_input("Pet name", value="Mochi")

if "owner" not in st.session_state:
    st.session_state["owner"] = Owner(
        name=owner_name,
        available_minutes_per_day=available_minutes_per_day,
        preferences={"preferred_time_of_day": owner_preferred_time},
    )
else:
    st.session_state["owner"].name = owner_name
    st.session_state["owner"].set_availability(available_minutes_per_day)
    st.session_state["owner"].preferences = {"preferred_time_of_day": owner_preferred_time}

row3_col1, row3_col2, row3_col3 = st.columns([1, 1, 1])
with row3_col1:
    species = st.selectbox("Species", ["dog", "cat", "other"])
with row3_col2:
    breed = st.text_input("Breed", value="Unknown")
with row3_col3:
    age = st.number_input("Age", min_value=0, max_value=30, value=0)

special_needs_input = st.text_area("Special needs (one per line, optional)", value="")

if "pets" not in st.session_state:
    st.session_state["pets"] = []

row5_col1, row5_col2 = st.columns([1, 3])
with row5_col1:
    add_pet_clicked = st.button("Add Pet")

if add_pet_clicked:
    st.session_state.pop("_pending_dup", None)
    if age == 0:
        st.error("Please enter a valid age for your pet. Age must be at least 1.")
    else:
        special_needs = [line.strip() for line in special_needs_input.splitlines() if line.strip()]
        exact_duplicate = any(p.name == pet_name and p.age == age for p in st.session_state["pets"])
        if exact_duplicate:
            st.session_state["_pending_dup"] = dict(
                name=pet_name, species=species, breed=breed, age=age, special_needs=special_needs
            )
        else:
            pet = Pet(
                name=pet_name,
                species=species,
                breed=breed,
                age=age,
                special_needs=special_needs,
            )
            st.session_state["pets"].append(pet)
            if pet.has_special_needs():
                st.warning(f"⚠️ {pet.name} has special care needs: " + ", ".join(pet.special_needs))
            else:
                st.success(f"Pet saved: {pet_name} ({species})")
            st.write("**Pet Profile:**")
            st.json(pet.get_care_profile())

if "_pending_dup" in st.session_state:
    d = st.session_state["_pending_dup"]
    st.warning(f"A pet named '{d['name']}' with age {d['age']} already exists.")
    if st.button(f"Yes, add {d['name']} anyway", key="confirm_duplicate_pet"):
        pet = Pet(
            name=d["name"],
            species=d["species"],
            breed=d["breed"],
            age=d["age"],
            special_needs=d["special_needs"],
        )
        st.session_state["pets"].append(pet)
        del st.session_state["_pending_dup"]
        if pet.has_special_needs():
            st.warning(f"⚠️ {pet.name} has special care needs: " + ", ".join(pet.special_needs))
        else:
            st.success(f"Pet saved: {pet.name} ({pet.species})")
        st.write("**Pet Profile:**")
        st.json(pet.get_care_profile())

if st.session_state["pets"]:
    active_pet_name = st.selectbox("Active pet", options=[p.name for p in st.session_state["pets"]])
else:
    st.info("Add a pet first.")
    active_pet_name = None

st.markdown("### Tasks")
st.caption("Add a few tasks. In your final version, these should feed into your scheduler.")

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
with col4:
    scheduled_time = st.text_input("Scheduled time", value="", placeholder="e.g. 08:00")
with col5:
    task_preferred_time = st.selectbox("Preferred time of day", ["morning", "afternoon", "evening"], index=0, key="task_preferred_time")

if st.button("Add task"):
    if active_pet_name is None:
        st.error("Add a pet and select it as the active pet before adding tasks.")
    elif not task_title or not task_title.strip():
        st.error("Task title cannot be empty.")
    elif not scheduled_time:
        st.error("Scheduled time cannot be empty. Please enter a time in HH:MM format.")
    elif not re.fullmatch(r"\d{2}:\d{2}", scheduled_time):
        st.error("Scheduled time must be in HH:MM format, e.g. 08:00")
    else:
        st.session_state["owner"].add_task(
            Task(
                name=task_title,
                duration_minutes=int(duration),
                priority=priority,
                scheduled_time=scheduled_time,
                category="General",
                frequency="daily",
                preferred_time_of_day=task_preferred_time,
                pet_name=active_pet_name,
            )
        )

if st.session_state["owner"].get_tasks():
    st.write("Current tasks:")
    st.markdown("""
    <style>
    div[data-testid="stButton"] button {
        border: 1px solid #555;
        background-color: transparent;
        border-radius: 6px;
        padding: 4px 12px;
        font-size: 14px;
        white-space: nowrap;
        width: 100%;
    }
    div[data-testid="stButton"] button:hover {
        border-color: #888;
        background-color: #2a2a2a;
    }
    div[data-testid="stVerticalBlock"] div[data-testid="stText"] p,
    div[data-testid="stMarkdownContainer"] p {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    div[data-testid="stHorizontalBlock"] {
        border-top: 1px solid #555;
    }
    div[data-testid="stHorizontalBlock"] div[data-testid="column"] {
        border-right: 1px solid #555;
        padding: 8px 10px;
    }
    # div[data-testid="stHorizontalBlock"] div[data-testid="column"]:first-child {
    #     border-left: 1px solid #555;
    # }
    </style>
    """, unsafe_allow_html=True)
    tasks_snapshot = list(st.session_state["owner"].get_tasks())
    task_to_complete = None
    task_to_remove = None
    for task in tasks_snapshot:
        cols = st.columns([2, 1.2, 1.2, 1.2, 1.2, 1.5, 1.2, 1.2])
        cols[0].write(task.name)
        cols[1].write(task.scheduled_time)
        cols[2].write(f"{task.duration_minutes} min")
        cols[3].write(task.priority)
        cols[4].write("✓ Done" if task.completed else "Pending")
        today = date.today()
        if task.schedule_date == today:
            date_label = "Today"
        elif task.schedule_date == today + timedelta(days=1):
            date_label = "Tomorrow"
        else:
            date_label = task.schedule_date.strftime("%b %d")
        cols[5].write(date_label)
        if cols[6].button("✔", key=f"complete_{id(task)}", use_container_width=True):
            task_to_complete = task
        if cols[7].button("✕", key=f"remove_{id(task)}", use_container_width=True):
            task_to_remove = task
    if task_to_complete is not None:
        was_already_completed = task_to_complete.completed
        next_task = task_to_complete.mark_complete()
        if was_already_completed:
            st.info(f"'{task_to_complete.name}' was already completed.")
        elif next_task is not None:
            st.session_state["owner"].add_task(next_task)
            st.success(f"'{task_to_complete.name}' marked complete. Next occurrence scheduled for {next_task.schedule_date}.")
        else:
            st.success(f"'{task_to_complete.name}' marked complete.")
        st.rerun()
    if task_to_remove is not None:
        st.session_state["owner"].remove_task(task_to_remove)
        st.success(f"'{task_to_remove.name}' removed.")
        st.rerun()
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("This button should call your scheduling logic once you implement it.")

if st.button("Generate schedule"):
    if not (st.session_state["pets"] and active_pet_name and st.session_state["owner"].get_tasks()):
        st.warning("Add an owner, a pet, and at least one task before generating a schedule.")
    else:
        active_pet = next(p for p in st.session_state["pets"] if p.name == active_pet_name)
        schedule = Schedule(
            schedule_date=date.today(),
            owner=st.session_state["owner"],
            pet=active_pet,
        )
        pet_tasks = [t for t in st.session_state["owner"].get_tasks() if t.pet_name == active_pet_name]
        schedule.generate(
            tasks=pet_tasks,
            available_minutes=st.session_state["owner"].available_minutes_per_day,
        )
        st.session_state["schedule"] = schedule

if st.session_state.get("schedule"):
    schedule = st.session_state["schedule"]
    st.success(schedule.get_summary())
    if schedule.skipped_tasks:
        st.warning(schedule.get_skipped_summary())

    st.subheader("📅 Sorted by Time")
    sorted_tasks = schedule.sort_by_time()
    st.table([{"name": task.name, "scheduled_time": task.scheduled_time} for _, task in sorted_tasks])

    st.subheader("⚠️ Conflict Warnings")
    warnings = schedule.detect_conflicts()
    if warnings:
        for warning in warnings:
            st.error(warning)
    else:
        st.success("No scheduling conflicts detected.")

    st.subheader("🔍 Filter by Status")
    status_filter = st.radio("Filter by status", ["All", "Completed", "Incomplete"], index=0)
    if status_filter == "All":
        filtered = schedule.filter_tasks(completed=None)
    elif status_filter == "Completed":
        filtered = schedule.filter_tasks(completed=True)
    else:
        filtered = schedule.filter_tasks(completed=False)
    st.table([{"name": t.name, "scheduled_time": t.scheduled_time} for t in filtered])