"""Time-series trend intelligence engine.

Calculates verified trends, growth rates, moving averages, peaks, and troughs
from actual dataset time series without speculative claims.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from app.domains.base import TrendRule
from app.schemas.domain_blueprint import TrendItemSchema


def compute_trends(
    df: pd.DataFrame,
    validated_trends: List[Tuple[TrendRule, str, str]],
) -> List[TrendItemSchema]:
    """Calculate statistical time-series trends, peaks, troughs, and growth rates."""
    results: List[TrendItemSchema] = []

    for rule, metric_col, date_col in validated_trends:
        if date_col not in df.columns or metric_col not in df.columns:
            continue

        clean_df = df[[date_col, metric_col]].dropna().copy()
        if clean_df.empty:
            continue

        try:
            # Parse datetime
            clean_df["parsed_date"] = pd.to_datetime(clean_df[date_col], errors="coerce")
            clean_df = clean_df.dropna(subset=["parsed_date"])
            if len(clean_df) < 3:
                continue

            clean_df = clean_df.sort_values("parsed_date")

            # Determine grouping frequency based on span
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

            # Calculate metrics
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

            # Linear slope to determine trend direction
            x = np.arange(len(ts))
            y = ts.values.astype(float)
            slope, _ = np.polyfit(x, y, 1) if len(x) >= 2 else (0.0, 0.0)

            if slope > 0.05 * np.std(y):
                direction = "increasing"
            elif slope < -0.05 * np.std(y):
                direction = "decreasing"
            else:
                direction = "stable"

            # 3-period moving average
            ma = ts.rolling(window=min(3, len(ts)), min_periods=1).mean()

            data_points: List[Dict[str, Any]] = [
                {
                    "date": dt.strftime("%Y-%m-%d"),
                    "value": round(float(v), 2),
                    "moving_avg": round(float(m), 2),
                }
                for dt, v, m in zip(ts.index, ts.values, ma.values)
            ]

            desc = f"{metric_col.capitalize()} is {direction} over the observation window"
            if growth_pct is not None:
                desc += f" (net change: {growth_pct:+0.1f}%)"
            desc += f". Peak of {round(peak_val, 2):,} on {peak_str}."

            results.append(
                TrendItemSchema(
                    metric_name=metric_col,
                    time_column=date_col,
                    trend_direction=direction,
                    growth_rate_pct=growth_pct,
                    peak_period=peak_str,
                    trough_period=trough_str,
                    seasonality_detected=False,
                    description=desc,
                    data_points=data_points,
                )
            )
        except Exception:
            continue

    return results
