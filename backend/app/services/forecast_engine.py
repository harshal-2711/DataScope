"""Time-series statistical forecasting engine.

Provides optional, mathematically grounded forecasting using Holt's Linear
Exponential Smoothing with analytical prediction intervals (80% and 95%).
Never presents forecasts as guaranteed outcomes.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from app.schemas.domain_blueprint import (
    ForecastPointSchema,
    ForecastResponse,
    HistoricalPointSchema,
)
from app.services.trend_engine import _find_numeric_metrics, _find_time_column


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


def _fit_holt_linear(
    series: np.ndarray,
) -> Tuple[float, float, float, float, np.ndarray, float]:
    """Fit Holt's linear exponential smoothing model using grid search over (alpha, beta).
    Returns (best_alpha, best_beta, level_end, trend_end, fitted_values, rmse).
    """
    n = len(series)
    best_sse = float("inf")
    best_alpha = 0.3
    best_beta = 0.1
    best_level = float(series[-1])
    best_trend = 0.0
    best_fitted = np.zeros(n)

    # Initial level and trend estimates
    init_level = float(series[0])
    init_trend = float(series[1] - series[0]) if n > 1 else 0.0

    alphas = [0.1, 0.2, 0.3, 0.5, 0.7]
    betas = [0.05, 0.1, 0.2, 0.3]

    for a in alphas:
        for b in betas:
            level = init_level
            trend = init_trend
            fitted = np.zeros(n)
            sse = 0.0

            for t in range(n):
                pred = level + trend
                fitted[t] = pred
                actual = series[t]
                error = actual - pred
                sse += error * error

                # Update state
                new_level = a * actual + (1 - a) * (level + trend)
                new_trend = b * (new_level - level) + (1 - b) * trend
                level = new_level
                trend = new_trend

            if sse < best_sse:
                best_sse = sse
                best_alpha = a
                best_beta = b
                best_level = level
                best_trend = trend
                best_fitted = fitted

    rmse = math.sqrt(best_sse / n) if n > 0 else 0.0
    return best_alpha, best_beta, best_level, best_trend, best_fitted, rmse


def compute_forecast(
    df: pd.DataFrame,
    dataset_id: str,
    horizon: int = 6,
    metric: Optional[str] = None,
    granularity: Optional[str] = None,
) -> ForecastResponse:
    """Compute optional statistical forecast for a dataset time series."""
    horizon = max(1, min(horizon, 24))  # Cap horizon between 1 and 24

    time_col = _find_time_column(df)
    numeric_metrics = _find_numeric_metrics(df)

    if not time_col:
        return ForecastResponse(
            dataset_id=dataset_id,
            is_available=False,
            unavailable_reason="Forecast unavailable because the dataset does not contain a usable time or date dimension.",
            horizon=horizon,
            limitations=["Time-series forecasting requires a parseable date or timestamp column."],
        )

    selected_metric = metric if (metric and metric in numeric_metrics) else (numeric_metrics[0] if numeric_metrics else None)

    if not selected_metric:
        return ForecastResponse(
            dataset_id=dataset_id,
            is_available=False,
            unavailable_reason="Forecast unavailable because no continuous numeric metric was found to forecast.",
            time_column=time_col,
            horizon=horizon,
            limitations=["Forecasting requires a continuous numeric target metric."],
        )

    # Parse dates and filter non-null
    parsed_dates = pd.to_datetime(df[time_col], errors="coerce")
    clean_df = pd.DataFrame({
        "date": parsed_dates,
        "metric": pd.to_numeric(df[selected_metric], errors="coerce"),
    }).dropna().sort_values("date")

    if len(clean_df) < 6:
        return ForecastResponse(
            dataset_id=dataset_id,
            is_available=False,
            unavailable_reason=f"Forecast unavailable because the dataset contains only {len(clean_df)} valid historical observations (minimum 6 required).",
            metric=selected_metric,
            time_column=time_col,
            horizon=horizon,
            limitations=["At least 6 reliable historical periods are required for statistical time-series forecasting."],
        )

    # Determine frequency / granularity
    span_days = (clean_df["date"].max() - clean_df["date"].min()).days
    if granularity in ("D", "W", "M", "Q", "Y"):
        freq = granularity
    elif span_days > 730:
        freq = "M" if span_days <= 1800 else "Q"
    elif span_days > 60:
        freq = "W" if span_days <= 180 else "M"
    else:
        freq = "D"

    clean_df["period"] = clean_df["date"].dt.to_period(freq).dt.to_timestamp()
    ts = clean_df.groupby("period")["metric"].sum()

    if len(ts) < 6:
        # Try finer frequency if period collapsed to < 6
        clean_df["period"] = clean_df["date"].dt.to_period("D").dt.to_timestamp()
        ts = clean_df.groupby("period")["metric"].sum()
        freq = "D"

    if len(ts) < 6:
        return ForecastResponse(
            dataset_id=dataset_id,
            is_available=False,
            unavailable_reason=f"Forecast unavailable because the aggregated time series contains only {len(ts)} periods (minimum 6 required).",
            metric=selected_metric,
            time_column=time_col,
            horizon=horizon,
            limitations=["Minimum 6 historical time buckets required to compute level and trend parameters."],
        )

    series_vals = ts.values.astype(float)
    alpha, beta, end_level, end_trend, fitted, rmse = _fit_holt_linear(series_vals)

    # Accuracy metrics
    actuals = series_vals
    errors = np.abs(actuals - fitted)
    mae = float(np.mean(errors))

    # MAPE with zero-division guard
    nonzero_mask = actuals != 0
    if np.any(nonzero_mask):
        mape = float(np.mean(np.abs(actuals[nonzero_mask] - fitted[nonzero_mask]) / np.abs(actuals[nonzero_mask])) * 100.0)
    else:
        mape = 0.0

    # Historical data points
    historical_points: List[HistoricalPointSchema] = [
        HistoricalPointSchema(
            period=dt.strftime("%Y-%m-%d"),
            actual=round(float(v), 2),
        )
        for dt, v in zip(ts.index, ts.values)
    ]

    # Forecast future points
    last_date = ts.index[-1]
    last_val = float(ts.iloc[-1])
    forecast_points: List[ForecastPointSchema] = []

    # Check if target is all non-negative
    is_non_negative = np.all(series_vals >= 0)

    for h in range(1, horizon + 1):
        if freq == "D":
            future_dt = last_date + pd.Timedelta(days=h)
        elif freq == "W":
            future_dt = last_date + pd.Timedelta(weeks=h)
        elif freq == "M":
            future_dt = last_date + pd.DateOffset(months=h)
        elif freq == "Q":
            future_dt = last_date + pd.DateOffset(months=h * 3)
        elif freq == "Y":
            future_dt = last_date + pd.DateOffset(years=h)
        else:
            future_dt = last_date + pd.Timedelta(days=h * 7)

        point_forecast = end_level + (h * end_trend)
        # Expanding standard error over horizon
        se_h = rmse * math.sqrt(h)

        lower_80 = point_forecast - (1.28 * se_h)
        upper_80 = point_forecast + (1.28 * se_h)
        lower_95 = point_forecast - (1.96 * se_h)
        upper_95 = point_forecast + (1.96 * se_h)

        if is_non_negative:
            point_forecast = max(0.0, point_forecast)
            lower_80 = max(0.0, lower_80)
            lower_95 = max(0.0, lower_95)

        forecast_points.append(
            ForecastPointSchema(
                period=future_dt.strftime("%Y-%m-%d"),
                forecast=round(float(point_forecast), 2),
                lower_bound_80=round(float(lower_80), 2),
                upper_bound_80=round(float(upper_80), 2),
                lower_bound_95=round(float(lower_95), 2),
                upper_bound_95=round(float(upper_95), 2),
            )
        )

    # Projected growth over horizon
    end_forecast = forecast_points[-1].forecast if forecast_points else last_val
    proj_growth_pct: Optional[float] = None
    if last_val > 0:
        proj_growth_pct = round(((end_forecast - last_val) / last_val) * 100.0, 1)

    # Confidence score based on MAPE
    conf_score = max(0.50, min(0.95, round(1.0 - (mape / 100.0), 2))) if mape < 100 else 0.50

    return ForecastResponse(
        dataset_id=dataset_id,
        is_available=True,
        metric=selected_metric,
        time_column=time_col,
        horizon=horizon,
        method_used=f"Holt's Linear Exponential Smoothing (alpha={alpha}, beta={beta})",
        historical_points=historical_points,
        forecast_points=forecast_points,
        projected_growth_pct=proj_growth_pct,
        accuracy_metrics={
            "mape": round(mape, 2),
            "rmse": round(rmse, 2),
            "mae": round(mae, 2),
        },
        confidence_score=conf_score,
        limitations=[
            "Forecasts are purely mathematical projections assuming continuation of historical level and trend trajectories.",
            "External market shocks, competitor actions, seasonal shifts not captured in history, and regulatory changes cannot be predicted.",
            "Prediction intervals widen as the forecast horizon extends, indicating increasing uncertainty.",
        ],
        disclaimer=(
            "Forecasts are mathematical extrapolations of historical patterns based on in-sample data. "
            "They do not account for unforeseen external events or structural market shifts. Not guaranteed outcomes."
        ),
    )
