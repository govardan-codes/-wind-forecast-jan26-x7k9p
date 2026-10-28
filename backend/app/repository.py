"""In-memory data store, populated from a disk cache, the live Elexon API, or synthetic sample data."""
import json
import threading
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from typing import Iterable, Optional

from . import sample_data
from .config import Settings
from .domain import Actual, Forecast, parse_ts
from .elexon import ElexonClient
from .forecast_logic import ForecastIndex


class DataStore:
    def __init__(self, source: str = "elexon"):
        self.source = source
        self.status = "loading"  # loading | ready | error
        self.error: Optional[str] = None
        self.actuals: dict[datetime, float] = {}
        self.index = ForecastIndex([])

    def set_data(self, actuals: Iterable[Actual], forecasts: Iterable[Forecast]) -> None:
        self.actuals = {a.start_time: a.generation for a in actuals}
        self.index = ForecastIndex(forecasts)
        self.status, self.error = "ready", None

    # ---- loading -----------------------------------------------------------------
    def load(self, settings: Settings, client: Optional[ElexonClient] = None) -> None:
        try:
            actuals, forecasts = _load_dataset(settings, client)
            self.set_data(actuals, forecasts)
        except Exception as exc:  # surfaced via /api/health, never crashes the server
            self.status, self.error = "error", str(exc)

    def load_in_background(self, settings: Settings) -> threading.Thread:
        t = threading.Thread(target=self.load, args=(settings,), daemon=True)
        t.start()
        return t


def _load_dataset(settings: Settings, client: Optional[ElexonClient]) -> tuple[list[Actual], list[Forecast]]:
    s, e = settings.scope_start, settings.scope_end
    if settings.data_source == "sample":
        return sample_data.generate(s, e)

    cache = Path(settings.cache_dir) / f"elexon_wind_{s}_{e}.json"
    if cache.exists():
        raw = json.loads(cache.read_text())
        return ([Actual(parse_ts(a["t"]), a["g"]) for a in raw["actuals"]],
                [Forecast(parse_ts(f["t"]), parse_ts(f["p"]), f["g"]) for f in raw["forecasts"]])

    client = client or ElexonClient(settings.elexon_base_url, settings.request_timeout)
    actuals = client.fetch_actuals(s, e)
    pub_from = datetime.combine(s, time(0), tzinfo=timezone.utc) - timedelta(days=3)
    pub_to = datetime.combine(e, time(0), tzinfo=timezone.utc) + timedelta(days=1)
    forecasts = client.fetch_forecasts(pub_from, pub_to)
    # keep only forecasts that target slots inside the scope window
    lo = datetime.combine(s, time(0), tzinfo=timezone.utc)
    hi = datetime.combine(e + timedelta(days=1), time(0), tzinfo=timezone.utc)
    forecasts = [f for f in forecasts if lo <= f.start_time < hi]
    if not actuals or not forecasts:
        raise RuntimeError("Elexon returned no wind actuals/forecasts for the requested window")

    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({
        "actuals": [{"t": a.start_time.isoformat(), "g": a.generation} for a in actuals],
        "forecasts": [{"t": f.start_time.isoformat(), "p": f.publish_time.isoformat(), "g": f.generation}
                      for f in forecasts]}))
    return actuals, forecasts
