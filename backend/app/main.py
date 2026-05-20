from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import router as api_v1_router
from app.config import get_settings
from app.db import init_db
from app.logging_config import configure_logging
from app.scheduler import start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    start_scheduler()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.debug)

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/docs",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url, "http://localhost:5173", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_v1_router)
    return app


app = create_app()
