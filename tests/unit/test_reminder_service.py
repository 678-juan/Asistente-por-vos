from datetime import date, datetime

import pytest

from src.exceptions import (
    DatabaseError,
    DuplicateReminderError,
    InvalidReminderError,
    ReminderPersistenceError,
)
from src.models import PENDING, Reminder
from src.reminder_service import ReminderService
from src.repository import ReminderRepository


@pytest.fixture
def repository(mocker):
    return mocker.MagicMock(spec=ReminderRepository)


@pytest.fixture
def service(repository):
    return ReminderService(repository)


def test_crea_recordatorio(service, repository):
    scheduled_at = datetime(2026, 10, 13, 15, 0)
    saved = Reminder(1, "Llevar a la mascota al veterinario", scheduled_at, PENDING)
    repository.exists_same.return_value = False
    repository.save.return_value = saved

    result = service.create_reminder(
        "Llevar a la mascota al veterinario",
        scheduled_at,
    )

    assert result.id == 1
    assert result.status == PENDING
    repository.save.assert_called_once()


def test_evento_vacio_es_invalido(service, repository):
    with pytest.raises(InvalidReminderError):
        service.create_reminder("", datetime(2026, 10, 13, 15, 0))

    repository.save.assert_not_called()


def test_recordatorio_duplicado(service, repository):
    repository.exists_same.return_value = True

    with pytest.raises(DuplicateReminderError):
        service.create_reminder(
            "Llevar a la mascota al veterinario",
            datetime(2026, 10, 13, 15, 0),
        )

    repository.save.assert_not_called()


def test_lista_por_fecha_ordenada(service, repository):
    repository.find_by_date.return_value = [
        Reminder(2, "Cena", datetime(2026, 10, 12, 18, 30)),
        Reminder(1, "Desayuno", datetime(2026, 10, 12, 8, 0)),
    ]

    result = service.list_reminders_by_date(date(2026, 10, 12))

    assert len(result) == 2
    assert result[0].scheduled_at.hour == 8
    assert result[1].scheduled_at.hour == 18
    assert result[0].scheduled_at.minute == 0
    assert result[1].scheduled_at.minute == 30


def test_fecha_sin_recordatorios_retorna_lista_vacia(service, repository):
    repository.find_by_date.return_value = []

    result = service.list_reminders_by_date(date(2026, 10, 15))

    assert result == []


def test_error_de_bd_se_convierte_en_error_de_persistencia(service, repository):
    repository.exists_same.return_value = False
    repository.save.side_effect = DatabaseError("detalle interno sensible")

    with pytest.raises(ReminderPersistenceError):
        service.create_reminder(
            "Nueva tarea",
            datetime(2026, 10, 13, 10, 0),
        )
