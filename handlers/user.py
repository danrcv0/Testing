# ==================== HANDLERS/USER.PY ====================
# Обработчики для обычных пользователей

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ChatMember, FSInputFile,InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from datetime import datetime, timedelta
from database import db
from pathlib import Path
import os
from utils.states import BookingStates, SubscriptionStates
from utils.keyboards import (
    get_main_keyboard, get_calendar_keyboard, get_time_slots_keyboard,
    get_confirm_booking_keyboard, get_my_bookings_keyboard, get_subscribe_keyboard,
    get_prices_keyboard, get_portfolio_keyboard
)
from utils.helpers import (
    generate_time_slots, get_prices_text, format_booking_info, 
    is_valid_phone, get_next_month, get_prev_month
)
from config import (
    ADMIN_ID, CHANNEL_ID, CHANNEL_LINK, PORTFOLIO_LINK
)
import logging

router = Router()
logger = logging.getLogger(__name__)
user_booking_data = {}



async def check_subscription(user_id: int, bot) -> bool:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        is_subscribed = member.status in ["member", "administrator", "creator"]
        logger.info(f'Проверка подписки для {user_id}: {is_subscribed}')
        return is_subscribed

@router.message(Command("start"))
async def start_handler(message: Message, state: FSMContext, bot):
    user_id = message.from_user.id

    if await check_subscription(user_id, bot) == True:
        if user_id not in user_booking_data:
            user_booking_data[user_id] = {}
        
        # Путь к изображению используя Path
        image_path = Path(__file__).parent.parent / "images" / "preview.png"
        
        # Текст приветствия
        welcome_text = (
            "Привет! Я Маша, ваш мастер маникюра с золотыми руками и любовью к своему делу. 💅\n\n"
            "Создам уникальный дизайн, подарю идеальное настроение и ухоженные ручки. "
            "Буду рада видеть вас в своём уютном уголке красоты! 😊✨\n\n"
            "<b>Выберите нужное действие:</b>"
        )
        
        try:
            if image_path.exists():
                # Отправляем фото с меню в caption (одно сообщение)
                await message.answer_photo(
                    photo=FSInputFile(str(image_path)),
                    caption=welcome_text,
                    reply_markup=get_main_keyboard(),
                    parse_mode="HTML"
                )
            else:
                logger.warning(f"Файл не найден: {image_path}")
                await message.answer(
                    welcome_text,
                    reply_markup=get_main_keyboard(),
                    parse_mode="HTML"
                )
        except Exception as e:
            logger.error(f"Ошибка при отправке фото: {type(e).__name__}: {e}")
            await message.answer(
                welcome_text,
                reply_markup=get_main_keyboard(),
                parse_mode="HTML"
            )
        
        
    else:
        await message.answer(
            "<b>📢 Для использования бота необходимо подписаться на канал!</b>\n\n"
            "Это поможит вам получать обновления и специальные предложения.",
            reply_markup=get_subscribe_keyboard(),
            parse_mode="HTML")
    await state.clear()

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext, bot):
    await state.clear()
    try:
        await callback.message.edit_caption(
            caption="👋 Добро пожаловать в салон маникюра!\n\nВыберите нужное действие:",
            reply_markup=get_main_keyboard()
        )
    except:
        await callback.message.edit_text(
            text="👋 Добро пожаловать в салон маникюра!\n\nВыберите нужное действие:",
            reply_markup=get_main_keyboard()
        )
    await callback.answer()

@router.callback_query(F.data == "check_subscription")
async def check_subscription_handler(callback: CallbackQuery, state: FSMContext, bot):
    user_id = callback.from_user.id
    is_subscribed = await check_subscription(user_id, bot)
        # Путь к изображению используя Path
    image_path = Path(__file__).parent.parent / "images" / "preview.png"
    
    # Текст приветствия
    welcome_text = (
        "Привет! Я Маша, ваш мастер маникюра с золотыми руками и любовью к своему делу. 💅\n\n"
        "Создам уникальный дизайн, подарю идеальное настроение и ухоженные ручки. "
        "Буду рада видеть вас в своём уютном уголке красоты! 😊✨\n\n"
        "<b>Выберите нужное действие:</b>"
    )
    if is_subscribed:
        await bot.send_photo(
            chat_id=callback.message.chat.id,
            photo=FSInputFile(str(image_path)),
            caption=welcome_text,
            reply_markup=get_main_keyboard(),
            parse_mode="HTML"
        )
        await state.clear()
    else:
        await callback.answer(
            "❌ Вы ещё не подписаны на канал. Пожалуйста, подпишитесь первым.",
            show_alert=True
        )
    
    await callback.answer()

