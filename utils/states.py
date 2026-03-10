# ==================== UTILS/STATES.PY ====================
# FSM (Finite State Machine) состояния

from aiogram.fsm.state import State, StatesGroup

class BookingStates(StatesGroup):
    """Состояния для бронирования"""
    waiting_for_date = State()              # Ожидание выбора даты
    waiting_for_time = State()              # Ожидание выбора времени
    waiting_for_name = State()              # Ожидание ввода имени
    waiting_for_phone = State()             # Ожидание ввода номера телефона
    waiting_for_confirmation = State()      # Ожидание подтверждения

class SubscriptionStates(StatesGroup):
    """Состояния для проверки подписки"""
    waiting_for_subscription_check = State()

class AdminStates(StatesGroup):
    """Состояния для админ-панели"""
    waiting_for_add_day = State()           # Ожидание добавления дня
    waiting_for_slots_date = State()        # Ожидание выбора даты для слотов
    waiting_for_time_slots = State()        # Ожидание ввода временных слотов
    waiting_for_close_day = State()         # Ожидание выбора дня для закрытия
    waiting_for_open_day = State()          # Ожидание выбора дня для открытия
    waiting_for_view_date = State()         # Ожидание выбора даты для просмотра
