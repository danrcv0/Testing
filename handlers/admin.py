# ==================== HANDLERS/ADMIN.PY ====================
# Обработчики для администратора

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from datetime import datetime
from database import db
from utils.states import AdminStates
from utils.keyboards import (
    get_admin_keyboard, get_admin_date_list_keyboard, get_admin_schedule_keyboard,
    get_main_keyboard
)
from utils.helpers import parse_time_slots_input
from config import ADMIN_ID, WORK_DAYS
import logging

router = Router()
logger = logging.getLogger(__name__)

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

@router.message(Command("admin"))
async def admin_start_check(message: Message):
    if is_admin(message.from_user.id):
        await message.answer(
            "<b>⚙️ Админ-панель</b>\n\n"
            "Выберите действие:",
            reply_markup=get_admin_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ У вас нет доступа к админ-панели.")

@router.callback_query(F.data == "admin_menu")
async def admin_menu(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа.", show_alert=True)
        return
    
    await state.clear()
    await callback.message.edit_text(
        "<b>⚙️ Админ-панель</b>\n\n"
        "Выберите действие:",
        reply_markup=get_admin_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

# ==================== ДОБАВЛЕНИЕ РАБОЧЕГО ДНЯ ====================

@router.callback_query(F.data == "admin_add_day")
async def admin_add_day(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа.", show_alert=True)
        return
    
    await callback.message.edit_text(
        "<b>➕ Добавить рабочий день</b>\n\n"
        "Введите дату в формате <code>YYYY-MM-DD</code>\n"
        "Например: <code>2024-03-15</code>",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_for_add_day)
    await callback.answer()

@router.message(AdminStates.waiting_for_add_day)
async def handle_add_day(message: Message, state: FSMContext):
    date = message.text.strip()
    
    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        
        if date_obj.weekday() not in WORK_DAYS:
            await message.answer(
                "❌ Выходные дни добавлять нельзя. Выберите рабочий день (Пн-Сб).",
                parse_mode="HTML"
            )
            return
        
        if date_obj.date() < datetime.now().date():
            await message.answer("❌ Нельзя добавлять дни в прошлом.", parse_mode="HTML")
            return
        
        success = await db.add_working_day(date)
        
        if success:
            from utils.helpers import generate_time_slots
            slots = generate_time_slots()
            for slot in slots:
                await db.add_time_slot(date, slot)
            
            formatted_date = date_obj.strftime("%d.%m.%Y")
            await message.answer(
                f"✅ Рабочий день <b>{formatted_date}</b> добавлен с {len(slots)} слотами!",
                parse_mode="HTML"
            )
        else:
            await message.answer("⚠️ Этот день уже добавлен.", parse_mode="HTML")
        
        await state.clear()
        await message.answer(
            "<b>⚙️ Админ-панель</b>\n\n"
            "Выберите действие:",
            reply_markup=get_admin_keyboard(),
            parse_mode="HTML"
        )
        
    except ValueError:
        await message.answer(
            "❌ Неверный формат. Используйте формат <code>YYYY-MM-DD</code>",
            parse_mode="HTML"
        )

# ==================== ДОБАВЛЕНИЕ ВРЕМЕННЫХ СЛОТОВ ====================

@router.callback_query(F.data == "admin_add_slots")
async def admin_add_slots(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа.", show_alert=True)
        return
    
    working_days = await db.get_working_days()
    
    if not working_days:
        await callback.answer(
            "❌ Нет рабочих дней. Сначала добавьте рабочие дни.",
            show_alert=True
        )
        return
    
    await callback.message.edit_text(
        "<b>⏰ Добавить временные слоты</b>\n\n"
        "Выберите дату:",
        reply_markup=get_admin_date_list_keyboard(working_days, "slots"),
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_for_slots_date)
    await callback.answer()

@router.callback_query(AdminStates.waiting_for_slots_date, F.data.startswith("admin_select_date_slots_"))
async def select_slots_date(callback: CallbackQuery, state: FSMContext):
    date = callback.data.replace("admin_select_date_slots_", "")
    await state.update_data(slots_date=date)
    
    existing_slots = await db.get_all_slots(date)
    slots_text = "\n".join(existing_slots) if existing_slots else "Нет слотов"
    
    await callback.message.edit_text(
        f"<b>Напишите новые слоты для {date}:</b>\n\n"
        f"<b>Текущие слоты:</b>\n<code>{slots_text}</code>\n\n"
        f"<b>Формат ввода:</b> <code>10:00 11:00 12:00 13:00...</code>",
        parse_mode="HTML"
    )
    
    await state.set_state(AdminStates.waiting_for_time_slots)
    await callback.answer()

@router.message(AdminStates.waiting_for_time_slots)
async def handle_time_slots(message: Message, state: FSMContext):
    slots = parse_time_slots_input(message.text)
    
    if not slots:
        await message.answer(
            "❌ Не найдены слоты. Используйте формат <code>10:00 11:00 12:00</code>",
            parse_mode="HTML"
        )
        return
    
    data = await state.get_data()
    date = data.get("slots_date")
    
    available_slots = await db.get_available_slots(date)
    
    for slot in available_slots:
        await db.delete_time_slot(date, slot)
    
    for slot in slots:
        await db.add_time_slot(date, slot)
    
    await message.answer(
        f"✅ Слоты для {date} обновлены!\n\n"
        f"<b>Новые слоты ({len(slots)}):</b>\n"
        f"<code>{'  '.join(slots)}</code>",
        parse_mode="HTML"
    )
    
    await state.clear()
    await message.answer(
        "<b>⚙️ Админ-панель</b>\n\n"
        "Выберите действие:",
        reply_markup=get_admin_keyboard(),
        parse_mode="HTML"
    )

# ==================== ПРОСМОТР РАСПИСАНИЯ ====================

@router.callback_query(F.data == "admin_view_schedule")
async def admin_view_schedule(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа.", show_alert=True)
        return
    
    working_days = await db.get_working_days()
    
    if not working_days:
        await callback.answer("❌ Нет рабочих дней.", show_alert=True)
        return
    
    await callback.message.edit_text(
        "<b>🔍 Просмотр расписания</b>\n\n"
        "Выберите дату:",
        reply_markup=get_admin_date_list_keyboard(working_days, "view"),
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_for_view_date)
    await callback.answer()

@router.callback_query(AdminStates.waiting_for_view_date, F.data.startswith("admin_select_date_view_"))
async def handle_view_schedule(callback: CallbackQuery, state: FSMContext):
    date = callback.data.replace("admin_select_date_view_", "")
    bookings = await db.get_bookings_for_date(date)
    
    if not bookings:
        await callback.message.edit_text(
            "<b>📅 На эту дату нет записей.</b>",
            reply_markup=get_admin_date_list_keyboard([date], "view"),
            parse_mode="HTML"
        )
    else:
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%d.%m.%Y")
        except:
            formatted_date = date
        
        schedule_text = f"<b>📅 Расписание на {formatted_date}:</b>\n\n"
        
        for booking_id, time, name, phone in bookings:
            schedule_text += f"<b>{time}</b> — {name} ({phone})\n"
        
        all_slots = await db.get_all_slots(date)
        available_slots = await db.get_available_slots(date)
        booked_count = len(all_slots) - len(available_slots)
        
        schedule_text += f"\n<i>Занято: {booked_count}/{len(all_slots)} слотов</i>"
        
        await callback.message.edit_text(
            schedule_text,
            reply_markup=get_admin_schedule_keyboard(bookings, date),
            parse_mode="HTML"
        )
    
    await callback.answer()

@router.callback_query(F.data.startswith("admin_cancel_booking_"))
async def admin_cancel_booking(callback: CallbackQuery, bot):
    booking_id = int(callback.data.replace("admin_cancel_booking_", ""))
    await db.cancel_booking(booking_id)
    
    try:
        from main import scheduler
        scheduler.remove_job(f"reminder_{booking_id}")
    except:
        pass
    
    await callback.answer("✅ Запись отменена.", show_alert=True)
    await callback.message.edit_text(
        "<b>⚙️ Админ-панель</b>\n\n"
        "Выберите действие:",
        reply_markup=get_admin_keyboard(),
        parse_mode="HTML"
    )

# ==================== ЗАКРЫТИЕ ДНЯ ====================

@router.callback_query(F.data == "admin_close_day")
async def admin_close_day(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа.", show_alert=True)
        return
    
    working_days = await db.get_working_days()
    
    if not working_days:
        await callback.answer("❌ Нет рабочих дней.", show_alert=True)
        return
    
    await callback.message.edit_text(
        "<b>❌ Закрыть день</b>\n\n"
        "Выберите дату:",
        reply_markup=get_admin_date_list_keyboard(working_days, "close"),
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_for_close_day)
    await callback.answer()

@router.callback_query(AdminStates.waiting_for_close_day, F.data.startswith("admin_select_date_close_"))
async def handle_close_day(callback: CallbackQuery, state: FSMContext):
    date = callback.data.replace("admin_select_date_close_", "")
    success = await db.close_day(date)
    
    if success:
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%d.%m.%Y")
        except:
            formatted_date = date
        
        await callback.message.edit_text(
            f"✅ День <b>{formatted_date}</b> закрыт.",
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            "❌ Ошибка при закрытии дня.",
            parse_mode="HTML"
        )
    
    await state.clear()
    
    import asyncio
    await asyncio.sleep(1)
    
    await callback.message.edit_text(
        "<b>⚙️ Админ-панель</b>\n\n"
        "Выберите действие:",
        reply_markup=get_admin_keyboard(),
        parse_mode="HTML"
    )

# ==================== ОТКРЫТИЕ ЗАКРЫТОГО ДНЯ ====================

@router.callback_query(F.data == "admin_open_day")
async def admin_open_day(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа.", show_alert=True)
        return
    
    await callback.message.edit_text(
        "<b>✅ Открыть день</b>\n\n"
        "Введите дату в формате <code>YYYY-MM-DD</code>",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_for_open_day)
    await callback.answer()

@router.message(AdminStates.waiting_for_open_day)
async def handle_open_day(message: Message, state: FSMContext):
    date = message.text.strip()
    
    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        success = await db.open_day(date)
        
        if success:
            formatted_date = date_obj.strftime("%d.%m.%Y")
            await message.answer(
                f"✅ День <b>{formatted_date}</b> открыт.",
                parse_mode="HTML"
            )
        else:
            await message.answer("❌ Ошибка при открытии дня.", parse_mode="HTML")
        
        await state.clear()
        await message.answer(
            "<b>⚙️ Админ-панель</b>\n\n"
            "Выберите действие:",
            reply_markup=get_admin_keyboard(),
            parse_mode="HTML"
        )
        
    except ValueError:
        await message.answer(
            "❌ Неверный формат. Используйте формат <code>YYYY-MM-DD</code>",
            parse_mode="HTML"
        )
