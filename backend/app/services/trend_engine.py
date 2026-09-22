"""Time-series trend intelligence engine.

Calculates verified trends, growth rates, moving averages, peaks, troughs,
period-over-period comparisons, volatility, anomaly spikes/drops, structured
metric explorer catalogs, dynamic plain-English summaries, and answers
practical trend questions from actual dataset time series without speculative claims.
"""
from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Literal, Optional, Tuple

import numpy as np
import pandas as pd

from app.domains.base import TrendRule
from app.schemas.domain_blueprint import (
    CategoryTrendSchema,
    DomainIdentitySchema,
    DomainTrendInterpretationSchema,
    MetricContextSchema,
    MetricDescriptorSchema,
    PeriodComparisonSchema,
    PracticalTrendAnswersSchema,
    SpikeDropSchema,
    TimeDimensionValidationSchema,
    TrendItemSchema,
    TrendPointSchema,
    TrendsIntelligenceResponse,
    TrendSummarySchema,
)
from app.services.column_formatter import format_column_label
from app.services.column_profiler import profile_dataset
from app.services.domain_detector import detect_domain
from app.services.trend_domain_interpreter import (
    classify_metric_semantic_role,
    interpret_domain_trend,
)


def _clean_float(val: Any, decimals: int = 2) -> Optional[float]:
    if val is None:
        return None
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return round(f, decimals)
    except (ValueError, TypeError):
        return None


def _find_time_column(df: pd.DataFrame) -> Optional[str]:
    """Identify the most appropriate time/date column in a dataset."""
    # 1. Check for native datetime dtypes
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            return str(col)

    # 2. Check column names with common date keywords
    date_keywords = (
        "date", "timestamp", "datetime", "order_date", "transaction_date",
        "created_at", "updated_at", "invoice_date", "match_date",
        "admission_date", "release_date", "event_date", "time", "year", "season"
    )
    col_scores: List[Tuple[float, str]] = []

    for col in df.columns:
        col_lower = str(col).strip().lower().replace(" ", "_").replace("-", "_").replace("/", "_")
        score = 0.0

        for kw in date_keywords:
            if kw == col_lower:
                score += 10.0
            elif kw in col_lower:
                score += 5.0

        # Test parsing a sample of non-null values
        if score > 0 or df[col].dtype == "object":
            sample = df[col].dropna().head(20)
            if not sample.empty:
                try:
                    parsed = pd.to_datetime(sample, errors="coerce")
                    valid_pct = parsed.notna().mean()
                    if valid_pct >= 0.7:
                        score += valid_pct * 15.0
                except Exception:
                    pass

        if score > 5.0:
            col_scores.append((score, str(col)))

    if col_scores:
        col_scores.sort(key=lambda x: x[0], reverse=True)
        return col_scores[0][1]

    return None


def _find_numeric_metrics(df: pd.DataFrame) -> List[str]:
    """Find valid continuous numeric metrics excluding pure IDs or constant indices."""
    metrics: List[str] = []
    id_terms = ("id", "_id", "code", "zip", "postal", "phone", "key", "number")

    for col in df.columns:
        col_str = str(col)
        col_lower = col_str.lower().strip().replace(" ", "_").replace("/", "_")
        if pd.api.types.is_numeric_dtype(df[col]) and not pd.api.types.is_bool_dtype(df[col]):
            if any(col_lower == t or col_lower.endswith(f"_{t}") for t in ("id", "code", "zip", "key", "phone")):
                continue
            non_null = df[col].dropna()
            if non_null.nunique() > 1:
                metrics.append(col_str)

    return metrics


def _find_categorical_dimensions(df: pd.DataFrame) -> List[str]:
    """Find good categorical grouping dimensions (cardinality between 2 and 40)."""
    categories: List[str] = []
    id_terms = ("id", "_id", "key", "uuid", "hash")

    for col in df.columns:
        col_str = str(col)
        col_lower = col_str.lower().strip()
        if any(col_lower.endswith(t) or col_lower == t for t in id_terms):
            continue
        if df[col].dtype == "object" or isinstance(df[col].dtype, pd.CategoricalDtype):
            nunique = df[col].nunique()
            if 2 <= nunique <= 40:
                categories.append(col_str)

    return categories


