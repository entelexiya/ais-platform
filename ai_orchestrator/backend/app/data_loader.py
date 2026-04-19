import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOCK_DIR = os.path.join(BASE_DIR, "data", "mock")

def load_staff() -> list:
    """Загрузка базы сотрудников из Excel."""
    file_path = os.path.join(MOCK_DIR, "нагрузка учителей для хакатона 2025-2026.xlsx")
    if not os.path.exists(file_path):
        print(f"Staff file not found: {file_path}")
        return []
    try:
        df = pd.read_excel(file_path)
        # Нормализуем названия колонок к тому, что ожидает scheduler.py
        df = df.rename(columns={
            "ФИО": "ФИО",
            "Предмет": "Предмет",
            "Должность": "Должность",
            "Квалификация": "Квалификация",
        })
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"Error loading staff: {e}")
        return []

def load_schedule() -> list:
    """Загрузка расписания из Excel."""
    file_path = os.path.join(MOCK_DIR, "для хакатона расписание.xlsx")
    if not os.path.exists(file_path):
        print(f"Schedule file not found: {file_path}")
        return []
    try:
        df = pd.read_excel(file_path)
        # Нормализуем к именам, которые ожидает scheduler.py
        df = df.rename(columns={
            "День": "День",
            "Класс": "Класс",
            "Урок": "Урок",
            "Учитель": "Учитель",
            "Предмет": "Предмет",
            "Кабинет": "Кабинет",
        })
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"Error loading schedule: {e}")
        return []
