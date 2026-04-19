import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.security import setup_rate_limiting
from app.core.scheduler import scheduler
from app.controllers import prediction_controller

logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Healthcare ML Pipeline")

    try:
        if settings.app_env == "production":
            scheduler.start()
            logger.info("Scheduler started")

        yield

    finally:
        logger.info("Shutting down Healthcare ML Pipeline")
        scheduler.shutdown()


def create_application() -> FastAPI:

    app = FastAPI(
        title="Healthcare ML Pipeline API",
        description="Production-ready ML inference and retraining system",
        version="1.0.0",
        docs_url="/docs" if settings.app_env != "production" else None,
        redoc_url="/redoc" if settings.app_env != "production" else None,
        lifespan=lifespan
    )

    origins = (
        ["https://clinical-sanctuary-web.vercel.app/"]
        if settings.app_env == "production"
        else ["*"]
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    setup_rate_limiting(app)

    app.include_router(prediction_controller.router)

    return app


app = create_application()


@app.get("/")
async def root():
    return {
        "name": "Healthcare ML Pipeline API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs" if settings.app_env != "production" else None
    }