def _classify_metric(
    col_name: str,
    series: pd.Series,
    total_rows: int,
    domain_id: Optional[str] = None,
    all_columns: Optional[List[str]] = None,
) -> MetricDescriptorSchema:
    """Classify a numerical column into a structured, dataset-aware Metric Descriptor."""
    clean_label = format_column_label(col_name)
    col_lower = col_name.lower().replace(" ", "_").replace("/", "_").replace("-", "_")

    missing_count = int(series.isna().sum())
    missing_pct = round((missing_count / total_rows) * 100.0, 1) if total_rows > 0 else 0.0
    non_null = series.dropna()

    if missing_pct == 0.0:
        availability = "100% Complete"
    elif missing_pct < 10.0:
        availability = f"High ({100.0 - missing_pct:.1f}% Populated)"
    else:
        availability = f"Moderate ({100.0 - missing_pct:.1f}% Populated)"

    # Default values
    group = "Other Measures"
    semantic_type = "General Numerical"
    unit = "Units"
    recommended_agg: Literal["sum", "mean", "median", "count"] = "sum"
    description = f"Tracks numeric values of {clean_label} observed over time."
    confidence = 0.80

    # Domain-aware role classification
    role, role_label, role_conf = classify_metric_semantic_role(
        col_name=col_name,
        domain_id=domain_id,
        all_columns=all_columns,
    )

    # 1. Financial Metrics
    fin_keywords = ("sales", "revenue", "profit", "cost", "discount", "shipping", "budget", "expenditure", "freight", "fee", "tax", "expense", "spend", "amount", "price", "income", "earnings", "charges", "turnover", "tender_value")
    # 2. Operational Metrics
    ops_keywords = ("quantity", "units", "orders", "transactions", "count", "headcount", "volume", "duration", "aging", "processing_time", "delivery_time", "lead_time", "turnaround", "cycle_time", "delay", "days", "hours", "minutes", "bids", "bidders", "stay")
    # 3. Performance Metrics
    perf_keywords = ("conversion_rate", "percentage", "rate", "efficiency", "score", "marks", "gpa", "grade", "index", "rating", "accuracy", "strike_rate", "margin", "ratio", "pct")

    # Specific human-friendly names and descriptions
    if col_lower in ("sales", "sales_amount", "total_sales", "sale_amount", "gross_sales"):
        clean_label = "Sales Revenue"
        group = "Financial Metrics"
        semantic_type = "Financial / Revenue"
        recommended_agg = "sum"
        unit = "Currency"
        description = "Total revenue generated during each selected time period."
        confidence = 0.98
    elif col_lower in ("profit", "net_profit", "gross_profit", "profit_margin"):
        clean_label = "Profit"
        group = "Financial Metrics"
        semantic_type = "Financial / Profit"
        recommended_agg = "sum" if "margin" not in col_lower else "mean"
        unit = "Currency" if "margin" not in col_lower else "Percentage"
        description = "Total recorded profit during each selected time period."
        confidence = 0.98
    elif col_lower in ("quantity", "qty", "units_sold", "order_quantity", "items_count"):
        clean_label = "Units Sold"
        group = "Operational Metrics"
        semantic_type = "Operational / Volume"
        recommended_agg = "sum"
        unit = "Units"
        description = "Total quantity of products sold during each selected time period."
        confidence = 0.98
    elif col_lower in ("discount", "discount_amount", "discount_value", "discounts"):
        clean_label = "Discount"
        group = "Financial Metrics"
        semantic_type = "Financial / Discount"
        recommended_agg = "sum" if "rate" not in col_lower else "mean"
        unit = "Currency" if "rate" not in col_lower else "Percentage"
        description = "Total or average discount, depending on the selected aggregation."
        confidence = 0.96
    elif col_lower in ("shipping_cost", "shipping", "freight_value", "freight_cost"):
        clean_label = "Shipping Cost"
        group = "Financial Metrics"
        semantic_type = "Financial / Expense"
        recommended_agg = "sum"
        unit = "Currency"
        description = "Total recorded shipping cost during each selected time period."
        confidence = 0.96
    elif col_lower in ("aging", "order_aging", "aging_days", "processing_days", "delivery_days"):
        clean_label = "Order Aging"
        group = "Operational Metrics"
        semantic_type = "Operational / Turnaround"
        recommended_agg = "mean"
        unit = "Days"
        description = "The selected aging measurement over time."
        confidence = 0.95
    elif "tenderperiod_durationindays" in col_lower or "durationindays" in col_lower:
        clean_label = "Tender Duration (Days)"
        group = "Operational Metrics"
        semantic_type = "Operational / Turnaround"
        recommended_agg = "mean"
        unit = "Days"
        description = "Elapsed duration in days from tender publication to submission/award."
        confidence = 0.97
    elif "numberoftenderers" in col_lower or "bidders" in col_lower:
        clean_label = "Number of Bidders"
        group = "Operational Metrics"
        semantic_type = "Operational / Volume"
        recommended_agg = "mean"
        unit = "Bidders"
        description = "Total participating bidder submissions across tenders."
        confidence = 0.96
    elif role == "revenue":
        clean_label = "Sales Revenue" if clean_label in ("Sales", "Revenue", "Sales Amount") else clean_label
        group = "Financial Metrics"
        semantic_type = "Financial / Revenue"
        recommended_agg = "sum"
        unit = "Currency"
        description = f"Total revenue generated for {clean_label} over time."
        confidence = role_conf
    elif role == "profit":
        group = "Financial Metrics"
        semantic_type = "Financial / Profit"
        recommended_agg = "sum" if "margin" not in col_lower else "mean"
        unit = "Currency" if "margin" not in col_lower else "Percentage"
        description = f"Recorded profit/margin for {clean_label} over time."
        confidence = role_conf
    elif role == "loss":
        group = "Financial Metrics"
        semantic_type = "Financial / Loss"
        recommended_agg = "sum"
        unit = "Currency"
        description = f"Financial loss deficit recorded for {clean_label} over time."
        confidence = role_conf
    elif role == "expense_cost":
        group = "Financial Metrics"
        semantic_type = "Financial / Expense"
        recommended_agg = "sum"
        unit = "Currency"
        description = f"Recorded operational expenses/costs for {clean_label}."
        confidence = role_conf
    elif role == "sports_wins":
        group = "Performance Metrics"
        semantic_type = "Sports / Match Wins"
        recommended_agg = "sum"
        unit = "Wins"
        description = f"Total match victories for {clean_label}."
        confidence = role_conf
    elif role == "sports_losses":
        group = "Performance Metrics"
        semantic_type = "Sports / Defeats"
        recommended_agg = "sum"
        unit = "Losses"
        description = f"Total match defeats for {clean_label}."
        confidence = role_conf
    elif role in ("sports_scoring", "sports_metrics"):
        group = "Performance Metrics"
        semantic_type = "Sports / Performance Measure"
        recommended_agg = "sum" if not any(t in col_lower for t in ("avg", "rate", "pct")) else "mean"
        unit = "Runs" if "run" in col_lower else ("Points" if "point" in col_lower else ("Goals" if "goal" in col_lower else "Score"))
        description = f"Sports athletic performance metric for {clean_label}."
        confidence = role_conf
    elif role == "healthcare_patient_volume":
        group = "Operational Metrics"
        semantic_type = "Healthcare / Patient Volume"
        recommended_agg = "sum"
        unit = "Patients" if "patient" in col_lower else "Count"
        description = f"Total patient admissions and volume for {clean_label}."
        confidence = role_conf
    elif role == "healthcare_recovery":
        group = "Performance Metrics"
        semantic_type = "Healthcare / Recovery Rate"
        recommended_agg = "mean"
        unit = "Percentage" if any(t in col_lower for t in ("rate", "pct")) else "Patients"
        description = f"Patient recovery and discharge progression for {clean_label}."
        confidence = role_conf
    elif role == "healthcare_readmission":
        group = "Performance Metrics"
        semantic_type = "Healthcare / Readmission Rate"
        recommended_agg = "mean" if any(t in col_lower for t in ("rate", "pct")) else "sum"
        unit = "Percentage" if any(t in col_lower for t in ("rate", "pct")) else "Patients"
        description = f"Patient readmission rate for {clean_label}."
        confidence = role_conf
    elif role == "hr_headcount":
        group = "Operational Metrics"
        semantic_type = "HR / Workforce Capacity"
        recommended_agg = "mean"
        unit = "Employees"
        description = f"Total employee staffing capacity for {clean_label}."
        confidence = role_conf
    elif role == "hr_attrition":
        group = "Operational Metrics"
        semantic_type = "HR / Attrition Rate"
        recommended_agg = "mean" if any(t in col_lower for t in ("rate", "pct")) else "sum"
        unit = "Percentage" if any(t in col_lower for t in ("rate", "pct")) else "Employees"
        description = f"Employee turnover rate for {clean_label}."
        confidence = role_conf
    elif role == "hr_salary":
        group = "Financial Metrics"
        semantic_type = "HR / Compensation"
        recommended_agg = "mean"
        unit = "Currency"
        description = f"Employee compensation and payroll for {clean_label}."
        confidence = role_conf
    elif role in ("hr_attendance", "edu_attendance"):
        group = "Operational Metrics"
        semantic_type = "Engagement / Attendance"
        recommended_agg = "mean"
        unit = "Percentage" if any(t in col_lower for t in ("rate", "pct")) else "Days"
        description = f"Attendance rate for {clean_label}."
        confidence = role_conf
    elif role == "edu_student_performance":
        group = "Performance Metrics"
        semantic_type = "Education / Student Performance"
        recommended_agg = "mean"
        unit = "Score" if "gpa" not in col_lower else "GPA"
        description = f"Student academic performance score for {clean_label}."
        confidence = role_conf
    elif role == "edu_failure_rate":
        group = "Performance Metrics"
        semantic_type = "Education / Failure Rate"
        recommended_agg = "mean"
        unit = "Percentage"
        description = f"Course failure/dropout rate for {clean_label}."
        confidence = role_conf
    elif role == "ops_delivery_time":
        group = "Operational Metrics"
        semantic_type = "Operational / Turnaround"
        recommended_agg = "mean"
        unit = "Days" if any(t in col_lower for t in ("day", "aging", "delay")) else ("Hours" if "hour" in col_lower else "Units")
        description = f"Delivery and turnaround duration for {clean_label}."
        confidence = role_conf
    elif role == "ops_defect_rate":
        group = "Performance Metrics"
        semantic_type = "Quality / Defect Rate"
        recommended_agg = "mean" if any(t in col_lower for t in ("rate", "pct")) else "sum"
        unit = "Percentage" if any(t in col_lower for t in ("rate", "pct")) else "Defects"
        description = f"Quality defect rate for {clean_label}."
        confidence = role_conf
    elif role == "procurement_cost":
        group = "Financial Metrics"
        semantic_type = "Procurement / Spending"
        recommended_agg = "sum"
        unit = "Currency"
        description = f"Procurement spending and contract value for {clean_label}."
        confidence = role_conf
    elif role == "ops_order_volume":
        group = "Operational Metrics"
        semantic_type = "Operational / Volume"
        recommended_agg = "sum"
        unit = "Units"
        description = f"Order and throughput volume for {clean_label}."
        confidence = role_conf
    elif any(k in col_lower for k in fin_keywords):
        group = "Financial Metrics"
        semantic_type = "Financial / Monetary"
        recommended_agg = "mean" if ("margin" in col_lower or "price" in col_lower or "rate" in col_lower) else "sum"
        unit = "Percentage" if ("margin" in col_lower or "rate" in col_lower) else "Currency"
        description = f"Financial measure of {clean_label} aggregated over time."
        confidence = 0.92
    elif any(k in col_lower for k in ops_keywords):
        group = "Operational Metrics"
        semantic_type = "Operational / Throughput"
        recommended_agg = "mean" if any(t in col_lower for t in ("duration", "time", "days", "hours", "aging", "delay", "stay", "turnaround")) else "sum"
        unit = "Days" if any(t in col_lower for t in ("duration", "days", "aging", "delay")) else ("Hours" if "hour" in col_lower else ("Count" if "count" in col_lower else "Units"))
        description = f"Operational throughput or turnaround measure of {clean_label}."
        confidence = 0.91
    elif any(k in col_lower for k in perf_keywords):
        group = "Performance Metrics"
        semantic_type = "Performance / Index"
        recommended_agg = "mean"
        unit = "Percentage" if any(t in col_lower for t in ("pct", "rate", "percentage", "ratio")) else "Score"
        description = f"Performance rating, efficiency score, or percentage index for {clean_label}."
        confidence = 0.89
    elif "/" in col_name or "." in col_name:
        group = "Dataset-Specific Metrics"
        semantic_type = "Specialized Measure"
        recommended_agg = "sum" if not any(t in col_lower for t in ("rate", "score", "avg", "mean", "ratio")) else "mean"
        unit = "Units"
        description = f"Specialized dataset metric for {clean_label}."
        confidence = 0.85

    # Compute preview aggregate
    preview_val: Optional[float] = None
    if not non_null.empty:
        if recommended_agg == "mean":
            preview_val = round(float(non_null.mean()), 2)
        else:
            preview_val = round(float(non_null.sum()), 2)

    return MetricDescriptorSchema(
        column_name=col_name,
        display_name=clean_label,
        description=description,
        semantic_type=semantic_type,
        group=group,
        recommended_aggregation=recommended_agg,
        unit=unit,
        confidence=confidence,
        missing_count=missing_count,
        missing_percentage=missing_pct,
        data_availability=availability,
        preview_value=preview_val,
        is_primary_recommendation=False,
        recommendation_reason=None,
    )


