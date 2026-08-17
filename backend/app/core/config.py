class Settings:
    APP_NAME: str = "DataScope API"
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Dataset upload configuration (Phase 2)
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: dict[str, str] = {
        ".csv": "csv",
        ".xlsx": "xlsx",
        ".xls": "xls",
    }
    PREVIEW_ROW_COUNT: int = 10


settings = Settings()
