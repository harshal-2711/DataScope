"""Turns a profiled dataset into a ranked list of ready-to-render charts.

Design goals (Phase 3 requirements):
  - No manual axis/column/aggregation selection by the user -- this module
    decides all of that from the column profiles alone.
  - All aggregation happens here, on the backend, over the full dataset --
    the frontend only ever receives already-aggregated, chart-sized data,
    so this scales to large datasets without shipping raw rows to the UI.
  - Categorical columns must still produce a chart even when the dataset
    has no numeric measure at all (count of rows per category) -- this was
    the "silent drop" bug: don't require a numeric partner to exist.
  - Output is capped and diversified (not 8 bar charts) so the result is a
    small, genuinely useful set rather than an exhaustive combinatorial
    dump of every column pairing.
  - Strictly enforce analytical chart validation rules:
    * Categorical comparisons -> Bar chart
    * Valid time trends -> Line chart
    * Continuous numerical distributions -> Histogram
    * Numerical relationships -> Scatter plot
    * Part-to-whole -> Pie/Donut (only for additive sums with <= 6 categories)
    * NEVER use pie charts for durations, averages, rates, or > 6 categories
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Tuple

import numpy as np
import pandas as pd

from app.core.config import settings
from app.services.column_formatter import (
    detect_column_unit,
    format_business_chart_title,
    format_chart_description,
    format_column_label,
    format_metric_display,
)
from app.services.column_profiler import ColumnProfile, profile_dataset
from app.services.semantic_rules import (
    dimension_importance,
    metric_importance,
    prettify,
)
from app.services.type_inference import detect_dataset_currency

ChartType = Literal["bar", "line", "pie", "histogram", "scatter"]

_SUM_NAME_HINTS = (
    "total", "sum", "amount", "revenue", "sales", "units", "volume",
    "spend", "cost", "budget", "appropriation", "expenditure", "disbursement",
)

_MEAN_NAME_HINTS = (
    "price", "rate", "rating", "score", "pct", "percent", "margin", "duration", "days", "hours",
    "bidders", "tenderers", "age", "tenure", "gpa", "ctr", "cpc", "discount", "lead_time", "turnaround",
)

TOP_K_DIMENSIONS = 4
TOP_K_METRICS = 4
TOP_K_HIGH_CARDINALITY_DIMENSIONS = 2
TOP_N_HIGH_CARDINALITY_CATEGORIES = 50
MIN_DIMENSION_SCORE_FOR_HIGH_CARDINALITY = 2.0
SCATTER_MIN_CORRELATION = 0.3
SCATTER_MIN_CORRELATION_BOTH_IMPORTANT = 0.15
MAX_CATEGORIES_HARD_CAP = 60


@dataclass
class ChartSpec:
    id: str
    chart_type: ChartType
    title: str
    description: str
    x_label: str
    y_label: str
    data: List[Dict[str, Any]]
    score: float = field(repr=False, default=0.0)
    dimension_column: Optional[str] = None
    metric_column: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "chart_type": self.chart_type,
            "title": self.title,
            "description": self.description,
            "x_label": self.x_label,
            "y_label": self.y_label,
            "data": self.data,
            "dimension_column": self.dimension_column,
            "metric_column": self.metric_column,
        }


def _clean(value: Any) -> Any:
    """Coerce a single aggregated value into something JSON-safe."""
    if value is None:
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        f = float(value)
        return None if (np.isnan(f) or np.isinf(f)) else round(f, 4)
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, float):
        return None if (np.isnan(value) or np.isinf(value)) else round(value, 4)
    return value


def _pick_aggregation(column_name: str) -> str:
    """Heuristic: does this numeric column read as a total (sum) or a typical value (mean)?"""
    lowered = column_name.lower()
    if any(hint in lowered for hint in _MEAN_NAME_HINTS):
        return "mean"
    if any(hint in lowered for hint in _SUM_NAME_HINTS):
        return "sum"
    return "mean"


def _fold_into_other(
    series: pd.Series, max_categories: int
) -> Tuple[pd.Series, bool]:
    """Keep the top categories of an already-sorted (descending) series."""
    if len(series) <= max_categories:
        return series, False

    kept = series.iloc[:max_categories]
    other_total = series.iloc[max_categories:].sum()
    largest_individual = float(kept.iloc[0])

    if other_total <= largest_individual:
        return pd.concat([kept, pd.Series({"Other": other_total})]), True

    expanded_limit = min(MAX_CATEGORIES_HARD_CAP, len(series))
    expanded = series.iloc[:expanded_limit]
    return expanded, False


def _category_counts_chart(
    df: pd.DataFrame, col: str, chart_id: str, dim_score: float
) -> ChartSpec:
    counts = df[col].value_counts(dropna=True).sort_values(ascending=False)
    total_categories = len(counts)
    counts.index = counts.index.map(str)
    shown, folded = _fold_into_other(counts, settings.MAX_CATEGORIES_PER_CHART)
    data = [{"x": str(idx), "y": _clean(val)} for idx, val in shown.items()]
    pretty_col = format_column_label(col)
    
    coverage_note = ""
    if not folded and len(shown) < total_categories:
        coverage_note = f" (Showing top {len(shown)} of {total_categories} values)"

    spread = float(counts.std()) / (float(counts.mean()) + 1e-9) if len(counts) > 1 else 0.0
    score = (3.5 + min(spread, 2.0)) * dim_score
    
    is_tender = "tender" in col.lower() or "ocid" in col.lower()
    title = format_business_chart_title(None, col, agg="count", chart_type="bar")
    description = format_chart_description(None, col, agg="count", chart_type="bar", coverage_note=coverage_note)
    y_axis_label = "Number of Tenders" if is_tender else "Count"

    return ChartSpec(
        id=chart_id,
        chart_type="bar",
        title=title,
        description=description,
        x_label=pretty_col,
        y_label=y_axis_label,
        data=data,
        score=score,
        dimension_column=col,
    )


def _category_proportion_pie(
    df: pd.DataFrame, col: str, chart_id: str, dim_score: float
) -> Optional[ChartSpec]:
    counts = df[col].value_counts(dropna=True).sort_values(ascending=False)
    if len(counts) > settings.PIE_CHART_MAX_CATEGORIES or len(counts) <= 1:
        return None

    counts.index = counts.index.map(str)
    data = [{"x": str(idx), "y": _clean(val)} for idx, val in counts.items()]
    pretty_col = format_column_label(col)
    
    title = format_business_chart_title(None, col, agg="count", chart_type="pie")
    description = format_chart_description(None, col, agg="count", chart_type="pie")

    return ChartSpec(
        id=chart_id,
        chart_type="pie",
        title=title,
        description=description,
        x_label=pretty_col,
        y_label="Share of Total",
        data=data,
        score=3.0 * dim_score,
        dimension_column=col,
    )


def _category_measure_pie(
    df: pd.DataFrame, cat_col: str, num_col: str, chart_id: str, dim_score: float, met_score: float
) -> Optional[ChartSpec]:
    """A metric-weighted donut for additive part-to-whole measures (e.g. Spend by Category).
    
    STRICT VALIDATION: Never use pie charts for durations, averages, rates, ratios, percentages,
    or categories > 6!
    """
    agg = _pick_aggregation(num_col)
    if agg != "sum":
        return None

    lowered_metric = num_col.lower()
    if any(k in lowered_metric for k in ("duration", "days", "time", "hours", "rate", "ratio", "pct", "percent", "gpa", "score", "price", "bidders", "tenderers")):
        return None

    grouped = df.groupby(cat_col, dropna=True)[num_col].agg("sum")
    grouped = grouped.dropna().sort_values(ascending=False)
    if grouped.empty or grouped.nunique() <= 1 or (grouped < 0).any() or len(grouped) > settings.PIE_CHART_MAX_CATEGORIES:
        return None

    grouped.index = grouped.index.map(str)
    pretty_metric = format_column_label(num_col)
    pretty_dim = format_column_label(cat_col)
    data = [{"x": str(idx), "y": _clean(val)} for idx, val in grouped.items()]
    cv = float(grouped.std()) / (abs(float(grouped.mean())) + 1e-9)
    score = (5.0 + min(cv, 3.0)) * dim_score * met_score

    title = format_business_chart_title(num_col, cat_col, agg="sum", chart_type="pie")
    description = format_chart_description(num_col, cat_col, agg="sum", chart_type="pie")

    return ChartSpec(
        id=chart_id,
        chart_type="pie",
        title=title,
        description=description,
        x_label=pretty_dim,
        y_label=f"Total {pretty_metric}",
        data=data,
        score=score,
        dimension_column=cat_col,
        metric_column=num_col,
    )


def _categorical_measure_bar(
    df: pd.DataFrame,
    cat_col: str,
    num_col: str,
    chart_id: str,
    dim_score: float,
    met_score: float,
    *,
    top_n_only: bool = False,
) -> Optional[ChartSpec]:
    agg = _pick_aggregation(num_col)
    grouped = df.groupby(cat_col, dropna=True)[num_col].agg(agg)
    grouped = grouped.dropna().sort_values(ascending=False)
    if grouped.empty or grouped.nunique() <= 1:
        return None

    total_categories = len(grouped)
    grouped.index = grouped.index.map(str)
    limit = settings.MAX_CATEGORIES_PER_CHART if not top_n_only else TOP_N_HIGH_CARDINALITY_CATEGORIES
    coverage_note = ""
    
    if top_n_only:
        shown = grouped.iloc[:limit]
        folded = False
        if len(shown) < total_categories:
            coverage_note = f" (Showing top {len(shown)} of {total_categories} values)"
    elif agg == "sum":
        shown, folded = _fold_into_other(grouped, limit)
        if not folded and len(shown) < total_categories:
            coverage_note = f" (Showing top {len(shown)} of {total_categories} values)"
    else:
        shown = grouped.iloc[:limit]
        if len(shown) < total_categories:
            coverage_note = f" (Showing top {len(shown)} of {total_categories} values)"

    data = [{"x": str(idx), "y": _clean(val)} for idx, val in shown.items()]
    pretty_metric = format_column_label(num_col)
    pretty_dim = format_column_label(cat_col)
    cv = float(grouped.std()) / (abs(float(grouped.mean())) + 1e-9)
    score = (4.0 + min(cv, 3.0)) * dim_score * met_score

    title = format_business_chart_title(num_col, cat_col, agg=agg, chart_type="bar")
    if top_n_only:
        title = f"{title} (Top {len(shown)})"
    description = format_chart_description(num_col, cat_col, agg=agg, chart_type="bar", coverage_note=coverage_note)
    
    y_axis_label = f"Average {pretty_metric}" if agg == "mean" else f"Total {pretty_metric}"

    return ChartSpec(
        id=chart_id,
        chart_type="bar",
        title=title,
        description=description,
        x_label=pretty_dim,
        y_label=y_axis_label,
        data=data,
        score=score,
        dimension_column=cat_col,
        metric_column=num_col,
    )


def _histogram(
    df: pd.DataFrame, col: str, chart_id: str, met_score: float
) -> Optional[ChartSpec]:
    values = df[col].dropna().astype(float)
    if values.nunique() <= 1:
        return None

    bins = min(settings.HISTOGRAM_BIN_COUNT, max(5, values.nunique()))
    counts, edges = np.histogram(values, bins=bins)
    total = int(counts.sum())
    data = []
    for i in range(len(counts)):
        lo, hi = float(edges[i]), float(edges[i + 1])
        decimals = 0 if (hi - edges[0]) >= 10 else 2
        label = f"{lo:,.{decimals}f}\u2013{hi:,.{decimals}f}"
        pct = round(100 * int(counts[i]) / total, 1) if total else 0.0
        data.append(
            {"x": label, "y": int(counts[i]), "range_low": round(lo, 4),
             "range_high": round(hi, 4), "percent": pct}
        )

    pretty_col = format_column_label(col)
    title = f"{pretty_col} Distribution"
    description = format_chart_description(col, None, chart_type="histogram")
    score = (3.5 + min(float(np.std(counts)) / (float(np.mean(counts)) + 1e-9), 2.0)) * met_score

    return ChartSpec(
        id=chart_id,
        chart_type="histogram",
        title=title,
        description=description,
        x_label=f"{pretty_col} Range",
        y_label="Number of Records",
        data=data,
        score=score,
        metric_column=col,
    )


def _timeseries_line(
    df: pd.DataFrame, date_col: str, num_col: str, chart_id: str, met_score: float
) -> Optional[ChartSpec]:
    working = df[[date_col, num_col]].copy()
    working[date_col] = pd.to_datetime(working[date_col], errors="coerce", format="mixed")
    working = working.dropna(subset=[date_col, num_col])
    if working.empty:
        return None

    span_days = (working[date_col].max() - working[date_col].min()).days
    if span_days > 730:
        freq = "MS"
    elif span_days > 90:
        freq = "W"
    else:
        freq = "D"

    agg = _pick_aggregation(num_col)
    grouped = (
        working.set_index(date_col)[num_col]
        .resample(freq)
        .agg(agg)
        .dropna()
    )
    if len(grouped) < 2 or grouped.nunique() <= 1:
        return None

    data = [
        {"x": idx.date().isoformat(), "y": _clean(val)} for idx, val in grouped.items()
    ]
    pretty_metric = format_column_label(num_col)
    pretty_date = format_column_label(date_col)
    cv = float(grouped.std()) / (abs(float(grouped.mean())) + 1e-9)
    score = (5.0 + min(cv, 3.0)) * met_score

    title = format_business_chart_title(num_col, date_col, agg=agg, chart_type="line")
    description = format_chart_description(num_col, date_col, agg=agg, chart_type="line")
    y_axis_label = f"Average {pretty_metric}" if agg == "mean" else f"Total {pretty_metric}"

    return ChartSpec(
        id=chart_id,
        chart_type="line",
        title=title,
        description=description,
        x_label=pretty_date,
        y_label=y_axis_label,
        data=data,
        score=score,
        metric_column=num_col,
    )


def _scatter(
    df: pd.DataFrame,
    col_x: str,
    col_y: str,
    chart_id: str,
    met_score_x: float,
    met_score_y: float,
    id_col: Optional[str] = None,
) -> Optional[ChartSpec]:
    cols = [col_x, col_y] + ([id_col] if id_col else [])
    pair = df[cols].dropna(subset=[col_x, col_y])
    if len(pair) < 5:
        return None
    corr = pair[col_x].corr(pair[col_y])
    if pd.isna(corr):
        return None

    both_important = met_score_x >= 2.0 and met_score_y >= 2.0
    min_corr = SCATTER_MIN_CORRELATION_BOTH_IMPORTANT if both_important else SCATTER_MIN_CORRELATION
    if abs(float(corr)) < min_corr:
        return None

    sample = pair if len(pair) <= settings.SCATTER_MAX_POINTS else pair.sample(
        settings.SCATTER_MAX_POINTS, random_state=42
    )

    data = []
    for _, row in sample.iterrows():
        pt: Dict[str, Any] = {"x": _clean(row[col_x]), "y": _clean(row[col_y])}
        if id_col and id_col in row:
            pt["id"] = str(row[id_col])
        data.append(pt)

    pretty_x = format_column_label(col_x)
    pretty_y = format_column_label(col_y)
    score = (4.0 + min(abs(float(corr)) * 3.0, 3.0)) * (met_score_x + met_score_y) / 2.0

    return ChartSpec(
        id=chart_id,
        chart_type="scatter",
        title=f"{pretty_x} vs {pretty_y}",
        description=format_chart_description(col_y, col_x, chart_type="scatter"),
        x_label=pretty_x,
        y_label=pretty_y,
        data=data,
        score=score,
        dimension_column=col_x,
        metric_column=col_y,
    )


def _select_diverse(
    candidates: List[ChartSpec], max_charts: int
) -> List[ChartSpec]:
    per_type_cap = {
        "bar": 4,
        "line": 2,
        "scatter": 2,
        "histogram": 2,
        "pie": 2,
    }
    ranked = sorted(candidates, key=lambda c: c.score, reverse=True)
    selected: List[ChartSpec] = []
    type_counts: Dict[str, int] = {}
    for c in ranked:
        if len(selected) >= max_charts:
            break
        cap = per_type_cap.get(c.chart_type, 2)
        if type_counts.get(c.chart_type, 0) >= cap:
            continue
        selected.append(c)
        type_counts[c.chart_type] = type_counts.get(c.chart_type, 0) + 1
    return selected


@dataclass
class ColumnRanking:
    profiles: List[ColumnProfile]
    top_metrics: List[str]
    top_dimensions: List[str]
    important_hc_dimensions: List[str]
    datetime_cols: List[str]
    all_metrics: List[str]
    all_dimensions: List[str]


def rank_columns(df: pd.DataFrame) -> ColumnRanking:
    profiles = profile_dataset(df)
    by_role: Dict[str, List[ColumnProfile]] = {}
    for p in profiles:
        by_role.setdefault(p.role, []).append(p)

    numeric_cols = [p.name for p in by_role.get("numeric", [])]
    categorical_cols = [p.name for p in by_role.get("categorical", [])]
    boolean_cols = [p.name for p in by_role.get("boolean", [])]
    datetime_cols = [p.name for p in by_role.get("datetime", [])]
    high_cardinality_cols = [p.name for p in by_role.get("high_cardinality", [])]
    groupable_cols = categorical_cols + boolean_cols

    ranked_metrics = sorted(numeric_cols, key=metric_importance, reverse=True)
    ranked_dimensions = sorted(groupable_cols, key=dimension_importance, reverse=True)

    important_hc_dims = [
        c for c in high_cardinality_cols
        if dimension_importance(c) >= MIN_DIMENSION_SCORE_FOR_HIGH_CARDINALITY
    ]
    important_hc_dims = sorted(important_hc_dims, key=dimension_importance, reverse=True)

    return ColumnRanking(
        profiles=profiles,
        top_metrics=ranked_metrics[:TOP_K_METRICS],
        top_dimensions=ranked_dimensions[:TOP_K_DIMENSIONS],
        important_hc_dimensions=important_hc_dims[:TOP_K_HIGH_CARDINALITY_DIMENSIONS],
        datetime_cols=datetime_cols,
        all_metrics=ranked_metrics,
        all_dimensions=ranked_dimensions + important_hc_dims,
    )


def generate_recommendations(
    df: pd.DataFrame, ranking: Optional[ColumnRanking] = None
) -> List[ChartSpec]:
    if ranking is None:
        ranking = rank_columns(df)
    top_metrics = ranking.top_metrics
    top_dimensions = ranking.top_dimensions
    important_hc_dims = ranking.important_hc_dimensions
    datetime_cols = ranking.datetime_cols

    candidates: List[ChartSpec] = []
    counter = 0

    def next_id() -> str:
        nonlocal counter
        counter += 1
        return f"chart_{counter}"

    # 1) Category counts
    for col in top_dimensions:
        dim_score = dimension_importance(col)
        candidates.append(_category_counts_chart(df, col, next_id(), dim_score))
        distinct = df[col].nunique(dropna=True)
        if distinct <= settings.PIE_CHART_MAX_CATEGORIES and dim_score >= 2.0:
            pie_spec = None
            if top_metrics:
                pie_spec = _category_measure_pie(
                    df, col, top_metrics[0], next_id(),
                    dim_score, metric_importance(top_metrics[0]),
                )
            if pie_spec is None:
                pie_spec = _category_proportion_pie(df, col, next_id(), dim_score)
            if pie_spec is not None:
                candidates.append(pie_spec)

    # 2) Categorical x numeric measure breakdowns
    for cat_col in top_dimensions:
        dim_score = dimension_importance(cat_col)
        for num_col in top_metrics:
            met_score = metric_importance(num_col)
            spec = _categorical_measure_bar(
                df, cat_col, num_col, next_id(), dim_score, met_score
            )
            if spec is not None:
                candidates.append(spec)

    # 2b) "Top N"-style breakdowns for high-cardinality dimensions
    for cat_col in important_hc_dims:
        dim_score = dimension_importance(cat_col)
        for num_col in top_metrics[:2]:
            met_score = metric_importance(num_col)
            spec = _categorical_measure_bar(
                df, cat_col, num_col, next_id(), dim_score, met_score, top_n_only=True
            )
            if spec is not None:
                candidates.append(spec)

    # 3) Numeric distributions
    for col in top_metrics:
        spec = _histogram(df, col, next_id(), metric_importance(col))
        if spec is not None:
            candidates.append(spec)

    # 4) Time series
    for date_col in datetime_cols[:2]:
        pairs_added = 0
        for num_col in top_metrics:
            if pairs_added >= settings.TIMESERIES_MAX_PAIRS:
                break
            spec = _timeseries_line(
                df, date_col, num_col, next_id(), metric_importance(num_col)
            )
            if spec is not None:
                candidates.append(spec)
                pairs_added += 1

    # 5) Scatter plots
    id_col = top_dimensions[0] if top_dimensions else None
    if len(top_metrics) >= 2:
        corr_pairs: List[Tuple[str, str, float]] = []
        for i in range(len(top_metrics)):
            for j in range(i + 1, len(top_metrics)):
                a, b = top_metrics[i], top_metrics[j]
                pair = df[[a, b]].dropna()
                if len(pair) < 5:
                    continue
                corr = pair[a].corr(pair[b])
                if pd.isna(corr):
                    continue
                corr_pairs.append((a, b, abs(float(corr))))
        corr_pairs.sort(key=lambda t: t[2], reverse=True)
        for a, b, _ in corr_pairs[: settings.SCATTER_MAX_PAIRS]:
            spec = _scatter(
                df, a, b, next_id(), metric_importance(a), metric_importance(b), id_col
            )
            if spec is not None:
                candidates.append(spec)

    return _select_diverse(candidates, settings.MAX_RECOMMENDED_CHARTS)


# --- KPI summary -----------------------------------------------------------

_ORDER_NAME_HINTS = ("order", "transaction", "invoice", "booking")


def compute_kpis(df: pd.DataFrame, ranking: Optional[ColumnRanking] = None) -> List[Dict[str, Any]]:
    if ranking is None:
        ranking = rank_columns(df)

    kpis: List[Dict[str, Any]] = []
    row_count = int(len(df))
    dataset_currency = detect_dataset_currency(df)

    for col in ranking.top_metrics[:4]:
        agg = _pick_aggregation(col)
        series = df[col].dropna()
        if series.empty:
            continue
        value = float(series.sum()) if agg == "sum" else float(series.mean())
        label = f"Total {format_column_label(col)}" if agg == "sum" else f"Average {format_column_label(col)}"
        
        unit, semantic_type, sym = detect_column_unit(col, series=series, dataset_currency=dataset_currency)
        formatted = format_metric_display(value, unit=unit, semantic_type=semantic_type, currency_symbol=sym)
        
        kpis.append({
            "label": label,
            "value": round(value, 2),
            "kind": _kpi_kind(col),
            "format": "currency" if semantic_type == "currency" else ("percentage" if semantic_type == "percentage" else "number"),
            "unit": unit,
            "formatted_value": formatted,
            "source_column": col,
            "aggregation": agg,
            "semantic_type": semantic_type,
            "formatting_rule": f"{agg.upper()} of {col} formatted as {semantic_type} ({unit})",
        })

    looks_order_shaped = any(
        any(hint in c.lower() for hint in _ORDER_NAME_HINTS) for c in df.columns
    )
    is_tender_shaped = any("tender" in c.lower() or "ocid" in c.lower() for c in df.columns)
    
    count_label = "Total Tenders" if is_tender_shaped else ("Total Orders" if looks_order_shaped else "Total Records")
    count_unit = "tenders" if is_tender_shaped else ("orders" if looks_order_shaped else "records")
    formatted_count = f"{row_count:,} {count_unit}"
    kpis.append({
        "label": count_label,
        "value": row_count,
        "kind": "orders",
        "format": "count",
        "unit": count_unit,
        "formatted_value": formatted_count,
        "source_column": "Dataset Rows",
        "aggregation": "count",
        "semantic_type": "count",
        "formatting_rule": "Total discrete record count across dataset",
    })

    for col in ranking.top_metrics:
        if _pick_aggregation(col) == "sum" and row_count > 0:
            total = float(df[col].dropna().sum())
            avg_val = total / row_count
            unit, semantic_type, sym = detect_column_unit(col, series=df[col], dataset_currency=dataset_currency)
            formatted_avg = format_metric_display(avg_val, unit=unit, semantic_type=semantic_type, currency_symbol=sym)
            kpis.append({
                "label": f"Average {format_column_label(col)} per Row",
                "value": round(avg_val, 2),
                "kind": "average",
                "format": "currency" if semantic_type == "currency" else "number",
                "unit": unit,
                "formatted_value": formatted_avg,
                "source_column": col,
                "aggregation": "mean",
                "semantic_type": semantic_type,
                "formatting_rule": f"Average {col} per observation row",
            })
            break

    return kpis[:5]


def _kpi_kind(column_name: str) -> str:
    lowered = column_name.lower()
    if any(h in lowered for h in ("profit", "margin", "income", "earning")):
        return "profit"
    if any(h in lowered for h in ("sales", "revenue", "spend", "cost", "value", "amount")):
        return "sales"
    if any(h in lowered for h in ("quantity", "qty", "units", "bidders", "tenderers")):
        return "quantity"
    if any(h in lowered for h in ("discount", "rate", "pct")):
        return "discount"
    return "generic"


# --- Drill-down --------------------------------------------------------------

def generate_drilldown(
    df: pd.DataFrame,
    filters: List[Tuple[str, str]],
    ranking: Optional[ColumnRanking] = None,
) -> Optional[Dict[str, Any]]:
    if not filters:
        return None
    if ranking is None:
        ranking = rank_columns(df)

    subset = df
    for dim, val in filters:
        if dim not in subset.columns:
            return None
        subset = subset[subset[dim].astype(str) == str(val)]
        if subset.empty:
            return None

    current_dim, current_value = filters[-1]
    filtered_dims = {dim for dim, _ in filters}

    kpis = compute_kpis(subset, ranking)

    trend_chart = None
    if ranking.datetime_cols and ranking.top_metrics:
        date_col = ranking.datetime_cols[0]
        primary_metric = ranking.top_metrics[0]
        spec = _timeseries_line(
            subset, date_col, primary_metric, "drilldown_trend",
            metric_importance(primary_metric),
        )
        if spec is not None:
            spec.title = f"{current_value} \u2014 {format_column_label(primary_metric)} Over Time"
            trend_chart = spec.to_dict()

    secondary_chart = None
    secondary_dimension_column = None
    candidate_dims: List[str] = []
    for d in ranking.top_dimensions + ranking.important_hc_dimensions:
        if d not in filtered_dims and d not in candidate_dims:
            candidate_dims.append(d)

    def _child_dimension_score(dim: str) -> float:
        distinct_here = subset[dim].nunique(dropna=True)
        if distinct_here <= 1:
            return -1.0
        granularity_bonus = 1.0 + min(float(np.log1p(distinct_here)), 3.0)
        return dimension_importance(dim) * granularity_bonus

    candidate_dims = [d for d in candidate_dims if _child_dimension_score(d) > 0]
    candidate_dims.sort(key=_child_dimension_score, reverse=True)

    if candidate_dims and ranking.top_metrics:
        second_dim = candidate_dims[0]
        primary_metric = ranking.top_metrics[0]
        is_high_cardinality = second_dim in ranking.important_hc_dimensions
        spec = _categorical_measure_bar(
            subset, second_dim, primary_metric, "drilldown_secondary",
            dimension_importance(second_dim), metric_importance(primary_metric),
            top_n_only=is_high_cardinality,
        )
        if spec is not None:
            pretty_dim = format_column_label(second_dim)
            pretty_met = format_column_label(primary_metric)
            spec.title = f"{pretty_dim} Breakdown Within {current_value}"
            spec.description = (
                f"Compares '{pretty_met}' across '{pretty_dim}' within {format_column_label(current_dim)} = \"{current_value}\"."
            )
            secondary_chart = spec.to_dict()
            secondary_dimension_column = second_dim

    return {
        "dimension": current_dim,
        "dimension_label": format_column_label(current_dim),
        "value": str(current_value),
        "row_count": int(len(subset)),
        "kpis": kpis,
        "trend_chart": trend_chart,
        "secondary_chart": secondary_chart,
        "secondary_dimension": secondary_dimension_column,
        "applied_filters": [{"dimension": d, "value": v} for d, v in filters],
    }
