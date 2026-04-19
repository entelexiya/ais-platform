"""
Seed script: заполняет БД реалистичными данными для демо.
Запускать через: python -m app.db.seed_data
"""
import json
import os
from sqlalchemy.orm import Session
from .database import SessionLocal, engine, Base
from .models import (
    Teacher, Room, Parallel, Class, LentaGroup,
    TimeSlot, ScheduleEntry, StaffScheduleEntry,
    RoomType, DayEnum, StaffEntryType
)

DAYS = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница"]

LESSON_TIMES = {
    1: ("08:00", "08:45"),
    2: ("08:55", "09:40"),
    3: ("09:50", "10:35"),
    4: ("10:55", "11:40"),
    5: ("11:50", "12:35"),
    6: ("12:45", "13:30"),
}

EMPLOYEES = [
    {"id": 1, "full_name": "Гульнара Дюсенова", "short_name": "Гульнара", "role": "Завхоз", "subject": None, "qualification": "Административный персонал", "max_hours": 8},
    {"id": 2, "full_name": "Мадина Ахметова", "short_name": "Мадина", "role": "Секретарь", "subject": None, "qualification": "Административный персонал", "max_hours": 8},
    {"id": 3, "full_name": "Болат Сейткали", "short_name": "Болат", "role": "Учитель", "subject": "Математика", "qualification": "Математика", "max_hours": 20},
    {"id": 4, "full_name": "Петрова Ольга", "short_name": "Петрова О.", "role": "Учитель", "subject": "Математика", "qualification": "Математика", "max_hours": 20},
    {"id": 5, "full_name": "Байжанов Данияр", "short_name": "Байжанов Д.", "role": "Учитель", "subject": "Информатика", "qualification": "Информатика", "max_hours": 18},
    {"id": 6, "full_name": "Нуров Азамат", "short_name": "Нуров А.", "role": "Учитель", "subject": "Физика", "qualification": "Физика", "max_hours": 18},
    {"id": 7, "full_name": "Жакенова Камила", "short_name": "Жакенова К.", "role": "Учитель", "subject": "Химия", "qualification": "Химия", "max_hours": 18},
    {"id": 8, "full_name": "Ли Наталья", "short_name": "Ли Н.", "role": "Учитель", "subject": "Биология", "qualification": "Биология", "max_hours": 18},
    {"id": 9, "full_name": "Серик Ержанов", "short_name": "Серик", "role": "Техработник", "subject": None, "qualification": "Сантехник/Электрик", "max_hours": 8},
    {"id": 10, "full_name": "Романов Дмитрий", "short_name": "Романов Д.", "role": "Учитель", "subject": "Физкультура", "qualification": "Физкультура", "max_hours": 22},
    {"id": 11, "full_name": "Касенова Амина", "short_name": "Касенова А.", "role": "Учитель", "subject": "Английский язык", "qualification": "Английский язык", "max_hours": 20},
    {"id": 12, "full_name": "Джаксыбекова Дина", "short_name": "Джаксыбекова Д.", "role": "Учитель", "subject": "Английский язык", "qualification": "Английский язык", "max_hours": 20},
    {"id": 13, "full_name": "Бекова Айгуль", "short_name": "Бекова А.", "role": "Учитель", "subject": "Казахский язык", "qualification": "Казахский язык", "max_hours": 20},
    {"id": 14, "full_name": "Сейтжанов Ерлан", "short_name": "Сейтжанов Е.", "role": "Учитель", "subject": "Казахский язык", "qualification": "Казахский язык", "max_hours": 20},
    {"id": 15, "full_name": "Мусина Гульбану", "short_name": "Мусина Г.", "role": "Учитель", "subject": "История", "qualification": "История", "max_hours": 18},
    {"id": 16, "full_name": "Козлова Виктория", "short_name": "Козлова В.", "role": "Учитель", "subject": "География", "qualification": "География", "max_hours": 18},
    {"id": 17, "full_name": "Адамов Санжар", "short_name": "Адамов С.", "role": "Учитель", "subject": "Музыка", "qualification": "Музыка", "max_hours": 12},
    {"id": 18, "full_name": "Пак Максим", "short_name": "Пак М.", "role": "Учитель", "subject": "ИЗО", "qualification": "ИЗО", "max_hours": 12},
    {"id": 19, "full_name": "Шевченко Марина", "short_name": "Шевченко М.", "role": "Учитель", "subject": "Русский язык", "qualification": "Русский язык", "max_hours": 20},
    {"id": 20, "full_name": "Дюсенов Нурлан", "short_name": "Дюсенов Н.", "role": "Учитель", "subject": "Геометрия", "qualification": "Математика", "max_hours": 18},
    # Администрация
    {"id": 21, "full_name": "Директор Школы", "short_name": "Директор", "role": "Директор", "subject": None, "qualification": "Управление", "max_hours": 8},
    {"id": 22, "full_name": "Завуч Сатова", "short_name": "Завуч", "role": "Завуч", "subject": None, "qualification": "Педагогика", "max_hours": 8},
]

