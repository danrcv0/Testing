# ==================== DATABASE.PY ====================
# Работа с базой данных SQLite

import sqlite3
import asyncio
from datetime import datetime
from typing import List, Optional, Tuple
from config import DATABASE_NAME

class Database:
    """Класс для работы с SQLite базой данных"""
    
    def __init__(self, db_name: str = DATABASE_NAME):
        self.db_name = db_name
        
    async def init_db(self):
        """Инициализация БД - создание таблиц"""
        # Запускаем в отдельном потоке
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._create_tables)
        
    def _create_tables(self):
        """Создание таблиц в БД"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Таблица рабочих дней
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS working_days (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE NOT NULL,
                is_closed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица временных слотов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS time_slots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                is_booked INTEGER DEFAULT 0,
                unique(date, time),
                FOREIGN KEY(date) REFERENCES working_days(date) ON DELETE CASCADE
            )
        ''')
        
        # Таблица записей клиентов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, date, time),
                FOREIGN KEY(date) REFERENCES working_days(date) ON DELETE CASCADE
            )
        ''')
        
        # Таблица напоминаний
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                reminder_date TIMESTAMP NOT NULL,
                is_sent INTEGER DEFAULT 0,
                UNIQUE(booking_id),
                FOREIGN KEY(booking_id) REFERENCES bookings(id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def add_working_day(self, date: str) -> bool:
        """Добавить рабочий день"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, 
                lambda: self._add_working_day(date)
            )
            return True
        except sqlite3.IntegrityError:
            return False
    
    def _add_working_day(self, date: str):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO working_days (date) VALUES (?)', (date,))
        conn.commit()
        conn.close()
    
    async def close_day(self, date: str) -> bool:
        """Закрыть день"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._close_day(date)
            )
            return True
        except:
            return False
    
    def _close_day(self, date: str):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('UPDATE working_days SET is_closed = 1 WHERE date = ?', (date,))
        conn.commit()
        conn.close()
    
    async def open_day(self, date: str) -> bool:
        """Открыть закрытый день"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._open_day(date)
            )
            return True
        except:
            return False
    
    def _open_day(self, date: str):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('UPDATE working_days SET is_closed = 0 WHERE date = ?', (date,))
        conn.commit()
        conn.close()
    
    async def add_time_slot(self, date: str, time: str) -> bool:
        """Добавить временный слот"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._add_time_slot(date, time)
            )
            return True
        except sqlite3.IntegrityError:
            return False
    
    def _add_time_slot(self, date: str, time: str):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO time_slots (date, time, is_booked) VALUES (?, ?, 0)',
            (date, time)
        )
        conn.commit()
        conn.close()
    
    async def get_available_slots(self, date: str) -> List[str]:
        """Получить доступные слоты на конкретный день"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._get_available_slots(date)
        )
    
    def _get_available_slots(self, date: str) -> List[str]:
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT time FROM time_slots WHERE date = ? AND is_booked = 0 ORDER BY time',
            (date,)
        )
        slots = [row[0] for row in cursor.fetchall()]
        conn.close()
        return slots
    
    async def get_all_slots(self, date: str) -> List[str]:
        """Получить все слоты на день (бронированные и свободные)"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._get_all_slots(date)
        )
    
    def _get_all_slots(self, date: str) -> List[str]:
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT time FROM time_slots WHERE date = ? ORDER BY time',
            (date,)
        )
        slots = [row[0] for row in cursor.fetchall()]
        conn.close()
        return slots
    
    async def delete_time_slot(self, date: str, time: str) -> bool:
        """Удалить временный слот"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._delete_time_slot(date, time)
            )
            return True
        except:
            return False
    
    def _delete_time_slot(self, date: str, time: str):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            'DELETE FROM time_slots WHERE date = ? AND time = ?',
            (date, time)
        )
        conn.commit()
        conn.close()
    
    async def create_booking(self, user_id: int, date: str, time: str, 
                            name: str, phone: str) -> bool:
        """Создать запись (бронирование)"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._create_booking(user_id, date, time, name, phone)
            )
            return True
        except sqlite3.IntegrityError:
            return False
    
    def _create_booking(self, user_id: int, date: str, time: str, 
                       name: str, phone: str):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Создаём запись
        cursor.execute(
            '''INSERT INTO bookings (user_id, date, time, name, phone) 
               VALUES (?, ?, ?, ?, ?)''',
            (user_id, date, time, name, phone)
        )
        
        # Отмечаем слот как занятый
        cursor.execute(
            'UPDATE time_slots SET is_booked = 1 WHERE date = ? AND time = ?',
            (date, time)
        )
        
        conn.commit()
        conn.close()
    
    async def get_booking_id(self, user_id: int, date: str, time: str) -> Optional[int]:
        """Получить ID записи"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._get_booking_id(user_id, date, time)
        )
    
    def _get_booking_id(self, user_id: int, date: str, time: str) -> Optional[int]:
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id FROM bookings WHERE user_id = ? AND date = ? AND time = ?',
            (user_id, date, time)
        )
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    async def get_user_booking(self, user_id: int) -> Optional[Tuple]:
        """Получить текущую запись пользователя"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._get_user_booking(user_id)
        )
    
    def _get_user_booking(self, user_id: int) -> Optional[Tuple]:
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            '''SELECT id, date, time, name, phone, created_at 
               FROM bookings 
               WHERE user_id = ? 
               ORDER BY created_at DESC 
               LIMIT 1''',
            (user_id,)
        )
        result = cursor.fetchone()
        conn.close()
        return result
    
    async def cancel_booking(self, booking_id: int) -> bool:
        """Отменить запись"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._cancel_booking(booking_id)
            )
            return True
        except:
            return False
    
    def _cancel_booking(self, booking_id: int):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Получаем дату и время записи
        cursor.execute(
            'SELECT date, time FROM bookings WHERE id = ?',
            (booking_id,)
        )
        result = cursor.fetchone()
        
        if result:
            date, time = result
            
            # Делаем слот снова доступным
            cursor.execute(
                'UPDATE time_slots SET is_booked = 0 WHERE date = ? AND time = ?',
                (date, time)
            )
            
            # Удаляем запись
            cursor.execute('DELETE FROM bookings WHERE id = ?', (booking_id,))
            
            # Удаляем напоминание
            cursor.execute('DELETE FROM reminders WHERE booking_id = ?', (booking_id,))
        
        conn.commit()
        conn.close()
    
    async def get_bookings_for_date(self, date: str) -> List[Tuple]:
        """Получить все записи на конкретный день (для админа)"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._get_bookings_for_date(date)
        )
    
    def _get_bookings_for_date(self, date: str) -> List[Tuple]:
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, time, name, phone FROM bookings WHERE date = ? ORDER BY time',
            (date,)
        )
        bookings = cursor.fetchall()
        conn.close()
        return bookings
    
    async def get_user_has_booking(self, user_id: int) -> bool:
        """Проверить, есть ли у пользователя записи"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._get_user_has_booking(user_id)
        )
    
    def _get_user_has_booking(self, user_id: int) -> bool:
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT COUNT(*) FROM bookings WHERE user_id = ?',
            (user_id,)
        )
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    
    async def get_working_days(self) -> List[str]:
        """Получить все рабочие дни"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._get_working_days()
        )
    
    def _get_working_days(self) -> List[str]:
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT date FROM working_days WHERE is_closed = 0 ORDER BY date'
        )
        days = [row[0] for row in cursor.fetchall()]
        conn.close()
        return days
    
    async def is_day_closed(self, date: str) -> bool:
        """Проверить, закрыт ли день"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._is_day_closed(date)
        )
    
    def _is_day_closed(self, date: str) -> bool:
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT is_closed FROM working_days WHERE date = ?',
            (date,)
        )
        result = cursor.fetchone()
        conn.close()
        return result[0] == 1 if result else False
    
    # Методы для напоминаний
    async def add_reminder(self, booking_id: int, user_id: int, reminder_date: str) -> bool:
        """Добавить напоминание"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._add_reminder(booking_id, user_id, reminder_date)
            )
            return True
        except:
            return False
    
    def _add_reminder(self, booking_id: int, user_id: int, reminder_date: str):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO reminders (booking_id, user_id, reminder_date) 
               VALUES (?, ?, ?)''',
            (booking_id, user_id, reminder_date)
        )
        conn.commit()
        conn.close()
    
    async def get_pending_reminders(self) -> List[Tuple]:
        """Получить непоказанные напоминания"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._get_pending_reminders()
        )
    
    def _get_pending_reminders(self) -> List[Tuple]:
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            '''SELECT reminders.id, reminders.user_id, bookings.time 
               FROM reminders 
               JOIN bookings ON reminders.booking_id = bookings.id 
               WHERE reminders.is_sent = 0 AND reminders.reminder_date <= datetime('now')
            '''
        )
        reminders = cursor.fetchall()
        conn.close()
        return reminders
    
    async def mark_reminder_sent(self, reminder_id: int):
        """Отметить напоминание как отправленное"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self._mark_reminder_sent(reminder_id)
        )
    
    def _mark_reminder_sent(self, reminder_id: int):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE reminders SET is_sent = 1 WHERE id = ?',
            (reminder_id,)
        )
        conn.commit()
        conn.close()
    
    async def get_all_reminders(self) -> List[Tuple]:
        """Получить все не отправленные напоминания (для восстановления при перезагрузке)"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._get_all_reminders()
        )
    
    def _get_all_reminders(self) -> List[Tuple]:
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            '''SELECT reminders.id, reminders.user_id, reminders.reminder_date, bookings.time 
               FROM reminders 
               JOIN bookings ON reminders.booking_id = bookings.id 
               WHERE reminders.is_sent = 0
            '''
        )
        reminders = cursor.fetchall()
        conn.close()
        return reminders


# Создаём глобальный объект БД
db = Database()
