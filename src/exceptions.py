class EmptyAudioError(Exception):
    """No se proporciono audio procesable."""


class SpeechNotRecognizedError(Exception):
    """El motor no pudo reconocer voz."""


class LowConfidenceError(Exception):
    """El reconocimiento tiene una confianza insuficiente."""


class IncompleteCommandError(Exception):
    """La instruccion no contiene todos los campos necesarios."""

    def __init__(self, missing_fields):
        self.missing_fields = list(missing_fields)
        super().__init__(
            "Faltan campos necesarios: " + ", ".join(self.missing_fields)
        )


class EmptyCommandError(Exception):
    """La instruccion esta vacia."""


class UnsupportedIntentError(Exception):
    """La instruccion solicita una accion fuera del alcance."""


class PastDateError(Exception):
    """La fecha del recordatorio ya paso."""


class InvalidReminderError(Exception):
    """Los datos del recordatorio no son validos."""


class DuplicateReminderError(Exception):
    """Ya existe el mismo recordatorio."""


class DatabaseError(Exception):
    """Ocurrio un error general de base de datos."""


class ReminderPersistenceError(Exception):
    """No pudo persistirse el recordatorio."""


class NotificationError(Exception):
    """No pudo enviarse una notificacion."""
