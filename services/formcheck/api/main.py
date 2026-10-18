from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from formcheck.api.routes import router
from formcheck.config import get_settings
from formcheck.db import init_db
from formcheck.storage import ObjectStorage

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("formcheck.api")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    init_db()
    try:
        storage = ObjectStorage(settings)
        storage.ensure_bucket()
    except Exception:
        logger.exception("MinIO bucket bootstrap failed; uploads may fail until MinIO is ready")
    # Import broker so API process can enqueue Dramatiq messages
    from formcheck.worker import broker as _broker  # noqa: F401

    yield


app = FastAPI(
    title="FormCheck API",
    version="0.1.0",
    lifespan=lifespan,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
