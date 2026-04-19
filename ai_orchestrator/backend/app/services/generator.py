import json
import re
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.models import Class, LentaGroup, Parallel, Room, ScheduleEntry, Teacher, TimeSlot

DAYS = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница"]
LESSONS = [1, 2, 3, 4, 5, 6]
DEFAULT_CLASSES = ["1А", "2Б", "3А", "5А", "8А", "9А"]
MAX_DAILY_TEACHER_LOAD = 6
MAX_SAME_SUBJECT_PER_DAY = 2

HARD_SUBJECTS = {
    "Математика",
    "Геометрия",
    "Физика",
    "Химия",
    "Биология",
    "Английский язык",
    "Русский язык",
    "Казахский язык",
}
LIGHT_SUBJECTS = {
    "Музыка",
    "ИЗО",
    "Классный час",
    "Самостоятельная работа",
    "Физкультура",
}

DEFAULT_CURRICULUM = {
    1: {
        "Математика": 5,
        "Английский язык": 2,
        "Казахский язык": 3,
        "Русский язык": 3,
        "Познание мира": 2,
        "Физкультура": 3,
        "Музыка": 1,
        "ИЗО": 1,
        "Классный час": 1,
        "Самостоятельная работа": 9,
    },
    2: {
        "Математика": 5,
        "Английский язык": 2,
        "Казахский язык": 3,
        "Русский язык": 3,
        "Познание мира": 2,
        "Физкультура": 3,
        "Музыка": 1,
        "ИЗО": 1,
        "Информатика": 1,
        "Классный час": 1,
        "Самостоятельная работа": 8,
    },
    3: {
        "Математика": 5,
        "Английский язык": 3,
        "Казахский язык": 3,
        "Русский язык": 3,
        "Познание мира": 2,
        "Физкультура": 3,
        "Музыка": 1,
        "ИЗО": 1,
        "Информатика": 1,
        "Классный час": 1,
        "Самостоятельная работа": 7,
    },
    4: {
        "Математика": 5,
        "Английский язык": 3,
        "Казахский язык": 3,
        "Русский язык": 3,
        "Познание мира": 2,
        "Физкультура": 3,
        "Музыка": 1,
        "ИЗО": 1,
        "Информатика": 1,
        "Классный час": 1,
        "Самостоятельная работа": 7,
    },
    5: {
        "Математика": 5,
        "Английский язык": 3,
        "Казахский язык": 3,
        "Русский язык": 3,
        "История": 2,
        "Информатика": 2,
        "Биология": 2,
        "Физкультура": 3,
        "Музыка": 1,
        "ИЗО": 1,
        "Классный час": 1,
        "Самостоятельная работа": 4,
    },
    6: {
        "Математика": 5,
        "Английский язык": 3,
        "Казахский язык": 3,
        "Русский язык": 3,
        "История": 2,
        "Информатика": 2,
        "Биология": 2,
        "География": 2,
        "Физкультура": 3,
        "Классный час": 1,
        "Самостоятельная работа": 4,
    },
    7: {
        "Математика": 4,
        "Геометрия": 2,
        "Английский язык": 3,
        "Казахский язык": 3,
        "Русский язык": 2,
        "История": 2,
        "Информатика": 2,
        "Биология": 2,
        "География": 2,
        "Физика": 2,
        "Физкультура": 3,
        "Классный час": 1,
        "Самостоятельная работа": 2,
    },
    8: {
        "Математика": 4,
        "Геометрия": 2,
        "Английский язык": 3,
        "Казахский язык": 3,
        "Русский язык": 2,
        "История": 2,
        "Информатика": 2,
        "Биология": 2,
        "География": 2,
        "Физика": 2,
        "Химия": 2,
        "Физкультура": 3,
        "Классный час": 1,
    },
    9: {
        "Математика": 4,
        "Геометрия": 2,
        "Английский язык": 3,
        "Казахский язык": 3,
        "Русский язык": 2,
        "История": 2,
        "Информатика": 2,
        "Биология": 2,
        "География": 2,
        "Физика": 2,
        "Химия": 2,
        "Физкультура": 3,
        "Классный час": 1,
    },
    10: {
        "Математика": 5,
        "Геометрия": 2,
        "Английский язык": 3,
        "Казахский язык": 3,
        "Русский язык": 2,
        "История": 2,
        "Информатика": 2,
        "Физика": 3,
        "Химия": 2,
        "Биология": 2,
        "Физкультура": 2,
        "Самостоятельная работа": 2,
    },
    11: {
        "Математика": 5,
        "Геометрия": 2,
        "Английский язык": 3,
        "Казахский язык": 3,
        "Русский язык": 2,
        "История": 2,
        "Информатика": 2,
        "Физика": 3,
        "Химия": 2,
        "Биология": 2,
        "Физкультура": 2,
        "Самостоятельная работа": 2,
    },
}

