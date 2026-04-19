from sqlalchemy.orm import Session

from app.db.models import LentaGroup, Parallel, Room, ScheduleEntry, Teacher


DEMO_ENGLISH_TEACHERS = [
    {
        "full_name": "Ермекова Алтын",
        "short_name": "Ермекова А.",
        "role": "Учитель",
        "subject": "Английский язык",
        "qualification": "Английский язык",
        "max_hours_per_week": 20,
    },
    {
        "full_name": "Байтурсынова Минара",
        "short_name": "Байтурсынова М.",
        "role": "Учитель",
        "subject": "Английский язык",
        "qualification": "Английский язык",
        "max_hours_per_week": 20,
    },
]


LENTA_ASSIGNMENTS = {
    3: [
        ("Beginner", "Касенова А.", "201"),
        ("Pre-Intermediate", "Джаксыбекова Д.", "202"),
        ("Intermediate", "Ермекова А.", "203"),
        ("Upper-Intermediate", "Байтурсынова М.", "204"),
    ],
    5: [
        ("Beginner", "Касенова А.", "201"),
        ("Intermediate", "Джаксыбекова Д.", "202"),
    ],
}


def _get_or_create_teacher(db: Session, payload: dict) -> Teacher:
    teacher = db.query(Teacher).filter_by(full_name=payload["full_name"]).first()
    if teacher:
        return teacher
    teacher = Teacher(**payload)
    db.add(teacher)
    db.flush()
    return teacher


def apply_demo_fixes(db: Session) -> None:
    teacher_map = {}
    for payload in DEMO_ENGLISH_TEACHERS:
        teacher = _get_or_create_teacher(db, payload)
        teacher_map[teacher.short_name] = teacher

    for teacher in db.query(Teacher).all():
        if teacher.short_name:
            teacher_map[teacher.short_name] = teacher

    room_map = {room.number: room for room in db.query(Room).all()}

    for grade, assignments in LENTA_ASSIGNMENTS.items():
        parallel = db.query(Parallel).filter_by(grade=grade).first()
        if not parallel:
            parallel = Parallel(grade=grade, has_lenta=True, lenta_subject="Английский язык")
            db.add(parallel)
            db.flush()
        else:
            parallel.has_lenta = True
            if not parallel.lenta_subject:
                parallel.lenta_subject = "Английский язык"
        for group_name, teacher_short, room_number in assignments:
            group = (
                db.query(LentaGroup)
                .filter_by(parallel_id=parallel.id, group_name=group_name)
                .first()
            )
            teacher = teacher_map.get(teacher_short)
            room = room_map.get(room_number)
            if not group:
                level = list(dict.fromkeys(a[0] for a in assignments)).index(group_name) + 1
                group = LentaGroup(
                    parallel_id=parallel.id,
                    group_name=group_name,
                    level=level,
                    teacher_id=teacher.id if teacher else None,
                    room_id=room.id if room else None,
                )
                db.add(group)
                db.flush()
            else:
                if teacher:
                    group.teacher_id = teacher.id
                if room:
                    group.room_id = room.id

    invalid_lenta_entries = (
        db.query(ScheduleEntry)
        .filter(
            ScheduleEntry.is_lenta == True,
            ScheduleEntry.class_id.isnot(None),
            ScheduleEntry.teacher_id.isnot(None),
        )
        .all()
    )
    for entry in invalid_lenta_entries:
        db.delete(entry)

    db.commit()
