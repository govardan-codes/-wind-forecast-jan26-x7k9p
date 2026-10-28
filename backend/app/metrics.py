"""Forecast accuracy metrics. Convention: error = actual - forecast (same sign as the dashboard 'gap')."""
from math import sqrt
from typing import Optional, Sequence


def compute_metrics(pairs: Sequence[tuple[float, float]]) -> dict:
    """`pairs` are (actual, forecast) in MW. Returns MAE, RMSE, MAPE, bias and helpers."""
    n = len(pairs)
    if n == 0:
        return {"count": 0, "mae": None, "rmse": None, "mape": None, "bias": None, "nmae": None,
                "mapeCount": 0, "meanActual": None}
    errors = [a - f for a, f in pairs]
    mae = sum(abs(e) for e in errors) / n
    rmse = sqrt(sum(e * e for e in errors) / n)
    bias = sum(errors) / n
    pct = [abs(a - f) / a * 100 for a, f in pairs if a != 0]  # MAPE undefined where actual == 0
    mape: Optional[float] = sum(pct) / len(pct) if pct else None
    mean_actual = sum(a for a, _ in pairs) / n
    nmae = mae / mean_actual * 100 if mean_actual else None
    return {"count": n, "mae": mae, "rmse": rmse, "mape": mape, "bias": bias, "nmae": nmae,
            "mapeCount": len(pct), "meanActual": mean_actual}