DEFAULT_LENTA_SLOTS = {
    3: ("Вторник", 3),
    5: ("Четверг", 2),
}

ROOM_KEYWORDS = {
    "Английский язык": ("англий",),
    "Казахский язык": ("казах",),
    "Русский язык": ("русск",),
    "Информатика": ("информ",),
    "Физика": ("физик",),
    "Химия": ("хими",),
    "Биология": ("биолог",),
    "История": ("истори",),
    "География": ("географ",),
    "Музыка": ("музык",),
    "ИЗО": ("изо",),
    "Физкультура": ("спорт",),
    "Математика": ("математ",),
    "Геометрия": ("математ",),
}

FALLBACK_SUBJECT_TEACHERS = {
    "Геометрия": ["Математика", "Геометрия"],
    "Познание мира": ["История", "География", "Биология"],
    "ИЗО": ["ИЗО"],
    "Самостоятельная работа": [],
    "Классный час": [],
}


def _parse_class_name(class_name: str) -> Tuple[int, str]:
    digits = re.findall(r"\d+", class_name or "")
    letters = "".join(re.findall(r"[А-Яа-яA-Za-z]", class_name or "")).upper()
    return (int(digits[0]) if digits else 0, letters[-1] if letters else "")


def _load_constraints(raw_constraints: Optional[str]) -> Dict[str, bool]:
    if not raw_constraints:
        return {}
    try:
        parsed = json.loads(raw_constraints)
        return parsed if isinstance(parsed, dict) else {}
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}


def get_curriculum(class_name: str) -> Dict[str, int]:
    grade, _ = _parse_class_name(class_name)
    curriculum = dict(DEFAULT_CURRICULUM.get(grade, DEFAULT_CURRICULUM[9]))
    total = sum(curriculum.values())
    max_weekly_slots = len(DAYS) * len(LESSONS)
    if total < max_weekly_slots:
        curriculum["Самостоятельная работа"] = curriculum.get("Самостоятельная работа", 0) + (
            max_weekly_slots - total
        )
    return curriculum


def _resolve_requested_classes(classes: Optional[List[str]], db: Session) -> List[str]:
    if classes:
        return classes

    existing_classes = db.query(Class).order_by(Class.grade, Class.letter, Class.name).all()
    if existing_classes:
        return [class_.name for class_ in existing_classes]
    return DEFAULT_CLASSES


def _find_or_create_class(class_name: str, db: Session) -> Class:
    existing = db.query(Class).filter(Class.name == class_name).first()
    if existing:
        return existing

    grade, letter = _parse_class_name(class_name)
    created = Class(
        name=class_name,
        grade=grade or 1,
        letter=letter or "А",
        parallel_id=None,
        student_count=25,
    )
    db.add(created)
    db.flush()
    return created


def _teacher_subject_score(teacher: Teacher, subject: str) -> Optional[int]:
    if not subject or subject in {"Самостоятельная работа", "Классный час"}:
        return None

    subject_lower = subject.lower()
    teacher_subject = (teacher.subject or "").lower()
    teacher_qualification = (teacher.qualification or "").lower()
    fallbacks = [item.lower() for item in FALLBACK_SUBJECT_TEACHERS.get(subject, [])]

    if teacher_subject == subject_lower:
        return 0
    if subject_lower in teacher_subject or subject_lower in teacher_qualification:
        return 1
    if any(item == teacher_subject for item in fallbacks):
        return 2
    if any(item in teacher_qualification for item in fallbacks):
        return 3
    return None