def _build_metrics_catalog(
    df: pd.DataFrame,
    numeric_metrics: List[str],
    domain_id: Optional[str] = None,
) -> List[MetricDescriptorSchema]:
    """Build a comprehensive catalog of all available metrics in the dataset."""
    total_rows = len(df)
    catalog: List[MetricDescriptorSchema] = []
    all_cols = [str(c) for c in df.columns]

    for col in numeric_metrics:
        if col in df.columns:
            desc = _classify_metric(
                col_name=col,
                series=df[col],
                total_rows=total_rows,
                domain_id=domain_id,
                all_columns=all_cols,
            )
            catalog.append(desc)

    return catalog


def _pick_primary_metric(catalog: List[MetricDescriptorSchema]) -> Tuple[Optional[str], Optional[str]]:
    """Automatically recommend one primary metric based on domain, completeness, and analytical usefulness."""
    if not catalog:
        return None, None

    # Priority score calculation
    scored: List[Tuple[float, MetricDescriptorSchema, str]] = []

    group_weights = {
        "Financial Metrics": 100.0,
        "Operational Metrics": 90.0,
        "Performance Metrics": 85.0,
        "Dataset-Specific Metrics": 75.0,
        "Other Measures": 50.0,
    }

    for m in catalog:
        base_score = group_weights.get(m.group, 50.0)
        # Favor complete data
        completeness_bonus = (100.0 - m.missing_percentage) * 0.25
        # Favor high confidence
        conf_bonus = m.confidence * 20.0
        # Check specific prioritized names
        col_lower = m.column_name.lower()
        if any(term in col_lower for term in ("sales", "revenue", "amount", "tender_value", "total_sales")):
            base_score += 40.0
        elif any(term in col_lower for term in ("duration", "durationindays", "profit", "quantity")):
            base_score += 25.0

        total_score = base_score + completeness_bonus + conf_bonus

        reason = (
            f"'{m.display_name}' is recommended because it is a key {m.group.lower().rstrip('s')} measure "
            f"({m.data_availability}) with strong temporal aggregation utility."
        )
        scored.append((total_score, m, reason))

    scored.sort(key=lambda x: x[0], reverse=True)
    best_match = scored[0]
    best_match[1].is_primary_recommendation = True
    best_match[1].recommendation_reason = best_match[2]

    return best_match[1].column_name, best_match[2]


