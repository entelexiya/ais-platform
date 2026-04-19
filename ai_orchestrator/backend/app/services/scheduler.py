from datetime import datetime
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.ai.rag_service import check_compliance
from app.db.database import SessionLocal
from app.db.models import ScheduleEntry, Teacher, TeacherAbsenceEvent, TimeSlot
from app.services.conflict_checker import ConflictChecker
from app.services.notification_service import (
    dispatch_director_alert,
    dispatch_substitution_notification,
    send_to_school_group,
)

DAY_SEQUENCE = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница"]
ADMIN_FALLBACK_ROLES = {"Завуч", "Директор"}
SUBJECT_COMPATIBILITY = {
    "Математика": {"Геометрия", "Информатика"},
    "Геометрия": {"Математика"},
    "Физика": {"Информатика", "Математика"},
    "Химия": {"Биология"},
    "Биология": {"Химия", "Познание мира"},
    "История": {"География", "Познание мира"},
    "География": {"История", "Познание мира"},
    "Русский язык": {"Казахский язык"},
    "Казахский язык": {"Русский язык"},
    "Английский язык": set(),
    "Информатика": {"Математика", "Физика"},
    "Познание мира": {"История", "География", "Биология"},
}


def _normalize_name(value: str) -> str:
    return "".join(ch.lower() for ch in (value or "") if ch.isalnum())


def _resolve_target_day(target_day: Optional[str]) -> str:
    if target_day and target_day in DAY_SEQUENCE:
        return target_day

    lowered = (target_day or "").strip().lower()
    alias_map = {
        "today": DAY_SEQUENCE[datetime.now().weekday()] if datetime.now().weekday() < 5 else DAY_SEQUENCE[0],
        "сегодня": DAY_SEQUENCE[datetime.now().weekday()] if datetime.now().weekday() < 5 else DAY_SEQUENCE[0],
    }
    if lowered in alias_map:
        return alias_map[lowered]

    return DAY_SEQUENCE[datetime.now().weekday()] if datetime.now().weekday() < 5 else DAY_SEQUENCE[0]


def _find_teacher(db: Session, teacher_name: str) -> Optional[Teacher]:
    normalized = _normalize_name(teacher_name)
    teachers = db.query(Teacher).all()
    for teacher in teachers:
        variants = [teacher.full_name or "", teacher.short_name or ""]
        for variant in variants:
            candidate = _normalize_name(variant)
            if candidate and (
                normalized in candidate
                or candidate in normalized
                or candidate[:4] == normalized[:4]
            ):
                return teacher
    return None


def _class_label(lesson: ScheduleEntry) -> str:
    if lesson.class_:
        return lesson.class_.name
    if lesson.lenta_group:
        return f"Лента: {lesson.lenta_group.group_name}"
    return "Группа"


def _teacher_weekly_load(db: Session, teacher_id: int) -> int:
    return db.query(ScheduleEntry).filter(ScheduleEntry.teacher_id == teacher_id).count()


def _subject_score(absent_teacher: Teacher, teacher: Teacher, lesson_subject: str) -> Tuple[int, str]:
    if teacher.role in ADMIN_FALLBACK_ROLES:
        return (50, "admin_fallback")

    teacher_subject = teacher.subject or ""
    absent_subject = absent_teacher.subject or lesson_subject
    compatible = SUBJECT_COMPATIBILITY.get(absent_subject, set()) | SUBJECT_COMPATIBILITY.get(lesson_subject, set())

    if teacher_subject == lesson_subject:
        return (0, "exact_subject")
    if teacher_subject == absent_subject:
        return (1, "same_absent_subject")
    if teacher_subject in compatible:
        return (2, "compatible_subject")
    if teacher.qualification and absent_teacher.qualification and teacher.qualification == absent_teacher.qualification:
        return (3, "same_qualification")
    return (99, "incompatible")


def _find_candidates(
    db: Session,
    checker: ConflictChecker,
    absent_teacher: Teacher,
    lesson: ScheduleEntry,
) -> List[Dict]:
    slot = lesson.time_slot
    if not slot:
        return []

    candidates = (
        db.query(Teacher)
        .filter(Teacher.id != absent_teacher.id)
        .all()
    )

    ranked_candidates = []
    for teacher in candidates:
        if teacher.role not in {"Учитель"} and teacher.role not in ADMIN_FALLBACK_ROLES:
            continue
        if not checker.check_teacher_availability(teacher.id, lesson.time_slot_id):
            continue

        load_info = checker.check_teacher_daily_load(teacher.id, slot.day)
        if load_info["overload"]:
            continue

        weekly_load = _teacher_weekly_load(db, teacher.id)
        max_hours = teacher.max_hours_per_week or 20
        if teacher.role == "Учитель" and weekly_load >= max_hours:
            continue

        subject_rank, match_type = _subject_score(absent_teacher, teacher, lesson.subject or "")
        if subject_rank >= 99:
            continue

        ranked_candidates.append(
            {
                "teacher": teacher,
                "match_type": match_type,
                "subject_rank": subject_rank,
                "daily_load": load_info["lessons"],
                "weekly_load": weekly_load,
                "is_admin_fallback": teacher.role in ADMIN_FALLBACK_ROLES,
            }
        )

    ranked_candidates.sort(
        key=lambda item: (
            item["subject_rank"],
            item["daily_load"],
            item["weekly_load"],
            item["teacher"].short_name or item["teacher"].full_name,
        )
    )
    return ranked_candidates