ROOMS_DATA = [
    {"number": "101", "name": "Кабинет математики", "capacity": 30, "room_type": "classroom"},
    {"number": "102", "name": "Кабинет информатики", "capacity": 25, "room_type": "lab"},
    {"number": "103", "name": "Кабинет физики", "capacity": 28, "room_type": "lab"},
    {"number": "104", "name": "Кабинет химии", "capacity": 28, "room_type": "lab"},
    {"number": "105", "name": "Кабинет биологии", "capacity": 28, "room_type": "lab"},
    {"number": "201", "name": "Кабинет английского (1)", "capacity": 20, "room_type": "classroom"},
    {"number": "202", "name": "Кабинет английского (2)", "capacity": 20, "room_type": "classroom"},
    {"number": "203", "name": "Кабинет английского (3)", "capacity": 20, "room_type": "classroom"},
    {"number": "204", "name": "Кабинет английского (4)", "capacity": 20, "room_type": "classroom"},
    {"number": "205", "name": "Кабинет казахского (1)", "capacity": 25, "room_type": "classroom"},
    {"number": "206", "name": "Кабинет казахского (2)", "capacity": 25, "room_type": "classroom"},
    {"number": "301", "name": "Кабинет истории", "capacity": 30, "room_type": "classroom"},
    {"number": "302", "name": "Кабинет географии", "capacity": 30, "room_type": "classroom"},
    {"number": "303", "name": "Кабинет русского языка", "capacity": 30, "room_type": "classroom"},
    {"number": "304", "name": "Кабинет музыки", "capacity": 35, "room_type": "auditorium"},
    {"number": "305", "name": "Кабинет ИЗО", "capacity": 30, "room_type": "classroom"},
    {"number": "спортзал", "name": "Спортивный зал", "capacity": 60, "room_type": "gym"},
    {"number": "актовый", "name": "Актовый зал", "capacity": 200, "room_type": "auditorium"},
]

# Параллели и классы
PARALLELS_DATA = [
    {"grade": 1, "has_lenta": False, "lenta_subject": None, "classes": ["1А", "1Б"]},
    {"grade": 2, "has_lenta": False, "lenta_subject": None, "classes": ["2А", "2Б"]},
    {"grade": 3, "has_lenta": True, "lenta_subject": "Английский язык", "classes": ["3А", "3Б", "3В"]},
    {"grade": 4, "has_lenta": False, "lenta_subject": None, "classes": ["4А", "4Б"]},
    {"grade": 5, "has_lenta": True, "lenta_subject": "Английский язык", "classes": ["5А", "5Б"]},
    {"grade": 6, "has_lenta": False, "lenta_subject": None, "classes": ["6А", "6Б"]},
    {"grade": 7, "has_lenta": False, "lenta_subject": None, "classes": ["7А", "7В"]},
    {"grade": 8, "has_lenta": False, "lenta_subject": None, "classes": ["8А", "8Б"]},
    {"grade": 9, "has_lenta": False, "lenta_subject": None, "classes": ["9А", "9Б"]},
]

# Лента для 3-й параллели: 4 уровневые группы английского
LENTA_GROUPS_3 = [
    {"group_name": "Beginner", "level": 1, "teacher_short": "Касенова А.", "room_number": "201"},
    {"group_name": "Pre-Intermediate", "level": 2, "teacher_short": "Джаксыбекова Д.", "room_number": "202"},
    {"group_name": "Intermediate", "level": 3, "teacher_short": "Касенова А.", "room_number": "203"},
    {"group_name": "Upper-Intermediate", "level": 4, "teacher_short": "Джаксыбекова Д.", "room_number": "204"},
]

# Лента для 5-й параллели
LENTA_GROUPS_5 = [
    {"group_name": "Beginner", "level": 1, "teacher_short": "Касенова А.", "room_number": "201"},
    {"group_name": "Intermediate", "level": 2, "teacher_short": "Джаксыбекова Д.", "room_number": "202"},
]