@router.callback_query(F.data == "show_prices")
async def show_prices(callback: CallbackQuery,bot):
    # Путь к изображению прайса
    price_image_path = Path(__file__).parent.parent / "images" / "price.png"
    
    await callback.answer()
    
    try:
        if price_image_path.exists():
            # Отправляем сообщение с фото
            try:
                await callback.message.edit_media(
                    media=InputMediaPhoto(media=FSInputFile(str(price_image_path)), 
                    caption="💅 Наши прайсы:"),
                    reply_markup=get_main_keyboard()
                )
            except:
                await bot.send_photo(
                    chat_id=callback.message.chat.id,
                    photo=FSInputFile(str(price_image_path)),
                    caption="💅 Наши прайсы:",
                    reply_markup=get_main_keyboard(),
                    parse_mode="HTML"
                )
        else:
            logger.warning(f"Файл не найден: {price_image_path}")
            # Если фото не найдено, отправляем текст
            prices_text = get_prices_text()
            await callback.message.answer(
                prices_text,
                reply_markup=get_prices_keyboard(),
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"Ошибка при отправке прайса: {e}")
        # Fallback на текст
        prices_text = get_prices_text()
        try:
            await callback.message.answer(
                prices_text,
                reply_markup=get_prices_keyboard(),
                parse_mode="HTML"
            )
        except Exception as e2:
            logger.error(f"Ошибка при отправке текстового прайса: {e2}")

@router.callback_query(F.data == "show_portfolio")
async def show_portfolio(callback: CallbackQuery):
    try:
        await callback.message.edit_caption(
            caption="<b>🎨 Портфолио</b>\n\n"
            "Посмотрите примеры наших работ:",
            reply_markup=get_portfolio_keyboard(),
            parse_mode="HTML"
        )
    except:
        await callback.message.edit_text(
            text="<b>🎨 Портфолио</b>\n\n"
            "Посмотрите примеры наших работ:",
            reply_markup=get_portfolio_keyboard(),
            parse_mode="HTML"
        )
    await callback.answer()

@router.callback_query(F.data == "book_appointment")
async def book_appointment(callback: CallbackQuery, state: FSMContext, bot):
    user_id = callback.from_user.id
    
    is_subscribed = await check_subscription(user_id, bot)
    if not is_subscribed:
        try:
            await callback.message.edit_caption(
                caption="<b>📢 Для записи необходимо подписаться на канал!</b>\n\nЭто поможит вам получать обновления и специальные предложения."
                ,
                reply_markup=get_subscribe_keyboard(),
                parse_mode="HTML"
            )
        except:
            await callback.message.edit_text(
                text="<b>📢 Для записи необходимо подписаться на канал!</b>\n\nЭто поможит вам получать обновления и специальные предложения."
                ,
                reply_markup=get_subscribe_keyboard(),
                parse_mode="HTML"
            )
        await state.set_state(SubscriptionStates.waiting_for_subscription_check)
        await callback.answer()
        return
    
    has_booking = await db.get_user_has_booking(user_id)
    if has_booking:
        await callback.answer(
            "⚠️ У вас уже есть активная запись.",
            show_alert=True
        )
        return
    
    if user_id not in user_booking_data:
        user_booking_data[user_id] = {}
    
    today = datetime.now()
    try:
        await callback.message.edit_caption(
            caption="<b>📅 Выберите дату для записи:</b>",
            reply_markup=get_calendar_keyboard(today.year, today.month, db),
            parse_mode="HTML"
        )
    except:
        await callback.message.edit_text(
            text="<b>📅 Выберите дату для записи:</b>",
            reply_markup=get_calendar_keyboard(today.year, today.month, db),
            parse_mode="HTML"
        )
    await state.set_state(BookingStates.waiting_for_date)
    await callback.answer()

