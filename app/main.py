import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.api import auth
from app.core.db import engine

logger = logging.getLogger(__name__)


async def ping_db(async_engine):
    async with async_engine.connect() as conn:
        _ = await conn.execute(text("SELECT 1;"))
        logger.info("Database connection established")


@asynccontextmanager
async def lifespan(application: FastAPI):
    try:
        await ping_db(engine)
    except Exception:
        logger.exception("Failed to establish database connection")
        raise

    yield
    await engine.dispose()


app = FastAPI(
    title="Fin Ledger",
    lifespan=lifespan,
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
)


app.include_router(auth.router)
