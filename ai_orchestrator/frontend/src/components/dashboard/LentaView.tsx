import { useEffect, useState } from "react";
import axios from "axios";

const API_BASE = `http://${window.location.hostname}:8000/api`;

const LEVEL_COLORS: Record<string, string> = {
  "Beginner": "bg-blue-500/20 border-blue-500/40 text-blue-300",
  "Pre-Intermediate": "bg-green-500/20 border-green-500/40 text-green-300",
  "Intermediate": "bg-yellow-500/20 border-yellow-500/40 text-yellow-300",
  "Upper-Intermediate": "bg-red-500/20 border-red-500/40 text-red-300",
};

const DAYS = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница"];
const DAYS_SHORT: Record<string, string> = {
  "Понедельник": "Пн", "Вторник": "Вт", "Среда": "Ср",
  "Четверг": "Чт", "Пятница": "Пт",
};

interface LentaGroup {
  id: number;
  group_name: string;
  level: number;
  teacher: string | null;
  room: string | null;
}

interface ParallelData {
  id: number;
  grade: number;
  has_lenta: boolean;
  lenta_subject: string | null;
  classes: string[];
  lenta_groups: LentaGroup[];
}

interface TimeSlotItem {
  id: number;
  day: string;
  lesson: number;
  start_time: string;
  end_time: string;
}

interface Props {
  className?: string;
}