def compute_trends_intelligence(
    df: pd.DataFrame,
    dataset_id: str,
    granularity: str = "auto",
    metric: Optional[str] = None,
    category_col: Optional[str] = None,
    domain: Optional[DomainIdentitySchema] = None,
) -> TrendsIntelligenceResponse:
    """Compute comprehensive time-series trends intelligence with domain awareness."""
    # Ensure domain is available
    if domain is None:
        profiles = profile_dataset(df)
        domain = detect_domain(df, profiles)

    time_col = _find_time_column(df)
    numeric_metrics = _find_numeric_metrics(df)
    categories = _find_categorical_dimensions(df)

    # Build structured metric catalog with domain context
    metrics_catalog = _build_metrics_catalog(df, numeric_metrics, domain_id=domain.domain_id if domain else None)
    primary_metric_col, primary_reason = _pick_primary_metric(metrics_catalog)

    # If no time column exists, return graceful unsupported state
    if not time_col:
        return TrendsIntelligenceResponse(
            dataset_id=dataset_id,
            has_time_dimension=False,
            time_validation=TimeDimensionValidationSchema(
                has_time_dimension=False,
                quality_status="No Time Dimension",
                notes=["No date, timestamp, or year column was detected in this dataset."],
            ),
            metrics_catalog=metrics_catalog,
            primary_metric=primary_metric_col,
            primary_metric_reason=primary_reason,
            available_metrics=numeric_metrics,
            available_categories=categories,
            limitations=[
                "Dataset lacks a usable temporal dimension.",
                "Trends, period-over-period comparisons, and time-series forecasting cannot be calculated without dates.",
            ],
        )

    # Validate time column
    raw_series = df[time_col]
    total_rows = len(raw_series)
    missing_dates = int(raw_series.isna().sum())

    parsed_dates = pd.to_datetime(raw_series, errors="coerce")
    invalid_dates = int(raw_series.notna().sum() - parsed_dates.notna().sum())
    valid_dates_series = parsed_dates.dropna()

    if len(valid_dates_series) < 1:
        return TrendsIntelligenceResponse(
            dataset_id=dataset_id,
            has_time_dimension=False,
            time_validation=TimeDimensionValidationSchema(
                has_time_dimension=False,
                time_column=time_col,
                missing_dates_count=missing_dates,
                invalid_dates_count=invalid_dates,
                quality_status="Insufficient Dates",
                notes=["No valid date records could be parsed from the time column."],
            ),
            metrics_catalog=metrics_catalog,
            primary_metric=primary_metric_col,
            primary_metric_reason=primary_reason,
            available_metrics=numeric_metrics,
            available_categories=categories,
            limitations=["Insufficient valid date records to compute time-series trends."],
        )

    min_date = valid_dates_series.min()
    max_date = valid_dates_series.max()
    date_span_days = int((max_date - min_date).days)
    duplicate_dates = int(valid_dates_series.duplicated().sum())

    # Detect interval frequency
    sorted_unique_dates = valid_dates_series.drop_duplicates().sort_values()
    intervals = sorted_unique_dates.diff().dt.days.dropna()
    median_interval = float(intervals.median()) if len(intervals) > 0 else 0.0

    if len(sorted_unique_dates) <= 1:
        detected_freq = "single_period"
    elif median_interval <= 1.5:
        detected_freq = "daily"
    elif 6.0 <= median_interval <= 8.0:
        detected_freq = "weekly"
    elif 27.0 <= median_interval <= 32.0:
        detected_freq = "monthly"
    elif 85.0 <= median_interval <= 95.0:
        detected_freq = "quarterly"
    elif 350.0 <= median_interval <= 370.0:
        detected_freq = "yearly"
    else:
        detected_freq = "irregular"

    has_irregular = detected_freq == "irregular" or (len(intervals) > 2 and intervals.std() > 15)

    quality_status = "Healthy"
    notes: List[str] = []
    if missing_dates > 0:
        notes.append(f"{missing_dates} rows have missing date values.")
        quality_status = "Warning"
    if invalid_dates > 0:
        notes.append(f"{invalid_dates} rows contain unparseable date strings.")
        quality_status = "Warning"
    if detected_freq == "single_period":
        notes.append("Dataset observations span a single date or uniform observation period.")
        quality_status = "Limited Timeline"
    elif has_irregular:
        notes.append("Time intervals between records are non-uniform.")

    time_validation = TimeDimensionValidationSchema(
        has_time_dimension=True,
        time_column=time_col,
        date_range={
            "min_date": min_date.strftime("%Y-%m-%d"),
            "max_date": max_date.strftime("%Y-%m-%d"),
            "total_days": date_span_days,
            "observation_count": len(valid_dates_series),
        },
        detected_frequency=detected_freq,
        missing_dates_count=missing_dates,
        invalid_dates_count=invalid_dates,
        duplicate_dates_count=duplicate_dates,
        has_irregular_intervals=has_irregular,
        quality_status=quality_status,
        notes=notes,
    )

    # Pick selected metric (prefer user choice, else primary recommendation, else first available)
    selected_metric = metric if (metric and metric in numeric_metrics) else (primary_metric_col or (numeric_metrics[0] if numeric_metrics else None))

    if not selected_metric:
        return TrendsIntelligenceResponse(
            dataset_id=dataset_id,
            has_time_dimension=True,
            time_validation=time_validation,
            metrics_catalog=metrics_catalog,
            primary_metric=primary_metric_col,
            primary_metric_reason=primary_reason,
            available_metrics=numeric_metrics,
            available_categories=categories,
            limitations=["Dataset contains a valid time dimension, but no continuous numeric metrics were found to aggregate over time."],
        )

    # Find selected descriptor
    selected_desc = next((m for m in metrics_catalog if m.column_name == selected_metric), None)
    if not selected_desc:
        selected_desc = _classify_metric(selected_metric, df[selected_metric], total_rows)

    # Select granularity
    selected_granularity = granularity.upper() if granularity else "AUTO"
    if selected_granularity not in ("D", "W", "M", "Q", "Y"):
        # Smart auto-granularity
        if date_span_days > 730:
            selected_granularity = "M" if date_span_days <= 1800 else "Q"
        elif date_span_days > 60:
            selected_granularity = "W" if date_span_days <= 180 else "M"
        else:
            selected_granularity = "D"

    # Prepare DataFrame for time aggregation
    metric_series = pd.to_numeric(df[selected_metric], errors="coerce")
    clean_df = pd.DataFrame({
        "date": parsed_dates,
        "metric": metric_series,
    })
    if category_col and category_col in df.columns:
        clean_df["category"] = df[category_col].astype(str)

    raw_count = len(clean_df)
    clean_df = clean_df.dropna(subset=["date", "metric"]).sort_values("date")
    valid_row_count = len(clean_df)
    excluded_row_count = raw_count - valid_row_count

    # 1. Metric Context Card
    agg_method_str = "Average (Mean)" if selected_desc.recommended_aggregation == "mean" else "Sum (Total)"
    granularity_names = {"D": "Daily", "W": "Weekly", "M": "Monthly", "Q": "Quarterly", "Y": "Yearly"}
    gran_label = granularity_names.get(selected_granularity, selected_granularity)

    metric_context = MetricContextSchema(
        metric_display_name=f"{gran_label} {selected_desc.display_name}",
        source_column=selected_metric,
        semantic_type=selected_desc.semantic_type,
        aggregation_method=agg_method_str,
        time_column=time_col,
        time_granularity=f"{gran_label} ({selected_granularity})",
        records_included=valid_row_count,
        records_excluded=excluded_row_count,
        missing_percentage=selected_desc.missing_percentage,
        calculation_explanation=(
            f"Aggregated {selected_desc.display_name} by applying {agg_method_str} across {time_col} "
            f"bucketed into {gran_label.lower()} intervals. {valid_row_count:,} valid observations were included "
            f"({excluded_row_count:,} records excluded due to null values)."
        ),
        limitations=[
            f"Missing values in '{selected_metric}': {selected_desc.missing_percentage:.1f}%.",
            f"Time aggregation grain: {gran_label}.",
        ],
    )

    if valid_row_count == 0:
        return TrendsIntelligenceResponse(
            dataset_id=dataset_id,
            has_time_dimension=True,
            time_validation=time_validation,
            metrics_catalog=metrics_catalog,
            primary_metric=primary_metric_col,
            primary_metric_reason=primary_reason,
            selected_metric=selected_metric,
            selected_metric_descriptor=selected_desc,
            metric_context=metric_context,
            available_metrics=numeric_metrics,
            available_categories=categories,
            selected_granularity=selected_granularity,
            limitations=["All metric values for this selection are missing or null."],
        )

    # Aggregate by selected period
    clean_df["period"] = clean_df["date"].dt.to_period(selected_granularity).dt.to_timestamp()
    if selected_desc.recommended_aggregation == "mean":
        ts = clean_df.groupby("period")["metric"].mean()
    else:
        ts = clean_df.groupby("period")["metric"].sum()

    if len(ts) < 2 and detected_freq != "single_period":
        # Fallback to daily if period collapsed everything to 1 row
        clean_df["period"] = clean_df["date"].dt.to_period("D").dt.to_timestamp()
        if selected_desc.recommended_aggregation == "mean":
            ts = clean_df.groupby("period")["metric"].mean()
        else:
            ts = clean_df.groupby("period")["metric"].sum()
        selected_granularity = "D"

    # Moving averages
    ma_3 = ts.rolling(window=min(3, len(ts)), min_periods=1).mean()
    ma_7 = ts.rolling(window=min(7, len(ts)), min_periods=1).mean()

    # Outlier / Anomaly detection: residuals from rolling mean
    mean_val = float(ts.mean())
    std_val = float(ts.std()) if len(ts) > 1 else 0.0

    time_series_points: List[TrendPointSchema] = []
    spikes_and_drops: List[SpikeDropSchema] = []

    for dt, val, m3, m7 in zip(ts.index, ts.values, ma_3.values, ma_7.values):
        v = float(val)
        is_spike = False
        is_drop = False
        sigma = 0.0

        if std_val > 0:
            sigma = (v - mean_val) / std_val
            if sigma >= 2.0:
                is_spike = True
                spikes_and_drops.append(
                    SpikeDropSchema(
                        date=dt.strftime("%Y-%m-%d"),
                        value=round(v, 2),
                        expected_value=round(mean_val, 2),
                        deviation_sigma=round(sigma, 2),
                        type="spike",
                        description=f"Significant spike of {round(v, 2):,} ({round(sigma, 1)} std dev above average).",
                    )
                )
            elif sigma <= -2.0:
                is_drop = True
                spikes_and_drops.append(
                    SpikeDropSchema(
                        date=dt.strftime("%Y-%m-%d"),
                        value=round(v, 2),
                        expected_value=round(mean_val, 2),
                        deviation_sigma=round(sigma, 2),
                        type="drop",
                        description=f"Significant drop to {round(v, 2):,} ({round(abs(sigma), 1)} std dev below average).",
                    )
                )

        time_series_points.append(
            TrendPointSchema(
                date=dt.strftime("%Y-%m-%d"),
                formatted_date=dt.strftime("%b %Y" if selected_granularity in ("M", "Q", "Y") else "%Y-%m-%d"),
                value=round(v, 2),
                moving_avg_3=round(float(m3), 2),
                moving_avg_7=round(float(m7), 2),
                is_spike=is_spike,
                is_drop=is_drop,
                anomaly_score=round(sigma, 2) if std_val > 0 else None,
            )
        )

    # Period-over-period comparison (latest vs prior)
    if len(ts) >= 2:
        current_period_idx = ts.index[-1]
        previous_period_idx = ts.index[-2]
        current_val = float(ts.iloc[-1])
        previous_val = float(ts.iloc[-2])
        abs_change = current_val - previous_val
        pct_change = round(((current_val - previous_val) / previous_val) * 100.0, 2) if previous_val != 0 else None
        growth_dir = "increasing" if abs_change > 0 else ("decreasing" if abs_change < 0 else "stable")
        
        # Overall change from start to finish
        start_val = float(ts.iloc[0])
        if start_val != 0:
            overall_change_pct = round(((current_val - start_val) / start_val) * 100.0, 2)
        elif current_val > start_val:
            overall_change_pct = 100.0
        elif current_val < start_val:
            overall_change_pct = -100.0
        else:
            overall_change_pct = 0.0
        
        best_idx = ts.idxmax()
        best_val = float(ts.max())
        worst_idx = ts.idxmin()
        worst_val = float(ts.min())

        period_comp = PeriodComparisonSchema(
            current_period=current_period_idx.strftime("%Y-%m-%d"),
            previous_period=previous_period_idx.strftime("%Y-%m-%d"),
            current_val=round(current_val, 2),
            previous_val=round(previous_val, 2),
            absolute_change=round(abs_change, 2),
            pct_change=pct_change,
            growth_direction=growth_dir,
            best_period=best_idx.strftime("%Y-%m-%d"),
            best_val=round(best_val, 2),
            worst_period=worst_idx.strftime("%Y-%m-%d"),
            worst_val=round(worst_val, 2),
        )
    else:
        current_period_idx = ts.index[0]
        previous_period_idx = None
        current_val = float(ts.iloc[0])
        previous_val = None
        abs_change = None
        pct_change = None
        overall_change_pct = None
        growth_dir = "stable"
        best_idx = ts.index[0]
        best_val = current_val
        worst_idx = ts.index[0]
        worst_val = current_val
        period_comp = None

    # Volatility
    cv = (std_val / mean_val) if mean_val > 0 else 0.0
    if len(ts) < 3:
        stability = "Insufficient Data"
    elif cv < 0.15:
        stability = "Stable (Low Volatility)"
    elif cv < 0.40:
        stability = "Moderate Volatility"
    else:
        stability = "High Volatility"

    # Category-wise trends
    category_trends: List[CategoryTrendSchema] = []
    categories_increased: List[str] = []
    categories_declined: List[str] = []

    cat_to_use = category_col if (category_col and category_col in df.columns) else (categories[0] if categories else None)

    if cat_to_use and "category" in clean_df.columns:
        top_cats = clean_df["category"].value_counts().head(5).index.tolist()
        for cat in top_cats:
            cat_df = clean_df[clean_df["category"] == cat]
            if selected_desc.recommended_aggregation == "mean":
                cat_ts = cat_df.groupby("period")["metric"].mean()
            else:
                cat_ts = cat_df.groupby("period")["metric"].sum()

            if len(cat_ts) >= 1:
                c_prev = float(cat_ts.iloc[-2]) if len(cat_ts) >= 2 else float(cat_ts.iloc[0])
                c_curr = float(cat_ts.iloc[-1])
                c_diff = c_curr - c_prev if len(cat_ts) >= 2 else 0.0
                c_pct = round(((c_curr - c_prev) / c_prev) * 100.0, 2) if (len(cat_ts) >= 2 and c_prev != 0) else None
                c_dir = "increasing" if c_diff > 0 else ("decreasing" if c_diff < 0 else "stable")

                if c_diff > 0:
                    categories_increased.append(str(cat))
                elif c_diff < 0:
                    categories_declined.append(str(cat))

                series_pts = [
                    {"date": dt.strftime("%Y-%m-%d"), "value": round(float(v), 2)}
                    for dt, v in cat_ts.items()
                ]

                category_trends.append(
                    CategoryTrendSchema(
                        category=str(cat),
                        previous_val=round(c_prev, 2),
                        current_val=round(c_curr, 2),
                        absolute_change=round(c_diff, 2),
                        pct_change=c_pct,
                        direction=c_dir,
                        series=series_pts,
                    )
                )

    # 2. Trend Status & Dynamic Plain-English Summary
    data_sufficiency: Literal["Robust", "Moderate", "Limited", "Insufficient"]
    if len(ts) >= 12:
        data_sufficiency = "Robust"
        data_sufficiency_note = f"{len(ts)} periods recorded; sufficient for longitudinal trend evaluation."
    elif len(ts) >= 4:
        data_sufficiency = "Moderate"
        data_sufficiency_note = f"{len(ts)} periods recorded; short-to-medium trend observable."
    elif len(ts) >= 2:
        data_sufficiency = "Limited"
        data_sufficiency_note = f"{len(ts)} periods recorded; comparisons are directional only."
    else:
        data_sufficiency = "Insufficient"
        data_sufficiency_note = "Single observation period recorded; longitudinal growth cannot be evaluated."

    trend_status: Literal["Increasing", "Decreasing", "Stable", "Fluctuating", "Insufficient Data"]
    if len(ts) < 2:
        trend_status = "Insufficient Data"
        direction_val: Literal["increasing", "decreasing", "stable", "fluctuating", "insufficient_data"] = "insufficient_data"
        status_desc = "Single observation window recorded — baseline only."
    else:
        if overall_change_pct is not None and overall_change_pct > 3.0:
            trend_status = "Increasing"
            direction_val = "increasing"
            status_desc = f"Overall upward growth (+{overall_change_pct:.1f}% across observed periods)."
        elif overall_change_pct is not None and overall_change_pct < -3.0:
            trend_status = "Decreasing"
            direction_val = "decreasing"
            status_desc = f"Overall downward contraction ({overall_change_pct:.1f}% across observed periods)."
        elif cv > 0.45:
            trend_status = "Fluctuating"
            direction_val = "fluctuating"
            status_desc = "High period-to-period variability with alternating movements."
        else:
            trend_status = "Stable"
            direction_val = "stable"
            status_desc = "Consistent performance with low variance across periods."

    # Compute Domain-Aware Trend Interpretation
    domain_interp = interpret_domain_trend(
        metric_name=selected_desc.display_name,
        metric_column=selected_metric,
        direction=direction_val,
        abs_change=abs_change,
        pct_change=pct_change,
        overall_change_pct=overall_change_pct,
        current_val=current_val,
        previous_val=previous_val,
        all_dataset_columns=[str(c) for c in df.columns],
        domain=domain,
        granularity_label=gran_label,
    )

    if len(ts) < 2:
        plain_summary = (
            f"Only a single time period is available ({current_period_idx.strftime('%Y-%m-%d')} with baseline value of {current_val:,.2f}). "
            f"A period-over-period growth or decline comparison cannot be calculated without multi-period date records."
        )
    else:
        prev_date_str = previous_period_idx.strftime('%B %Y' if selected_granularity in ('M', 'Q', 'Y') else '%Y-%m-%d') if previous_period_idx else "prior period"
        curr_date_str = current_period_idx.strftime('%B %Y' if selected_granularity in ('M', 'Q', 'Y') else '%Y-%m-%d')
        peak_date_str = best_idx.strftime('%B %Y' if selected_granularity in ('M', 'Q', 'Y') else '%Y-%m-%d')

        if abs_change is not None and abs_change != 0 and pct_change is not None and previous_val is not None:
            movement_word = "increased" if abs_change > 0 else "decreased"
            change_noun = "an increase" if abs_change > 0 else "a decrease"
            plain_summary = (
                f"{gran_label} {selected_desc.display_name} {movement_word} from {previous_val:,.2f} in {prev_date_str} to "
                f"{current_val:,.2f} in {curr_date_str}, {change_noun} of {abs(abs_change):,.2f} ({abs(pct_change):.1f}%). "
                f"{domain_interp.contextual_interpretation} "
                f"Across all {len(ts)} observed periods, the all-time peak of {best_val:,.2f} was recorded in {peak_date_str}."
            )
        else:
            plain_summary = (
                f"{gran_label} {selected_desc.display_name} remained stable at {current_val:,.2f} in {curr_date_str}. "
                f"{domain_interp.contextual_interpretation} "
                f"Across all {len(ts)} observed periods, the highest recorded value was {best_val:,.2f} in {peak_date_str}."
            )

    trend_summary = TrendSummarySchema(
        trend_status=trend_status,
        status_description=status_desc,
        plain_english_summary=plain_summary,
        latest_period=current_period_idx.strftime("%Y-%m-%d"),
        latest_value=round(current_val, 2),
        previous_period=previous_period_idx.strftime("%Y-%m-%d") if previous_period_idx else None,
        previous_value=round(previous_val, 2) if previous_val is not None else None,
        latest_change_absolute=round(abs_change, 2) if abs_change is not None else None,
        latest_change_pct=pct_change,
        overall_period_change_pct=overall_change_pct,
        highest_period=best_idx.strftime("%Y-%m-%d"),
        highest_value=round(best_val, 2),
        lowest_period=worst_idx.strftime("%Y-%m-%d"),
        lowest_value=round(worst_val, 2),
        data_sufficiency=data_sufficiency,
        data_sufficiency_note=data_sufficiency_note,
    )

    # 3. "What This Chart Tells You" Dynamic Bullets
    what_tells_you: List[str] = []
    if len(ts) < 2:
        what_tells_you.append(f"Recorded single-period baseline for {selected_desc.display_name} on {current_period_idx.strftime('%Y-%m-%d')}.")
        what_tells_you.append(f"Aggregated metric value: {current_val:,.2f} ({agg_method_str}).")
        what_tells_you.append("No historical period-over-period comparison is possible with one unique date.")
    else:
        what_tells_you.append(
            f"Overall trajectory for {selected_desc.display_name} is {trend_status.lower()}, moving from {float(ts.iloc[0]):,.2f} at start to {current_val:,.2f} in the latest period."
        )
        what_tells_you.append(
            f"Contextual Domain Insight: {domain_interp.contextual_interpretation}"
        )
        what_tells_you.append(
            f"All-time peak for {selected_desc.display_name} occurred on {best_idx.strftime('%Y-%m-%d')} ({best_val:,.2f}), while lowest recorded value was on {worst_idx.strftime('%Y-%m-%d')} ({worst_val:,.2f})."
        )
        if pct_change is not None:
            dir_text = "increased" if pct_change > 0 else ("decreased" if pct_change < 0 else "remained flat")
            what_tells_you.append(
                f"In the most recent period, {selected_desc.display_name} {dir_text} by {abs(pct_change):.1f}% (net change of {abs_change:+,.2f})."
            )
        what_tells_you.append(
            f"{selected_desc.display_name} exhibits {stability.lower()} with {len(spikes_and_drops)} statistical anomalies detected."
        )

    # 4. Metric-Specific Domain Interpretation
    interpretation_parts = [domain_interp.contextual_interpretation]
    if domain_interp.qualification:
        interpretation_parts.append(domain_interp.qualification)
    if domain_interp.distinction_note:
        interpretation_parts.append(domain_interp.distinction_note)
    interpretation = " ".join(interpretation_parts)

    # Practical Answers
    if len(ts) >= 2 and previous_period_idx is not None and previous_val is not None:
        prev_txt = f"{previous_val:,.2f} recorded in period {previous_period_idx.strftime('%Y-%m-%d')}"
        abs_txt = f"Net change of {abs_change:+,.2f}"
        pct_txt = f"Percentage change of {pct_change:+0.1f}%" if pct_change is not None else "N/A"
        next_investigation = (
            f"Review underlying segments in the latest period. "
            f"Check whether leading contributors ({', '.join(categories_increased[:2]) if categories_increased else 'top categories'}) "
            f"explain recent period movement. {domain_interp.qualification}"
        )
    else:
        prev_txt = f"Baseline value of {current_val:,.2f} recorded on {current_period_idx.strftime('%Y-%m-%d')} (single time observation in dataset)"
        abs_txt = "Net change: N/A (single observation period)"
        pct_txt = "Percentage change: N/A (single observation period)"
        next_investigation = (
            f"The dataset records observations across a single time period ({current_period_idx.strftime('%Y-%m-%d')}). "
            f"To evaluate longitudinal trends and period-over-period growth, incorporate records across multiple time horizons."
        )

    practical_answers = PracticalTrendAnswersSchema(
        metric_analyzed=f"{selected_desc.display_name} ({domain_interp.metric_role}, {gran_label} period)",
        previous_value_text=prev_txt,
        current_value_text=f"{current_val:,.2f} recorded in latest period {current_period_idx.strftime('%Y-%m-%d')}",
        absolute_change_text=abs_txt,
        pct_change_text=pct_txt,
        best_period_text=f"Peak value of {best_val:,.2f} on {best_idx.strftime('%Y-%m-%d')}",
        worst_period_text=f"Trough value of {worst_val:,.2f} on {worst_idx.strftime('%Y-%m-%d')}",
        categories_increased=categories_increased[:5],
        categories_declined=categories_declined[:5],
        stability_text=f"{stability} (Coefficient of Variation: {round(cv, 3)})",
        outliers_text=f"{len(spikes_and_drops)} statistical spikes or drops detected beyond +/-2 std dev baseline",
        next_investigation_text=next_investigation,
    )

    limitations = [
        "Historical observation only. Descriptive trends reflect recorded dataset entries and do not establish external causality.",
        "Market dynamics, seasonal factors, and unrecorded variables cannot be verified from internal columns alone.",
    ]
    if domain_interp.distinction_note:
        limitations.append(domain_interp.distinction_note)
    if len(ts) < 12:
        limitations.append(f"Time series contains {len(ts)} periods (<12); multi-year seasonality cannot be conclusively established.")

    return TrendsIntelligenceResponse(
        dataset_id=dataset_id,
        has_time_dimension=True,
        time_validation=time_validation,
        metrics_catalog=metrics_catalog,
        primary_metric=primary_metric_col,
        primary_metric_reason=primary_reason,
        selected_metric=selected_metric,
        selected_metric_descriptor=selected_desc,
        metric_context=metric_context,
        domain_interpretation=domain_interp,
        trend_summary=trend_summary,
        what_this_chart_tells_you=what_tells_you,
        metric_interpretation=interpretation,
        available_metrics=numeric_metrics,
        available_categories=categories,
        selected_granularity=selected_granularity,
        period_comparison=period_comp,
        volatility_cv=round(cv, 4),
        stability_rating=stability,
        time_series=time_series_points,
        category_trends=category_trends,
        spikes_and_drops=spikes_and_drops,
        practical_answers=practical_answers,
        limitations=limitations,
    )


