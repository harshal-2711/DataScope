"""Universal statistics engine for tabular datasets.

Calculates comprehensive parametric and non-parametric statistics for any dataset:
- Central tendency: mean, median, mode
- Dispersion: min, max, range, variance, standard deviation, IQR
- Percentiles: 25th, 50th, 75th, 90th, 99th
- Outliers: 3x IQR and Z-score (>3.0) boundaries
- Data hygiene: null counts, percentages, duplicate rows, cardinality ratios
- Bivariate: Pearson correlation matrix for numeric column pairs
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd

from app.services.column_formatter import detect_column_unit
from app.services.type_inference import detect_dataset_currency


def _clean_float(val: Any) -> Optional[float]:
    """Coerce value to clean JSON-serializable float or None."""
    if val is None:
        return None
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return round(f, 4)
    except (ValueError, TypeError):
        return None


def compute_column_numeric_stats(series: pd.Series) -> Dict[str, Any]:
    """Compute detailed descriptive statistics for a single numeric column."""
    non_null = pd.to_numeric(series, errors="coerce").dropna()
    total_count = len(series)
    valid_count = len(non_null)
    null_count = total_count - valid_count

    if valid_count == 0:
        return {
            "valid_count": 0,
            "null_count": null_count,
            "null_pct": round((null_count / total_count) * 100.0, 2) if total_count > 0 else 0.0,
        }

    # Central tendency
    mean_val = _clean_float(non_null.mean())
    median_val = _clean_float(non_null.median())
    mode_series = non_null.mode()
    mode_val = _clean_float(mode_series.iloc[0]) if not mode_series.empty else None

    # Dispersion
    min_val = _clean_float(non_null.min())
    max_val = _clean_float(non_null.max())
    range_val = _clean_float(non_null.max() - non_null.min()) if min_val is not None and max_val is not None else None
    var_val = _clean_float(non_null.var(ddof=1)) if valid_count > 1 else 0.0
    std_val = _clean_float(non_null.std(ddof=1)) if valid_count > 1 else 0.0

    # Percentiles
    p25 = _clean_float(non_null.quantile(0.25))
    p50 = median_val
    p75 = _clean_float(non_null.quantile(0.75))
    p90 = _clean_float(non_null.quantile(0.90))
    p99 = _clean_float(non_null.quantile(0.99))

    # IQR and Outliers
    iqr_val = _clean_float((p75 - p25)) if p75 is not None and p25 is not None else 0.0
    outlier_count = 0
    if p25 is not None and p75 is not None and iqr_val is not None and iqr_val > 0:
        lower_bound = p25 - (3.0 * iqr_val)
        upper_bound = p75 + (3.0 * iqr_val)
        outlier_count = int(((non_null < lower_bound) | (non_null > upper_bound)).sum())

    # Skewness
    skew_val = _clean_float(non_null.skew()) if valid_count > 2 else 0.0

    return {
        "valid_count": valid_count,
        "null_count": null_count,
        "null_pct": round((null_count / total_count) * 100.0, 2) if total_count > 0 else 0.0,
        "mean": mean_val,
        "median": median_val,
        "mode": mode_val,
        "min": min_val,
        "max": max_val,
        "range": range_val,
        "variance": var_val,
        "std_dev": std_val,
        "p25": p25,
        "p50": p50,
        "p75": p75,
        "p90": p90,
        "p99": p99,
        "iqr": iqr_val,
        "outlier_count": outlier_count,
        "skewness": skew_val,
    }


def compute_column_categorical_stats(series: pd.Series) -> Dict[str, Any]:
    """Compute frequency and cardinality statistics for a categorical/text column."""
    total_count = len(series)
    non_null = series.dropna().astype(str)
    valid_count = len(non_null)
    null_count = total_count - valid_count

    if valid_count == 0:
        return {
            "valid_count": 0,
            "null_count": null_count,
            "unique_count": 0,
            "null_pct": round((null_count / total_count) * 100.0, 2) if total_count > 0 else 0.0,
            "top_values": [],
        }

    unique_count = int(non_null.nunique())
    cardinality_ratio = _clean_float(unique_count / valid_count) if valid_count > 0 else 0.0

    val_counts = non_null.value_counts().head(5)
    top_values = [
        {
            "value": str(val),
            "count": int(count),
            "pct": round((count / valid_count) * 100.0, 2),
        }
        for val, count in val_counts.items()
    ]

    mode_val = str(val_counts.index[0]) if not val_counts.empty else None

    return {
        "valid_count": valid_count,
        "null_count": null_count,
        "unique_count": unique_count,
        "cardinality_ratio": cardinality_ratio,
        "null_pct": round((null_count / total_count) * 100.0, 2) if total_count > 0 else 0.0,
        "mode": mode_val,
        "top_values": top_values,
    }


def compute_universal_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute the universal statistical profile for any uploaded tabular dataset."""
    row_count = int(len(df))
    col_count = int(df.shape[1])
    total_cells = row_count * col_count
    total_missing_cells = int(df.isna().sum().sum())
    missing_pct = round((total_missing_cells / total_cells) * 100.0, 2) if total_cells > 0 else 0.0

    dup_rows = int(df.duplicated().sum())
    dup_pct = round((dup_rows / row_count) * 100.0, 2) if row_count > 0 else 0.0

    numeric_columns: Dict[str, Dict[str, Any]] = {}
    categorical_columns: Dict[str, Dict[str, Any]] = {}
    numeric_col_names: List[str] = []

    dataset_currency = detect_dataset_currency(df)

    for col in df.columns:
        col_name = str(col)
        s = df[col]
        unit, sem_type, sym = detect_column_unit(col_name, series=s, dataset_currency=dataset_currency)
        if pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s):
            col_stats = compute_column_numeric_stats(s)
            col_stats["unit"] = unit
            col_stats["semantic_type"] = sem_type
            col_stats["currency_symbol"] = sym
            numeric_columns[col_name] = col_stats
            numeric_col_names.append(col_name)
        else:
            cat_stats = compute_column_categorical_stats(s)
            cat_stats["unit"] = unit
            cat_stats["semantic_type"] = sem_type
            categorical_columns[col_name] = cat_stats

    # Pearson correlation matrix for numeric columns (up to 12 columns for performance)
    correlation_matrix: Dict[str, Dict[str, Optional[float]]] = {}
    if len(numeric_col_names) >= 2:
        selected_numeric = numeric_col_names[:12]
        corr_df = df[selected_numeric].corr(method="pearson")
        for col_a in selected_numeric:
            correlation_matrix[col_a] = {}
            for col_b in selected_numeric:
                val = corr_df.loc[col_a, col_b]
                correlation_matrix[col_a][col_b] = _clean_float(val)

    return {
        "dataset_summary": {
            "row_count": row_count,
            "column_count": col_count,
            "total_cells": total_cells,
            "missing_cells": total_missing_cells,
            "missing_pct": missing_pct,
            "duplicate_rows": dup_rows,
            "duplicate_pct": dup_pct,
            "numeric_column_count": len(numeric_columns),
            "categorical_column_count": len(categorical_columns),
        },
        "numeric_statistics": numeric_columns,
        "categorical_statistics": categorical_columns,
        "correlation_matrix": correlation_matrix,
    }