export default function LentaView({ className = "" }: Props) {
  const [parallels, setParallels] = useState<ParallelData[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [message, setMessage] = useState<{ text: string; ok: boolean } | null>(null);

  // Form state
  const [selectedParallel, setSelectedParallel] = useState<number | null>(null);
  const [selectedDay, setSelectedDay] = useState("Вторник");
  const [selectedLesson, setSelectedLesson] = useState(3);

  // Time slots map (fetched dynamically)
  const [timeSlots, setTimeSlots] = useState<Record<string, Record<number, number>>>({});

  useEffect(() => {
    fetchParallels();
    fetchTimeSlots();
  }, []);

  async function fetchParallels() {
    try {
      const r = await axios.get(`${API_BASE}/schedule/parallels`);
      const lentaParallels = r.data.parallels.filter((p: ParallelData) => p.has_lenta);
      setParallels(lentaParallels);
      if (lentaParallels.length > 0) setSelectedParallel(lentaParallels[0].id);
    } catch {
      setParallels([]);
    } finally {
      setLoading(false);
    }
  }

  async function fetchTimeSlots() {
    const fallback = () => {
      const map: Record<string, Record<number, number>> = {};
      const dayIndex: Record<string, number> = {
        "Понедельник": 0, "Вторник": 1, "Среда": 2, "Четверг": 3, "Пятница": 4,
      };
      for (const day of DAYS) {
        map[day] = {};
        for (let lesson = 1; lesson <= 6; lesson++) {
          map[day][lesson] = dayIndex[day] * 6 + lesson;
        }
      }
      return map;
    };

    try {
      const r = await axios.get(`${API_BASE}/schedule/time-slots`);
      const map: Record<string, Record<number, number>> = {};
      (r.data.time_slots as TimeSlotItem[]).forEach((slot) => {
        if (!map[slot.day]) map[slot.day] = {};
        map[slot.day][slot.lesson] = slot.id;
      });
      setTimeSlots(Object.keys(map).length > 0 ? map : fallback());
    } catch {
      setTimeSlots(fallback());
    }
  }

  async function handleCreateLenta() {
    if (!selectedParallel) return;
    const slotId = timeSlots[selectedDay]?.[selectedLesson];
    if (!slotId) {
      setMessage({ text: "Не удалось определить временной слот", ok: false });
      return;
    }

    setCreating(true);
    setMessage(null);
    try {
      const r = await axios.post(`${API_BASE}/schedule/lenta-v2`, {
        parallel_id: selectedParallel,
        time_slot_id: slotId,
      });
      if (r.data.ok) {
        setMessage({ text: r.data.message, ok: true });
        fetchParallels();
      } else {
        setMessage({
          text: "Конфликты: " + r.data.conflicts.join("; "),
          ok: false,
        });
      }
    } catch (e: any) {
      setMessage({ text: e.response?.data?.detail ?? "Ошибка создания ленты", ok: false });
    } finally {
      setCreating(false);
    }
  }

  const activeParallel = parallels.find((p) => p.id === selectedParallel);

  if (loading) {
    return (
      <div className={`flex items-center justify-center h-40 ${className}`}>
        <div className="text-white/50 animate-pulse">Загружаем параллели...</div>
      </div>
    );
  }

  return (
    <div className={className}>
      <div className="mb-4">
        <h2 className="text-white font-bold text-lg">Система лент</h2>
        <p className="text-white/50 text-sm">
          Кросс-классовое уровневое деление параллели на группы
        </p>
      </div>

      {/* Explanation card */}
      <div className="bg-white/5 border border-white/10 rounded-xl p-4 mb-5 text-sm text-white/60">
        <span className="text-white/80 font-medium">Как работает лента: </span>
        Все классы параллели одновременно снимаются с уроков и делятся на уровневые группы.
        Например, 3А + 3Б + 3В = 75 учеников → 4 группы по уровню английского в 4 кабинетах.
        Система автоматически блокирует этот слот для всех классов параллели.
      </div>

      {parallels.length === 0 ? (
        <div className="text-white/40 text-center py-12">
          Нет параллелей с системой лент. Проверьте настройки БД.
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {/* Левая часть: выбор и настройка */}
          <div>
            <div className="bg-white/5 border border-white/10 rounded-xl p-4 space-y-4">
              <div>
                <label className="text-white/60 text-xs mb-1.5 block">Параллель</label>
                <div className="flex gap-2 flex-wrap">
                  {parallels.map((p) => (
                    <button
                      key={p.id}
                      onClick={() => setSelectedParallel(p.id)}
                      className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                        selectedParallel === p.id
                          ? "bg-purple-500/30 border border-purple-400/50 text-purple-200"
                          : "bg-white/5 border border-white/10 text-white/60 hover:bg-white/10"
                      }`}
                    >
                      {p.grade} класс
                      <span className="text-xs ml-1 opacity-60">
                        ({p.classes.join(", ")})
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-white/60 text-xs mb-1.5 block">День недели</label>
                  <select
                    value={selectedDay}
                    onChange={(e) => setSelectedDay(e.target.value)}
                    className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-purple-400"
                  >
                    {DAYS.map((d) => (
                      <option key={d} value={d} className="bg-gray-800">
                        {d}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-white/60 text-xs mb-1.5 block">Урок</label>
                  <select
                    value={selectedLesson}
                    onChange={(e) => setSelectedLesson(Number(e.target.value))}
                    className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-purple-400"
                  >
                    {[1, 2, 3, 4, 5, 6].map((n) => (
                      <option key={n} value={n} className="bg-gray-800">
                        {n}-й урок
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <button
                onClick={handleCreateLenta}
                disabled={creating || !selectedParallel}
                className="w-full py-2.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 disabled:opacity-50 text-white rounded-xl font-medium text-sm transition-all"
              >
                {creating ? "Создаём ленту..." : `Забронировать ${DAYS_SHORT[selectedDay]} урок ${selectedLesson}`}
              </button>

              {message && (
                <div
                  className={`p-3 rounded-lg text-sm ${
                    message.ok
                      ? "bg-green-500/15 border border-green-500/30 text-green-300"
                      : "bg-red-500/15 border border-red-500/30 text-red-300"
                  }`}
                >
                  {message.ok ? "✅ " : "⚠️ "}
                  {message.text}
                </div>
              )}
            </div>
          </div>

          {/* Правая часть: группы выбранной параллели */}
          <div>
            {activeParallel && (
              <div className="space-y-3">
                <div className="text-white/60 text-xs font-medium uppercase tracking-wider">
                  Группы {activeParallel.grade}-й параллели • {activeParallel.lenta_subject}
                </div>
                {activeParallel.lenta_groups.length === 0 ? (
                  <div className="text-white/30 text-sm text-center py-8 border border-white/10 rounded-xl">
                    Группы не настроены
                  </div>
                ) : (
                  activeParallel.lenta_groups
                    .sort((a, b) => a.level - b.level)
                    .map((group) => (
                      <div
                        key={group.id}
                        className={`border rounded-xl p-3 flex items-center justify-between ${
                          LEVEL_COLORS[group.group_name] ??
                          "bg-white/5 border-white/10 text-white/70"
                        }`}
                      >
                        <div>
                          <div className="font-medium text-sm">{group.group_name}</div>
                          <div className="text-xs opacity-70 mt-0.5">
                            Уровень {group.level}
                          </div>
                        </div>
                        <div className="text-right text-xs">
                          <div className="opacity-80">
                            👤 {group.teacher ?? "Не назначен"}
                          </div>
                          <div className="opacity-60 mt-0.5">
                            🚪 каб. {group.room ?? "—"}
                          </div>
                        </div>
                      </div>
                    ))
                )}

                {/* Классы параллели */}
                <div className="bg-white/5 border border-white/10 rounded-xl p-3">
                  <div className="text-white/50 text-xs mb-2">Классы в параллели:</div>
                  <div className="flex gap-2 flex-wrap">
                    {activeParallel.classes.map((c) => (
                      <span
                        key={c}
                        className="px-2 py-0.5 bg-white/10 rounded text-white/80 text-xs"
                      >
                        {c}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
