# ==================== MAIN.PY ====================
# Главный файл бота

import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import BOT_TOKEN, ADMIN_ID
from database import db
from handlers import user, admin
from utils.helpers import clear_old_reminders

# ==================== ЛОГИРОВАНИЕ ====================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== ИНИЦИАЛИЗАЦИЯ ====================

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
scheduler = AsyncIOScheduler()

# ==================== РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ ====================

dp.include_routers(
    user.router,
    admin.router
)

# ==================== ФУНКЦИИ ДЛЯ НАПОМИНАНИЙ ====================

async def check_and_send_reminders(bot: Bot):
    try:
        reminders = await db.get_pending_reminders()
        
        for reminder_id, user_id, time in reminders:
            try:
                await bot.send_message(
                    user_id,
                    f'<b>⏰ Напоминаем, что вы записаны на наращивание ресниц завтра в {time}.</b>\n\n'
                    f'Ждём вас! ❤️',
                    parse_mode='HTML'
                )
                await db.mark_reminder_sent(reminder_id)
            except Exception as e:
                logger.error(f'Ошибка при отправке напоминания {reminder_id}: {e}')
    except Exception as e:
        logger.error(f'Ошибка при проверке напоминаний: {e}')

async def restore_reminders():
    try:
        reminders = await db.get_all_reminders()
        
        for reminder_id, user_id, reminder_date, time in reminders:
            try:
                reminder_dt = datetime.fromisoformat(reminder_date)
                now = datetime.now()
                
                if reminder_dt > now:
                    scheduler.add_job(
                        send_reminder_task,
                        'date',
                        run_date=reminder_dt,
                        args=[user_id, time],
                        id=f'restored_reminder_{reminder_id}',
                        replace_existing=True
                    )
                    logger.info(f'Восстановлено напоминание {reminder_id} на {reminder_dt}')
            except Exception as e:
                logger.error(f'Ошибка при восстановлении напоминания {reminder_id}: {e}')
    except Exception as e:
        logger.error(f'Ошибка при восстановлении напоминаний: {e}')

async def send_reminder_task(user_id: int, time: str):
    try:
        await bot.send_message(
            user_id,
            f'<b>⏰ Напоминаем, что вы записаны на наращивание ресниц завтра в {time}.</b>\n\n'
            f'Ждём вас! ❤️',
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f'Ошибка при отправке напоминания пользователю {user_id}: {e}')

async def cleanup_old_data():
    try:
        clear_old_reminders()
    except Exception as e:
        logger.error(f'Ошибка при очистке старых данных: {e}')

async def init_schedule():
    """Инициализация расписания на месяц вперед (если оно пусто)"""
    try:
        from config import SCHEDULE_DAYS_AHEAD, WORK_DAYS
        from utils.helpers import generate_time_slots
        
        existing_days = await db.get_working_days()
        
        # Если дней меньше 5, инициализируем расписание
        if len(existing_days) < 5:
            logger.info('Инициализация расписания на месяц вперед...')
            today = datetime.now()
            slots = generate_time_slots()
            
            for i in range(SCHEDULE_DAYS_AHEAD):
                date_obj = today + timedelta(days=i)
                
                # Пропускаем выходные (воскресенье = 6)
                if date_obj.weekday() not in WORK_DAYS:
                    continue
                
                date_str = date_obj.strftime("%Y-%m-%d")
                
                # Проверяем, есть ли уже такой день
                if date_str not in existing_days:
                    await db.add_working_day(date_str)
                    
                    # Добавляем слоты
                    for slot in slots:
                        await db.add_time_slot(date_str, slot)
                    
                    logger.info(f'Добавлен день {date_str} с {len(slots)} слотами')
            
            logger.info('Расписание инициализировано')
    except Exception as e:
        logger.error(f'Ошибка при инициализации расписания: {e}')

# ==================== ЗАПУСК БОТА ====================

async def main():
    await db.init_db()
    logger.info('База данных инициализирована')
    
    await init_schedule()
    logger.info('Расписание проверено и инициализировано если необходимо')
    
    scheduler.start()
    logger.info('Планировщик запущен')
    
    scheduler.add_job(
        check_and_send_reminders,
        'interval',
        minutes=1,
        args=[bot],
        id='check_reminders',
        replace_existing=True
    )
    
    scheduler.add_job(
        cleanup_old_data,
        'cron',
        hour=0,
        minute=0,
        id='cleanup_old_data',
        replace_existing=True
    )
    
    await restore_reminders()
    
    try:
        await bot.send_message(
            ADMIN_ID,
            '<b>✅ Бот запущен!</b>\n\n'
            f'Время запуска: {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}',
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f'Ошибка при отправке уведомления админу: {e}')
    
    logger.info('Полинг сообщений начал работу')
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        scheduler.shutdown()

if __name__ == '__main__':
    asyncio.run(main())
