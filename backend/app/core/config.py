import os
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Explicitly load .env file from backend directory
_backend_env = Path(__file__).resolve().parent.parent.parent / ".env"
if _backend_env.exists():
    load_dotenv(dotenv_path=_backend_env, override=True)
else:
    load_dotenv(override=True)


class Settings(BaseSettings):
    APP_NAME: str = "DataScope Enterprise Platform"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Supabase Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "")
    SUPABASE_DB_URL: str = os.getenv("SUPABASE_DB_URL", "")

    # Database Configuration (Supabase PostgreSQL / SQLite fallback for isolated test suites)
    DATABASE_URL: str = os.getenv("DATABASE_URL", os.getenv("SUPABASE_DB_URL", "sqlite:///./datascope.db"))
    DATABASE_URL_TEST: str = os.getenv("DATABASE_URL_TEST", "sqlite:///./test_datascope.db")

    # Authentication & Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "datascope-super-secret-key-change-in-production-2026-secure-jwt")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Google OAuth 2.0 Credentials
    GOOGLE_CLIENT_ID: Optional[str] = os.getenv("GOOGLE_CLIENT_ID", None)
    GOOGLE_CLIENT_SECRET: Optional[str] = os.getenv("GOOGLE_CLIENT_SECRET", None)
    GOOGLE_REDIRECT_URI: Optional[str] = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:5173/auth/google/callback")

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ]

    # Dataset upload configuration
    MAX_UPLOAD_SIZE_MB: int = 25
    ALLOWED_EXTENSIONS: Dict[str, str] = {
        ".csv": "csv",
        ".xlsx": "xlsx",
        ".xls": "xls",
        ".json": "json",
    }
    PREVIEW_ROW_COUNT: int = 15

    # In-memory Dataset LRU cache capacity for high-speed calculation acceleration
    MAX_STORED_DATASETS: int = 20

    # Column profiling & AI recommendations
    IDENTIFIER_UNIQUENESS_RATIO: float = 0.95
    MAX_CATEGORICAL_CARDINALITY: int = 50
    MIN_DATETIME_PARSE_RATIO: float = 0.9
    MAX_CATEGORIES_PER_CHART: int = 8
    PIE_CHART_MAX_CATEGORIES: int = 6
    HISTOGRAM_BIN_COUNT: int = 12
    SCATTER_MAX_POINTS: int = 500
    SCATTER_MAX_PAIRS: int = 3
    TIMESERIES_MAX_PAIRS: int = 3
    MAX_RECOMMENDED_CHARTS: int = 8

    class Config:
        case_sensitive = True
        extra = "allow"


settings = Settings()