def seed(db: Session, reset: bool = False):
    if reset:
        # Удаляем только данные расписания, не трогаем users/tasks
        for model in [StaffScheduleEntry, ScheduleEntry, LentaGroup,
                      Class, Parallel, Room, TimeSlot]:
            db.query(model).delete()
        # Удаляем учителей (не users)
        db.query(Teacher).delete()
        db.commit()

    # 1. Учителя / сотрудники
    teacher_map = {}  # short_name -> Teacher
    for emp in EMPLOYEES:
        existing = db.query(Teacher).filter_by(full_name=emp["full_name"]).first()
        if existing:
            teacher_map[emp["short_name"]] = existing
            continue
        t = Teacher(
            full_name=emp["full_name"],
            short_name=emp["short_name"],
            role=emp["role"],
            subject=emp["subject"],
            qualification=emp["qualification"],
            max_hours_per_week=emp["max_hours"],
        )
        db.add(t)
        db.flush()
        teacher_map[emp["short_name"]] = t
    db.commit()

    # 2. Кабинеты
    room_map = {}  # number -> Room
    for r in ROOMS_DATA:
        existing = db.query(Room).filter_by(number=r["number"]).first()
        if existing:
            room_map[r["number"]] = existing
            continue
        room = Room(
            number=r["number"],
            name=r["name"],
            capacity=r["capacity"],
            room_type=r["room_type"],
        )
        db.add(room)
        db.flush()
        room_map[r["number"]] = room
    db.commit()

    # 3. Временные слоты
    slot_map = {}  # (day, lesson_num) -> TimeSlot
    for day in DAYS:
        for lesson_num, (start, end) in LESSON_TIMES.items():
            existing = db.query(TimeSlot).filter_by(day=day, lesson_number=lesson_num).first()
            if existing:
                slot_map[(day, lesson_num)] = existing
                continue
            ts = TimeSlot(day=day, lesson_number=lesson_num, start_time=start, end_time=end)
            db.add(ts)
            db.flush()
            slot_map[(day, lesson_num)] = ts
    db.commit()

    # 4. Параллели и классы
    parallel_map = {}  # grade -> Parallel
    class_map = {}     # name -> Class
    for pd in PARALLELS_DATA:
        existing = db.query(Parallel).filter_by(grade=pd["grade"]).first()
        if existing:
            parallel_map[pd["grade"]] = existing
        else:
            p = Parallel(
                grade=pd["grade"],
                has_lenta=pd["has_lenta"],
                lenta_subject=pd["lenta_subject"],
            )
            db.add(p)
            db.flush()
            parallel_map[pd["grade"]] = p

        for cname in pd["classes"]:
            existing_c = db.query(Class).filter_by(name=cname).first()
            if existing_c:
                class_map[cname] = existing_c
                continue
            grade_num = int(cname[:-1])
            letter = cname[-1]
            c = Class(
                name=cname,
                grade=grade_num,
                letter=letter,
                parallel_id=parallel_map[pd["grade"]].id,
                student_count=25,
            )
            db.add(c)
            db.flush()
            class_map[cname] = c
    db.commit()

    # 5. Группы лент
    for parallel_grade, groups in [(3, LENTA_GROUPS_3), (5, LENTA_GROUPS_5)]:
        parallel = parallel_map.get(parallel_grade)
        if not parallel:
            continue
        existing_groups = db.query(LentaGroup).filter_by(parallel_id=parallel.id).count()
        if existing_groups > 0:
            continue
        for g in groups:
            teacher = teacher_map.get(g["teacher_short"])
            room = room_map.get(g["room_number"])
            lg = LentaGroup(
                parallel_id=parallel.id,
                group_name=g["group_name"],
                level=g["level"],
                teacher_id=teacher.id if teacher else None,
                room_id=room.id if room else None,
            )
            db.add(lg)
    db.commit()

    # 6. Базовое расписание для демо (несколько классов на неделю)
    _seed_demo_schedule(db, teacher_map, room_map, slot_map, class_map)

    # 7. Расписание для технического персонала
    _seed_staff_schedule(db, teacher_map, slot_map)

    db.commit()
    print("✅ Seed завершён успешно.")


