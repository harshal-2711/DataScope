from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field


class ColumnInferenceSchema(BaseModel):
    name: str
    original_type: str
    inferred_type: str
    confidence: float
    missing_count: int
    missing_percentage: float
    unique_count: int
    sample_values: List[Any] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class FileDiagnosticsSchema(BaseModel):
    encoding_used: str = "utf-8"
    delimiter_used: str = ","
    duplicate_columns_renamed: List[str] = Field(default_factory=list)
    malformed_rows_skipped: int = 0
    warnings: List[str] = Field(default_factory=list)


class DatasetSummary(BaseModel):
    dataset_id: str = Field(
        description="Server-side id for this dataset. Pass to the "
        "recommendations endpoint to fetch auto-generated charts."
    )
    filename: str
    file_type: str
    row_count: int
    column_count: int
    columns: List[str]
    dtypes: Dict[str, str]
    inferred_columns: List[ColumnInferenceSchema] = Field(default_factory=list)
    diagnostics: Optional[FileDiagnosticsSchema] = None
    preview: List[Dict[str, Any]] = Field(
        description="First N rows of the dataset (N = settings.PREVIEW_ROW_COUNT)."
    )


ColumnRoleLiteral = Literal[
    "numeric", "categorical", "datetime", "boolean",
    "identifier", "high_cardinality", "ignore",
]


class ColumnProfileSchema(BaseModel):
    name: str
    role: ColumnRoleLiteral
    dtype: str
    non_null_count: int
    null_count: int
    distinct_count: int
    reason: str


ChartTypeLiteral = Literal["bar", "line", "pie", "histogram", "scatter"]


class ChartDataPoint(BaseModel):
    # Python 3.9 compatible union (no `X | Y` syntax, which requires 3.10+
    # at the point Pydantic evaluates the annotation).
    x: Union[str, float, int, bool, None]
    y: Union[str, float, int, bool, None]


class ChartSpecSchema(BaseModel):
    id: str
    chart_type: ChartTypeLiteral
    title: str
    description: str
    x_label: str
    y_label: str
    data: List[Dict[str, Any]]
    # Raw (non-prettified) source column names, present for charts backed
    # by a categorical dimension and/or numeric measure.
    dimension_column: Optional[str] = None
    metric_column: Optional[str] = None
    # Rich analytical hierarchy fields
    analytical_question: Optional[str] = None
    metric_definition: Optional[str] = None
    unit: Optional[str] = None
    aggregation: Optional[str] = None
    grouping: Optional[str] = None
    time_granularity: Optional[str] = None
    dataset_grain: Optional[str] = None
    data_coverage: Optional[str] = None
    explanation: Optional[str] = None
    limitations: Optional[str] = None


class KpiSchema(BaseModel):
    label: str
    value: float
    kind: str
    format: str


class RecommendationsResponse(BaseModel):
    dataset_id: str
    chart_count: int
    charts: List[ChartSpecSchema]
    column_profiles: List[ColumnProfileSchema]
    kpis: List[KpiSchema] = Field(default_factory=list)


class DrilldownFilter(BaseModel):
    dimension: str
    value: str


class DrilldownResponse(BaseModel):
    dataset_id: str
    dimension: str
    dimension_label: str
    value: str
    row_count: int
    kpis: List[KpiSchema]
    trend_chart: Optional[ChartSpecSchema] = None
    secondary_chart: Optional[ChartSpecSchema] = None
    # Present when secondary_chart's bars can themselves be drilled into a
    # further level; None when no further meaningful dimension exists.
    secondary_dimension: Optional[str] = None
    applied_filters: List[DrilldownFilter] = Field(default_factory=list)
