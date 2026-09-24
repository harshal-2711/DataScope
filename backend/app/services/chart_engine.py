"""Domain chart recommendation and generation engine.

Strictly follows the analytical hierarchy:
DATA UNDERSTANDING -> DATASET GRAIN -> DOMAIN DETECTION -> ANALYTICAL QUESTION ->
METRIC VALIDATION -> CHART SELECTION -> EXPLANATION -> LIMITATIONS

Rules enforced:
- Bar charts for category comparisons
- Line charts for valid time trends
- Histograms for distributions
- Scatter plots for numerical relationships
- Pie/donut charts ONLY for valid part-to-whole data with <= 6 categories
- NEVER use pie charts for averages, rates, or durations
- Remove duplicate and low-value charts
- Populate analytical questions, metric definition, units, explanations, and limitations
- Human-readable column labels and business titles across all specs
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from app.domains.base import ChartRule
from app.schemas.domain_blueprint import DomainChartSpecSchema
from app.services.column_formatter import (
    format_business_chart_title,
    format_chart_description,
    format_column_label,
)


def _clean_val(v: Any) -> Any:
    if v is None:
        return None
    if isinstance(v, (np.integer, int)):
        return int(v)
    if isinstance(v, (np.floating, float)):
        f = float(v)
        return None if (math.isnan(f) or math.isinf(f)) else round(f, 2)
    if isinstance(v, (pd.Timestamp, np.datetime64)):
        return str(v)[:10]
    return str(v)


def _infer_unit(col_name: str) -> str:
    lowered = col_name.lower()
    if any(k in lowered for k in ("price", "cost", "revenue", "sales", "amount", "budget", "spend", "value", "fee", "salary", "charge")):
        return "Amount"
    if any(k in lowered for k in ("pct", "percent", "rate", "share", "ratio", "margin")):
        return "Percentage (%)"
    if any(k in lowered for k in ("days", "duration", "time", "hours", "tenure", "lead_time")):
        return "Days"
    if any(k in lowered for k in ("bidders", "tenderers")):
        return "Number of Bidders"
    if any(k in lowered for k in ("count", "orders", "bids", "tenders", "items", "units", "quantity", "runs", "wickets")):
        return "Count"
    return "Units"


def generate_domain_charts(
    df: pd.DataFrame,
    validated_charts: List[Tuple[ChartRule, Optional[str], Optional[str]]],
    dataset_grain_label: str = "One row per observation",
) -> List[DomainChartSpecSchema]:
    """Generate ready-to-render, validated chart specifications with analytical metadata."""
    charts: List[DomainChartSpecSchema] = []
    row_count = len(df)

    for rule, dim_col, metric_col in validated_charts:
        try:
            # 1. Histograms for distributions
            if rule.chart_type == "histogram" and metric_col and metric_col in df.columns:
                s = pd.to_numeric(df[metric_col], errors="coerce").dropna()
                if len(s) >= 5:
                    counts, bin_edges = np.histogram(s, bins=min(10, len(s.unique())))
                    data: List[Dict[str, Any]] = []
                    for i in range(len(counts)):
                        bin_label = f"{round(bin_edges[i], 1)} - {round(bin_edges[i+1], 1)}"
                        data.append({"x": bin_label, "y": int(counts[i])})

                    pretty_metric = format_column_label(metric_col)
                    charts.append(
                        DomainChartSpecSchema(
                            id=rule.id,
                            title=rule.title or f"{pretty_metric} Distribution",
                            chart_type="histogram",
                            x_label=f"{pretty_metric} Range",
                            y_label="Observation Frequency",
                            metric_column=metric_col,
                            data=data,
                            business_question=rule.business_question,
                            analytical_question=rule.business_question or f"What is the frequency distribution of '{pretty_metric}' across observations?",
                            metric_definition=f"Binned frequency count of continuous measure '{pretty_metric}'.",
                            unit=_infer_unit(metric_col),
                            aggregation="count",
                            grouping=f"Bins of {pretty_metric}",
                            dataset_grain=dataset_grain_label,
                            data_coverage=f"{len(s):,} of {row_count:,} rows ({round(len(s)/row_count*100, 1)}%)",
                            explanation=f"Histogram reveals the skewness, modality, and spread of '{pretty_metric}'.",
                            limitations="Binned into discrete intervals. Extreme outliers may compress central bin granularity.",
                        )
                    )

            # 2. Scatter plots for continuous numerical relationships
            elif rule.chart_type == "scatter" and dim_col and metric_col and dim_col in df.columns and metric_col in df.columns:
                clean = df[[dim_col, metric_col]].dropna()
                if len(clean) >= 5:
                    sample_df = clean.head(150)
                    data = [
                        {"x": _clean_val(r[dim_col]), "y": _clean_val(r[metric_col])}
                        for _, r in sample_df.iterrows()
                    ]
                    pretty_dim = format_column_label(dim_col)
                    pretty_metric = format_column_label(metric_col)
                    charts.append(
                        DomainChartSpecSchema(
                            id=rule.id,
                            title=rule.title or f"{pretty_metric} vs {pretty_dim}",
                            chart_type="scatter",
                            x_label=pretty_dim,
                            y_label=pretty_metric,
                            dimension_column=dim_col,
                            metric_column=metric_col,
                            data=data,
                            business_question=rule.business_question,
                            analytical_question=rule.business_question or f"How does '{pretty_metric}' vary in relation to '{pretty_dim}'?",
                            metric_definition=f"Bivariate pairing between '{pretty_metric}' and '{pretty_dim}'.",
                            unit=f"{_infer_unit(metric_col)} vs {_infer_unit(dim_col)}",
                            aggregation="individual_observations",
                            grouping="entity_observations",
                            dataset_grain=dataset_grain_label,
                            data_coverage=f"{len(clean):,} of {row_count:,} rows ({round(len(clean)/row_count*100, 1)}%)",
                            explanation=f"Evaluates correlation, clustering, and outlier dispersion between '{pretty_dim}' and '{pretty_metric}'.",
                            limitations="Scatter plots demonstrate statistical association, never causal certainty.",
                        )
                    )

            # 3. Bar, Line, Pie charts
            elif dim_col and dim_col in df.columns:
                agg_type = getattr(rule, "aggregation", "sum") or "sum"

                if metric_col and metric_col in df.columns:
                    clean = df[[dim_col, metric_col]].dropna()
                    if clean.empty:
                        continue

                    if agg_type == "mean":
                        grouped = clean.groupby(dim_col)[metric_col].mean().sort_values(ascending=False)
                    else:
                        grouped = clean.groupby(dim_col)[metric_col].sum()
                        if rule.chart_type != "line":
                            grouped = grouped.sort_values(ascending=False)
                else:
                    clean = df[[dim_col]].dropna()
                    if clean.empty:
                        continue
                    grouped = clean[dim_col].value_counts()
                    agg_type = "count"

                if len(grouped) == 0:
                    continue

                chart_type = rule.chart_type
                lowered_metric = (metric_col or "").lower()
                is_duration_or_average = (
                    agg_type in ("mean", "average", "median", "rate", "ratio")
                    or any(k in lowered_metric for k in ("duration", "days", "time", "rate", "ratio", "avg", "mean", "bidders", "tenderers", "gpa", "score"))
                )

                # Strict Rule: Never use pie charts for durations, averages, or > 6 categories
                if chart_type == "pie":
                    if is_duration_or_average or len(grouped) > 6:
                        chart_type = "bar"

                max_cats = 6 if chart_type == "pie" else (rule.max_categories or 12)
                top_n = grouped.head(max_cats)

                data = [
                    {"x": _clean_val(k), "y": _clean_val(v)}
                    for k, v in top_n.items()
                ]

                pretty_dim = format_column_label(dim_col)
                pretty_metric = format_column_label(metric_col) if metric_col else "Count"

                title = rule.title
                if not title or "/" in title or "tender/" in title.lower():
                    title = format_business_chart_title(metric_col, dim_col, agg=agg_type, chart_type=chart_type)

                unit_str = _infer_unit(metric_col) if metric_col else "Count"
                question = rule.business_question or (
                    f"Which {pretty_dim} categories account for the highest {agg_type} {pretty_metric}?"
                )

                explanation = (
                    f"Part-to-whole breakdown of top {len(data)} {pretty_dim} segments."
                    if chart_type == "pie"
                    else f"Compares {agg_type} '{pretty_metric}' across distinct '{pretty_dim}' groups."
                )

                limitations = (
                    f"Displays top {len(data)} categories by {agg_type}. Remaining categories aggregated or excluded."
                    if len(grouped) > max_cats
                    else "All observed distinct categories displayed."
                )

                y_axis_label = f"Average {pretty_metric}" if agg_type == "mean" else (f"Total {pretty_metric}" if metric_col else "Count")

                charts.append(
                    DomainChartSpecSchema(
                        id=rule.id,
                        title=title,
                        chart_type=chart_type,
                        x_label=pretty_dim,
                        y_label=y_axis_label,
                        dimension_column=dim_col,
                        metric_column=metric_col,
                        aggregation=agg_type,
                        data=data,
                        business_question=question,
                        analytical_question=question,
                        metric_definition=f"{agg_type.capitalize()} of '{pretty_metric if metric_col else pretty_dim}'",
                        unit=unit_str,
                        grouping=pretty_dim,
                        dataset_grain=dataset_grain_label,
                        data_coverage=f"{len(clean):,} of {row_count:,} rows ({round(len(clean)/row_count*100, 1)}%)",
                        explanation=explanation,
                        limitations=limitations,
                    )
                )

        except Exception:
            continue

    return charts
