"""Runtime configuration, read from environment variables with safe defaults."""
import os
from dataclasses import dataclass
from datetime import date
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    # Elexon Insights API host (the docs site is bmrs.elexon.co.uk, the data API is data.elexon.co.uk)
    elexon_base_url: str = "https://data.elexon.co.uk/bmrs/api/v1"
    request_timeout: float = 60.0
    # Challenge scope: decisions made for delivery days in January 2026 only
    scope_start: date = date(2026, 1, 1)
    scope_end: date = date(2026, 1, 31)
    # Day-ahead cutoff policy: "per_slot" (publishTime < startTime - horizon) or "day_ahead" (fixed gate on D-1)
    cutoff_mode: str = "per_slot"
    horizon_hours: float = 12.0
    gate_hour_utc: int = 10  # only used by "day_ahead" mode (approximate GB auction gate, UK = UTC in January)
    # "elexon" = live API (cached to disk), "sample" = synthetic demo data (offline)
    data_source: str = "elexon"
    cache_dir: str = "./data_cache"
    cors_origins: tuple = ("http://localhost:5173", "http://localhost:3000")


@lru_cache
def get_settings() -> Settings:
    origins = os.getenv("CORS_ORIGINS")
    return Settings(
        elexon_base_url=os.getenv("ELEXON_BASE_URL", Settings.elexon_base_url),
        cutoff_mode=os.getenv("CUTOFF_MODE", Settings.cutoff_mode),
        horizon_hours=float(os.getenv("HORIZON_HOURS", Settings.horizon_hours)),
        gate_hour_utc=int(os.getenv("GATE_HOUR_UTC", Settings.gate_hour_utc)),
        data_source=os.getenv("DATA_SOURCE", Settings.data_source),
        cache_dir=os.getenv("CACHE_DIR", Settings.cache_dir),
        cors_origins=tuple(o.strip() for o in origins.split(",")) if origins else Settings.cors_origins,
    )
