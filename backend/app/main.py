import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database.connection import init_db
from app.api.health import router as health_router
from app.api.documents import router as documents_router
from app.api.facts import router as facts_router
from app.api.relationships import router as relationships_router
from app.api.overview import router as overview_router

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("factlens")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing FactLens database schema...")
    try:
        init_db()
        logger.info("Database schema initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
    yield
    logger.info("FactLens API shutting down.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Evidence-Grounded Cross-Document Fact Resolution Knowledge Layer",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Supports Vercel preview URLs, localhost, and custom domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health_router)
app.include_router(documents_router, prefix="/api")
app.include_router(facts_router, prefix="/api")
app.include_router(relationships_router, prefix="/api")
app.include_router(overview_router, prefix="/api")


@app.api_route("/", methods=["GET", "HEAD"])
def root():
    return {
        "service": "FactLens API",
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "health_url": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=(settings.ENVIRONMENT == "development")
    )
