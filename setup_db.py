import sqlite3
import os

def setup():
    # Основной путь к базе данных
    db_path = 'ai_orchestrator/backend/orchestrator.db'
    if not os.path.exists(db_path):
        # Fallback если запуск не из корня
        db_path = 'backend/orchestrator.db'
    
    if not os.path.exists(db_path):
        print(f"❌ База данных {db_path} не найдена!")
        return

    print(f"🔄 Подключение к основной базе: {db_path}")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # --- 1. ОЧИСТКА СООБЩЕНИЙ ---
    try:
        cur.execute("DELETE FROM tg_messages")
        print("✅ Таблица сообщений (tg_messages) очищена.")
    except Exception:
        pass
        
    # --- 2. ИНИЦИАЛИЗАЦИЯ 3-СТАДИЙНОГО ФИДБЕКА ---
    try:
        # Очищаем старые задачи
        cur.execute("DELETE FROM task_reminders")
        
        tasks = [
            # Стадия 1: Запрос (is_accepted=0, is_completed=0)
            ("Подготовить актовый зал к AIS Hack 3.0", "Гульнара", "Сегодня", 0, 0),
            ("Заказать 20 бутылей воды", "Мадина", "Завтра", 0, 0),

            # Стадия 2: В обработке (is_accepted=1, is_completed=0)
            ("Починить замок на запасном выходе", "Серик", "Сегодня", 1, 0),
            ("Организовать замену: Математика", "Директор", "Срочно", 1, 0),
            ("Проанализировать посещаемость", "Секретарь", "Пятница", 1, 0),

            # Стадия 3: Выполнено (is_completed=1)
            ("Снять показания счетчиков", "Серик", "Среда", 1, 1),
            ("Разослать письмо родителям 4Б", "Петрова О.", "Сегодня", 1, 1)
        ]
        
        cur.executemany(
            "INSERT INTO task_reminders (title, assignee, deadline, is_accepted, is_completed) VALUES (?, ?, ?, ?, ?)", 
            tasks
        )
        print("✅ Система фидбека (3 стадии) успешно инициализирована!")
    except Exception as e:
        print(f"❌ Ошибка при настройке задач: {e}")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    setup()
