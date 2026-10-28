"""Deterministic synthetic data so the app can be demoed offline (DATA_SOURCE=sample). NOT real Elexon data."""
import math
import random
from datetime import date, datetime, time, timedelta, timezone

from .domain import Actual, Forecast
from .forecast_logic import SLOT


def generate(start: date, end: date, seed: int = 42) -> tuple[list[Actual], list[Forecast]]:
    rng = random.Random(seed)
    t0 = datetime.combine(start, time(0), tzinfo=timezone.utc)
    t1 = datetime.combine(end + timedelta(days=1), time(0), tzinfo=timezone.utc)

    def truth(t: datetime) -> float:
        h = (t - t0).total_seconds() / 3600
        return max(0.0, 6000 + 3500 * math.sin(h / 31) + 1500 * math.sin(h / 7.3 + 1))

    actuals, forecasts = [], []
    t = t0
    while t < t1:
        actuals.append(Actual(t, round(max(0.0, truth(t) + rng.gauss(0, 150)), 1)))
        t += SLOT
    p = t0 - timedelta(days=3)
    while p < t1:  # hourly publications, 48h look-ahead; error grows with horizon
        for k in range(1, 97):
            target = p + k * SLOT
            if t0 <= target < t1:
                sigma = 150 + 25 * k
                forecasts.append(Forecast(target, p, round(max(0.0, truth(target) + rng.gauss(0, sigma)), 1)))
        p += timedelta(hours=1)
    return actuals, forecasts
