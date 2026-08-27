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

    # Dataset store (Phase 3)
    # Datasets are kept in memory only, keyed by a generated dataset_id.
    # No database — capped and LRU-evicted so memory can't grow unbounded
    # across repeated uploads within a running process.
    MAX_STORED_DATASETS: int = 5

    # Column profiling (Phase 3)
    # A column whose distinct/non-null ratio exceeds this is treated as an
    # identifier (e.g. an id/uuid column) and excluded from chart generation.
    IDENTIFIER_UNIQUENESS_RATIO: float = 0.95
    # Above this many distinct values, a text/categorical column is treated
    # as high-cardinality (excluded from grouping charts — it would produce
    # unreadable axes) rather than categorical.
    MAX_CATEGORICAL_CARDINALITY: int = 50
    # A datetime-looking text column must have at least this fraction of its
    # non-null values successfully parse as dates to be classified datetime.
    MIN_DATETIME_PARSE_RATIO: float = 0.9

    # Recommendation engine (Phase 3)
    # Per grouped bar/line chart, keep the top-N categories/buckets and fold
    # the remainder into a single "Other" bucket so axes stay readable.
    MAX_CATEGORIES_PER_CHART: int = 8
    # Categorical columns at or below this cardinality are also offered as
    # pie charts (proportion of whole); above it, only bar charts make sense.
    PIE_CHART_MAX_CATEGORIES: int = 6
    HISTOGRAM_BIN_COUNT: int = 12
    # Scatter plots are capped in point count (random sample) so payloads
    # stay small even for very large datasets.
    SCATTER_MAX_POINTS: int = 500
    SCATTER_MAX_PAIRS: int = 3
    TIMESERIES_MAX_PAIRS: int = 3
    MAX_RECOMMENDED_CHARTS: int = 8


settings = Settings()
