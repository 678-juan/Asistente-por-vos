import sqlite3
from abc import ABC, abstractmethod
from datetime import datetime

from .exceptions import DatabaseError
from .models import NOTIFIED, PENDING, Reminder


class ReminderRepository(ABC):
    @abstractmethod
    def exists_same(self, event, scheduled_at):
        pass

    @abstractmethod
    def save(self, reminder):
        pass

    @abstractmethod
    def find_by_date(self, date):
        pass

    @abstractmethod
    def find_pending(self):
        pass

    @abstractmethod
    def update_status(self, reminder_id, status):
        pass


class SQLiteReminderRepository(ReminderRepository):
    def __init__(self, database="recordatorios.db"):
        self.database = database
        try:
            with sqlite3.connect(self.database) as connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS reminders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event TEXT NOT NULL,
                        scheduled_at TEXT NOT NULL,
                        status TEXT NOT NULL
                    )
                    """
                )
        except sqlite3.Error as exc:
            raise DatabaseError(str(exc)) from exc

    def _connect(self):
        return sqlite3.connect(self.database)

    def exists_same(self, event, scheduled_at):
        try:
            with self._connect() as connection:
                row = connection.execute(
                    "SELECT 1 FROM reminders WHERE event = ? AND scheduled_at = ?",
                    (event, scheduled_at.isoformat()),
                ).fetchone()
                return row is not None
        except sqlite3.Error as exc:
            raise DatabaseError(str(exc)) from exc

    def save(self, reminder):
        try:
            with self._connect() as connection:
                cursor = connection.execute(
                    "INSERT INTO reminders (event, scheduled_at, status) VALUES (?, ?, ?)",
                    (reminder.event, reminder.scheduled_at.isoformat(), reminder.status),
                )
                reminder.id = cursor.lastrowid
                return reminder
        except sqlite3.Error as exc:
            raise DatabaseError(str(exc)) from exc

    def find_by_date(self, date):
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start.replace(hour=23, minute=59, second=59, microsecond=999999)
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    """
                    SELECT id, event, scheduled_at, status
                    FROM reminders
                    WHERE scheduled_at BETWEEN ? AND ?
                    ORDER BY scheduled_at ASC
                    """,
                    (start.isoformat(), end.isoformat()),
                ).fetchall()
                return [self._row_to_reminder(row) for row in rows]
        except sqlite3.Error as exc:
            raise DatabaseError(str(exc)) from exc

    def find_pending(self):
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    "SELECT id, event, scheduled_at, status FROM reminders "
                    "WHERE status = ? ORDER BY scheduled_at ASC",
                    (PENDING,),
                ).fetchall()
                return [self._row_to_reminder(row) for row in rows]
        except sqlite3.Error as exc:
            raise DatabaseError(str(exc)) from exc

    def update_status(self, reminder_id, status):
        try:
            with self._connect() as connection:
                connection.execute(
                    "UPDATE reminders SET status = ? WHERE id = ?",
                    (status, reminder_id),
                )
                return True
        except sqlite3.Error as exc:
            raise DatabaseError(str(exc)) from exc

    @staticmethod
    def _row_to_reminder(row):
        return Reminder(
            id=row[0],
            event=row[1],
            scheduled_at=datetime.fromisoformat(row[2]),
            status=row[3],
        )
