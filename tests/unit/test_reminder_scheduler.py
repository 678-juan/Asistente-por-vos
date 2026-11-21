from datetime import datetime

import pytest
from unittest.mock import call

from src.exceptions import NotificationError
from src.models import NOTIFIED, PENDING, Reminder
from src.reminder_scheduler import Notifier, ReminderScheduler
from src.repository import ReminderRepository


@pytest.fixture
def repository(mocker):
    return mocker.MagicMock(spec=ReminderRepository)


@pytest.fixture
def notifier(mocker):
    return mocker.MagicMock(spec=Notifier)


@pytest.fixture
def scheduler(repository, notifier):
    return ReminderScheduler(repository, notifier)


@pytest.fixture
def now():
    return datetime(2026, 10, 12, 9, 0)


def test_notifica_recordatorio_vencido(scheduler, repository, notifier, now):
    reminder = Reminder(1, "Reunión", datetime(2026, 10, 12, 9, 0), PENDING)
    repository.find_pending.return_value = [reminder]

    due = scheduler.check_due_reminders(now)

    assert due == [reminder]
    notifier.notify.assert_called_once_with(reminder)
    repository.update_status.assert_called_once_with(reminder.id, NOTIFIED)


def test_recordatorio_futuro_no_se_notifica(scheduler, repository, notifier, now):
    reminder = Reminder(2, "Cita", datetime(2026, 10, 12, 15, 0), PENDING)
    repository.find_pending.return_value = [reminder]

    due = scheduler.check_due_reminders(now)

    assert due == []
    notifier.notify.assert_not_called()
    repository.update_status.assert_not_called()


def test_recordatorio_ya_notificado_se_ignora(scheduler, repository, notifier, now):
    reminder = Reminder(3, "Compra", datetime(2026, 10, 12, 8, 0), NOTIFIED)
    repository.find_pending.return_value = [reminder]

    due = scheduler.check_due_reminders(now)

    assert due == []
    notifier.notify.assert_not_called()
    repository.update_status.assert_not_called()


def test_falla_notificacion_no_bloquea_segundo_recordatorio(
    scheduler, repository, notifier, now
):
    first = Reminder(1, "Primero", datetime(2026, 10, 12, 8, 0), PENDING)
    second = Reminder(2, "Segundo", datetime(2026, 10, 12, 8, 30), PENDING)
    repository.find_pending.return_value = [first, second]
    notifier.notify.side_effect = [NotificationError("fallo"), None]

    due = scheduler.check_due_reminders(now)

    assert due == [second]
    repository.update_status.assert_called_once_with(second.id, NOTIFIED)
    assert first.status == PENDING


def test_notifica_en_orden_cronologico(scheduler, repository, notifier, now):
    first = Reminder(1, "Primero", datetime(2026, 10, 12, 8, 59), PENDING)
    second = Reminder(2, "Segundo", datetime(2026, 10, 12, 9, 0), PENDING)
    repository.find_pending.return_value = [second, first]

    due = scheduler.check_due_reminders(now)

    assert due == [first, second]
    assert notifier.notify.call_args_list == [call(first), call(second)]
    assert repository.update_status.call_args_list == [
        call(first.id, NOTIFIED),
        call(second.id, NOTIFIED),
    ]