def _seed_demo_schedule(db, teacher_map, room_map, slot_map, class_map):
    """Создаёт демо-расписание для нескольких классов."""
    if db.query(ScheduleEntry).count() > 0:
        return

    demo_lessons = [
        # 3А — понедельник
        ("3А", "Понедельник", 1, "Математика", "Болат", "101"),
        ("3А", "Понедельник", 2, "Русский язык", "Шевченко М.", "303"),
        ("3А", "Понедельник", 3, "Английский язык", "Касенова А.", "201"),
        ("3А", "Понедельник", 4, "Физкультура", "Романов Д.", "спортзал"),
        ("3А", "Вторник", 1, "Математика", "Болат", "101"),
        ("3А", "Вторник", 2, "История", "Мусина Г.", "301"),
        ("3А", "Вторник", 3, "Математика", "Болат", "101"),
        ("3А", "Среда", 1, "Казахский язык", "Бекова А.", "205"),
        ("3А", "Среда", 2, "Математика", "Болат", "101"),
        ("3А", "Среда", 3, "Русский язык", "Шевченко М.", "303"),
        ("3А", "Четверг", 1, "Математика", "Болат", "101"),
        ("3А", "Четверг", 2, "Физкультура", "Романов Д.", "спортзал"),
        ("3А", "Пятница", 1, "Музыка", "Адамов С.", "304"),
        ("3А", "Пятница", 2, "Казахский язык", "Бекова А.", "205"),
        # 5А — несколько уроков
        ("5А", "Понедельник", 1, "Математика", "Петрова О.", "102"),
        ("5А", "Понедельник", 2, "Физика", "Нуров А.", "103"),
        ("5А", "Понедельник", 3, "Английский язык", "Касенова А.", "201"),
        ("5А", "Вторник", 1, "Информатика", "Байжанов Д.", "102"),
        ("5А", "Вторник", 2, "Математика", "Петрова О.", "102"),
        ("5А", "Среда", 1, "Химия", "Жакенова К.", "104"),
        ("5А", "Среда", 2, "Биология", "Ли Н.", "105"),
        # 9А — профиль
        ("9А", "Понедельник", 1, "Математика", "Болат", "101"),
        ("9А", "Понедельник", 2, "Информатика", "Байжанов Д.", "102"),
        ("9А", "Понедельник", 3, "Физика", "Нуров А.", "103"),
        ("9А", "Вторник", 1, "Геометрия", "Дюсенов Н.", "101"),
        ("9А", "Вторник", 2, "Химия", "Жакенова К.", "104"),
        ("9А", "Среда", 1, "Математика", "Болат", "101"),
    ]

    for class_name, day, lesson_num, subject, teacher_short, room_number in demo_lessons:
        cls = class_map.get(class_name)
        teacher = teacher_map.get(teacher_short)
        room = room_map.get(room_number)
        slot = slot_map.get((day, lesson_num))
        if not cls or not slot:
            continue
        entry = ScheduleEntry(
            class_id=cls.id,
            teacher_id=teacher.id if teacher else None,
            room_id=room.id if room else None,
            time_slot_id=slot.id,
            subject=subject,
        )
        db.add(entry)
    db.commit()


def _seed_staff_schedule(db, teacher_map, slot_map):
    """Создаёт плановое расписание для технического персонала и администрации."""
    if db.query(StaffScheduleEntry).count() > 0:
        return

    # Завхоз: утренний обход каждый день (1-й урок)
    aigerim = teacher_map.get("Гульнара")
    if aigerim:
        for day in DAYS:
            slot = slot_map.get((day, 1))
            if slot:
                db.add(StaffScheduleEntry(
                    staff_id=aigerim.id,
                    time_slot_id=slot.id,
                    entry_type=StaffEntryType.duty,
                    description="Плановый обход территории и кабинетов",
                ))

    # Техработник (Серик): дежурство с 1 по 3 урок каждый день
    akhmet = teacher_map.get("Серик")
    if akhmet:
        for day in DAYS:
            for lesson in [1, 2, 3]:
                slot = slot_map.get((day, lesson))
                if slot:
                    db.add(StaffScheduleEntry(
                        staff_id=akhmet.id,
                        time_slot_id=slot.id,
                        entry_type=StaffEntryType.duty,
                        description="Техническое дежурство",
                    ))

    # Директор: ежедневная работа с документами (6-й урок) + пятница - педсовет (5-й)
    director = teacher_map.get("Директор")
    if director:
        for day in DAYS:
            slot = slot_map.get((day, 6))
            if slot:
                db.add(StaffScheduleEntry(
                    staff_id=director.id,
                    time_slot_id=slot.id,
                    entry_type=StaffEntryType.meeting,
                    description="Работа с документами и отчётами",
                ))
        # Пятница 5-й урок — педсовет
        slot = slot_map.get(("Пятница", 5))
        if slot:
            db.add(StaffScheduleEntry(
                staff_id=director.id,
                time_slot_id=slot.id,
                entry_type=StaffEntryType.meeting,
                description="Педагогический совет",
            ))

    # Завуч: посещение уроков (понедельник 3-й, среда 2-й)
    zavuch = teacher_map.get("Завуч")
    if zavuch:
        for day, lesson, desc in [
            ("Понедельник", 3, "Посещение урока математики в 3А (контроль)"),
            ("Среда", 2, "Посещение урока английского в 5А (контроль)"),
            ("Пятница", 4, "Методическое совещание учителей"),
        ]:
            slot = slot_map.get((day, lesson))
            if slot:
                db.add(StaffScheduleEntry(
                    staff_id=zavuch.id,
                    time_slot_id=slot.id,
                    entry_type=StaffEntryType.meeting,
                    description=desc,
                ))

    db.commit()


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()
