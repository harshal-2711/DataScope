"""Universal Time-Series Statistical Forecasting Engine for DataScope.

Dataset-agnostic forecasting supporting multiple baseline and trend methods:
- Naive Baseline
- Moving Average
- Holt's Linear Exponential Smoothing
- Linear Trend Extrapolation
- Auto Model Selection with Holdout / In-sample Validation

Includes prediction intervals (80% and 95%), domain-aware interpretation,
frequency inference, and data hygiene protections. Never presents forecasts
as guaranteed outcomes.
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
from app.services.column_formatter import detect_column_unit, format_column_label
from app.services.trend_engine import _find_time_column
from app.services.type_inference import detect_dataset_currency


def _find_forecasting_metrics(df: pd.DataFrame) -> List[str]:
    """Find valid numeric metrics for time-series forecasting, including constant series, excluding IDs."""
    metrics: List[str] = []
    for col in df.columns:
        col_str = str(col)
        col_lower = col_str.lower().strip().replace(" ", "_").replace("/", "_")
        if pd.api.types.is_numeric_dtype(df[col]) and not pd.api.types.is_bool_dtype(df[col]):
            if any(col_lower == t or col_lower.endswith(f"_{t}") for t in ("id", "code", "zip", "key", "phone")):
                continue
            non_null = df[col].dropna()
            if non_null.nunique() >= 1:
                metrics.append(col_str)
    return metrics


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


def _calc_metrics(actual: np.ndarray, predicted: np.ndarray) -> Dict[str, float]:
    """Calculate MAE, RMSE, and zero-safe MAPE between actual and predicted vectors."""
    n = len(actual)
    if n == 0:
        return {"mae": 0.0, "rmse": 0.0, "mape": 0.0}

    errors = actual - predicted
    mae = float(np.mean(np.abs(errors)))
    rmse = float(math.sqrt(np.mean(errors ** 2)))

    # Zero-division guarded MAPE
    nonzero_mask = np.abs(actual) > 1e-7
    if np.any(nonzero_mask):
        mape = float(np.mean(np.abs(errors[nonzero_mask]) / np.abs(actual[nonzero_mask])) * 100.0)
    else:
        mape = 0.0

    return {
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "mape": round(min(mape, 999.9), 2),
    }


# --- Forecasting Model Implementations ---------------------------------------

def _fit_naive(
    series: np.ndarray, horizon: int
) -> Tuple[np.ndarray, np.ndarray, Dict[str, float], str]:
    """Naive Baseline model: projects the latest observed value."""
    n = len(series)
    last_val = float(series[-1])
    fitted = np.full(n, last_val)
    if n > 1:
        fitted[1:] = series[:-1]
    
    forecast = np.full(horizon, last_val)
    metrics = _calc_metrics(series[1:] if n > 1 else series, fitted[1:] if n > 1 else fitted)
    desc = "Naive Baseline (Latest Observed Level)"
    return fitted, forecast, metrics, desc


def _fit_moving_average(
    series: np.ndarray, horizon: int, window: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray, Dict[str, float], str]:
    """Adaptive Moving Average model."""
    n = len(series)
    w = window or max(2, min(5, max(1, n // 3)))
    fitted = np.zeros(n)
    
    for t in range(n):
        start_idx = max(0, t - w)
        fitted[t] = float(np.mean(series[start_idx:t])) if t > 0 else series[0]
        
    tail_mean = float(np.mean(series[-w:])) if n >= w else float(np.mean(series))
    forecast = np.full(horizon, tail_mean)
    metrics = _calc_metrics(series[1:] if n > 1 else series, fitted[1:] if n > 1 else fitted)
    desc = f"Moving Average (window={w} periods)"
    return fitted, forecast, metrics, desc


def _fit_linear_trend(
    series: np.ndarray, horizon: int
) -> Tuple[np.ndarray, np.ndarray, Dict[str, float], str]:
    """Ordinary Least Squares linear trend extrapolation."""
    n = len(series)
    x = np.arange(n)
    if n > 1:
        slope, intercept = np.polyfit(x, series, deg=1)
    else:
        slope, intercept = 0.0, float(series[0])

    fitted = slope * x + intercept
    future_x = np.arange(n, n + horizon)
    forecast = slope * future_x + intercept
    metrics = _calc_metrics(series, fitted)
    desc = f"Linear Trend (slope={slope:.2f}/period)"
    return fitted, forecast, metrics, desc


def _fit_holt_linear(
    series: np.ndarray, horizon: int
) -> Tuple[np.ndarray, np.ndarray, Dict[str, float], str]:
    """Holt's Linear Exponential Smoothing with grid-search parameter tuning."""
    n = len(series)
    best_sse = float("inf")
    best_alpha = 0.3
    best_beta = 0.1
    best_level = float(series[-1])
    best_trend = 0.0
    best_fitted = np.zeros(n)

    init_level = float(series[0])
    init_trend = float(series[1] - series[0]) if n > 1 else 0.0

    alphas = [0.1, 0.2, 0.3, 0.5, 0.7]
    betas = [0.02, 0.05, 0.1, 0.2, 0.3]

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

    # Forecast points
    forecast = np.array([best_level + (h * best_trend) for h in range(1, horizon + 1)])
    metrics = _calc_metrics(series, best_fitted)
    desc = f"Holt's Linear Exponential Smoothing (alpha={best_alpha}, beta={best_beta})"
    return best_fitted, forecast, metrics, desc


