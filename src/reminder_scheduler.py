from .exceptions import NotificationError
from .models import NOTIFIED


class Notifier:
    def notify(self, reminder):
        raise NotificationError("El notificador no esta configurado.")


class ReminderScheduler:
    def __init__(self, repository, notifier):
        self.repository = repository
        self.notifier = notifier

    def check_due_reminders(self, now):
        due = []
        reminders = self.repository.find_pending()
        for reminder in sorted(reminders, key=lambda item: item.scheduled_at):
            if reminder.status != "PENDING":
                continue
            if reminder.scheduled_at > now:
                continue
            try:
                self.notifier.notify(reminder)
            except (NotificationError, Exception):
                continue
            try:
                self.repository.update_status(reminder.id, NOTIFIED)
                due.append(reminder)
            except Exception:
                continue
        return due
