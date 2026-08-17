from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import dataset, health
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    description="DataScope backend API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(dataset.router, prefix="/api")


@app.get("/")
def root():
    return {"service": settings.APP_NAME, "status": "running"}
