from datetime import datetime

import pytest

from src.command_interpreter import CommandInterpreter
from src.exceptions import (
    EmptyCommandError,
    IncompleteCommandError,
    PastDateError,
    UnsupportedIntentError,
)
from src.models import CREATE_REMINDER, QUERY_REMINDERS


@pytest.fixture
def interpreter():
    return CommandInterpreter()


@pytest.fixture
def now():
    return datetime(2026, 10, 12, 9, 0)


def test_crea_recordatorio_para_mañana(interpreter, now):
    result = interpreter.interpret(
        "recuérdame llevar a mi mascota al veterinario mañana a las tres de la tarde",
        now,
    )

    assert result.intent == CREATE_REMINDER
    assert result.event == "llevar a mi mascota al veterinario"
    assert result.scheduled_at == datetime(2026, 10, 13, 15, 0)


def test_consulta_recordatorios_de_hoy(interpreter, now):
    result = interpreter.interpret("qué recordatorios tengo para hoy", now)

    assert result.intent == QUERY_REMINDERS
    assert result.query_date == datetime(2026, 10, 12, 0, 0)
    assert result.event is None


def test_crea_recordatorio_con_fecha_numerica(interpreter, now):
    result = interpreter.interpret(
        "recuérdame pagar el recibo del agua el 20 de octubre "
        "a las 8 de la mañana",
        now,
    )

    assert result.intent == CREATE_REMINDER
    assert result.event == "pagar el recibo del agua"
    assert result.scheduled_at == datetime(2026, 10, 20, 8, 0)


def test_recordatorio_sin_hora_es_incompleto(interpreter, now):
    with pytest.raises(IncompleteCommandError) as exc_info:
        interpreter.interpret("recuérdame sacar al perro mañana", now)

    assert exc_info.value.missing_fields == ["time"]


def test_comando_vacio(interpreter, now):
    with pytest.raises(EmptyCommandError):
        interpreter.interpret("   ", now)


def test_intencion_no_soportada(interpreter, now):
    with pytest.raises(UnsupportedIntentError):
        interpreter.interpret("cuéntame un chiste", now)


def test_fecha_ayer_lanza_error(interpreter, now):
    with pytest.raises(PastDateError):
        interpreter.interpret(
            "recuérdame ir al banco ayer a las 10 de la mañana",
            now,
        )