def _serialize_preview(
    absent_teacher: Teacher,
    lesson: ScheduleEntry,
    candidate_info: Optional[Dict],
    all_candidates: Optional[List[Dict]] = None,
) -> Dict:
    slot = lesson.time_slot
    room = lesson.room
    substitute_teacher = candidate_info["teacher"] if candidate_info else None
    substitute_name = (
        substitute_teacher.short_name or substitute_teacher.full_name
        if substitute_teacher
        else "Отсутствует"
    )
    class_name = _class_label(lesson)

    status_msg = (
        "Замена найдена"
        if substitute_teacher
        else "Нет доступных сотрудников для автоматической замены"
    )

    if substitute_teacher:
        compliance = check_compliance(
            f"Замена учителя ({absent_teacher.qualification}) на "
            f"сотрудника ({substitute_teacher.qualification}) по предмету {lesson.subject}."
        )
        if not compliance.get("compliant", True):
            status_msg += " • требуется ручная проверка приказа"
        else:
            status_msg += " • проверено по RAG"

    return {
        "entry_id": lesson.id,
        "missing_teacher": absent_teacher.short_name or absent_teacher.full_name,
        "substitute_teacher": substitute_name,
        "substitute_teacher_id": substitute_teacher.id if substitute_teacher else None,
        "lesson_number": slot.lesson_number if slot else None,
        "class_name": class_name,
        "room": room.number if room else "—",
        "day": slot.day if slot else None,
        "subject": lesson.subject,
        "status": status_msg,
        "match_type": candidate_info["match_type"] if candidate_info else None,
        "load": {
            "daily": candidate_info["daily_load"] if candidate_info else None,
            "weekly": candidate_info["weekly_load"] if candidate_info else None,
            "max_weekly": substitute_teacher.max_hours_per_week if substitute_teacher else None,
        },
        "checks": {
            "time_free": bool(substitute_teacher),
            "qual_match": bool(candidate_info and candidate_info["subject_rank"] <= 3),
            "admin_fallback": bool(candidate_info and candidate_info["is_admin_fallback"]),
            "load_ok": bool(
                candidate_info and
                (candidate_info["weekly_load"] or 0) < (substitute_teacher.max_hours_per_week if substitute_teacher else 20)
            ),
        },
        "was_became_table": (
            f"Было: {absent_teacher.short_name or absent_teacher.full_name} → Стало: {substitute_name}"
        ),
        "rejected_candidates": [
            {
                "name": c["teacher"].short_name or c["teacher"].full_name,
                "reason": "Превышение нагрузки (Прик. МОН №110)" if c.get("weekly_load", 0) >= (c["teacher"].max_hours_per_week or 20) - 1 else "Другой предмет / не соответствует квалификации",
            }
            for c in (all_candidates or [])[1:4]
        ],
    }


def find_substitution(
    teacher_name: str,
    target_date: str = None,
    db: Session = None,
) -> List[Dict]:
    own_session = db is None
    if own_session:
        db = SessionLocal()

    try:
        absent_teacher = _find_teacher(db, teacher_name)
        if not absent_teacher:
            return []

        target_day = _resolve_target_day(target_date)
        lessons = (
            db.query(ScheduleEntry)
            .join(TimeSlot, ScheduleEntry.time_slot_id == TimeSlot.id)
            .filter(
                ScheduleEntry.teacher_id == absent_teacher.id,
                TimeSlot.day == target_day,
            )
            .order_by(TimeSlot.lesson_number)
            .all()
        )
        if not lessons:
            return []

        checker = ConflictChecker(db)
        previews = []
        for lesson in lessons:
            candidate_info = _find_candidates(db, checker, absent_teacher, lesson)
            previews.append(_serialize_preview(absent_teacher, lesson, candidate_info[0] if candidate_info else None, candidate_info))
        return previews
    finally:
        if own_session and db is not None:
            db.close()


