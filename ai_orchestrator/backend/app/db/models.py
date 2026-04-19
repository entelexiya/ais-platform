from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, Enum, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)


class TaskReminder(Base):
    __tablename__ = "task_reminders"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    assignee = Column(String)
    deadline = Column(String)
    is_accepted = Column(Boolean, default=False)
    is_completed = Column(Boolean, default=False)


class TeacherAbsenceEvent(Base):
    __tablename__ = "teacher_absence_events"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False, index=True)
    day = Column(String, nullable=False, index=True)
    source = Column(String, default="dashboard")
    reason = Column(String, nullable=True)
    raw_message = Column(Text, nullable=True)
    status = Column(String, default="pending")
    substitutions_count = Column(Integer, default=0)
    unresolved_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    teacher = relationship("Teacher", back_populates="absence_events")


# ─── Schedule domain ─────────────────────────────────────────────────────────

class RoomType(str, enum.Enum):
    classroom = "classroom"
    gym = "gym"
    lab = "lab"
    auditorium = "auditorium"
    other = "other"


class DayEnum(str, enum.Enum):
    monday = "Понедельник"
    tuesday = "Вторник"
    wednesday = "Среда"
    thursday = "Четверг"
    friday = "Пятница"


class StaffEntryType(str, enum.Enum):
    lesson = "lesson"
    duty = "duty"
    meeting = "meeting"
    task = "task"
    free = "free"


class Teacher(Base):
    """Все сотрудники: учителя, завхоз, слесарь, директор, завуч."""
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    short_name = Column(String)           # Аскар, Смирнова Е.
    role = Column(String, default="Учитель")    # Учитель / Завхоз / Техработник / Директор / Завуч / Секретарь
    subject = Column(String, nullable=True)     # основной предмет (для учителей)
    qualification = Column(String, nullable=True)
    max_hours_per_week = Column(Integer, default=20)
    telegram_chat_id = Column(String, nullable=True)
    whatsapp_number = Column(String, nullable=True)
    # JSON-строка: {"no_friday_afternoon": true}
    constraints = Column(Text, nullable=True)

    schedule_entries = relationship("ScheduleEntry", back_populates="teacher",
                                    foreign_keys="ScheduleEntry.teacher_id")
    staff_entries = relationship("StaffScheduleEntry", back_populates="staff")
    lenta_groups = relationship("LentaGroup", back_populates="teacher")
    absence_events = relationship("TeacherAbsenceEvent", back_populates="teacher")


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(String, unique=True)   # "101", "спортзал"
    name = Column(String, nullable=True)
    capacity = Column(Integer, default=30)
    room_type = Column(String, default=RoomType.classroom)

    schedule_entries = relationship("ScheduleEntry", back_populates="room")
    lenta_groups = relationship("LentaGroup", back_populates="room")


class Parallel(Base):
    """Параллель классов, например все 3-и классы (3А, 3Б, 3В)."""
    __tablename__ = "parallels"

    id = Column(Integer, primary_key=True, index=True)
    grade = Column(Integer)              # 1-11
    has_lenta = Column(Boolean, default=False)
    lenta_subject = Column(String, nullable=True)  # "Английский язык"

    classes = relationship("Class", back_populates="parallel")
    lenta_groups = relationship("LentaGroup", back_populates="parallel")


class Class(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)       # "3А"
    grade = Column(Integer)
    letter = Column(String)                  # "А"
    parallel_id = Column(Integer, ForeignKey("parallels.id"), nullable=True)
    student_count = Column(Integer, default=25)
    homeroom_teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)

    parallel = relationship("Parallel", back_populates="classes")
    schedule_entries = relationship("ScheduleEntry", back_populates="class_")


class LentaGroup(Base):
    """Уровневая группа внутри параллели (для системы лент)."""
    __tablename__ = "lenta_groups"

    id = Column(Integer, primary_key=True, index=True)
    parallel_id = Column(Integer, ForeignKey("parallels.id"))
    group_name = Column(String)      # "Beginner", "Pre-Intermediate", "Intermediate", "Upper"
    level = Column(Integer, default=1)  # 1=низший, 4=высший
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=True)

    parallel = relationship("Parallel", back_populates="lenta_groups")
    teacher = relationship("Teacher", back_populates="lenta_groups")
    room = relationship("Room", back_populates="lenta_groups")
    schedule_entries = relationship("ScheduleEntry", back_populates="lenta_group")


class TimeSlot(Base):
    __tablename__ = "time_slots"

    id = Column(Integer, primary_key=True, index=True)
    day = Column(String)              # "Понедельник"
    lesson_number = Column(Integer)   # 1-6
    start_time = Column(String)       # "08:00"
    end_time = Column(String)         # "08:45"

    schedule_entries = relationship("ScheduleEntry", back_populates="time_slot")
    staff_entries = relationship("StaffScheduleEntry", back_populates="time_slot")


class ScheduleEntry(Base):
    """Один урок в расписании."""
    __tablename__ = "schedule_entries"

    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=True)
    time_slot_id = Column(Integer, ForeignKey("time_slots.id"))
    subject = Column(String)
    is_lenta = Column(Boolean, default=False)
    lenta_group_id = Column(Integer, ForeignKey("lenta_groups.id"), nullable=True)
    is_substitution = Column(Boolean, default=False)
    original_teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)

    class_ = relationship("Class", back_populates="schedule_entries")
    teacher = relationship("Teacher", back_populates="schedule_entries",
                           foreign_keys=[teacher_id])
    original_teacher = relationship("Teacher", foreign_keys=[original_teacher_id])
    room = relationship("Room", back_populates="schedule_entries")
    time_slot = relationship("TimeSlot", back_populates="schedule_entries")
    lenta_group = relationship("LentaGroup", back_populates="schedule_entries")


class StaffScheduleEntry(Base):
    """Расписание для всех сотрудников (учителя, завхоз, директор и т.д.)."""
    __tablename__ = "staff_schedule_entries"

    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(Integer, ForeignKey("teachers.id"))
    time_slot_id = Column(Integer, ForeignKey("time_slots.id"))
    entry_type = Column(String, default=StaffEntryType.free)
    description = Column(String, nullable=True)
    task_reminder_id = Column(Integer, ForeignKey("task_reminders.id"), nullable=True)

    staff = relationship("Teacher", back_populates="staff_entries")
    time_slot = relationship("TimeSlot", back_populates="staff_entries")
    task_reminder = relationship("TaskReminder")
