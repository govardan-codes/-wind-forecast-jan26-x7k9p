"""Core business rule: which forecast was the latest one available at decision time?

A buyer must commit in the day-ahead market *before* delivery, so for each 30-minute
slot we only may use forecasts published strictly before a cutoff, and we want the
most recent of those.
"""
from bisect import bisect_left
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from typing import Iterable, Optional

from .domain import Forecast

SLOT = timedelta(minutes=30)


def cutoff_for(start: datetime, mode: str = "per_slot", horizon_hours: float = 12.0, gate_hour_utc: int = 10) -> datetime:
    """Latest publish time (exclusive) a forecast may have to be usable for the slot starting at `start`."""
    if mode == "per_slot":
        return start - timedelta(hours=horizon_hours)
    if mode == "day_ahead":  # fixed gate on the previous calendar day
        prev_day = start.date() - timedelta(days=1)
        return datetime.combine(prev_day, time(gate_hour_utc), tzinfo=timezone.utc)
    raise ValueError(f"Unknown cutoff mode: {mode}")


def slots_for_day(day: date) -> list[datetime]:
    """The 48 half-hourly slot start times (UTC) of a delivery day."""
    first = datetime.combine(day, time(0), tzinfo=timezone.utc)
    return [first + i * SLOT for i in range(48)]


class ForecastIndex:
    """Forecasts grouped by target slot and sorted by publish time for fast lookup."""

    def __init__(self, forecasts: Iterable[Forecast]):
        grouped: dict[datetime, dict[datetime, Forecast]] = defaultdict(dict)
        for f in forecasts:
            grouped[f.start_time][f.publish_time] = f  # de-duplicate identical (slot, publishTime)
        self._items = {s: sorted(d.values(), key=lambda f: f.publish_time) for s, d in grouped.items()}
        self._keys = {s: [f.publish_time for f in items] for s, items in self._items.items()}

    def __len__(self) -> int:
        return sum(len(v) for v in self._items.values())

    def latest_before_cutoff(self, start: datetime, mode: str = "per_slot", horizon_hours: float = 12.0,
                             gate_hour_utc: int = 10) -> Optional[Forecast]:
        keys = self._keys.get(start)
        if not keys:
            return None
        cutoff = cutoff_for(start, mode, horizon_hours, gate_hour_utc)
        i = bisect_left(keys, cutoff)  # keys[:i] are strictly earlier than cutoff
        return self._items[start][i - 1] if i > 0 else None
