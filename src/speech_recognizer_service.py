from .exceptions import (
    EmptyAudioError,
    LowConfidenceError,
    SpeechNotRecognizedError,
)


class SpeechRecognizerService:
    """Capa pequena sobre un motor STT intercambiable."""

    def __init__(self, engine, confidence_threshold=0.60):
        self.engine = engine
        self.confidence_threshold = float(confidence_threshold)

    def transcribe(self, audio):
        if audio is None or (isinstance(audio, (bytes, bytearray, str)) and len(audio) == 0):
            raise EmptyAudioError("No se recibio audio.")

        result = self.engine(audio)
        if isinstance(result, dict):
            text = result.get("text")
            confidence = result.get("confidence", 1.0)
        else:
            text = getattr(result, "text", None)
            confidence = getattr(result, "confidence", 1.0)

        if text is None:
            raise SpeechNotRecognizedError("No se detecto voz.")

        normalized = str(text).strip().lower()
        if not normalized:
            raise SpeechNotRecognizedError("No se detecto voz.")

        try:
            confidence_value = float(confidence)
        except (TypeError, ValueError):
            confidence_value = 0.0

        if confidence_value < self.confidence_threshold:
            raise LowConfidenceError("La confianza del reconocimiento es baja.")

        return normalized
