"""Thin client for the Elexon Insights (BMRS) API: FUELHH (actuals) and WINDFOR (forecasts)."""
import time as _time
from datetime import date, datetime, timedelta, timezone
from typing import Iterator, Optional

import httpx

from .domain import Actual, Forecast, parse_ts


def _chunks(start: date, end: date, days: int) -> Iterator[tuple[date, date]]:
    """Split [start, end] (inclusive) into windows of at most `days` days."""
    cur = start
    while cur <= end:
        nxt = min(cur + timedelta(days=days - 1), end)
        yield cur, nxt
        cur = nxt + timedelta(days=1)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class ElexonClient:
    def __init__(self, base_url: str, timeout: float = 60.0, client: Optional[httpx.Client] = None,
                 retries: int = 3, backoff: float = 1.5):
        self._base = base_url.rstrip("/")
        self._client = client or httpx.Client(timeout=timeout)
        self._retries = retries
        self._backoff = backoff

    def _get_json(self, path: str, params: dict) -> list[dict]:
        last_exc: Optional[Exception] = None
        for attempt in range(self._retries):
            try:
                resp = self._client.get(f"{self._base}{path}", params={**params, "format": "json"})
                resp.raise_for_status()
                body = resp.json()
                return body["data"] if isinstance(body, dict) else body  # stream = list, non-stream = {"data": [...]}
            except (httpx.HTTPError, ValueError) as exc:
                last_exc = exc
                _time.sleep(self._backoff ** attempt)
        raise RuntimeError(f"Elexon request failed for {path}: {last_exc}")

    def fetch_actuals(self, start: date, end: date, chunk_days: int = 7) -> list[Actual]:
        """Wind outturn per 30-min slot (FUELHH, fuelType=WIND). Latest publish wins on duplicates."""
        latest: dict[datetime, tuple[datetime, float]] = {}
        for lo, hi in _chunks(start, end, chunk_days):
            rows = self._get_json("/datasets/FUELHH/stream", {
                "settlementDateFrom": lo.isoformat(), "settlementDateTo": hi.isoformat(), "fuelType": "WIND"})
            for r in rows:
                if r.get("fuelType") != "WIND" or r.get("generation") is None:
                    continue
                st = parse_ts(r["startTime"])
                pub = parse_ts(r.get("publishTime") or r["startTime"])
                if st not in latest or pub >= latest[st][0]:
                    latest[st] = (pub, float(r["generation"]))
        return [Actual(st, gen) for st, (_, gen) in sorted(latest.items())]

    def fetch_forecasts(self, publish_from: datetime, publish_to: datetime, chunk_days: int = 3) -> list[Forecast]:
        """Every wind forecast revision published in the window (WINDFOR)."""
        out: list[Forecast] = []
        for lo, hi in _chunks(publish_from.date(), publish_to.date(), chunk_days):
            rows = self._get_json("/datasets/WINDFOR/stream", {
                "publishDateTimeFrom": _iso(datetime.combine(lo, datetime.min.time(), tzinfo=timezone.utc)),
                "publishDateTimeTo": _iso(datetime.combine(hi + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc))})
            for r in rows:
                if r.get("generation") is None:
                    continue
                out.append(Forecast(parse_ts(r["startTime"]), parse_ts(r["publishTime"]), float(r["generation"])))
        return out
