import { Fragment, useEffect, useMemo, useState } from "react";
import axios from "axios";

const API_BASE = `http://${window.location.hostname}:8000/api`;

const DAYS_SHORT: Record<string, string> = {
  "Понедельник": "Пн",
  "Вторник": "Вт",
  "Среда": "Ср",
  "Четверг": "Чт",
  "Пятница": "Пт",
};

interface HeatmapSlot {
  day: string;
  lesson: number;
  count: number;
  lessons: number;
  load: number;
  overload: boolean;
  entries: string[];
}

interface TeacherRow {
  id: number;
  name: string;
  subject: string | null;
  slots: HeatmapSlot[];
  total_lessons: number;
  max_hours: number;
  overloaded_days: string[];
}

interface RoomRow {
  id: number;
  name: string;
  label: string;
  room_type: string;
  slots: HeatmapSlot[];
  occupied_slots: number;
  conflict_slots: number;
}

interface HeatmapSummary {
  teachers_total: number;
  teachers_overloaded: number;
  rooms_total: number;
  rooms_conflicted: number;
  teacher_load_total: number;
}

interface HeatmapResponse {
  teachers: TeacherRow[];
  rooms: RoomRow[];
  days: string[];
  lessons: number[];
  summary: HeatmapSummary;
}

type ViewMode = "teachers" | "rooms";
type FilterMode = "all" | "attention" | "free";

function loadColor(load: number): string {
  const hue = Math.round((1 - load) * 120);
  const saturation = load > 0.1 ? 72 : 18;
  const lightness = load > 0.85 ? 44 : 54;
  return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}

function slotKey(day: string, lesson: number): string {
  return `${day}-${lesson}`;
}

interface Props {
  className?: string;
}

