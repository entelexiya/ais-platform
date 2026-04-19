"""
Schedule conflict checks and heatmap aggregation for teachers and rooms.
"""

from collections import defaultdict
from typing import Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import Room, ScheduleEntry, Teacher, TimeSlot

DAYS = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница"]
LESSONS = [1, 2, 3, 4, 5, 6]


class ConflictReport:
    def __init__(self, conflict_type: str, description: str, entry_id: Optional[int] = None):
        self.conflict_type = conflict_type
        self.description = description
        self.entry_id = entry_id

    def to_dict(self) -> Dict:
        return {
            "type": self.conflict_type,
            "description": self.description,
            "entry_id": self.entry_id,
        }


class ConflictChecker:
    def __init__(self, db: Session):
        self.db = db

    def check_teacher_availability(
        self,
        teacher_id: int,
        time_slot_id: int,
        exclude_entry_id: Optional[int] = None,
    ) -> bool:
        query = self.db.query(ScheduleEntry).filter(
            ScheduleEntry.teacher_id == teacher_id,
            ScheduleEntry.time_slot_id == time_slot_id,
        )
        if exclude_entry_id:
            query = query.filter(ScheduleEntry.id != exclude_entry_id)
        return query.first() is None

    def check_room_availability(
        self,
        room_id: int,
        time_slot_id: int,
        exclude_entry_id: Optional[int] = None,
    ) -> bool:
        query = self.db.query(ScheduleEntry).filter(
            ScheduleEntry.room_id == room_id,
            ScheduleEntry.time_slot_id == time_slot_id,
        )
        if exclude_entry_id:
            query = query.filter(ScheduleEntry.id != exclude_entry_id)
        return query.first() is None

    def check_teacher_daily_load(self, teacher_id: int, day: str) -> Dict:
        slot_ids = [
            slot.id
            for slot in self.db.query(TimeSlot).filter(TimeSlot.day == day).all()
        ]
        lessons_count = (
            self.db.query(ScheduleEntry)
            .filter(
                ScheduleEntry.teacher_id == teacher_id,
                ScheduleEntry.time_slot_id.in_(slot_ids),
            )
            .count()
        )
        max_daily = 6
        return {
            "lessons": lessons_count,
            "max_allowed": max_daily,
            "overload": lessons_count >= max_daily,
        }

    def find_conflicts_in_schedule(self) -> List[Dict]:
        conflicts: List[Dict] = []

        teacher_slot_counts = (
            self.db.query(
                ScheduleEntry.teacher_id,
                ScheduleEntry.time_slot_id,
                func.count(ScheduleEntry.id).label("cnt"),
            )
            .filter(ScheduleEntry.teacher_id.isnot(None))
            .group_by(ScheduleEntry.teacher_id, ScheduleEntry.time_slot_id)
            .having(func.count(ScheduleEntry.id) > 1)
            .all()
        )
        for row in teacher_slot_counts:
            teacher = self.db.query(Teacher).get(row.teacher_id)
            slot = self.db.query(TimeSlot).get(row.time_slot_id)
            name = teacher.short_name if teacher else f"id={row.teacher_id}"
            slot_desc = f"{slot.day} урок {slot.lesson_number}" if slot else f"slot={row.time_slot_id}"
            conflicts.append(
                ConflictReport(
                    "teacher_double_booking",
                    f"Учитель {name} назначен {row.cnt} раза в {slot_desc}",
                ).to_dict()
            )

        room_slot_counts = (
            self.db.query(
                ScheduleEntry.room_id,
                ScheduleEntry.time_slot_id,
                func.count(ScheduleEntry.id).label("cnt"),
            )
            .filter(ScheduleEntry.room_id.isnot(None))
            .group_by(ScheduleEntry.room_id, ScheduleEntry.time_slot_id)
            .having(func.count(ScheduleEntry.id) > 1)
            .all()
        )
        for row in room_slot_counts:
            room = self.db.query(Room).get(row.room_id)
            slot = self.db.query(TimeSlot).get(row.time_slot_id)
            room_desc = room.number if room else f"id={row.room_id}"
            slot_desc = f"{slot.day} урок {slot.lesson_number}" if slot else f"slot={row.time_slot_id}"
            conflicts.append(
                ConflictReport(
                    "room_double_booking",
                    f"Кабинет {room_desc} занят {row.cnt} раза в {slot_desc}",
                ).to_dict()
            )

        return conflicts

    def _build_slot_maps(self):
        slots = self.db.query(TimeSlot).order_by(TimeSlot.day, TimeSlot.lesson_number).all()
        by_id = {slot.id: slot for slot in slots}
        by_day_lesson = {(slot.day, slot.lesson_number): slot for slot in slots}
        return by_id, by_day_lesson

    def _group_entries_by_slot(self):
        teacher_slot_entries = defaultdict(list)
        room_slot_entries = defaultdict(list)
        entries = (
            self.db.query(ScheduleEntry)
            .outerjoin(TimeSlot, ScheduleEntry.time_slot_id == TimeSlot.id)
            .all()
        )
        for entry in entries:
            if entry.teacher_id:
                teacher_slot_entries[(entry.teacher_id, entry.time_slot_id)].append(entry)
            if entry.room_id:
                room_slot_entries[(entry.room_id, entry.time_slot_id)].append(entry)
        return teacher_slot_entries, room_slot_entries

    def _describe_entry(self, entry: ScheduleEntry) -> str:
        class_name = entry.class_.name if entry.class_ else "группа"
        room_name = entry.room.number if entry.room else "без кабинета"
        subject = entry.subject or "Без предмета"
        if entry.is_lenta and entry.lenta_group:
            return f"{subject}: {entry.lenta_group.group_name} ({room_name})"
        return f"{subject}: {class_name} ({room_name})"

    def _serialize_slot(
        self,
        day: str,
        lesson: int,
        entries: List[ScheduleEntry],
        denominator: int,
    ) -> Dict:
        count = len(entries)
        descriptions = [self._describe_entry(entry) for entry in entries]
        load = min(count / max(denominator, 1), 1.0)
        if count == 1:
            load = max(load, 0.55)
        overload = count > 1
        return {
            "day": day,
            "lesson": lesson,
            "count": count,
            "lessons": count,
            "load": round(load, 2),
            "overload": overload,
            "entries": descriptions,
        }

    def get_heatmap_data(self) -> Dict:
        _, slot_lookup = self._build_slot_maps()
        teacher_slot_entries, room_slot_entries = self._group_entries_by_slot()

        teachers = (
            self.db.query(Teacher)
            .filter(Teacher.role == "Учитель")
            .order_by(Teacher.short_name)
            .all()
        )
        rooms = self.db.query(Room).order_by(Room.number).all()

        teacher_rows = []
        overloaded_teacher_count = 0
        total_teacher_load = 0
        for teacher in teachers:
            row_slots = []
            daily_counts = defaultdict(int)
            for day in DAYS:
                for lesson in LESSONS:
                    slot = slot_lookup.get((day, lesson))
                    entries = teacher_slot_entries[(teacher.id, slot.id)] if slot else []
                    serialized = self._serialize_slot(day, lesson, entries, 1)
                    row_slots.append(serialized)
                    daily_counts[day] += serialized["count"]

            total_lessons = sum(slot["count"] for slot in row_slots)
            overloaded_days = [day for day, count in daily_counts.items() if count >= 6]
            if overloaded_days or any(slot["overload"] for slot in row_slots):
                overloaded_teacher_count += 1
            total_teacher_load += total_lessons
            teacher_rows.append(
                {
                    "id": teacher.id,
                    "name": teacher.short_name or teacher.full_name,
                    "subject": teacher.subject,
                    "slots": row_slots,
                    "total_lessons": total_lessons,
                    "max_hours": teacher.max_hours_per_week,
                    "overloaded_days": overloaded_days,
                }
            )

        room_rows = []
        conflicted_rooms = 0
        for room in rooms:
            row_slots = []
            for day in DAYS:
                for lesson in LESSONS:
                    slot = slot_lookup.get((day, lesson))
                    entries = room_slot_entries[(room.id, slot.id)] if slot else []
                    row_slots.append(self._serialize_slot(day, lesson, entries, 2))

            room_conflicts = sum(1 for slot in row_slots if slot["overload"])
            if room_conflicts:
                conflicted_rooms += 1
            room_rows.append(
                {
                    "id": room.id,
                    "name": room.number,
                    "label": room.name or room.number,
                    "room_type": room.room_type,
                    "slots": row_slots,
                    "occupied_slots": sum(1 for slot in row_slots if slot["count"] > 0),
                    "conflict_slots": room_conflicts,
                }
            )

        return {
            "days": DAYS,
            "lessons": LESSONS,
            "teachers": teacher_rows,
            "rooms": room_rows,
            "summary": {
                "teachers_total": len(teacher_rows),
                "teachers_overloaded": overloaded_teacher_count,
                "rooms_total": len(room_rows),
                "rooms_conflicted": conflicted_rooms,
                "teacher_load_total": total_teacher_load,
            },
        }
