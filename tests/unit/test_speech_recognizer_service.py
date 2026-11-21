import pytest

from src.exceptions import (
    EmptyAudioError,
    LowConfidenceError,
    SpeechNotRecognizedError,
)
from src.speech_recognizer_service import SpeechRecognizerService


@pytest.fixture
def stt_engine(mocker):
    return mocker.MagicMock()


@pytest.fixture
def speech_service(stt_engine):
    return SpeechRecognizerService(stt_engine, confidence_threshold=0.60)


def test_transcribe_normaliza_audio_valido(speech_service, stt_engine):
    audio = b"audio-valido"
    stt_engine.return_value = {
        "text": "  Recuérdame llevar a mi mascota al veterinario mañana a las tres de la tarde  ",
        "confidence": 0.92,
    }

    result = speech_service.transcribe(audio)

    assert result == "recuérdame llevar a mi mascota al veterinario mañana a las tres de la tarde"
    stt_engine.assert_called_once_with(audio)


def test_transcribe_rechaza_audio_vacio(speech_service, stt_engine):
    with pytest.raises(EmptyAudioError):
        speech_service.transcribe(b"")

    stt_engine.assert_not_called()


def test_transcribe_rechaza_texto_sin_voz(speech_service, stt_engine):
    stt_engine.return_value = {"text": "", "confidence": 0.0}

    with pytest.raises(SpeechNotRecognizedError):
        speech_service.transcribe(b"audio-sin-voz")


def test_transcribe_rechaza_baja_confianza(speech_service, stt_engine):
    stt_engine.return_value = {"text": "recuérdame algo", "confidence": 0.35}

    with pytest.raises(LowConfidenceError):
        speech_service.transcribe(b"audio-baja-confianza")