export default function HeatmapView({ className = "" }: Props) {
  const [data, setData] = useState<HeatmapResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [tooltip, setTooltip] = useState<{ text: string; x: number; y: number } | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("teachers");
  const [filter, setFilter] = useState<FilterMode>("all");

  useEffect(() => {
    axios
      .get(`${API_BASE}/schedule/heatmap`)
      .then((response) => setData(response.data))
      .catch(() =>
        setData({
          teachers: [],
          rooms: [],
          days: ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница"],
          lessons: [1, 2, 3, 4, 5, 6],
          summary: {
            teachers_total: 0,
            teachers_overloaded: 0,
            rooms_total: 0,
            rooms_conflicted: 0,
            teacher_load_total: 0,
          },
        })
      )
      .finally(() => setLoading(false));
  }, []);

  const days = data?.days ?? ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница"];
  const lessons = data?.lessons ?? [1, 2, 3, 4, 5, 6];

  const teacherRows = useMemo(() => {
    const source = data?.teachers ?? [];
    return source.filter((row) => {
      if (filter === "attention") {
        return row.overloaded_days.length > 0 || row.slots.some((slot) => slot.overload);
      }
      if (filter === "free") {
        return row.total_lessons <= 8;
      }
      return true;
    });
  }, [data, filter]);

  const roomRows = useMemo(() => {
    const source = data?.rooms ?? [];
    return source.filter((row) => {
      if (filter === "attention") {
        return row.conflict_slots > 0;
      }
      if (filter === "free") {
        return row.occupied_slots <= 6;
      }
      return true;
    });
  }, [data, filter]);

  if (loading) {
    return (
      <div className={`flex items-center justify-center h-64 ${className}`}>
        <div className="text-white/50 animate-pulse">Загружаем данные...</div>
      </div>
    );
  }

  const summary = data?.summary;
  const isTeachers = viewMode === "teachers";
  const rows = isTeachers ? teacherRows : roomRows;

  return (
    <div className={className}>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div>
          <h2 className="text-white font-bold text-lg">Тепловая карта нагрузки</h2>
          <p className="text-white/50 text-sm">
            {isTeachers ? (
              <>
                Учителей с перегрузкой:{" "}
                <span className="text-red-400 font-semibold">{summary?.teachers_overloaded ?? 0}</span> из{" "}
                {summary?.teachers_total ?? 0}
              </>
            ) : (
              <>
                Кабинетов с конфликтами:{" "}
                <span className="text-red-400 font-semibold">{summary?.rooms_conflicted ?? 0}</span> из{" "}
                {summary?.rooms_total ?? 0}
              </>
            )}
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          {(["teachers", "rooms"] as const).map((mode) => (
            <button
              key={mode}
              onClick={() => setViewMode(mode)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                viewMode === mode ? "bg-white/20 text-white" : "bg-white/5 text-white/50 hover:bg-white/10"
              }`}
            >
              {mode === "teachers" ? "Учителя" : "Кабинеты"}
            </button>
          ))}
          {(["all", "attention", "free"] as const).map((mode) => (
            <button
              key={mode}
              onClick={() => setFilter(mode)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                filter === mode ? "bg-white/20 text-white" : "bg-white/5 text-white/50 hover:bg-white/10"
              }`}
            >
              {mode === "all" ? "Все" : mode === "attention" ? "Внимание" : "Свободные"}
            </button>
          ))}
        </div>
      </div>

      <div className="flex items-center gap-3 mb-4 text-xs text-white/50 flex-wrap">
        <span>Нагрузка:</span>
        {[0, 0.55, 1].map((value) => (
          <div key={value} className="flex items-center gap-1">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: loadColor(value) }} />
            <span>
              {value === 0 ? "свободно" : value < 1 ? "занято" : "конфликт"}
            </span>
          </div>
        ))}
      </div>

      {rows.length === 0 ? (
        <div className="text-white/40 text-center py-12">
          Нет данных. Сначала запустите генерацию расписания.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <div
            className="grid gap-2 min-w-[1080px]"
            style={{
              gridTemplateColumns: `220px repeat(${days.length * lessons.length}, minmax(36px, 1fr)) 90px`,
            }}
          >
            <div className="text-white/60 text-sm font-medium px-2 py-2">
              {isTeachers ? "Учитель" : "Кабинет"}
            </div>

            {days.map((day) =>
              lessons.map((lesson) => (
                <div
                  key={slotKey(day, lesson)}
                  className="text-center text-[11px] text-white/50 py-2"
                >
                  <div>{DAYS_SHORT[day] ?? day}</div>
                  <div>{lesson}</div>
                </div>
              ))
            )}

            <div className="text-center text-white/60 text-sm font-medium py-2">Итого</div>

            {rows.map((row) => {
              const slotMap = new Map(row.slots.map((slot) => [slotKey(slot.day, slot.lesson), slot]));
              return (
                <Fragment key={`${viewMode}-${row.id}`}>
                  <div
                    className="border-t border-white/5 px-2 py-2 min-h-[56px]"
                  >
                    <div className="text-white/90 font-medium">
                      {"subject" in row ? row.name : row.name}
                    </div>
                    <div className="text-white/40 text-xs">
                      {"subject" in row ? row.subject || "Без предмета" : row.label}
                    </div>
                  </div>

                  {days.map((day) =>
                    lessons.map((lesson) => {
                      const slot = slotMap.get(slotKey(day, lesson)) ?? {
                        day,
                        lesson,
                        count: 0,
                        lessons: 0,
                        load: 0,
                        overload: false,
                        entries: [],
                      };

                      return (
                        <button
                          key={`${viewMode}-${row.id}-${day}-${lesson}`}
                          type="button"
                          className="border-t border-white/5 py-2 px-1"
                          onMouseEnter={(event) => {
                            const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
                            const title = "subject" in row ? row.name : `${row.name} • ${row.label}`;
                            const details = slot.entries.length > 0 ? slot.entries.join("; ") : "Свободно";
                            setTooltip({
                              text: `${title} — ${day}, урок ${lesson}: ${details}`,
                              x: rect.left + rect.width / 2,
                              y: rect.top - 8,
                            });
                          }}
                          onMouseLeave={() => setTooltip(null)}
                        >
                          <div
                            className="rounded h-8 flex items-center justify-center text-white text-[11px] font-bold transition-transform hover:scale-105"
                            style={{
                              backgroundColor: loadColor(slot.load),
                              boxShadow: slot.overload ? "0 0 10px rgba(239,68,68,0.55)" : "none",
                            }}
                          >
                            {slot.count > 0 ? slot.count : "—"}
                          </div>
                        </button>
                      );
                    })
                  )}

                  <div
                    className="border-t border-white/5 py-2 text-center"
                  >
                    <span className="text-sm font-bold text-white/80">
                      {"total_lessons" in row ? row.total_lessons : row.occupied_slots}
                    </span>
                    <div className="text-[10px] text-white/35">
                      {"total_lessons" in row ? `/${row.max_hours}` : `${row.conflict_slots} конф.`}
                    </div>
                  </div>
                </Fragment>
              );
            })}
          </div>
        </div>
      )}

      {tooltip && (
        <div
          className="fixed z-50 bg-gray-900 text-white text-xs px-3 py-1.5 rounded-lg shadow-xl pointer-events-none transform -translate-x-1/2 -translate-y-full max-w-[320px]"
          style={{ left: tooltip.x, top: tooltip.y }}
        >
          {tooltip.text}
        </div>
      )}
    </div>
  );
}
