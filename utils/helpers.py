# ==================== UTILS/HELPERS.PY ====================
# Вспомогательные функции

from datetime import datetime, timedelta
from config import WORK_START_HOUR, WORK_END_HOUR, SLOT_DURATION, DATABASE_NAME
import sqlite3

def generate_time_slots(start_hour: int = WORK_START_HOUR, 
                       end_hour: int = WORK_END_HOUR, 
                       duration: int = SLOT_DURATION) -> list:
    """Генерирует список временных слотов"""
    slots = []
    current_time = datetime.strptime(f"{start_hour:02d}:00", "%H:%M")
    end_time = datetime.strptime(f"{end_hour:02d}:00", "%H:%M")
    
    while current_time < end_time:
        slots.append(current_time.strftime("%H:%M"))
        current_time += timedelta(minutes=duration)
    
    return slots

def get_prices_text() -> str:
    """Возвращает текст с ценами"""
    from config import PRICES
    
    text = "<b>💰 Наши прайсы:</b>\n\n"
    
    return text

def format_booking_info(date: str, time: str, name: str, phone: str) -> str:
    """Форматирует информацию о бронировании"""
    from datetime import datetime
    
    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%d.%m.%Y")
    except:
        formatted_date = date
    
    text = (
        f"<b>📋 Информация о записи:</b>\n\n"
        f"<b>Дата:</b> {formatted_date}\n"
        f"<b>Время:</b> {time}\n"
        f"<b>Имя:</b> {name}\n"
        f"<b>Номер телефона:</b> {phone}\n"
    )
    
    return text

def format_schedule_message(date: str, bookings: list) -> str:
    """Форматирует сообщение с расписанием для канала"""
    from datetime import datetime
    
    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%d.%m.%Y (%A)")
    except:
        formatted_date = date
    
    text = f"<b>📅 Расписание на {formatted_date}:</b>\n\n"
    
    if bookings:
        for time, name, phone in bookings:
            text += f"<b>{time}</b> — {name} ({phone})\n"
    else:
        text += "<i>Нет записей</i>\n"
    
    return text

def get_next_month(year: int, month: int) -> tuple:
    """Получить следующий месяц"""
    if month == 12:
        return year + 1, 1
    return year, month + 1

def get_prev_month(year: int, month: int) -> tuple:
    """Получить предыдущий месяц"""
    if month == 1:
        return year - 1, 12
    return year, month - 1

def parse_time_slots_input(text: str) -> list:
    """Парсит введённые временные слоты (формат: 10:00 11:00 12:00 13:00...)"""
    slots = []
    parts = text.split()
    
    for part in parts:
        if ':' in part:
            try:
                # Проверяем формат HH:MM
                datetime.strptime(part, "%H:%M")
                slots.append(part)
            except:
                pass
    
    return slots

def is_valid_phone(phone: str) -> bool:
    """Проверяет формат номера телефона"""
    # Удаляем пробелы и спецсимволы
    cleaned = ''.join(c for c in phone if c.isdigit())
    # Проверяем, что минимум 10 цифр
    return len(cleaned) >= 10

def clear_old_reminders():
    """Очищает старые напоминания из БД (более месяца назад)"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    # Удаляем напоминания старше месяца
    one_month_ago = (datetime.now() - timedelta(days=30)).isoformat()
    cursor.execute(
        'DELETE FROM reminders WHERE reminder_date < ? AND is_sent = 1',
        (one_month_ago,)
    )
    
    conn.commit()
    conn.close()
