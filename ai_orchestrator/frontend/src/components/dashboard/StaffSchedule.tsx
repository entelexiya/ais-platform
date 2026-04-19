import { useEffect, useState } from "react";
import axios from "axios";

const API_BASE = `http://${window.location.hostname}:8000/api`;

const DAYS_SHORT: Record<string, string> = {
  "Понедельник": "Пн", "Вторник": "Вт", "Среда": "Ср",
  "Четверг": "Чт", "Пятница": "Пт",
};

const TYPE_STYLES: Record<string, string> = {
  lesson: "bg-blue-500/20 border-blue-500/30 text-blue-200",
  duty: "bg-yellow-500/20 border-yellow-500/30 text-yellow-200",
  meeting: "bg-purple-500/20 border-purple-500/30 text-purple-200",
  task: "bg-orange-500/20 border-orange-500/30 text-orange-200",
  free: "bg-white/5 border-white/10 text-white/30",
};

interface StaffItem {
  id: number;
  full_name: string;
  short_name: string;
  role: string;
  subject: string | null;
}

interface SlotItem {
  day: string;
  lesson: number;
  start_time: string;
  end_time: string;
  type: string;
  icon: string;
  description: string;
  subject?: string;
  class_name?: string;
  room?: string;
  is_substitution?: boolean;
}

interface DayData {
  day: string;
  slots: SlotItem[];
}

interface ScheduleData {
  staff_id: number;
  name: string;
  short_name: string;
  role: string;
  subject: string | null;
  max_hours_per_week: number;
  total_lessons_this_week: number;
  total_tasks_this_week: number;
  week: DayData[];
}

interface Props {
  className?: string;
}

