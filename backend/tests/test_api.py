from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.api import get_any_store
from app.domain import Actual, Forecast
from app.main import app
from app.repository import DataStore

UTC = timezone.utc
T0 = datetime(2026, 1, 15, 0, 0, tzinfo=UTC)


def build_store() -> DataStore:
    store = DataStore(source="test")
    actuals = [Actual(T0, 1000.0), Actual(T0 + timedelta(minutes=30), 800.0), Actual(datetime(2026, 1, 20, tzinfo=UTC), 5.0)]
    forecasts = [
        Forecast(T0, T0 - timedelta(hours=20), 900.0),            # usable
        Forecast(T0, T0 - timedelta(hours=11), 111.0),            # too late (inside the 12h window)
        Forecast(T0 + timedelta(minutes=30), T0 - timedelta(hours=14), 1000.0),
    ]
    store.set_data(actuals, forecasts)
    return store


def client() -> TestClient:
    store = build_store()
    app.dependency_overrides[get_any_store] = lambda: store
    return TestClient(app)


def test_actuals_filters_range():
    r = client().get("/api/actuals", params={"from": "2026-01-15", "to": "2026-01-15"})
    assert r.status_code == 200 and [p["generation"] for p in r.json()] == [1000.0, 800.0]


def test_actuals_rejects_out_of_scope_and_bad_range():
    c = client()
    assert c.get("/api/actuals", params={"from": "2025-12-31", "to": "2026-01-02"}).status_code == 422
    assert c.get("/api/actuals", params={"from": "2026-01-10", "to": "2026-01-05"}).status_code == 422


def test_forecasts_respect_day_ahead_cutoff():
    r = client().get("/api/forecasts", params={"deliveryDate": "2026-01-15"})
    body = r.json()
    assert r.status_code == 200 and [p["generation"] for p in body] == [900.0, 1000.0]
    assert body[0]["horizonHours"] == 20.0


def test_decision_gap_is_actual_minus_forecast():
    r = client().get("/api/decision", params={"deliveryDate": "2026-01-15"})
    pts = r.json()["points"]
    assert len(pts) == 48 and pts[0]["gap"] == 100.0 and pts[1]["gap"] == -200.0 and pts[2]["gap"] is None
    s = r.json()["summary"]
    assert s["shortfallMwh"] == 100.0 and s["surplusMwh"] == 50.0 and s["netGapMwh"] == -50.0


def test_evaluation_metrics():
    r = client().get("/api/evaluation", params={"month": "2026-01"})
    body = r.json()
    assert r.status_code == 200 and body["metrics"]["count"] == 2
    assert body["metrics"]["mae"] == 150.0 and body["metrics"]["bias"] == -50.0
    assert [s["error"] for s in body["slots"]] == [100.0, -200.0]


def test_evaluation_validation():
    c = client()
    assert c.get("/api/evaluation", params={"month": "2026-13"}).status_code == 422
    assert c.get("/api/evaluation", params={"month": "2025-06"}).status_code == 422
    assert c.get("/api/evaluation", params={"month": "bad"}).status_code == 422


def test_loading_state_returns_503():
    loading = DataStore(source="test")
    app.dependency_overrides[get_any_store] = lambda: loading
    c = TestClient(app)
    assert c.get("/api/health").json()["status"] == "loading"
    assert c.get("/api/decision", params={"deliveryDate": "2026-01-15"}).status_code == 503
