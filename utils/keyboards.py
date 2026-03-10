# ==================== UTILS/KEYBOARDS.PY ====================
# Клавиатуры для бота

from datetime import datetime, timedelta
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import WORK_DAYS, CHANNEL_LINK, PORTFOLIO_LINK, PRICES

def get_main_keyboard() -> InlineKeyboardMarkup:
    """Главное меню"""
    keyboard = [
        [InlineKeyboardButton(text="📅 Записаться на приём", callback_data="book_appointment")],
        [InlineKeyboardButton(text="💅 Мои записи", callback_data="my_bookings")],
        [InlineKeyboardButton(text="💰 Прайсы", callback_data="show_prices")],
        [InlineKeyboardButton(text="🎨 Портфолио", callback_data="show_portfolio")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_subscribe_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для подписки на канал"""
    keyboard = [
        [InlineKeyboardButton(text="🌸 Маша | Мастер маникюра", url=CHANNEL_LINK)],
        [InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_subscription")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_prices_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура прайсов"""
    keyboard = [
        [InlineKeyboardButton(text="📅 Записаться на приём", callback_data="book_appointment")],
        [InlineKeyboardButton(text="💅 Мои записи", callback_data="my_bookings")],
        [InlineKeyboardButton(text="🎨 Портфолио", callback_data="show_portfolio")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_portfolio_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура портфолио"""
    keyboard = [
        [InlineKeyboardButton(text="🎨 Смотреть портфолио", url=PORTFOLIO_LINK)],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_calendar_keyboard(year: int, month: int, db) -> InlineKeyboardMarkup:
    """Календарь для выбора даты (inline кнопки)"""
    keyboard = []

    month_names = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                   "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]

    nav_row = [
        InlineKeyboardButton(text="◀️", callback_data=f"prev_month_{year}_{month}"),
        InlineKeyboardButton(text=f"{month_names[month-1]} {year}", callback_data="ignore"),
        InlineKeyboardButton(text="▶️", callback_data=f"next_month_{year}_{month}"),
    ]
    keyboard.append(nav_row)

    days_header = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    keyboard.append([InlineKeyboardButton(text=day, callback_data="ignore") for day in days_header])

    first_day = datetime(year, month, 1)

    if month == 12:
        last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = datetime(year, month + 1, 1) - timedelta(days=1)

    offset = first_day.weekday()

    days = []

    for _ in range(offset):
        days.append(InlineKeyboardButton(text=" ", callback_data="ignore"))

    today = datetime.now().date()

    for day in range(1, last_day.day + 1):
        date_obj = datetime(year, month, day).date()
        date_str = date_obj.isoformat()

        # проверяем закрытый день
        is_closed = db._is_day_closed(date_str)

        if (
            date_obj >= today
            and date_obj.weekday() in WORK_DAYS
            and not is_closed
        ):
            days.append(
                InlineKeyboardButton(
                    text=str(day),
                    callback_data=f"select_date_{date_str}"
                )
            )
        else:
            days.append(
                InlineKeyboardButton(text=" ", callback_data="ignore")
            )

    for i in range(0, len(days), 7):
        keyboard.append(days[i:i+7])

    keyboard.append([
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_booking_process")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_time_slots_keyboard(time_slots: list) -> InlineKeyboardMarkup:
    """Клавиатура с выбором времени"""
    keyboard = []
    
    # Добавляем слоты по 2 в строку
    for i in range(0, len(time_slots), 2):
        row = []
        for slot in time_slots[i:i+2]:
            row.append(InlineKeyboardButton(
                text=slot,
                callback_data=f"select_time_{slot}"
            ))
        keyboard.append(row)
    
    # Кнопка "Назад"
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_calendar")])
    keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_booking_process")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_confirm_booking_keyboard() -> InlineKeyboardMarkup:
    """Подтверждение бронирования"""
    keyboard = [
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_booking")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_booking_process")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_my_bookings_keyboard(has_booking: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура для просмотра моих записей"""
    keyboard = []
    
    if has_booking:
        keyboard.append([InlineKeyboardButton(text="❌ Отменить запись", callback_data="cancel_my_booking")])
    
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Админ меню"""
    keyboard = [
        [InlineKeyboardButton(text="➕ Добавить рабочий день", callback_data="admin_add_day")],
        [InlineKeyboardButton(text="⏰ Добавить временные слоты", callback_data="admin_add_slots")],
        [InlineKeyboardButton(text="🔍 Просмотреть расписание", callback_data="admin_view_schedule")],
        [InlineKeyboardButton(text="❌ Закрыть день", callback_data="admin_close_day")],
        [InlineKeyboardButton(text="✅ Открыть день", callback_data="admin_open_day")],
        [InlineKeyboardButton(text="🔙 Вернуться", callback_data="back_to_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_admin_date_list_keyboard(dates: list, action: str) -> InlineKeyboardMarkup:
    """Клавиатура со списком дат для админа"""
    keyboard = []
    
    for date in dates[:31]:  # Максимум 31 день
        keyboard.append([InlineKeyboardButton(
            text=date,
            callback_data=f"admin_select_date_{action}_{date}"
        )])
    
    keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data="admin_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_admin_schedule_keyboard(bookings: list, date: str) -> InlineKeyboardMarkup:
    """Клавиатура для просмотра расписания (с возможностью отмены)"""
    keyboard = []
    
    for booking_id, time, name, phone in bookings:
        keyboard.append([InlineKeyboardButton(
            text=f"{time} - {name}",
            callback_data=f"admin_cancel_booking_{booking_id}"
        )])
    
    keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data="admin_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
