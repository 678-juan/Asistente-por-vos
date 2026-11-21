from .exceptions import NotificationError
from .models import NOTIFIED


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
                self.notifier(reminder)
            except Exception as exc:
                continue
            try:
                self.repository.update_status(reminder.id, NOTIFIED)
                due.append(reminder)
            except Exception:
                continue
        return due
