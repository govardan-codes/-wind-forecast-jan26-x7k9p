import math

from app.metrics import compute_metrics


def test_known_values():
    # (actual, forecast): errors (actual - forecast) = +10, -20, 0, +10
    m = compute_metrics([(110, 100), (80, 100), (100, 100), (110, 100)])
    assert m["count"] == 4
    assert math.isclose(m["mae"], 10.0)
    assert math.isclose(m["rmse"], math.sqrt((100 + 400 + 0 + 100) / 4))
    assert math.isclose(m["bias"], 0.0)
    assert math.isclose(m["mape"], (10 / 110 + 20 / 80 + 0 + 10 / 110) / 4 * 100)


def test_bias_sign_positive_means_under_forecast():
    assert compute_metrics([(120, 100)])["bias"] == 20


def test_mape_skips_zero_actuals():
    m = compute_metrics([(0, 10), (100, 90)])
    assert m["mapeCount"] == 1 and math.isclose(m["mape"], 10.0) and m["count"] == 2


def test_empty_input():
    m = compute_metrics([])
    assert m["count"] == 0 and m["mae"] is None and m["rmse"] is None