def process_teacher_absence_event(
    teacher_name: str,
    target_day: Optional[str] = None,
    reason: Optional[str] = None,
    source: str = "dashboard",
    raw_message: Optional[str] = None,
    db: Optional[Session] = None,
) -> Dict:
    own_session = db is None
    if own_session:
        db = SessionLocal()

    try:
        absent_teacher = _find_teacher(db, teacher_name)
        if not absent_teacher:
            return {"status": "teacher_not_found", "teacher_name": teacher_name, "substitutions": []}

        resolved_day = _resolve_target_day(target_day)
        lessons = (
            db.query(ScheduleEntry)
            .join(TimeSlot, ScheduleEntry.time_slot_id == TimeSlot.id)
            .filter(
                ScheduleEntry.teacher_id == absent_teacher.id,
                TimeSlot.day == resolved_day,
            )
            .order_by(TimeSlot.lesson_number)
            .all()
        )

        absence_event = TeacherAbsenceEvent(
            teacher_id=absent_teacher.id,
            day=resolved_day,
            source=source,
            reason=reason,
            raw_message=raw_message,
            status="pending",
        )
        db.add(absence_event)
        db.flush()

        if not lessons:
            absence_event.status = "no_lessons"
            db.commit()
            return {
                "status": "no_lessons",
                "event_id": absence_event.id,
                "teacher_name": absent_teacher.short_name or absent_teacher.full_name,
                "day": resolved_day,
                "substitutions": [],
                "unresolved": [],
            }

        checker = ConflictChecker(db)
        substitutions: List[Dict] = []
        unresolved: List[Dict] = []
        notifications: List[Dict] = []

        for lesson in lessons:
            candidates = _find_candidates(db, checker, absent_teacher, lesson)
            candidate_info = candidates[0] if candidates else None
            preview = _serialize_preview(absent_teacher, lesson, candidate_info, candidates)

            if not candidate_info:
                unresolved.append(preview)
                continue

            substitute = candidate_info["teacher"]
            previous_original = lesson.original_teacher_id or absent_teacher.id
            lesson.teacher_id = substitute.id
            lesson.original_teacher_id = previous_original
            lesson.is_substitution = True

            notification_result = dispatch_substitution_notification(
                db=db,
                substitute_teacher_name=substitute.full_name or substitute.short_name,
                missing_teacher_name=absent_teacher.full_name or absent_teacher.short_name,
                class_name=preview["class_name"],
                lesson_number=preview["lesson_number"],
                room=preview["room"],
                day=preview["day"],
                subject=preview["subject"] or "Урок",
            )

            preview["applied"] = True
            preview["notification"] = notification_result
            preview["substitute_teacher"] = substitute.short_name or substitute.full_name
            preview["substitute_teacher_id"] = substitute.id
            substitutions.append(preview)
            notifications.append(notification_result)

        director_alert = None
        if unresolved:
            lesson_labels = ", ".join(
                f"{item['lesson_number']} урок ({item['class_name']})" for item in unresolved
            )
            director_alert = dispatch_director_alert(
                db,
                (
                    f"⚠️ Не все замены найдены.\n"
                    f"Отсутствует: {absent_teacher.short_name or absent_teacher.full_name}\n"
                    f"День: {resolved_day}\n"
                    f"Нужна ручная обработка: {lesson_labels}"
                ),
            )

        absence_event.substitutions_count = len(substitutions)
        absence_event.unresolved_count = len(unresolved)
        absence_event.status = (
            "processed"
            if substitutions and not unresolved
            else "partial"
            if substitutions and unresolved
            else "unresolved"
        )

        db.commit()

        # Групповое уведомление в школьный WhatsApp-чат
        teacher_label = absent_teacher.short_name or absent_teacher.full_name
        if substitutions:
            lines = [f"📢 *Замена на {resolved_day}*\nОтсутствует: *{teacher_label}*\n"]
            for s in substitutions:
                lines.append(
                    f"• Урок {s['lesson_number']} | {s['class_name']} | {s['subject']}\n"
                    f"  Заменяет: *{s['substitute_teacher']}* (каб. {s['room']})"
                )
            send_to_school_group("\n".join(lines))
        elif unresolved:
            send_to_school_group(
                f"⚠️ *Отсутствие: {teacher_label}* ({resolved_day})\n"
                f"Замена не найдена для {len(unresolved)} уроков. Требуется ручное назначение."
            )

        return {
            "status": absence_event.status,
            "event_id": absence_event.id,
            "teacher_name": absent_teacher.short_name or absent_teacher.full_name,
            "teacher_id": absent_teacher.id,
            "day": resolved_day,
            "reason": reason,
            "source": source,
            "total_lessons": len(lessons),
            "substitutions_count": len(substitutions),
            "unresolved_count": len(unresolved),
            "substitutions": substitutions,
            "unresolved": unresolved,
            "notifications": notifications,
            "director_alert": director_alert,
        }
    finally:
        if own_session and db is not None:
            db.close()
