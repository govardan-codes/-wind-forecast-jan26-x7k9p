import json
from datetime import date, datetime, timezone

import httpx

from app.elexon import ElexonClient, _chunks


def make_client(handler) -> ElexonClient:
    return ElexonClient("https://example.test/api", client=httpx.Client(transport=httpx.MockTransport(handler)),
                        retries=1, backoff=0)


def test_chunks_cover_range_without_overlap():
    assert list(_chunks(date(2026, 1, 1), date(2026, 1, 10), 7)) == [
        (date(2026, 1, 1), date(2026, 1, 7)), (date(2026, 1, 8), date(2026, 1, 10))]


def test_actuals_filter_wind_and_keep_latest_publish():
    rows = [
        {"fuelType": "WIND", "startTime": "2026-01-01T00:00:00Z", "publishTime": "2026-01-01T00:10:00Z", "generation": 100},
        {"fuelType": "WIND", "startTime": "2026-01-01T00:00:00Z", "publishTime": "2026-01-01T00:20:00Z", "generation": 110},
        {"fuelType": "CCGT", "startTime": "2026-01-01T00:00:00Z", "publishTime": "2026-01-01T00:10:00Z", "generation": 999},
    ]
    client = make_client(lambda req: httpx.Response(200, content=json.dumps(rows)))
    out = client.fetch_actuals(date(2026, 1, 1), date(2026, 1, 1))
    assert [(a.start_time.isoformat(), a.generation) for a in out] == [("2026-01-01T00:00:00+00:00", 110.0)]


def test_forecasts_parsed_and_null_generation_skipped():
    rows = [
        {"startTime": "2026-01-02T00:00:00Z", "publishTime": "2026-01-01T12:00:00Z", "generation": 500},
        {"startTime": "2026-01-02T00:30:00Z", "publishTime": "2026-01-01T12:00:00Z", "generation": None},
    ]
    client = make_client(lambda req: httpx.Response(200, content=json.dumps(rows)))
    out = client.fetch_forecasts(datetime(2026, 1, 1, tzinfo=timezone.utc), datetime(2026, 1, 1, tzinfo=timezone.utc))
    assert len(out) == 1 and out[0].generation == 500.0


def test_http_error_raises_clear_message():
    client = make_client(lambda req: httpx.Response(500))
    try:
        client.fetch_actuals(date(2026, 1, 1), date(2026, 1, 1))
    except RuntimeError as exc:
        assert "Elexon request failed" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")
