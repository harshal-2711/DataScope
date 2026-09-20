"""Comparison intelligence engine.

Generates factual, evidence-based comparative analyses across categories,
segments, time periods, and entities without fabricating targets or missing values.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from app.domains.base import ComparisonRule
from app.schemas.domain_blueprint import ComparisonItemSchema


def compute_comparisons(
    df: pd.DataFrame,
    validated_comparisons: List[Tuple[ComparisonRule, str, str]],
) -> List[ComparisonItemSchema]:
    """Calculate verified comparative metrics between categories, time periods, or segments."""
    results: List[ComparisonItemSchema] = []

    for rule, dim_col, metric_col in validated_comparisons:
        if dim_col not in df.columns or metric_col not in df.columns:
            continue

        clean_df = df[[dim_col, metric_col]].dropna()
        if clean_df.empty or clean_df[dim_col].nunique() < 2:
            continue

        try:
            # Aggregate metric by dimension
            grouped = clean_df.groupby(dim_col)[metric_col].sum().sort_values(ascending=False)
            if len(grouped) < 2:
                continue

            top_name = str(grouped.index[0])
            top_val = float(grouped.iloc[0])
            second_name = str(grouped.index[1])
            second_val = float(grouped.iloc[1])

            diff = top_val - second_val
            pct_change = ((diff / second_val) * 100.0) if second_val > 0 else None

            # Prepare breakdown chart data
            data: List[Dict[str, Any]] = [
                {"category": str(k), "value": round(float(v), 2)}
                for k, v in grouped.head(8).items()
            ]

            insight_desc = f"{top_name} leads {second_name} by {round(diff, 2):,}"
            if pct_change is not None:
                insight_desc += f" (+{round(pct_change, 1)}%)"

            results.append(
                ComparisonItemSchema(
                    comparison_type=rule.comparison_type,
                    title=rule.title or f"{dim_col.capitalize()} Comparison on {metric_col.capitalize()}",
                    baseline=second_name,
                    target=top_name,
                    metric=metric_col,
                    baseline_value=round(second_val, 2),
                    target_value=round(top_val, 2),
                    difference=round(diff, 2),
                    pct_change=round(pct_change, 1) if pct_change is not None else None,
                    insight=insight_desc,
                    data=data,
                )
            )
        except Exception:
            continue

    return results