# --- Domain-Aware Narrative Interpretation -----------------------------------

def _generate_domain_interpretation(
    metric_name: str,
    semantic_type: str,
    unit: str,
    latest_val: float,
    final_val: float,
    growth_pct: Optional[float],
    horizon: int,
    freq_label: str,
    method_name: str,
) -> str:
    """Generate professional, cautious domain-aware executive interpretations."""
    pretty_name = format_column_label(metric_name)
    m_lower = metric_name.lower()
    
    change_abs = round(final_val - latest_val, 2)
    change_sign = "+" if change_abs > 0 else ""
    pct_str = f"{change_sign}{growth_pct:.1f}%" if growth_pct is not None else "N/A"
    
    direction = "an upward trajectory" if change_abs > 0.05 else "a downward trend" if change_abs < -0.05 else "relative stability"
    verb = "projected to increase" if change_abs > 0.05 else "projected to contract" if change_abs < -0.05 else "estimated to remain steady"

    # 1. Revenue / Sales
    if semantic_type == "currency" and any(k in m_lower for k in ("rev", "sale", "income", "gmv", "aov")):
        narrative = (
            f"Forecasted revenue for {pretty_name} is {verb} over the next {horizon} {freq_label.lower()} periods, "
            f"moving from {unit}{latest_val:,.2f} to an estimated {unit}{final_val:,.2f} ({pct_str}, net change {unit}{change_abs:,.2f}). "
            f"Based on historical trajectories fitted via {method_name}."
        )
    # 2. Profit / Margin
    elif "profit" in m_lower or "ebitda" in m_lower:
        narrative = (
            f"Forecasted profitability for {pretty_name} indicates {direction} across the {horizon}-{freq_label.lower()} horizon, "
            f"reaching an estimated {unit}{final_val:,.2f} ({pct_str} change from the latest {unit}{latest_val:,.2f}). "
            f"Note: Operational cost shifts or external market dynamics may alter actual returns."
        )
    # 3. Expenses / Cost / Spend
    elif any(k in m_lower for k in ("cost", "spend", "expense", "budget", "fee", "tax")):
        narrative = (
            f"Forecasted expenditure for {pretty_name} is {verb} by {pct_str}, "
            f"moving from {unit}{latest_val:,.2f} to {unit}{final_val:,.2f}. "
            f"Tracking historical level and rate parameters across {horizon} {freq_label.lower()} periods."
        )
    # 4. Volume / Quantity / Headcount / Orders
    elif semantic_type in ("quantity", "count") or any(k in m_lower for k in ("qty", "unit", "order", "count", "headcount", "patient", "student", "run")):
        u_str = f" {unit}" if unit and unit not in ("₹", "$", "€", "£") else ""
        narrative = (
            f"Forecasted volume for {pretty_name} suggests {direction} across the upcoming {horizon} {freq_label.lower()} periods, "
            f"projecting from {latest_val:,.2f}{u_str} to approximately {final_val:,.2f}{u_str} ({pct_str})."
        )
    # 5. Percentage / Rate / Churn
    elif semantic_type == "percentage" or unit == "%":
        narrative = (
            f"Forecasted rate for {pretty_name} is estimated to shift by {change_sign}{change_abs:.2f} percentage points, "
            f"moving from {latest_val:.2f}% to approximately {final_val:.2f}% over the {horizon}-{freq_label.lower()} forecast horizon."
        )
    # 6. Neutral / Unknown
    else:
        u_str = f" {unit}" if unit and unit not in ("units", "") else ""
        narrative = (
            f"Based on empirical historical patterns, statistical modeling projects {direction} for {pretty_name}, "
            f"moving from {latest_val:,.2f}{u_str} to an estimated {final_val:,.2f}{u_str} ({pct_str}) across {horizon} {freq_label.lower()} periods."
        )

    return f"{narrative} Forecasts are mathematical extrapolations of past patterns and do not guarantee future outcomes."


