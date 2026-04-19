import { useEffect, useState } from "react";
import axios from "axios";

const API_BASE = `http://${window.location.hostname}:8000/api`;

const DAYS = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница"];
const DAYS_SHORT: Record<string, string> = {
  "Понедельник": "Пн", "Вторник": "Вт", "Среда": "Ср",
  "Четверг": "Чт", "Пятница": "Пт",
};
const LESSONS = [1, 2, 3, 4, 5, 6];

interface Entry {
  id: number;
  time_slot_id: number;
  class: string;
  teacher: string | null;
  room: string | null;
  day: string;
  lesson: number;
  start_time: string | null;
  subject: string;
  is_lenta: boolean;
  lenta_group: string | null;
  is_substitution: boolean;
}

interface ConflictInfo {
  type: string;
  description: string;
}

interface Props {
  classFilter?: string;
  className?: string;
  refreshToken?: number;
}

interface TimeSlotItem {
  id: number;
  day: string;
  lesson: number;
  start_time: string;
  end_time: string;
}

export default function TimetableGrid({ classFilter, className = "", refreshToken = 0 }: Props) {
  const [entries, setEntries] = useState<Entry[]>([]);
  const [classes, setClasses] = useState<string[]>([]);
  const [selectedClass, setSelectedClass] = useState(classFilter || "3А");
  const [loading, setLoading] = useState(true);
  const [dragEntry, setDragEntry] = useState<Entry | null>(null);
  const [dragOverCell, setDragOverCell] = useState<{ day: string; lesson: number } | null>(null);
  const [conflictCell, setConflictCell] = useState<{ day: string; lesson: number; conflicts: ConflictInfo[] } | null>(null);
  const [saving, setSaving] = useState(false);
  const [notification, setNotification] = useState<{ text: string; ok: boolean } | null>(null);
  const [timeSlotMap, setTimeSlotMap] = useState<Record<string, Record<number, number>>>({});

  function slotId(day: string, lesson: number): number | null {
    return timeSlotMap[day]?.[lesson] ?? null;
  }

  useEffect(() => {
    fetchSchedule();
  }, [selectedClass, refreshToken]);

  useEffect(() => {
    fetchTimeSlots();
  }, []);

  async function fetchTimeSlots() {
    try {
      const r = await axios.get(`${API_BASE}/schedule/time-slots`);
      const map: Record<string, Record<number, number>> = {};
      (r.data.time_slots as TimeSlotItem[]).forEach((slot) => {
        if (!map[slot.day]) map[slot.day] = {};
        map[slot.day][slot.lesson] = slot.id;
      });
      setTimeSlotMap(map);
    } catch {
      setTimeSlotMap({});
    }
  }

  async function fetchSchedule() {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (selectedClass) params.class_name = selectedClass;
      const r = await axios.get(`${API_BASE}/schedule/db-schedule`, { params });
      const data: Entry[] = r.data.schedule ?? [];
      setEntries(data);

      // Extract unique classes for selector
      if (!classFilter) {
        const all = await axios.get(`${API_BASE}/schedule/db-schedule`);
        const allClasses = Array.from(
          new Set((all.data.schedule as Entry[]).map((e) => e.class).filter(Boolean))
        ).sort();
        setClasses(allClasses as string[]);
      }
    } catch {
      setEntries([]);
    } finally {
      setLoading(false);
    }
  }

  function getEntry(day: string, lesson: number): Entry | undefined {
    return entries.find((e) => e.day === day && e.lesson === lesson);
  }

  async function checkConflict(
    entry: Entry,
    targetDay: string,
    targetLesson: number
  ): Promise<ConflictInfo[]> {
    const targetSlotId = slotId(targetDay, targetLesson);
    if (!targetSlotId) {
      return [{ type: "unknown_slot", description: "Не удалось определить временной слот" }];
    }
    try {
      const r = await axios.post(`${API_BASE}/schedule/check-conflict-v2`, {
        entry_id: entry.id,
        new_time_slot_id: targetSlotId,
      });
      return r.data.conflicts ?? [];
    } catch {
      return [];
    }
  }

  async function moveEntry(entry: Entry, targetDay: string, targetLesson: number) {
    const targetSlotId = slotId(targetDay, targetLesson);
    if (!targetSlotId) {
      showNotification("Не удалось определить временной слот", false);
      return;
    }
    setSaving(true);
    try {
      await axios.patch(
        `${API_BASE}/schedule/entry-v2/${entry.id}?new_time_slot_id=${targetSlotId}`
      );
      showNotification(`Урок перемещён: ${entry.subject} → ${DAYS_SHORT[targetDay]} урок ${targetLesson}`, true);
      fetchSchedule();
    } catch (e: any) {
      showNotification(e.response?.data?.detail ?? "Ошибка перемещения", false);
    } finally {
      setSaving(false);
    }
  }

  function showNotification(text: string, ok: boolean) {
    setNotification({ text, ok });
    setTimeout(() => setNotification(null), 3000);
  }

  // ── Drag handlers ──────────────────────────────────────────────────────────

  function handleDragStart(e: React.DragEvent, entry: Entry) {
    e.dataTransfer.effectAllowed = "move";
    setDragEntry(entry);
  }

  async function handleDragEnter(day: string, lesson: number) {
    setDragOverCell({ day, lesson });
    if (!dragEntry) return;
    if (dragEntry.day === day && dragEntry.lesson === lesson) {
      setConflictCell(null);
      return;
    }
    const conflicts = await checkConflict(dragEntry, day, lesson);
    if (conflicts.length > 0) {
      setConflictCell({ day, lesson, conflicts });
    } else {
      setConflictCell(null);
    }
  }

  function handleDragLeave() {
    setDragOverCell(null);
  }

  function handleDragOver(e: React.DragEvent) {
    e.preventDefault();
    e.dataTransfer.dropEffect = conflictCell ? "none" : "move";
  }

  async function handleDrop(e: React.DragEvent, day: string, lesson: number) {
    e.preventDefault();
    if (!dragEntry) return;
    if (dragEntry.day === day && dragEntry.lesson === lesson) {
      setDragEntry(null);
      setDragOverCell(null);
      return;
    }
    if (conflictCell?.day === day && conflictCell?.lesson === lesson) {
      showNotification(
        "⛔ Конфликт: " + conflictCell.conflicts.map((c) => c.description).join("; "),
        false
      );
      setDragEntry(null);
      setDragOverCell(null);
      setConflictCell(null);
      return;
    }
    await moveEntry(dragEntry, day, lesson);
    setDragEntry(null);
    setDragOverCell(null);
    setConflictCell(null);
  }

  function handleDragEnd() {
    setDragEntry(null);
    setDragOverCell(null);
    setConflictCell(null);
  }

  // ── Cell state ─────────────────────────────────────────────────────────────

  function cellState(day: string, lesson: number) {
    const isOver = dragOverCell?.day === day && dragOverCell?.lesson === lesson;
    const isConflict =
      conflictCell?.day === day && conflictCell?.lesson === lesson;
    const isDragging =
      dragEntry?.day === day && dragEntry?.lesson === lesson;
    return { isOver, isConflict, isDragging };
  }

  function cellClass(day: string, lesson: number, hasEntry: boolean) {
    const { isOver, isConflict, isDragging } = cellState(day, lesson);
    let base =
      "relative rounded-xl border transition-all duration-150 min-h-[60px] p-1.5 ";
    if (isDragging) return base + "opacity-30 border-white/10 bg-white/5";
    if (isConflict)
      return (
        base +
        "border-red-500/70 bg-red-500/15 shadow-[0_0_12px_rgba(239,68,68,0.5)] animate-pulse"
      );
    if (isOver && !isConflict)
      return base + "border-green-400/60 bg-green-500/15 scale-[1.02]";
    if (hasEntry)
      return base + "border-white/15 bg-white/[0.06] hover:border-white/25 cursor-grab active:cursor-grabbing";
    return base + "border-white/5 bg-white/[0.02]";
  }

  return (
    <div className={className}>
      {/* Class selector */}
      {!classFilter && classes.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {classes.slice(0, 15).map((c) => (
            <button
              key={c}
              onClick={() => setSelectedClass(c)}
              className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                selectedClass === c
                  ? "bg-blue-500/30 border border-blue-400/50 text-blue-200"
                  : "bg-white/5 border border-white/10 text-white/50 hover:bg-white/10"
              }`}
            >
              {c}
            </button>
          ))}
        </div>
      )}

      {/* Instructions */}
      <div className="text-white/40 text-xs mb-3">
        Перетащите урок в другую ячейку, чтобы переместить.{" "}
        <span className="text-red-400">Красная подсветка</span> = конфликт,{" "}
        <span className="text-green-400">зелёная</span> = свободно.
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-40">
          <div className="text-white/40 animate-pulse">Загружаем расписание из БД...</div>
        </div>
      ) : entries.length === 0 ? (
        <div className="text-white/30 text-center py-12">
          Нет данных для класса {selectedClass}. Запустите генерацию расписания или seed.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <div
            className="grid gap-1.5"
            style={{ gridTemplateColumns: `52px repeat(5, minmax(100px, 1fr))` }}
          >
            {/* Header */}
            <div />
            {DAYS.map((d) => (
              <div key={d} className="text-center text-white/50 text-xs font-medium py-1">
                {DAYS_SHORT[d]}
              </div>
            ))}

            {/* Rows */}
            {LESSONS.map((lesson) => (
              <>
                <div
                  key={`lbl-${lesson}`}
                  className="flex flex-col items-center justify-center"
                >
                  <span className="text-white/30 text-xs font-bold">{lesson}</span>
                </div>
                {DAYS.map((day) => {
                  const entry = getEntry(day, lesson);
                  const cs = cellState(day, lesson);
                  return (
                    <div
                      key={`${day}-${lesson}`}
                      className={cellClass(day, lesson, !!entry)}
                      onDragOver={handleDragOver}
                      onDragEnter={() => handleDragEnter(day, lesson)}
                      onDragLeave={handleDragLeave}
                      onDrop={(e) => handleDrop(e, day, lesson)}
                    >
                      {cs.isConflict && conflictCell && (
                        <div className="absolute -top-8 left-0 z-50 bg-red-900 text-red-200 text-[10px] px-2 py-1 rounded-lg shadow-xl whitespace-nowrap max-w-[200px] truncate">
                          ⛔ {conflictCell.conflicts[0]?.description}
                        </div>
                      )}
                      {entry ? (
                        <div
                          draggable
                          onDragStart={(e) => handleDragStart(e, entry)}
                          onDragEnd={handleDragEnd}
                          className={`h-full text-[11px] space-y-0.5 ${
                            entry.is_lenta
                              ? "text-purple-200"
                              : entry.is_substitution
                              ? "text-yellow-200"
                              : "text-white/80"
                          }`}
                        >
                          <div className="font-semibold leading-tight line-clamp-2">
                            {entry.is_lenta && (
                              <span className="text-purple-400 mr-1">⎇</span>
                            )}
                            {entry.subject}
                          </div>
                          {entry.teacher && (
                            <div className="text-white/40 text-[10px] leading-tight">
                              {entry.teacher}
                            </div>
                          )}
                          {entry.room && (
                            <div className="text-white/30 text-[10px]">
                              каб. {entry.room}
                            </div>
                          )}
                          {entry.is_substitution && (
                            <div className="text-yellow-300/70 text-[10px]">
                              ⚡ замена
                            </div>
                          )}
                          {entry.lenta_group && (
                            <div className="text-purple-300/70 text-[10px]">
                              {entry.lenta_group}
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="flex items-center justify-center h-full">
                          <span className="text-white/10 text-[10px]">—</span>
                        </div>
                      )}
                    </div>
                  );
                })}
              </>
            ))}
          </div>
        </div>
      )}

      {/* Saving overlay */}
      {saving && (
        <div className="fixed bottom-4 right-4 z-50 bg-blue-600 text-white text-sm px-4 py-2 rounded-xl shadow-xl flex items-center gap-2">
          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          Сохраняем...
        </div>
      )}

      {/* Notification */}
      {notification && (
        <div
          className={`fixed bottom-4 right-4 z-50 text-sm px-4 py-2.5 rounded-xl shadow-xl ${
            notification.ok
              ? "bg-green-600 text-white"
              : "bg-red-600 text-white"
          }`}
        >
          {notification.text}
        </div>
      )}
    </div>
  );
}
