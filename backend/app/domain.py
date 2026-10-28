"""Plain data types shared across the backend (no framework dependencies)."""
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class Actual:
    start_time: datetime
    generation: float  # MW


@dataclass(frozen=True)
class Forecast:
    start_time: datetime
    publish_time: datetime
    generation: float  # MW


def parse_ts(value: str) -> datetime:
    """Parse an ISO-8601 timestamp (with or without 'Z') into an aware UTC datetime."""
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