# --- Metric Ranking & Automatic Selection -------------------------------------

def _rank_forecasting_metrics(df: pd.DataFrame, time_col: str) -> List[Tuple[str, float, str]]:
    """Rank numeric columns by semantic relevance, domain context, data completeness, and time-series viability.

    Returns:
        List of tuples: (column_name, suitability_score, selection_rationale)
        sorted by score descending.
    """
    candidates = _find_forecasting_metrics(df)
    if not candidates:
        return []

    parsed_dates = pd.to_datetime(df[time_col], errors="coerce")
    total_rows = max(1, len(df))
    curr_sym = detect_dataset_currency(df)

    scored: List[Tuple[str, float, str]] = []

    for col in candidates:
        valid_mask = parsed_dates.notna() & df[col].notna()
        valid_count = int(valid_mask.sum())

        if valid_count < 6:
            score = -100.0 + valid_count
            rationale = f"Insufficient time-series observations ({valid_count} valid periods, minimum 6 required)."
            scored.append((col, score, rationale))
            continue

        score = 0.0
        pretty_name = format_column_label(col)
        col_lower = col.lower()
        unit_str, sem_type, _ = detect_column_unit(col, series=df[col], dataset_currency=curr_sym)

        # 1. Semantic Domain Relevance
        if sem_type == "currency" or any(k in col_lower for k in ("rev", "sale", "income", "gmv", "aov", "turnover")):
            score += 65.0
            sem_reason = "primary financial/revenue metric"
        elif "profit" in col_lower or "ebitda" in col_lower or "margin" in col_lower:
            score += 60.0
            sem_reason = "key profitability indicator"
        elif sem_type in ("quantity", "count") or any(k in col_lower for k in ("qty", "unit", "order", "headcount", "patient", "student", "run", "wicket", "view", "click", "goal")):
            score += 55.0
            sem_reason = "primary operational volume measure"
        elif any(k in col_lower for k in ("cost", "spend", "expense", "budget", "fee", "tax")):
            score += 48.0
            sem_reason = "expenditure metric"
        elif sem_type == "percentage" or unit_str == "%" or "rate" in col_lower:
            score += 35.0
            sem_reason = "performance rate metric"
        else:
            score += 25.0
            sem_reason = "continuous numerical time series"

        # 2. Completeness & Observation Count
        completeness = valid_count / total_rows
        score += completeness * 20.0
        score += min(15.0, (valid_count / 10.0))

        # 3. Variance / Diversity (prefer varied over constant, but constant is allowed)
        distinct_cnt = int(df[col].dropna().nunique())
        if distinct_cnt > 1:
            score += 10.0

        rationale = (
            f"Automatically selected as {sem_reason} based on high completeness "
            f"({int(completeness * 100)}%), {valid_count} sequential historical observations, "
            f"and strong domain relevance."
        )
        scored.append((col, score, rationale))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


# --- Main Forecast Engine ---------------------------------------------------

