"""FastAPI application entrypoint."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import router, set_store
from .config import get_settings
from .repository import DataStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    store = DataStore(source=settings.data_source)
    set_store(store)
    store.load_in_background(settings)  # non-blocking: /api/health reports loading|ready|error
    yield


app = FastAPI(title="Gridbricks Wind Forecast API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=list(get_settings().cors_origins),
                   allow_methods=["GET"], allow_headers=["*"])
app.include_router(router)