@router.callback_query(BookingStates.waiting_for_date, F.data.startswith("select_date_"))
async def select_date(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    date = callback.data.replace("select_date_", "")
    user_booking_data[user_id]["date"] = date
    
    available_slots = await db.get_available_slots(date)
    
    if not available_slots:
        await callback.answer("❌ На эту дату нет свободных слотов.",
            show_alert=True)
        return
    
    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%d.%m.%Y (%A)")
    except:
        formatted_date = date
    
    try:
        await callback.message.edit_caption(
            caption=f"<b>⏰ Выберите время для {formatted_date}:</b>",
            reply_markup=get_time_slots_keyboard(available_slots),
            parse_mode="HTML"
        )
    except:
        await callback.message.edit_text(
            text=f"<b>⏰ Выберите время для {formatted_date}:</b>",
            reply_markup=get_time_slots_keyboard(available_slots),
            parse_mode="HTML"
        )
    await state.set_state(BookingStates.waiting_for_time)
    await callback.answer()

@router.callback_query(BookingStates.waiting_for_date, F.data.startswith("prev_month_"))
async def prev_month(callback: CallbackQuery):
    parts = callback.data.replace("prev_month_", "").split("_")
    year, month = int(parts[0]), int(parts[1])
    prev_y, prev_m = get_prev_month(year, month)
    
    try:
        await callback.message.edit_caption(
            caption="<b>📅 Выберите дату для записи:</b>",
            reply_markup=get_calendar_keyboard(prev_y, prev_m,db),
            parse_mode="HTML"
        )
    except:
        await callback.message.edit_text(
            text="<b>📅 Выберите дату для записи:</b>",
            reply_markup=get_calendar_keyboard(prev_y, prev_m,db),
            parse_mode="HTML"
        )
    await callback.answer()

@router.callback_query(BookingStates.waiting_for_date, F.data.startswith("next_month_"))
async def next_month(callback: CallbackQuery):
    parts = callback.data.replace("next_month_", "").split("_")
    year, month = int(parts[0]), int(parts[1])
    next_y, next_m = get_next_month(year, month)
    
    try:
        await callback.message.edit_caption(
            caption="<b>📅 Выберите дату для записи:</b>",
            reply_markup=get_calendar_keyboard(next_y, next_m,db),
            parse_mode="HTML"
        )
    except:
        await callback.message.edit_text(
            text="<b>📅 Выберите дату для записи:</b>",
            reply_markup=get_calendar_keyboard(next_y, next_m,db),
            parse_mode="HTML"
        )
    await callback.answer()

@router.callback_query(BookingStates.waiting_for_time, F.data.startswith("select_time_"))
async def select_time(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    time = callback.data.replace("select_time_", "")
    user_booking_data[user_id]["time"] = time
    
    try:
        await callback.message.edit_caption(
            caption="<b>✍️ Введите ваше имя:</b>",
            parse_mode="HTML"
        )
    except:
        await callback.message.edit_text(
            text="<b>✍️ Введите ваше имя:</b>",
            parse_mode="HTML"
        )
    await state.set_state(BookingStates.waiting_for_name)
    await callback.answer()

@router.callback_query(BookingStates.waiting_for_time, F.data == "back_to_calendar")
async def back_to_calendar(callback: CallbackQuery, state: FSMContext):
    today = datetime.now()

    try:
        await callback.message.edit_caption(
            caption="<b>📅 Выберите дату для записи:</b>",
            reply_markup=get_calendar_keyboard(today.year, today.month,db),
            parse_mode="HTML"
        )
    except:
        await callback.message.edit_text(
            text="<b>📅 Выберите дату для записи:</b>",
            reply_markup=get_calendar_keyboard(today.year, today.month,db),
            parse_mode="HTML"
        )
    await state.set_state(BookingStates.waiting_for_date)
    await callback.answer()

@router.message(BookingStates.waiting_for_name)
async def input_name(message: Message, state: FSMContext):
    user_id = message.from_user.id
    name = message.text.strip()
    
    if len(name) < 2:
        await message.answer("<b>❌ Имя должно содержать минимум 2 символа.</b>", parse_mode="HTML")
        return
    
    user_booking_data[user_id]["name"] = name
    await message.answer(
        "<b>📱 Введите ваш номер телефона:</b>\n\n"
        "<i>Например: +7 (999) 123-45-67 или 89991234567</i>",
        parse_mode="HTML"
    )
    await state.set_state(BookingStates.waiting_for_phone)

@router.message(BookingStates.waiting_for_phone)
async def input_phone(message: Message, state: FSMContext):
    user_id = message.from_user.id
    phone = message.text.strip()
    
    if not is_valid_phone(phone):
        await message.answer(
            "<b>❌ Неверный формат номера.</b>\n\n"
            "<i>Введите корректный номер (минимум 10 цифр)</i>",
            parse_mode="HTML"
        )
        return
    
    user_booking_data[user_id]["phone"] = phone
    date = user_booking_data[user_id]["date"]
    time = user_booking_data[user_id]["time"]
    name = user_booking_data[user_id]["name"]
    
    booking_info = format_booking_info(date, time, name, phone)
    
    await message.answer(
        booking_info + "\n<b>✅ Подтвердите вашу запись:</b>",
        reply_markup=get_confirm_booking_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(BookingStates.waiting_for_confirmation)

@router.callback_query(BookingStates.waiting_for_confirmation, F.data == "confirm_booking")
async def confirm_booking(callback: CallbackQuery, state: FSMContext, bot):
    user_id = callback.from_user.id
    
    try:
        date = user_booking_data[user_id]["date"]
        time = user_booking_data[user_id]["time"]
        name = user_booking_data[user_id]["name"]
        phone = user_booking_data[user_id]["phone"]
        
        success = await db.create_booking(user_id, date, time, name, phone)
        
        if not success:
            await callback.answer(
                "❌ Ошибка при создании записи.",
                show_alert=True
            )
            return
        
        booking_id = await db.get_booking_id(user_id, date, time)
        
        # Планируем напоминание
        try:
            from main import scheduler
            booking_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
            reminder_time = booking_datetime - timedelta(hours=24)
            now = datetime.now()
            
            if reminder_time > now:
                await db.add_reminder(booking_id, user_id, reminder_time.isoformat())
                scheduler.add_job(
                    send_reminder,
                    'date',
                    run_date=reminder_time,
                    args=[user_id, time, bot],
                    id=f"reminder_{booking_id}",
                    replace_existing=True
                )
        except Exception as e:
            logger.error(f"Ошибка при планировании напоминания: {e}")
        
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%d.%m.%Y")
        except:
            formatted_date = date
        
        await callback.message.edit_text(
            f"<b>✅ Ваша запись подтверждена!</b>\n\n"
            f"<b>Дата:</b> {formatted_date}\n"
            f"<b>Время:</b> {time}\n\n"
            f"Спасибо за доверие! Ждём вас 😊",
            parse_mode="HTML"
        )
        
        username = callback.from_user.username or f"ID: {user_id}"
        admin_message = (
            f"<b>📌 Новая запись!</b>\n\n"
            f"<b>Имя:</b> {name}\n"
            f"<b>Телефон:</b> {phone}\n"
            f"<b>Дата:</b> {formatted_date}\n"
            f"<b>Время:</b> {time}\n"
            f"<b>Username:</b> @{username}"
        )
        
        try:
            await bot.send_message(ADMIN_ID, admin_message, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Ошибка при отправке админу: {e}")
        
        try:
            channel_message = (
                f"<b>#Новое бронирование</b>\n\n"
                f"<b>Дата:</b> {formatted_date}\n"
                f"<b>Время:</b> {time}\n"
            )
            await bot.send_message(CHANNEL_ID, channel_message, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Ошибка при отправке в канал: {e}")
        
        user_booking_data[user_id].clear()
        await state.clear()
        
        await callback.message.answer(
            "<b>Выберите действие:</b>",
            reply_markup=get_main_keyboard(),
            parse_mode="HTML"
        )
        
    except KeyError:
        await callback.answer("❌ Ошибка: потеряны данные записи.", show_alert=True)
    
    await callback.answer()

@router.callback_query(F.data == "cancel_booking_process")
async def cancel_booking_process(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if user_id in user_booking_data:
        user_booking_data[user_id].clear()
    
    await state.clear()
    try:
        await callback.message.edit_caption(
            caption="<b>Процесс отменён.</b>\n\n"
            "Выберите действие:",
            reply_markup=get_main_keyboard(),
            parse_mode="HTML"
        )
    except:
        await callback.message.edit_text(
            text="<b>Процесс отменён.</b>\n\n"
            "Выберите действие:",
            reply_markup=get_main_keyboard(),
            parse_mode="HTML"
        )
    await callback.answer()

@router.callback_query(F.data == "my_bookings")
async def my_bookings(callback: CallbackQuery, state: FSMContext, bot):
    user_id = callback.from_user.id
    
    booking = await db.get_user_booking(user_id)
    
    if not booking:
        try:
            await callback.message.edit_caption(
                caption="<b>📋 У вас нет активных записей.</b>\n\n"
                "Хотите записаться?",
                reply_markup=get_my_bookings_keyboard(has_booking=False),
                parse_mode="HTML"
            )
        except:
            await callback.message.edit_text(
                text="<b>📋 У вас нет активных записей.</b>\n\n"
                "Хотите записаться?",
                reply_markup=get_my_bookings_keyboard(has_booking=False),
                parse_mode="HTML"
            )
    else:
        booking_id, date, time, name, phone, created_at = booking
        
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%d.%m.%Y")
        except:
            formatted_date = date
        
        message_text = (
            f"<b>📋 Ваша запись:</b>\n\n"
            f"<b>Дата:</b> {formatted_date}\n"
            f"<b>Время:</b> {time}\n"
            f"<b>Имя:</b> {name}\n"
            f"<b>Телефон:</b> {phone}"
        )
        
        await callback.message.edit_text(
            text=message_text,
            reply_markup=get_my_bookings_keyboard(has_booking=True),
            parse_mode="HTML"
        )
    
    await callback.answer()

@router.callback_query(F.data == "cancel_my_booking")
async def cancel_my_booking(callback: CallbackQuery, bot):
    user_id = callback.from_user.id
    booking = await db.get_user_booking(user_id)
    
    if booking:
        booking_id = booking[0]
        await db.cancel_booking(booking_id)
        
        try:
            from main import scheduler
            scheduler.remove_job(f"reminder_{booking_id}")
        except:
            pass
        
        try:
            await bot.send_message(
                ADMIN_ID,
                f"<b>❌ Отменена запись</b>\n\n"
                f"<b>ID пользователя:</b> {user_id}\n"
                f"<b>Время отмены:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}",
                parse_mode="HTML"
            )
        except:
            pass
        
        await callback.message.edit_text(
            "<b>✅ Ваша запись отменена.</b>\n\n"
            "Выберите действие:",
            reply_markup=get_main_keyboard(),
            parse_mode="HTML"
        )
    else:
        try:
            await callback.message.edit_caption(
                caption="<b>❌ Не удалось найти вашу запись.</b>",
                reply_markup=get_main_keyboard(),
                parse_mode="HTML"
            )
        except:
            await callback.message.edit_text(
                text="<b>❌ Не удалось найти вашу запись.</b>",
                reply_markup=get_main_keyboard(),
                parse_mode="HTML"
            )
    
    await callback.answer()

async def send_reminder(user_id: int, time: str, bot):
    try:
        await bot.send_message(
            user_id,
            f"<b>⏰ Напоминаем, что вы записаны завтра в {time}.</b>\n\n"
            f"Ждём вас! ❤️",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка при отправке напоминания: {e}")



