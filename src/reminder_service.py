from datetime import date as Date, datetime

from .exceptions import (
    DatabaseError,
    DuplicateReminderError,
    InvalidReminderError,
    ReminderPersistenceError,
)
from .models import PENDING, Reminder


class ReminderService:
    def __init__(self, repository):
        self.repository = repository

    def create_reminder(self, event, scheduled_at):
        if event is None or not str(event).strip():
            raise InvalidReminderError("El evento no puede estar vacio.")
        if not isinstance(scheduled_at, datetime):
            raise InvalidReminderError("La fecha del recordatorio no es valida.")

        event = str(event).strip()
        try:
            if self.repository.exists_same(event, scheduled_at):
                raise DuplicateReminderError("El recordatorio ya existe.")
            return self.repository.save(Reminder(None, event, scheduled_at, PENDING))
        except DuplicateReminderError:
            raise
        except DatabaseError as exc:
            raise ReminderPersistenceError(str(exc)) from exc
        except Exception as exc:
            raise ReminderPersistenceError("No pudo guardarse el recordatorio.") from exc

    def list_reminders_by_date(self, date):
        if not isinstance(date, (datetime, Date)):
            raise InvalidReminderError("La fecha de consulta no es valida.")
        try:
            reminders = self.repository.find_by_date(date)
            return sorted(reminders, key=lambda reminder: reminder.scheduled_at)
        except DatabaseError as exc:
            raise ReminderPersistenceError(str(exc)) from exc
