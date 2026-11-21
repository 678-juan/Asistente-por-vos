from dataclasses import dataclass
from datetime import datetime
from typing import Optional


PENDING = "PENDING"
NOTIFIED = "NOTIFIED"

CREATE_REMINDER = "CREATE_REMINDER"
QUERY_REMINDERS = "QUERY_REMINDERS"


@dataclass
class ParsedCommand:
    intent: str
    event: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    query_date: Optional[datetime] = None


@dataclass
class Reminder:
    id: Optional[int]
    event: str
    scheduled_at: datetime
    status: str = PENDING
