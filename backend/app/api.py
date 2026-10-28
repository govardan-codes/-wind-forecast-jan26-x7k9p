"""HTTP routes. Business logic lives in forecast_logic.py / metrics.py; this layer only validates and shapes."""
import calendar
from datetime import date, datetime, time, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from .config import Settings, get_settings
from .forecast_logic import SLOT, slots_for_day
from .metrics import compute_metrics
from .models import (ActualPoint, DecisionPoint, DecisionResponse, DecisionSummary, EvaluationResponse,
                     ForecastPoint, Health, Metrics, SlotError)
from .repository import DataStore

router = APIRouter(prefix="/api")

_store: Optional[DataStore] = None


def set_store(store: DataStore) -> None:
    global _store
    _store = store


def get_any_store() -> DataStore:
    if _store is None:
        raise HTTPException(503, "Data store not initialised")
    return _store


def get_store(store: DataStore = Depends(get_any_store)) -> DataStore:
    if store.status == "loading":
        raise HTTPException(503, "Data is still loading from Elexon - please retry in a few seconds")
    if store.status == "error":
        raise HTTPException(503, f"Data failed to load: {store.error}")
    return store


def _in_scope(d: date, s: Settings, label: str) -> None:
    if not (s.scope_start <= d <= s.scope_end):
        raise HTTPException(422, f"{label} must be between {s.scope_start} and {s.scope_end} (challenge scope)")


def _cutoff_rule(s: Settings) -> str:
    if s.cutoff_mode == "day_ahead":
        return f"Latest forecast published before {s.gate_hour_utc:02d}:00 UTC on the day before delivery"
    return f"Latest forecast with publishTime < startTime - {s.horizon_hours:g}h"


def _latest(store: DataStore, s: Settings, start: datetime):
    return store.index.latest_before_cutoff(start, s.cutoff_mode, s.horizon_hours, s.gate_hour_utc)


@router.get("/health", response_model=Health)
def health(store: DataStore = Depends(get_any_store)):
    return Health(status=store.status, source=store.source, error=store.error)


@router.get("/actuals", response_model=list[ActualPoint])
def actuals(from_: date = Query(..., alias="from"), to: date = Query(...),
            store: DataStore = Depends(get_store), s: Settings = Depends(get_settings)):
    if to < from_:
        raise HTTPException(422, "'to' must be on or after 'from'")
    _in_scope(from_, s, "from")
    _in_scope(to, s, "to")
    lo = datetime.combine(from_, time(0), tzinfo=timezone.utc)
    hi = datetime.combine(to + timedelta(days=1), time(0), tzinfo=timezone.utc)
    return [ActualPoint(startTime=t, generation=g) for t, g in sorted(store.actuals.items()) if lo <= t < hi]


@router.get("/forecasts", response_model=list[ForecastPoint])
def forecasts(deliveryDate: date = Query(...), store: DataStore = Depends(get_store),
              s: Settings = Depends(get_settings)):
    _in_scope(deliveryDate, s, "deliveryDate")
    out = []
    for start in slots_for_day(deliveryDate):
        f = _latest(store, s, start)
        if f:
            out.append(ForecastPoint(startTime=start, publishTime=f.publish_time, generation=f.generation,
                                     horizonHours=(start - f.publish_time).total_seconds() / 3600))
    return out


@router.get("/decision", response_model=DecisionResponse)
def decision(deliveryDate: date = Query(...), store: DataStore = Depends(get_store),
             s: Settings = Depends(get_settings)):
    """Forecast available at decision time joined with the eventual actual, per slot (powers the dashboard)."""
    _in_scope(deliveryDate, s, "deliveryDate")
    points, fc_mwh, act_mwh, net, short, surplus, n_f, n_a = [], 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0
    hours = SLOT.total_seconds() / 3600
    for start in slots_for_day(deliveryDate):
        f = _latest(store, s, start)
        a = store.actuals.get(start)
        gap = (a - f.generation) if (f is not None and a is not None) else None
        points.append(DecisionPoint(startTime=start, forecast=f.generation if f else None,
                                    publishTime=f.publish_time if f else None, actual=a, gap=gap))
        if f:
            n_f += 1
            fc_mwh += f.generation * hours
        if a is not None:
            n_a += 1
            act_mwh += a * hours
        if gap is not None:
            net += gap * hours
            short += max(0.0, -gap) * hours
            surplus += max(0.0, gap) * hours
    return DecisionResponse(deliveryDate=deliveryDate, cutoffRule=_cutoff_rule(s), points=points,
                            summary=DecisionSummary(forecastMwh=fc_mwh, actualMwh=act_mwh, netGapMwh=net,
                                                    shortfallMwh=short, surplusMwh=surplus,
                                                    slotsWithForecast=n_f, slotsWithActual=n_a))


@router.get("/evaluation", response_model=EvaluationResponse)
def evaluation(month: str = Query(..., pattern=r"^\d{4}-\d{2}$"), store: DataStore = Depends(get_store),
               s: Settings = Depends(get_settings)):
    try:
        first = datetime.strptime(month, "%Y-%m").date()
    except ValueError:
        raise HTTPException(422, "month must be YYYY-MM")
    last = first.replace(day=calendar.monthrange(first.year, first.month)[1])
    if last < s.scope_start or first > s.scope_end:
        raise HTTPException(422, f"month must overlap {s.scope_start}..{s.scope_end} (challenge scope)")
    lo = datetime.combine(first, time(0), tzinfo=timezone.utc)
    hi = datetime.combine(last + timedelta(days=1), time(0), tzinfo=timezone.utc)

    slots, pairs = [], []
    for start, actual in sorted(store.actuals.items()):
        if not (lo <= start < hi):
            continue
        f = _latest(store, s, start)
        if f is None:
            continue
        err = actual - f.generation
        slots.append(SlotError(startTime=start, actual=actual, forecast=f.generation, error=err, absError=abs(err),
                               pctError=abs(err) / actual * 100 if actual != 0 else None))
        pairs.append((actual, f.generation))
    return EvaluationResponse(month=month, cutoffRule=_cutoff_rule(s), metrics=Metrics(**compute_metrics(pairs)),
                              slots=slots)