def compute_trends(
    df: pd.DataFrame,
    validated_trends: List[Tuple[TrendRule, str, str]],
) -> List[TrendItemSchema]:
    """Calculate statistical time-series trends, peaks, troughs, and growth rates.
    Maintained for backward compatibility with blueprint rules.
    """
    results: List[TrendItemSchema] = []

    for rule, metric_col, date_col in validated_trends:
        if date_col not in df.columns or metric_col not in df.columns:
            continue

        clean_df = df[[date_col, metric_col]].dropna().copy()
        if clean_df.empty:
            continue

        try:
            clean_df["parsed_date"] = pd.to_datetime(clean_df[date_col], errors="coerce")
            clean_df = clean_df.dropna(subset=["parsed_date"])
            if len(clean_df) < 3:
                continue

            clean_df = clean_df.sort_values("parsed_date")

            date_range = clean_df["parsed_date"].max() - clean_df["parsed_date"].min()
            days = date_range.days

            if days > 730:
                clean_df["period"] = clean_df["parsed_date"].dt.to_period("Y").dt.to_timestamp()
            elif days > 60:
                clean_df["period"] = clean_df["parsed_date"].dt.to_period("M").dt.to_timestamp()
            else:
                clean_df["period"] = clean_df["parsed_date"].dt.to_period("D").dt.to_timestamp()

            ts = clean_df.groupby("period")[metric_col].sum()
            if len(ts) < 2:
                continue

            start_val = float(ts.iloc[0])
            end_val = float(ts.iloc[-1])
            growth_pct: Optional[float] = None
            if start_val > 0:
                growth_pct = round(((end_val - start_val) / start_val) * 100.0, 1)

            peak_idx = ts.idxmax()
            peak_val = float(ts.max())
            peak_str = peak_idx.strftime("%Y-%m-%d")

            trough_idx = ts.idxmin()
            trough_val = float(ts.min())
            trough_str = trough_idx.strftime("%Y-%m-%d")

            x = np.arange(len(ts))
            y = ts.values.astype(float)
            slope, _ = np.polyfit(x, y, 1) if len(x) >= 2 else (0.0, 0.0)

            if slope > 0.05 * np.std(y):
                direction = "increasing"
            elif slope < -0.05 * np.std(y):
                direction = "decreasing"
            else:
                direction = "stable"

            ma = ts.rolling(window=min(3, len(ts)), min_periods=1).mean()

            data_points: List[Dict[str, Any]] = [
                {
                    "date": dt.strftime("%Y-%m-%d"),
                    "value": round(float(v), 2),
                    "moving_avg": round(float(m), 2),
                }
                for dt, v, m in zip(ts.index, ts.values, ma.values)
            ]

            results.append(
                TrendItemSchema(
                    metric_name=metric_col,
                    time_column=date_col,
                    trend_direction=direction,
                    growth_rate_pct=growth_pct,
                    peak_period=peak_str,
                    trough_period=trough_str,
                    seasonality_detected=False,
                    description=f"Calculated {direction} trend for '{metric_col}' over time.",
                    data_points=data_points,
                )
            )
        except Exception:
            continue

    return results
