import re
from datetime import datetime, timedelta

from .exceptions import (
    EmptyCommandError,
    IncompleteCommandError,
    PastDateError,
    UnsupportedIntentError,
)
from .models import CREATE_REMINDER, QUERY_REMINDERS, ParsedCommand


class CommandInterpreter:
    MONTHS = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
        "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
        "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
    }
    NUMBER_WORDS = {
        "una": 1, "uno": 1, "dos": 2, "tres": 3, "cuatro": 4,
        "cinco": 5, "seis": 6, "siete": 7, "ocho": 8,
        "nueve": 9, "diez": 10, "once": 11, "doce": 12,
    }

    def interpret(self, text, now):
        if text is None or not str(text).strip():
            raise EmptyCommandError("El comando esta vacio.")

        normalized = re.sub(r"\s+", " ", str(text).strip().lower())

        if any(word in normalized for word in (
            "listar", "consulta", "mostrar", "que tengo",
            "qué recordatorios", "que recordatorios", "recordatorios tengo",
        )):
            date = self._parse_date(normalized, now)
            if date is None:
                raise IncompleteCommandError(["fecha"])
            return ParsedCommand(QUERY_REMINDERS, query_date=date)

        if not any(word in normalized for word in (
            "recordar", "recuérdame", "recuerdame", "recuerda",
            "recordatorio", "crear", "agendar",
        )):
            raise UnsupportedIntentError("Intencion no soportada.")

        missing = []
        event = self._extract_event(normalized)
        date = self._parse_date(normalized, now)
        time = self._parse_time(normalized)
        if not event:
            missing.append("evento")
        if date is None:
            missing.append("fecha")
        if time is None:
            missing.append("time")
        if missing:
            raise IncompleteCommandError(missing)

        scheduled_at = datetime(
            date.year, date.month, date.day, time.hour, time.minute
        )
        if scheduled_at < now:
            raise PastDateError("La fecha u hora del recordatorio ya paso.")

        return ParsedCommand(CREATE_REMINDER, event=event, scheduled_at=scheduled_at)

    def _extract_event(self, text):
        patterns = (
            r"(?:recuérdame|recuerdame|recuerda|recordar(?:me)?|recordatorio|crear|agendar)\s+(?:que\s+)?(.+?)(?=\s+(?:hoy|mañana|ayer|el\s+\d{1,2}|a las?|las?)\b|$)",
        )
        match = re.search(patterns[0], text)
        if not match:
            return None
        event = match.group(1).strip(" ,.;:")
        return event or None

    def _parse_date(self, text, now):
        if "ayer" in text:
            return (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        if "mañana" in text and "de la mañana" not in text:
            return (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        if "hoy" in text:
            return now.replace(hour=0, minute=0, second=0, microsecond=0)

        match = re.search(r"\b(\d{1,2})\s+de\s+([a-z]+)(?:\s+de\s+(?:el\s+)?(\d{4}))?", text)
        if match:
            day = int(match.group(1))
            month = self.MONTHS.get(match.group(2))
            year = int(match.group(3)) if match.group(3) else now.year
            if month is None:
                return None
            try:
                return datetime(year, month, day)
            except ValueError:
                return None
        return None

    def _parse_time(self, text):
        match = re.search(
            r"(?:a\s+las?|las?|hora)\s+(\d{1,2})(?:[:.](\d{2}))?\s*(a\.? ?m\.?|p\.? ?m\.?|horas?)?",
            text,
        )
        if not match:
            word_match = re.search(
                r"(?:a\s+las?|las?|hora)\s+(una|uno|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce)"
                r"(?:\s*:\s*(\d{2}))?\s*(a\.? ?m\.?|p\.? ?m\.?|horas?)?",
                text,
            )
            if word_match:
                hour = self.NUMBER_WORDS[word_match.group(1)]
                minute = int(word_match.group(2) or 0)
                suffix = re.sub(r"\s+", "", word_match.group(3) or "").replace(".", "")
                if suffix == "pm" and hour < 12:
                    hour += 12
                elif suffix == "am" and hour == 12:
                    hour = 0
                elif "de la tarde" in text or "de la noche" in text:
                    if hour < 12:
                        hour += 12
                if hour > 23 or minute > 59:
                    return None
                return datetime(2000, 1, 1, hour, minute)
        if not match:
            match = re.search(
                r"\b(\d{1,2})(?:[:.](\d{2}))?\s*(a\.? ?m\.?|p\.? ?m\.?|horas)\b",
                text,
            )
        if not match:
            return None

        hour = int(match.group(1))
        minute = int(match.group(2) or 0)
        suffix = re.sub(r"\s+", "", match.group(3) or "").replace(".", "")

        if suffix == "pm" and hour < 12:
            hour += 12
        elif suffix == "am" and hour == 12:
            hour = 0

        if hour > 23 or minute > 59:
            return None
        return datetime(2000, 1, 1, hour, minute)
