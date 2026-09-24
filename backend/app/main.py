from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, companies, data_management, data_sources, dataset, health, realtime
from app.core.config import settings
from app.db.session import init_db
from app.services.sync_worker import sync_worker

# Initialize database tables on startup
init_db()

app = FastAPI(
    title=settings.APP_NAME,
    description="DataScope Multi-Tenant Business Intelligence & Real-Time Decision Intelligence Platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(companies.router, prefix="/api")
app.include_router(data_sources.router)
app.include_router(data_management.router, prefix="/api")
app.include_router(realtime.router, prefix="/api")
app.include_router(dataset.router, prefix="/api")


@app.on_event("startup")
async def on_startup():
    await sync_worker.start()


@app.on_event("shutdown")
async def on_shutdown():
    await sync_worker.stop()


@app.get("/")
def root():
    return {
        "service": settings.APP_NAME,
        "status": "running",
        "version": "1.0.0",
        "multi_tenant": True,
        "realtime": True,
        "live_sync": True,
    }