def _build_slot_map(db: Session) -> Dict[Tuple[str, int], TimeSlot]:
    slots = db.query(TimeSlot).all()
    return {(slot.day, slot.lesson_number): slot for slot in slots}


def _build_existing_occupancy(
    db: Session,
) -> Tuple[Dict[int, set], Dict[int, set], Dict[int, set], Dict[int, int], Dict[int, Dict[str, int]]]:
    class_busy: Dict[int, set] = defaultdict(set)
    teacher_busy: Dict[int, set] = defaultdict(set)
    room_busy: Dict[int, set] = defaultdict(set)
    weekly_teacher_load: Dict[int, int] = defaultdict(int)
    daily_teacher_load: Dict[int, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    entries = (
        db.query(ScheduleEntry)
        .join(TimeSlot, ScheduleEntry.time_slot_id == TimeSlot.id)
        .all()
    )
    for entry in entries:
        if entry.class_id:
            class_busy[entry.class_id].add(entry.time_slot_id)
        if entry.teacher_id:
            teacher_busy[entry.teacher_id].add(entry.time_slot_id)
            weekly_teacher_load[entry.teacher_id] += 1
            if entry.time_slot:
                daily_teacher_load[entry.teacher_id][entry.time_slot.day] += 1
        if entry.room_id:
            room_busy[entry.room_id].add(entry.time_slot_id)

    return class_busy, teacher_busy, room_busy, weekly_teacher_load, daily_teacher_load


def _cleanup_previous_schedule(classes: List[Class], db: Session) -> None:
    class_ids = [class_.id for class_ in classes]
    parallel_ids = sorted({class_.parallel_id for class_ in classes if class_.parallel_id})

    db.query(ScheduleEntry).filter(
        ScheduleEntry.class_id.in_(class_ids)
    ).delete(synchronize_session=False)

    if parallel_ids:
        lenta_group_ids = [
            group.id
            for group in db.query(LentaGroup).filter(LentaGroup.parallel_id.in_(parallel_ids)).all()
        ]
        if lenta_group_ids:
            db.query(ScheduleEntry).filter(
                ScheduleEntry.lenta_group_id.in_(lenta_group_ids)
            ).delete(synchronize_session=False)

    db.flush()


def _teacher_respects_constraints(teacher: Teacher, slot: TimeSlot) -> bool:
    constraints = _load_constraints(teacher.constraints)
    if constraints.get("no_friday_afternoon") and slot.day == "Пятница" and slot.lesson_number >= 4:
        return False
    return True


def _select_room_for_subject(
    subject: str,
    slot: TimeSlot,
    class_: Class,
    rooms: List[Room],
    room_busy: Dict[int, set],
) -> Optional[Room]:
    keywords = ROOM_KEYWORDS.get(subject, ())
    suitable_rooms = [room for room in rooms if room.capacity >= (class_.student_count or 0)]
    if not suitable_rooms:
        suitable_rooms = rooms

    preferred_rooms = []
    for room in suitable_rooms:
        room_blob = f"{room.number} {room.name or ''}".lower()
        if slot.id in room_busy[room.id]:
            continue
        if keywords and any(keyword in room_blob for keyword in keywords):
            preferred_rooms.append(room)
    if preferred_rooms:
        return preferred_rooms[0]

    for room in suitable_rooms:
        if slot.id not in room_busy[room.id]:
            return room
    return None


def _choose_subject_for_slot(
    curriculum: Dict[str, int],
    day: str,
    lesson: int,
    daily_subject_counts: Dict[str, Dict[str, int]],
    last_subject: Optional[str],
) -> str:
    candidates = [(subject, hours) for subject, hours in curriculum.items() if hours > 0]
    if not candidates:
        return "Самостоятельная работа"

    scored = []
    for subject, hours_left in candidates:
        score = hours_left * 10
        taught_today = daily_subject_counts[day][subject]

        if subject == "Самостоятельная работа" and len(candidates) > 1:
            score -= 100
        if subject == last_subject:
            score -= 18
        if taught_today >= MAX_SAME_SUBJECT_PER_DAY:
            score -= 25
        else:
            score -= taught_today * 6

        if subject in HARD_SUBJECTS:
            if lesson <= 2:
                score += 8
            elif lesson >= 5:
                score -= 10

        if subject in LIGHT_SUBJECTS:
            if lesson >= 5:
                score += 8
            elif lesson == 1:
                score -= 8

        if subject == "Физкультура" and lesson <= 2:
            score -= 6
        if subject == "Классный час" and day == "Пятница" and lesson >= 5:
            score += 10

        scored.append((score, subject))

    scored.sort(key=lambda item: (-item[0], item[1]))
    return scored[0][1]


def _choose_teacher_and_room(
    subject: str,
    slot: TimeSlot,
    class_: Class,
    teachers: List[Teacher],
    rooms: List[Room],
    teacher_busy: Dict[int, set],
    room_busy: Dict[int, set],
    weekly_teacher_load: Dict[int, int],
    daily_teacher_load: Dict[int, Dict[str, int]],
) -> Tuple[str, str, Optional[int], Optional[int], Optional[str]]:
    if subject in {"Самостоятельная работа", "Классный час"}:
        return ("Самостоятельная работа", "Кабинет класса", None, None, "self_study_slot")

    ranked_candidates = []
    for teacher in teachers:
        subject_score = _teacher_subject_score(teacher, subject)
        if subject_score is None:
            continue
        ranked_candidates.append(
            (
                subject_score,
                daily_teacher_load[teacher.id][slot.day],
                weekly_teacher_load[teacher.id],
                teacher.max_hours_per_week or 999,
                teacher,
            )
        )
    ranked_candidates.sort(key=lambda item: item[:4])

    for _, _, _, max_hours, teacher in ranked_candidates:
        if slot.id in teacher_busy[teacher.id]:
            continue
        if weekly_teacher_load[teacher.id] >= max_hours:
            continue
        if daily_teacher_load[teacher.id][slot.day] >= MAX_DAILY_TEACHER_LOAD:
            continue
        if not _teacher_respects_constraints(teacher, slot):
            continue

        room = _select_room_for_subject(subject, slot, class_, rooms, room_busy)
        teacher_busy[teacher.id].add(slot.id)
        weekly_teacher_load[teacher.id] += 1
        daily_teacher_load[teacher.id][slot.day] += 1

        room_id = room.id if room else None
        if room_id:
            room_busy[room_id].add(slot.id)

        return (
            teacher.short_name or teacher.full_name,
            room.number if room else "Кабинет класса",
            teacher.id,
            room_id,
            None,
        )

    return ("Самостоятельная работа", "Кабинет класса", None, None, f"no_teacher_for_{subject}")


def _add_lenta_entries(
    classes: List[Class],
    db: Session,
    slot_map: Dict[Tuple[str, int], TimeSlot],
    class_busy: Dict[int, set],
    teacher_busy: Dict[int, set],
    room_busy: Dict[int, set],
    weekly_teacher_load: Dict[int, int],
    daily_teacher_load: Dict[int, Dict[str, int]],
) -> Tuple[List[Dict], List[str]]:
    generated = []
    warnings: List[str] = []
    by_parallel: Dict[int, List[Class]] = defaultdict(list)
    for class_ in classes:
        if class_.parallel_id:
            by_parallel[class_.parallel_id].append(class_)

    for parallel_id, parallel_classes in by_parallel.items():
        parallel = db.query(Parallel).get(parallel_id)
        if not parallel or not parallel.has_lenta:
            continue

        lenta_groups = (
            db.query(LentaGroup)
            .filter(LentaGroup.parallel_id == parallel_id)
            .order_by(LentaGroup.level)
            .all()
        )
        if not lenta_groups:
            warnings.append(f"Параллель {parallel.grade}: нет настроенных групп ленты")
            continue

        target_day, target_lesson = DEFAULT_LENTA_SLOTS.get(parallel.grade, ("Вторник", 3))
        slot = slot_map.get((target_day, target_lesson))
        if not slot:
            warnings.append(f"Параллель {parallel.grade}: не найден слот для ленты")
            continue

        conflict = False
        for class_ in parallel_classes:
            if slot.id in class_busy[class_.id]:
                conflict = True
                break
        for group in lenta_groups:
            if not group.teacher_id or not group.room_id:
                conflict = True
                break
            if slot.id in teacher_busy[group.teacher_id] or slot.id in room_busy[group.room_id]:
                conflict = True
                break
        if conflict:
            warnings.append(f"Параллель {parallel.grade}: лента пропущена из-за конфликта")
            continue

        teacher_lines = []
        room_lines = []
        for group in lenta_groups:
            teacher = db.query(Teacher).get(group.teacher_id)
            room = db.query(Room).get(group.room_id)
            teacher_name = teacher.short_name if teacher else "Не назначен"
            room_name = room.number if room else "—"
            teacher_lines.append(f"{group.group_name}: {teacher_name}")
            room_lines.append(f"{group.group_name}: {room_name}")

            teacher_busy[group.teacher_id].add(slot.id)
            room_busy[group.room_id].add(slot.id)
            weekly_teacher_load[group.teacher_id] += 1
            daily_teacher_load[group.teacher_id][slot.day] += 1

            db.add(
                ScheduleEntry(
                    class_id=None,
                    teacher_id=group.teacher_id,
                    room_id=group.room_id,
                    time_slot_id=slot.id,
                    subject=parallel.lenta_subject or "Английский язык",
                    is_lenta=True,
                    lenta_group_id=group.id,
                )
            )

        for class_ in parallel_classes:
            class_busy[class_.id].add(slot.id)
            db.add(
                ScheduleEntry(
                    class_id=class_.id,
                    teacher_id=None,
                    room_id=None,
                    time_slot_id=slot.id,
                    subject=parallel.lenta_subject or "Английский язык",
                    is_lenta=True,
                    lenta_group_id=None,
                )
            )
            generated.append(
                {
                    "День": slot.day,
                    "Класс": class_.name,
                    "Урок": slot.lesson_number,
                    "Учитель": "\n".join(teacher_lines),
                    "Предмет": f"Лента: {parallel.lenta_subject or 'Английский язык'}",
                    "Кабинет": "\n".join(room_lines),
                    "isSplit": True,
                }
            )

    db.flush()
    return generated, warnings


def _collect_generation_summary(schedule: List[Dict]) -> Dict:
    self_study_slots = sum(1 for item in schedule if item["Предмет"] == "Самостоятельная работа")
    lenta_slots = sum(1 for item in schedule if str(item["Предмет"]).startswith("Лента:"))
    unique_classes = len({item["Класс"] for item in schedule})
    unique_days = len({(item["Класс"], item["День"]) for item in schedule})
    return {
        "total_entries": len(schedule),
        "classes": unique_classes,
        "class_days": unique_days,
        "self_study_slots": self_study_slots,
        "lenta_slots": lenta_slots,
    }


def generate_weekly_schedule(
    classes: Optional[List[str]] = None,
    db: Optional[Session] = None,
    include_summary: bool = False,
) -> List[Dict] | Dict[str, Dict]:
    own_session = db is None
    db = db or SessionLocal()

    try:
        requested_classes = _resolve_requested_classes(classes, db)
        resolved_classes = [_find_or_create_class(class_name, db) for class_name in requested_classes]
        db.flush()

        _cleanup_previous_schedule(resolved_classes, db)

        slot_map = _build_slot_map(db)
        if not slot_map:
            return []

        (
            class_busy,
            teacher_busy,
            room_busy,
            weekly_teacher_load,
            daily_teacher_load,
        ) = _build_existing_occupancy(db)

        teachers = (
            db.query(Teacher)
            .filter(Teacher.role == "Учитель")
            .order_by(Teacher.short_name)
            .all()
        )
        rooms = db.query(Room).order_by(Room.capacity.desc(), Room.number).all()

        generated_schedule: List[Dict] = []
        generated_schedule, _ = _add_lenta_entries(
            resolved_classes,
            db,
            slot_map,
            class_busy,
            teacher_busy,
            room_busy,
            weekly_teacher_load,
            daily_teacher_load,
        )

        class_daily_subjects: Dict[int, Dict[str, Dict[str, int]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(int))
        )
        class_last_subject: Dict[int, Optional[str]] = defaultdict(lambda: None)
        class_warnings: Dict[str, List[str]] = defaultdict(list)

        for item in generated_schedule:
            class_ = next((candidate for candidate in resolved_classes if candidate.name == item["Класс"]), None)
            if not class_:
                continue
            class_daily_subjects[class_.id][item["День"]][item["Предмет"]] += 1
            class_last_subject[class_.id] = item["Предмет"]

        for class_ in sorted(resolved_classes, key=lambda item: (item.grade, item.letter, item.name)):
            curriculum = get_curriculum(class_.name)

            for day in DAYS:
                class_last_subject[class_.id] = None
                for lesson in LESSONS:
                    slot = slot_map.get((day, lesson))
                    if not slot or slot.id in class_busy[class_.id]:
                        continue

                    subject = _choose_subject_for_slot(
                        curriculum,
                        day,
                        lesson,
                        class_daily_subjects[class_.id],
                        class_last_subject[class_.id],
                    )
                    teacher_name, room_name, teacher_id, room_id, warning = _choose_teacher_and_room(
                        subject,
                        slot,
                        class_,
                        teachers,
                        rooms,
                        teacher_busy,
                        room_busy,
                        weekly_teacher_load,
                        daily_teacher_load,
                    )

                    final_subject = subject
                    if teacher_id is None and subject not in {"Самостоятельная работа", "Классный час"}:
                        final_subject = "Самостоятельная работа"
                        class_warnings[class_.name].append(
                            warning or f"no_teacher_for_{subject}"
                        )

                    curriculum[subject] = max(curriculum.get(subject, 1) - 1, 0)
                    class_busy[class_.id].add(slot.id)
                    class_daily_subjects[class_.id][day][final_subject] += 1
                    class_last_subject[class_.id] = final_subject

                    db.add(
                        ScheduleEntry(
                            class_id=class_.id,
                            teacher_id=teacher_id,
                            room_id=room_id,
                            time_slot_id=slot.id,
                            subject=final_subject,
                            is_lenta=False,
                        )
                    )
                    generated_schedule.append(
                        {
                            "День": day,
                            "Класс": class_.name,
                            "Урок": lesson,
                            "Учитель": teacher_name,
                            "Предмет": final_subject,
                            "Кабинет": room_name,
                            "isSplit": False,
                        }
                    )

            for subject, hours_left in curriculum.items():
                if hours_left > 0 and subject != "Самостоятельная работа":
                    class_warnings[class_.name].append(f"unplaced_{subject}_{hours_left}")

        db.commit()

        def schedule_sort_key(item: Dict) -> Tuple[int, str, int, int]:
            grade, letter = _parse_class_name(item["Класс"])
            return (
                grade,
                letter,
                DAYS.index(item["День"]) if item["День"] in DAYS else 99,
                item["Урок"],
            )

        generated_schedule.sort(key=schedule_sort_key)
        summary = _collect_generation_summary(generated_schedule)
        if class_warnings:
            summary["warnings"] = {
                class_name: warnings for class_name, warnings in class_warnings.items() if warnings
            }
        if include_summary:
            return {
                "schedule": generated_schedule,
                "summary": summary,
            }
        return generated_schedule
    finally:
        if own_session:
            db.close()