export default function StaffSchedule({ className = "" }: Props) {
  const [staffList, setStaffList] = useState<StaffItem[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [schedule, setSchedule] = useState<ScheduleData | null>(null);
  const [loadingSched, setLoadingSched] = useState(false);
  const [roleFilter, setRoleFilter] = useState<string>("all");

  useEffect(() => {
    axios
      .get(`${API_BASE}/schedule/staff`)
      .then((r) => {
        setStaffList(r.data.staff ?? []);
        if (r.data.staff?.length > 0) setSelectedId(r.data.staff[0].id);
      })
      .catch(() => setStaffList([]));
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    setLoadingSched(true);
    axios
      .get(`${API_BASE}/schedule/staff/${selectedId}/week`)
      .then((r) => setSchedule(r.data))
      .catch(() => setSchedule(null))
      .finally(() => setLoadingSched(false));
  }, [selectedId]);

  const roles = ["all", ...Array.from(new Set(staffList.map((s) => s.role)))];
  const filtered = roleFilter === "all"
    ? staffList
    : staffList.filter((s) => s.role === roleFilter);

  return (
    <div className={`flex gap-4 h-full ${className}`}>
      {/* Левая панель — список сотрудников */}
      <div className="w-56 flex-shrink-0 space-y-2">
        <div>
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            className="w-full bg-white/10 border border-white/20 rounded-lg px-2 py-1.5 text-white text-xs focus:outline-none focus:border-purple-400 mb-2"
          >
            {roles.map((r) => (
              <option key={r} value={r} className="bg-gray-800">
                {r === "all" ? "Все роли" : r}
              </option>
            ))}
          </select>
        </div>
        <div className="space-y-1 max-h-[70vh] overflow-y-auto pr-1">
          {filtered.map((s) => (
            <button
              key={s.id}
              onClick={() => setSelectedId(s.id)}
              className={`w-full text-left px-3 py-2 rounded-lg transition-all ${
                selectedId === s.id
                  ? "bg-white/15 border border-white/25 text-white"
                  : "bg-white/5 border border-transparent text-white/60 hover:bg-white/10"
              }`}
            >
              <div className="font-medium text-xs leading-tight">
                {s.short_name || s.full_name}
              </div>
              <div className="text-xs opacity-50 mt-0.5">{s.role}</div>
              {s.subject && (
                <div className="text-xs opacity-40">{s.subject}</div>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Правая часть — расписание */}
      <div className="flex-1 min-w-0">
        {loadingSched ? (
          <div className="flex items-center justify-center h-40">
            <div className="text-white/40 animate-pulse">Загружаем расписание...</div>
          </div>
        ) : !schedule ? (
          <div className="flex items-center justify-center h-40">
            <div className="text-white/30">Выберите сотрудника</div>
          </div>
        ) : (
          <div>
            {/* Шапка сотрудника */}
            <div className="flex flex-wrap items-start justify-between gap-3 mb-4">
              <div>
                <h2 className="text-white font-bold text-base">{schedule.name}</h2>
                <div className="text-white/50 text-xs mt-0.5">
                  {schedule.role}{schedule.subject ? ` • ${schedule.subject}` : ""}
                </div>
              </div>
              <div className="flex gap-3 text-xs">
                <div className="bg-blue-500/15 border border-blue-500/25 rounded-lg px-3 py-1.5 text-center">
                  <div className="text-blue-300 font-bold text-lg leading-none">
                    {schedule.total_lessons_this_week}
                  </div>
                  <div className="text-white/40 mt-0.5">уроков/нед</div>
                </div>
                {schedule.total_tasks_this_week > 0 && (
                  <div className="bg-orange-500/15 border border-orange-500/25 rounded-lg px-3 py-1.5 text-center">
                    <div className="text-orange-300 font-bold text-lg leading-none">
                      {schedule.total_tasks_this_week}
                    </div>
                    <div className="text-white/40 mt-0.5">задач</div>
                  </div>
                )}
                <div className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-center">
                  <div className="text-white/60 font-bold text-lg leading-none">
                    {schedule.max_hours_per_week}
                  </div>
                  <div className="text-white/30 mt-0.5">макс/нед</div>
                </div>
              </div>
            </div>

            {/* Сетка расписания */}
            <div className="overflow-x-auto">
              <div
                className="grid gap-2"
                style={{
                  gridTemplateColumns: `48px repeat(5, minmax(120px, 1fr))`,
                }}
              >
                {/* Заголовки дней */}
                <div />
                {schedule.week.map((d) => (
                  <div
                    key={d.day}
                    className="text-center text-white/60 text-xs font-medium pb-1"
                  >
                    {DAYS_SHORT[d.day] ?? d.day}
                  </div>
                ))}

                {/* Строки по урокам */}
                {[1, 2, 3, 4, 5, 6].map((lessonNum) => (
                  <>
                    <div
                      key={`label-${lessonNum}`}
                      className="flex items-start justify-center pt-2"
                    >
                      <span className="text-white/30 text-xs font-bold">{lessonNum}</span>
                    </div>
                    {schedule.week.map((dayData) => {
                      const slot = dayData.slots.find((s) => s.lesson === lessonNum);
                      if (!slot || slot.type === "free") {
                        return (
                          <div
                            key={`${dayData.day}-${lessonNum}`}
                            className="rounded-lg border border-white/5 bg-white/[0.02] p-2 min-h-[56px] flex items-center justify-center"
                          >
                            <span className="text-white/15 text-xs">—</span>
                          </div>
                        );
                      }
                      return (
                        <div
                          key={`${dayData.day}-${lessonNum}`}
                          className={`rounded-lg border p-2 min-h-[56px] text-xs ${
                            TYPE_STYLES[slot.type] ?? TYPE_STYLES.free
                          } ${slot.is_substitution ? "ring-1 ring-yellow-400/50" : ""}`}
                        >
                          <div className="flex items-center gap-1 mb-1">
                            <span>{slot.icon}</span>
                            <span className="font-medium leading-tight line-clamp-2">
                              {slot.description}
                            </span>
                          </div>
                          {slot.class_name && (
                            <div className="opacity-60 text-[11px]">
                              {slot.class_name}
                              {slot.room ? ` • каб. ${slot.room}` : ""}
                            </div>
                          )}
                          {slot.start_time && (
                            <div className="opacity-40 text-[10px] mt-0.5">
                              {slot.start_time}–{slot.end_time}
                            </div>
                          )}
                          {slot.is_substitution && (
                            <div className="text-yellow-300/80 text-[10px] mt-0.5">
                              ⚡ замена
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </>
                ))}
              </div>
            </div>

            {/* Легенда */}
            <div className="flex flex-wrap gap-3 mt-4 text-xs text-white/40">
              {Object.entries({ lesson: "📚 Урок", duty: "🚶 Дежурство", meeting: "👥 Встреча/совещание", task: "🔧 Задача" }).map(([k, v]) => (
                <div key={k} className="flex items-center gap-1.5">
                  <div className={`w-3 h-3 rounded border ${TYPE_STYLES[k]}`} />
                  {v}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
