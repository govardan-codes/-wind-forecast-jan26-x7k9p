from datetime import date, datetime, timezone

from app.domain import Forecast
from app.forecast_logic import ForecastIndex, cutoff_for, slots_for_day

UTC = timezone.utc
START = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)


def fc(publish: datetime, gen: float, start: datetime = START) -> Forecast:
    return Forecast(start, publish, gen)


def test_picks_latest_forecast_before_cutoff():
    idx = ForecastIndex([
        fc(datetime(2026, 1, 14, 6, 0, tzinfo=UTC), 100),
        fc(datetime(2026, 1, 14, 23, 0, tzinfo=UTC), 200),  # latest before cutoff (00:00 on the 15th)
        fc(datetime(2026, 1, 15, 3, 0, tzinfo=UTC), 300),   # after cutoff -> unusable
    ])
    assert idx.latest_before_cutoff(START).generation == 200


def test_cutoff_is_strictly_exclusive():
    cutoff = datetime(2026, 1, 15, 0, 0, tzinfo=UTC)  # START - 12h
    idx = ForecastIndex([fc(datetime(2026, 1, 14, 20, 0, tzinfo=UTC), 1), fc(cutoff, 2)])
    assert idx.latest_before_cutoff(START).generation == 1


def test_returns_none_when_nothing_available_in_time():
    idx = ForecastIndex([fc(datetime(2026, 1, 15, 6, 0, tzinfo=UTC), 5)])
    assert idx.latest_before_cutoff(START) is None
    assert idx.latest_before_cutoff(datetime(2030, 1, 1, tzinfo=UTC)) is None


def test_day_ahead_gate_mode():
    assert cutoff_for(START, "day_ahead", gate_hour_utc=10) == datetime(2026, 1, 14, 10, 0, tzinfo=UTC)
    idx = ForecastIndex([fc(datetime(2026, 1, 14, 9, 0, tzinfo=UTC), 1), fc(datetime(2026, 1, 14, 11, 0, tzinfo=UTC), 2)])
    assert idx.latest_before_cutoff(START, "day_ahead", gate_hour_utc=10).generation == 1


def test_duplicate_publications_are_collapsed():
    t = datetime(2026, 1, 14, 6, 0, tzinfo=UTC)
    assert len(ForecastIndex([fc(t, 1), fc(t, 2)])) == 1


def test_slots_for_day_has_48_half_hours():
    slots = slots_for_day(date(2026, 1, 15))
    assert len(slots) == 48 and slots[0].hour == 0 and slots[-1].hour == 23 and slots[-1].minute == 30
