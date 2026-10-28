# Gridbricks Wind Desk - Day-ahead wind forecast decision support

Web app for a UK utility's day-ahead power buying team. It answers two questions using national **Elexon wind** data for **January 2026**:

1. **Decision Dashboard** - what was the latest wind forecast *available when the buying decision had to be made*, and how did it compare with what wind actually delivered (gap = actual - forecast)?
2. **Accuracy Dashboard** - how accurate were those forecasts (MAE, RMSE, MAPE, bias, error over time, forecast-vs-actual scatter)?

- **Live app:** `<ADD VERCEL LINK HERE>` (API: `<ADD RENDER LINK HERE>`)
- **Demo video:** `<ADD UNLISTED YOUTUBE LINK HERE>`

## Run it

```bash
docker-compose up --build
# app:  http://localhost:3000      API docs: http://localhost:8000/docs
```

The first start downloads January 2026 wind data from Elexon (cached in a Docker volume afterwards). The UI shows a banner while loading. For an offline demo with **synthetic** data (clearly flagged in the UI): `DATA_SOURCE=sample docker-compose up --build`.

Without Docker:

```bash
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload      # :8000
cd frontend && npm install && npm run dev                                          # :5173 (proxies /api)
cd backend && pytest                                                               # tests
```

## Key design decisions

| Topic | Decision |
|---|---|
| Decision-time rule | For each 30-min slot, use the **latest forecast with `publishTime < startTime - 12h`** (strict). Configurable: `HORIZON_HOURS`, or `CUTOFF_MODE=day_ahead` for a fixed gate (default 10:00 UTC on D-1; approximate GB auction gate). |
| Sign convention | `gap = error = actual - forecast`, used everywhere. Negative = wind under-delivered, so extra power must be bought. Positive bias = forecasts too low. |
| MAPE | Slots with zero actual are excluded (count reported). Wind MAPE is unstable at low output, so MAE as % of mean wind (nMAE) is also shown. |
| Time | All times UTC (equal to UK time in January, so no DST handling is needed for this scope). |
| Data loading | Loaded once in the background at start, cached to disk. `/api/health` reports `loading/ready/error`; data endpoints return 503 until ready and the UI retries. |
| Scope | Requests outside Jan 2026 are rejected with 422 (`scope_start/scope_end` in `config.py`). |

## API

| Endpoint | Description |
|---|---|
| `GET /api/actuals?from=2026-01-01&to=2026-01-31` | WIND outturn per half hour (FUELHH) |
| `GET /api/forecasts?deliveryDate=2026-01-15` | Latest day-ahead-usable forecast per slot, with publish time and horizon |
| `GET /api/decision?deliveryDate=2026-01-15` | Forecast + actual + gap per slot and energy summary (powers page 1) |
| `GET /api/evaluation?month=2026-01` | MAE, RMSE, MAPE, bias, nMAE and per-slot errors |
| `GET /api/health` | Data load status |

## Files

```
docker-compose.yml          full stack (backend + nginx-served frontend)
render.yaml                 Render blueprint for the API
backend/
  app/config.py             env-driven settings (scope, cutoff rule, data source)
  app/domain.py             Actual / Forecast types, timestamp parsing
  app/forecast_logic.py     decision-time cutoff + latest-forecast-per-slot index (core rule)
  app/metrics.py            MAE / RMSE / MAPE / bias
  app/elexon.py             Elexon FUELHH + WINDFOR client (chunking, retries, dedupe)
  app/repository.py         in-memory store, disk cache, background load
  app/sample_data.py        synthetic data for offline demos
  app/models.py             response schemas
  app/api.py                routes + validation
  app/main.py               FastAPI app, CORS, startup load
  tests/                    pytest: cutoff logic, metrics, Elexon client (mocked HTTP), API
frontend/
  src/pages/DecisionDashboard.jsx    date picker, actual-vs-forecast chart, gap table
  src/pages/AccuracyDashboard.jsx    metric cards, error-over-time, scatter
  src/components/                    MetricCard, StatusBanner
  src/api.js, useApi.js, format.js   API client, data hook, formatting
  nginx.conf, Dockerfile, vercel.json
```

## Deployment

- **API on Render:** use `render.yaml` (Docker, root `backend`); set `CORS_ORIGINS` to the frontend URL. Free-tier disks are ephemeral, so each cold start re-downloads data (about a minute).
- **Frontend on Vercel:** root directory `frontend`, env `VITE_API_URL=<render url>`.

## Known limitations / next steps

- Single national wind series only (per scope); no demand or other fuel types.
- Elexon parameter names/limits should be re-verified against the live API if Elexon changes the stream endpoints (they are isolated in `app/elexon.py`).
- Ideas: forecast error by horizon, error bands on the decision chart, persisted database instead of in-memory cache.

## AI tools used

This project was built with AI assistance: **Claude (Anthropic)** was used to help design the architecture, write the code and tests, and draft this README. 
