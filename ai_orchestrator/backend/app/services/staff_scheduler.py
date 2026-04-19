"""
Расписание для всех категорий сотрудников:
учителя, завхоз, слесарь, директор, завуч.
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.db.models import (
    Teacher, ScheduleEntry, StaffScheduleEntry, TimeSlot,
    TaskReminder, StaffEntryType
)

DAYS = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница"]

SLOT_TYPE_ICONS = {
    "lesson": "📚",
    "duty": "🚶",
    "meeting": "👥",
    "task": "🔧",
    "free": "⬜",
}


def get_staff_weekly_schedule(staff_id: int, db: Session) -> Dict:
    """
    Возвращает недельное расписание сотрудника.
    Для учителей: уроки из ScheduleEntry.
    Для остального персонала: StaffScheduleEntry + динамические задачи.
    """
    staff = db.query(Teacher).get(staff_id)
    if not staff:
        return {"error": "Сотрудник не найден"}

    week_slots = []
    is_teacher = staff.role == "Учитель"

    for day in DAYS:
        day_slots = []
        time_slots = (
            db.query(TimeSlot)
            .filter(TimeSlot.day == day)
            .order_by(TimeSlot.lesson_number)
            .all()
        )

        for ts in time_slots:
            entry_data = {
                "day": day,
                "lesson": ts.lesson_number,
                "start_time": ts.start_time,
                "end_time": ts.end_time,
                "type": "free",
                "icon": "⬜",
                "description": "Окно",
                "subject": None,
                "class_name": None,
                "room": None,
            }

            if is_teacher:
                # Ищем урок в основном расписании
                sched_entry = (
                    db.query(ScheduleEntry)
                    .filter(
                        ScheduleEntry.teacher_id == staff_id,
                        ScheduleEntry.time_slot_id == ts.id,
                    )
                    .first()
                )
                if sched_entry:
                    class_name = sched_entry.class_.name if sched_entry.class_ else "—"
                    room_num = sched_entry.room.number if sched_entry.room else "—"
                    lenta_label = ""
                    if sched_entry.is_lenta and sched_entry.lenta_group:
                        lenta_label = f" [Лента: {sched_entry.lenta_group.group_name}]"
                    entry_data.update({
                        "type": "lesson",
                        "icon": "📚",
                        "description": f"{sched_entry.subject}{lenta_label}",
                        "subject": sched_entry.subject,
                        "class_name": class_name,
                        "room": room_num,
                        "is_substitution": sched_entry.is_substitution,
                    })
            else:
                # Для не-учителей: StaffScheduleEntry
                staff_entry = (
                    db.query(StaffScheduleEntry)
                    .filter(
                        StaffScheduleEntry.staff_id == staff_id,
                        StaffScheduleEntry.time_slot_id == ts.id,
                    )
                    .first()
                )
                if staff_entry:
                    entry_data.update({
                        "type": staff_entry.entry_type,
                        "icon": SLOT_TYPE_ICONS.get(staff_entry.entry_type, "⬜"),
                        "description": staff_entry.description or staff_entry.entry_type,
                    })

            day_slots.append(entry_data)

        week_slots.append({"day": day, "slots": day_slots})

    # Считаем статистику
    total_lessons = sum(
        1 for day_data in week_slots
        for s in day_data["slots"]
        if s["type"] == "lesson"
    )
    total_tasks = sum(
        1 for day_data in week_slots
        for s in day_data["slots"]
        if s["type"] == "task"
    )

    return {
        "staff_id": staff_id,
        "name": staff.full_name,
        "short_name": staff.short_name,
        "role": staff.role,
        "subject": staff.subject,
        "max_hours_per_week": staff.max_hours_per_week,
        "total_lessons_this_week": total_lessons,
        "total_tasks_this_week": total_tasks,
        "week": week_slots,
    }


def inject_task_into_schedule(staff_id: int, task_reminder_id: int, db: Session) -> Optional[Dict]:
    """
    Находит ближайший свободный слот у сотрудника и вставляет задачу.
    Возвращает данные о слоте или None если все слоты заняты.
    """
    staff = db.query(Teacher).get(staff_id)
    task = db.query(TaskReminder).get(task_reminder_id)
    if not staff or not task:
        return None

    # Ищем свободный слот (не урок и не задача)
    for day in DAYS:
        time_slots = (
            db.query(TimeSlot)
            .filter(TimeSlot.day == day)
            .order_by(TimeSlot.lesson_number)
            .all()
        )
        for ts in time_slots:
            # Пропускаем первый урок — утренний обход для завхоза
            if ts.lesson_number == 1 and staff.role in ["Завхоз", "Техработник"]:
                continue

            existing = (
                db.query(StaffScheduleEntry)
                .filter(
                    StaffScheduleEntry.staff_id == staff_id,
                    StaffScheduleEntry.time_slot_id == ts.id,
                )
                .first()
            )
            if not existing:
                # Свободный слот найден — вставляем задачу
                new_entry = StaffScheduleEntry(
                    staff_id=staff_id,
                    time_slot_id=ts.id,
                    entry_type=StaffEntryType.task,
                    description=task.title,
                    task_reminder_id=task_reminder_id,
                )
                db.add(new_entry)
                db.commit()
                return {
                    "day": ts.day,
                    "lesson": ts.lesson_number,
                    "start_time": ts.start_time,
                    "end_time": ts.end_time,
                    "task": task.title,
                    "staff": staff.short_name,
                }

    return None


def get_all_staff_list(db: Session) -> List[Dict]:
    """Список всех сотрудников для выпадающего списка в UI."""
    staff = db.query(Teacher).order_by(Teacher.role, Teacher.full_name).all()
    return [
        {
            "id": s.id,
            "full_name": s.full_name,
            "short_name": s.short_name,
            "role": s.role,
            "subject": s.subject,
        }
        for s in staff
    ]
