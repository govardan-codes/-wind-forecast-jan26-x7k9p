"""API response schemas."""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class ActualPoint(BaseModel):
    startTime: datetime
    generation: float


class ForecastPoint(BaseModel):
    startTime: datetime
    publishTime: datetime
    generation: float
    horizonHours: float


class DecisionPoint(BaseModel):
    startTime: datetime
    forecast: Optional[float] = None
    publishTime: Optional[datetime] = None
    actual: Optional[float] = None
    gap: Optional[float] = None  # actual - forecast (MW)


class DecisionSummary(BaseModel):
    forecastMwh: float
    actualMwh: float
    netGapMwh: float
    shortfallMwh: float  # energy by which wind under-delivered vs forecast (to be bought elsewhere)
    surplusMwh: float
    slotsWithForecast: int
    slotsWithActual: int


class DecisionResponse(BaseModel):
    deliveryDate: date
    cutoffRule: str
    points: list[DecisionPoint]
    summary: DecisionSummary


class SlotError(BaseModel):
    startTime: datetime
    actual: float
    forecast: float
    error: float  # actual - forecast
    absError: float
    pctError: Optional[float] = None


class Metrics(BaseModel):
    count: int
    mae: Optional[float] = None
    rmse: Optional[float] = None
    mape: Optional[float] = None
    bias: Optional[float] = None
    nmae: Optional[float] = None
    mapeCount: int = 0
    meanActual: Optional[float] = None


class EvaluationResponse(BaseModel):
    month: str
    cutoffRule: str
    metrics: Metrics
    slots: list[SlotError]


class Health(BaseModel):
    status: str
    source: str
    error: Optional[str] = None
