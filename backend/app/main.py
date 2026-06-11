from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.health import router as health_router
from app.core.config import get_settings
from app.core.database import engine
from app.core.logging import configure_logging
from app.domains.codes.router import admin_router as codes_admin_router
from app.domains.codes.router import router as codes_router
from app.domains.prizes.router import admin_router as prizes_admin_router
from app.domains.prizes.router import router as prizes_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(debug=settings.debug)
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(codes_router, prefix="/api/v1/codes", tags=["codes"])
app.include_router(codes_admin_router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(prizes_router, prefix="/api/v1/prizes", tags=["prizes"])
app.include_router(prizes_admin_router, prefix="/api/v1/admin", tags=["admin"])
