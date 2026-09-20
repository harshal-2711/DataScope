"""Domain chart generation engine.

Generates aggregated, ready-to-render chart specifications strictly using
frontend-supported chart types: bar, line, pie, histogram, scatter.
All aggregation happens on the server; raw data is never exposed.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from app.domains.base import ChartRule
from app.schemas.domain_blueprint import DomainChartSpecSchema


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


def generate_domain_charts(
    df: pd.DataFrame,
    validated_charts: List[Tuple[ChartRule, Optional[str], Optional[str]]],
) -> List[DomainChartSpecSchema]:
    """Generate ready-to-render chart specifications from validated blueprint rules."""
    charts: List[DomainChartSpecSchema] = []

    for rule, dim_col, metric_col in validated_charts:
        try:
            if rule.chart_type == "histogram" and metric_col and metric_col in df.columns:
                s = pd.to_numeric(df[metric_col], errors="coerce").dropna()
                if len(s) >= 5:
                    counts, bin_edges = np.histogram(s, bins=min(12, len(s.unique())))
                    data: List[Dict[str, Any]] = []
                    for i in range(len(counts)):
                        bin_label = f"{round(bin_edges[i], 1)} - {round(bin_edges[i+1], 1)}"
                        data.append({"x": bin_label, "y": int(counts[i])})

                    charts.append(
                        DomainChartSpecSchema(
                            id=rule.id,
                            title=rule.title,
                            chart_type="histogram",
                            x_label=metric_col.replace("_", " ").title(),
                            y_label="Frequency",
                            metric_column=metric_col,
                            data=data,
                            business_question=rule.business_question,
                        )
                    )

            elif rule.chart_type == "scatter" and dim_col and metric_col:
                # dim_col is metric1, metric_col is metric2
                clean = df[[dim_col, metric_col]].dropna()
                if len(clean) >= 5:
                    sample_df = clean.head(200)
                    data = [
                        {"x": _clean_val(r[dim_col]), "y": _clean_val(r[metric_col])}
                        for _, r in sample_df.iterrows()
                    ]
                    charts.append(
                        DomainChartSpecSchema(
                            id=rule.id,
                            title=rule.title,
                            chart_type="scatter",
                            x_label=dim_col.replace("_", " ").title(),
                            y_label=metric_col.replace("_", " ").title(),
                            dimension_column=dim_col,
                            metric_column=metric_col,
                            data=data,
                            business_question=rule.business_question,
                        )
                    )

            elif dim_col and dim_col in df.columns:
                # bar, line, pie
                if metric_col and metric_col in df.columns:
                    clean = df[[dim_col, metric_col]].dropna()
                    if clean.empty:
                        continue
                    if rule.chart_type == "line":
                        grouped = clean.groupby(dim_col)[metric_col].sum()
                    else:
                        grouped = clean.groupby(dim_col)[metric_col].sum().sort_values(ascending=False)
                else:
                    # Categorical count
                    clean = df[[dim_col]].dropna()
                    if clean.empty:
                        continue
                    grouped = clean[dim_col].value_counts()

                if len(grouped) == 0:
                    continue

                top_n = grouped.head(rule.max_categories or 12)
                data = [
                    {"x": _clean_val(k), "y": _clean_val(v)}
                    for k, v in top_n.items()
                ]

                charts.append(
                    DomainChartSpecSchema(
                        id=rule.id,
                        title=rule.title,
                        chart_type=rule.chart_type,
                        x_label=dim_col.replace("_", " ").title(),
                        y_label=(metric_col.replace("_", " ").title() if metric_col else "Count"),
                        dimension_column=dim_col,
                        metric_column=metric_col,
                        aggregation=rule.aggregation,
                        data=data,
                        business_question=rule.business_question,
                    )
                )

        except Exception:
            continue

    return charts