def compute_forecast(
    df: pd.DataFrame,
    dataset_id: str,
    horizon: int = 7,
    metric: Optional[str] = None,
    granularity: Optional[str] = None,
    method: Optional[str] = "auto",
) -> ForecastResponse:
    """Compute dataset-agnostic statistical forecast with automatic metric selection and multi-model evaluation."""
    # Sanitize horizon (1 to 60 periods)
    horizon = max(1, min(horizon, 60))

    time_col = _find_time_column(df)
    numeric_metrics = _find_forecasting_metrics(df)

    if not time_col:
        return ForecastResponse(
            dataset_id=dataset_id,
            is_available=False,
            unavailable_reason="Forecast unavailable because the dataset does not contain a parseable time or date column.",
            horizon=horizon,
            available_metrics=numeric_metrics,
            limitations=[
                "Time-series forecasting requires at least one date or timestamp dimension.",
                "Ensure your dataset includes a column formatted as ISO dates (YYYY-MM-DD), timestamps, or standard date formats.",
            ],
        )

    if not numeric_metrics:
        return ForecastResponse(
            dataset_id=dataset_id,
            is_available=False,
            unavailable_reason="Forecast unavailable because no continuous numeric metric was found to forecast.",
            time_column=time_col,
            horizon=horizon,
            available_metrics=[],
            limitations=["Forecasting requires at least one continuous numeric measure."],
        )

    # Rank and automatically select the most suitable forecasting metric
    ranked_metrics = _rank_forecasting_metrics(df, time_col)
    ranked_metric_names = [r[0] for r in ranked_metrics] if ranked_metrics else numeric_metrics

    if not ranked_metrics or ranked_metrics[0][1] < -50:
        best_candidate = ranked_metrics[0][0] if ranked_metrics else numeric_metrics[0]
        return ForecastResponse(
            dataset_id=dataset_id,
            is_available=False,
            unavailable_reason=f"Forecast unavailable because no numeric metric has at least 6 valid date-aligned historical observations (minimum 6 required).",
            metric=best_candidate,
            metric_label=format_column_label(best_candidate),
            available_metrics=ranked_metric_names,
            time_column=time_col,
            horizon=horizon,
            limitations=["At least 6 historical periods are required for statistically valid forecasting."],
        )

    if metric and metric in numeric_metrics:
        selected_metric = metric
        matched = next((r for r in ranked_metrics if r[0] == selected_metric), None)
        selection_rationale = matched[2] if matched else f"Selected '{format_column_label(selected_metric)}' for forecasting."
    else:
        selected_metric = ranked_metrics[0][0]
        selection_rationale = ranked_metrics[0][2]

    # Parse and clean time-series
    parsed_dates = pd.to_datetime(df[time_col], errors="coerce")
    valid_mask = parsed_dates.notna() & df[selected_metric].notna()
    
    if valid_mask.sum() < 6:
        return ForecastResponse(
            dataset_id=dataset_id,
            is_available=False,
            unavailable_reason=f"Forecast unavailable because '{selected_metric}' has only {valid_mask.sum()} valid date-metric observations (minimum 6 required).",
            metric=selected_metric,
            metric_label=format_column_label(selected_metric),
            available_metrics=ranked_metric_names,
            time_column=time_col,
            horizon=horizon,
            limitations=["At least 6 historical periods are required for statistically valid forecasting."],
        )

    clean_df = pd.DataFrame({
        "date": parsed_dates[valid_mask],
        "metric": pd.to_numeric(df.loc[valid_mask, selected_metric], errors="coerce"),
    }).dropna().sort_values("date")

    # Metric-specific aggregation: mean for percentages/rates/durations/scores, sum for additive volumes/currencies
    curr_sym = detect_dataset_currency(df)
    unit_str, sem_type, _ = detect_column_unit(selected_metric, series=clean_df["metric"], dataset_currency=curr_sym)
    agg_func = "mean" if sem_type in ("percentage", "duration", "score") or "rate" in selected_metric.lower() or "avg" in selected_metric.lower() else "sum"

    # Infer frequency / granularity
    span_days = max(1, (clean_df["date"].max() - clean_df["date"].min()).days)
    if granularity in ("D", "W", "M", "Q", "Y"):
        freq = granularity
    elif span_days > 730:
        freq = "M" if span_days <= 1800 else "Q"
    elif span_days > 60:
        freq = "W" if span_days <= 180 else "M"
    else:
        freq = "D"

    freq_labels = {"D": "Daily", "W": "Weekly", "M": "Monthly", "Q": "Quarterly", "Y": "Yearly"}
    freq_label = freq_labels.get(freq, "Daily")

    clean_df["period"] = clean_df["date"].dt.to_period(freq).dt.to_timestamp()
    ts = clean_df.groupby("period")["metric"].agg(agg_func)

    # Fallback to daily if grouped periods collapsed to < 6
    if len(ts) < 6 and freq != "D":
        clean_df["period"] = clean_df["date"].dt.to_period("D").dt.to_timestamp()
        ts = clean_df.groupby("period")["metric"].agg(agg_func)
        freq = "D"
        freq_label = "Daily"

    if len(ts) < 6:
        return ForecastResponse(
            dataset_id=dataset_id,
            is_available=False,
            unavailable_reason=f"Forecast unavailable because the aggregated time series contains only {len(ts)} historical {freq_label.lower()} periods (minimum 6 required).",
            metric=selected_metric,
            available_metrics=numeric_metrics,
            time_column=time_col,
            horizon=horizon,
            frequency=freq,
            frequency_label=freq_label,
            limitations=["Minimum 6 distinct historical time buckets required to compute statistical parameters."],
        )

    # Fill any missing intermediate time buckets with linear interpolation
    ts = ts.sort_index().interpolate(method="linear").bfill().ffill()
    
    series_vals = ts.values.astype(float)
    n_obs = len(series_vals)

    # Multi-Model Evaluation & Holdout Validation
    methods_dict = {
        "holt_linear": ("Holt's Linear Exponential Smoothing", _fit_holt_linear),
        "linear_trend": ("Linear Trend Extrapolation", _fit_linear_trend),
        "moving_average": ("Moving Average", _fit_moving_average),
        "naive": ("Naive Baseline", _fit_naive),
    }

    # Holdout setup when n_obs >= 10
    has_holdout = n_obs >= 10
    holdout_size = max(2, min(5, int(n_obs * 0.2))) if has_holdout else 0
    
    model_evaluations: List[Dict[str, Any]] = []
    fitted_map: Dict[str, np.ndarray] = {}
    forecast_map: Dict[str, np.ndarray] = {}
    desc_map: Dict[str, str] = {}

    for m_key, (m_title, m_func) in methods_dict.items():
        # Full in-sample fit & future forecast
        fitted_full, forecast_full, in_sample_metrics, m_desc = m_func(series_vals, horizon)
        fitted_map[m_key] = fitted_full
        forecast_map[m_key] = forecast_full
        desc_map[m_key] = m_desc

        # Holdout validation score
        if has_holdout:
            train_series = series_vals[:-holdout_size]
            test_series = series_vals[-holdout_size:]
            _, holdout_pred, _, _ = m_func(train_series, holdout_size)
            holdout_metrics = _calc_metrics(test_series, holdout_pred)
            eval_score = holdout_metrics["rmse"]
        else:
            holdout_metrics = {}
            eval_score = in_sample_metrics["rmse"]

        model_evaluations.append({
            "method_key": m_key,
            "method_name": m_title,
            "description": m_desc,
            "in_sample_metrics": in_sample_metrics,
            "holdout_metrics": holdout_metrics if has_holdout else None,
            "eval_score": eval_score,
            "is_selected": False,
        })

    # Model Selection (Auto or User-Specified)
    req_method = (method or "auto").lower()
    if req_method in methods_dict:
        selected_key = req_method
    else:
        # Auto-pick best model with lowest evaluation RMSE
        best_eval = min(model_evaluations, key=lambda m: m["eval_score"])
        selected_key = best_eval["method_key"]

    for m_eval in model_evaluations:
        if m_eval["method_key"] == selected_key:
            m_eval["is_selected"] = True

    active_fitted = fitted_map[selected_key]
    active_forecast = forecast_map[selected_key]
    active_desc = desc_map[selected_key]
    active_metrics = next(m["in_sample_metrics"] for m in model_evaluations if m["method_key"] == selected_key)
    rmse = active_metrics["rmse"]
    mape = active_metrics["mape"]

    # Non-negative series protection
    is_non_negative = np.all(series_vals >= 0)
    if is_non_negative:
        active_forecast = np.maximum(0.0, active_forecast)

    # Historical data points
    historical_points: List[HistoricalPointSchema] = [
        HistoricalPointSchema(
            period=dt.strftime("%Y-%m-%d"),
            actual=round(float(v), 2),
        )
        for dt, v in zip(ts.index, ts.values)
    ]

    # Future forecast points with expanding prediction intervals (80% and 95%)
    last_date = ts.index[-1]
    last_val = float(ts.iloc[-1])
    forecast_points: List[ForecastPointSchema] = []

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
            future_dt = last_date + pd.Timedelta(days=h)

        pt_val = float(active_forecast[h - 1])
        se_h = rmse * math.sqrt(h)

        lower_80 = pt_val - (1.28 * se_h)
        upper_80 = pt_val + (1.28 * se_h)
        lower_95 = pt_val - (1.96 * se_h)
        upper_95 = pt_val + (1.96 * se_h)

        if is_non_negative:
            pt_val = max(0.0, pt_val)
            lower_80 = max(0.0, lower_80)
            lower_95 = max(0.0, lower_95)

        forecast_points.append(
            ForecastPointSchema(
                period=future_dt.strftime("%Y-%m-%d"),
                forecast=round(pt_val, 2),
                lower_bound_80=round(lower_80, 2),
                upper_bound_80=round(upper_80, 2),
                lower_bound_95=round(lower_95, 2),
                upper_bound_95=round(upper_95, 2),
            )
        )

    # Change metrics
    final_val = forecast_points[-1].forecast if forecast_points else last_val
    abs_change = round(final_val - last_val, 2)
    proj_growth_pct: Optional[float] = None
    if abs(last_val) > 1e-7:
        proj_growth_pct = round(((final_val - last_val) / abs(last_val)) * 100.0, 1)

    # Confidence score calculation
    conf_score = max(0.50, min(0.95, round(1.0 - (min(mape, 100.0) / 150.0), 2)))

    # Horizon warning
    horizon_warning: Optional[str] = None
    if horizon > n_obs:
        horizon_warning = f"Forecast horizon of {horizon} periods exceeds historical data length ({n_obs} {freq_label.lower()} periods). Confidence intervals widen significantly."

    # Domain-aware interpretation
    domain_narrative = _generate_domain_interpretation(
        metric_name=selected_metric,
        semantic_type=sem_type,
        unit=unit_str,
        latest_val=last_val,
        final_val=final_val,
        growth_pct=proj_growth_pct,
        horizon=horizon,
        freq_label=freq_label,
        method_name=active_desc,
    )

    validation_summary = {
        "has_holdout": has_holdout,
        "holdout_periods": holdout_size,
        "total_historical_periods": n_obs,
        "validation_strategy": f"Time-based holdout ({holdout_size} periods)" if has_holdout else "In-sample residual evaluation (dataset < 10 periods)",
        "in_sample_accuracy": active_metrics,
        "holdout_accuracy": next((m["holdout_metrics"] for m in model_evaluations if m["method_key"] == selected_key), None),
    }

    historical_range = {
        "start_date": ts.index[0].strftime("%Y-%m-%d"),
        "end_date": ts.index[-1].strftime("%Y-%m-%d"),
        "total_periods": n_obs,
    }

    forecast_range = {
        "start_date": forecast_points[0].period if forecast_points else "",
        "end_date": forecast_points[-1].period if forecast_points else "",
        "total_periods": horizon,
    }

    return ForecastResponse(
        dataset_id=dataset_id,
        is_available=True,
        metric=selected_metric,
        metric_label=format_column_label(selected_metric),
        selection_rationale=selection_rationale,
        available_metrics=ranked_metric_names,
        time_column=time_col,
        horizon=horizon,
        frequency=freq,
        frequency_label=freq_label,
        method_used=active_desc,
        historical_points=historical_points,
        forecast_points=forecast_points,
        historical_range=historical_range,
        forecast_range=forecast_range,
        latest_actual=round(last_val, 2),
        final_forecast=round(final_val, 2),
        absolute_change=abs_change,
        projected_growth_pct=proj_growth_pct,
        accuracy_metrics=active_metrics,
        validation_summary=validation_summary,
        method_comparison=model_evaluations,
        confidence_score=conf_score,
        domain_interpretation=domain_narrative,
        unit=unit_str,
        currency_symbol=curr_sym,
        horizon_warning=horizon_warning,
        limitations=[
            "Forecasts are mathematical extrapolations of historical level, rate, and trend trajectories.",
            "External market shifts, regulatory shocks, and structural changes cannot be predicted from in-sample data alone.",
            "Prediction intervals widen as the forecast horizon extends, reflecting compounding uncertainty.",
        ],
        disclaimer=(
            "Forecasts are mathematical projections based on historical data. "
            "They do not account for unforeseen external events or structural market disruptions. Not guaranteed outcomes."
        ),
    )
