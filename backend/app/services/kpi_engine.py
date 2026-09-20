"""Factual KPI computation engine.

Computes mathematically verified domain KPIs over in-memory pandas DataFrames.
Never fabricates metrics or values.
"""
from __future__ import annotations

import math
from typing import Any, List, Optional, Tuple

import numpy as np
import pandas as pd

from app.domains.base import KpiRule
from app.schemas.domain_blueprint import DomainKpiSchema


def compute_domain_kpis(
    df: pd.DataFrame,
    validated_kpis: List[Tuple[KpiRule, List[str]]],
) -> List[DomainKpiSchema]:
    """Compute factual KPIs based on validated blueprint rules and mapped columns."""
    results: List[DomainKpiSchema] = []

    for rule, matched_cols in validated_kpis:
        if not matched_cols:
            continue

        col = matched_cols[0]
        if col not in df.columns:
            continue

        series = df[col].dropna()
        if series.empty:
            continue

        value: Optional[float] = None
        is_reliable = True

        try:
            if rule.formula == "sum":
                numeric_s = pd.to_numeric(series, errors="coerce").dropna()
                if not numeric_s.empty:
                    value = float(numeric_s.sum())
            elif rule.formula == "mean":
                numeric_s = pd.to_numeric(series, errors="coerce").dropna()
                if not numeric_s.empty:
                    value = float(numeric_s.mean())
            elif rule.formula == "count_distinct":
                value = float(series.nunique())
            elif rule.formula == "count":
                value = float(series.count())
            elif rule.formula == "max":
                numeric_s = pd.to_numeric(series, errors="coerce").dropna()
                if not numeric_s.empty:
                    value = float(numeric_s.max())
            elif rule.formula == "min":
                numeric_s = pd.to_numeric(series, errors="coerce").dropna()
                if not numeric_s.empty:
                    value = float(numeric_s.min())
            elif rule.formula in ("ratio", "rate"):
                # Ratio or rate (e.g. boolean flag mean or proportion)
                if series.dtype == "bool":
                    value = float(series.mean())
                else:
                    numeric_s = pd.to_numeric(series, errors="coerce").dropna()
                    if not numeric_s.empty:
                        value = float(numeric_s.mean())
        except Exception:
            value = None
            is_reliable = False

        if value is not None and not math.isnan(value) and not math.isinf(value):
            # Round value reasonably
            if rule.format == "percentage":
                # Convert fraction to percentage if <= 1.0
                if 0.0 <= value <= 1.0:
                    rounded_val = round(value * 100.0, 2)
                else:
                    rounded_val = round(value, 2)
            elif rule.format in ("currency", "number"):
                rounded_val = round(value, 2)
            else:
                rounded_val = round(value, 2)

            results.append(
                DomainKpiSchema(
                    id=rule.id,
                    name=rule.name,
                    description=rule.description,
                    value=rounded_val,
                    format=rule.format,
                    aggregation=rule.formula,
                    matched_columns=matched_cols,
                    business_meaning=rule.business_meaning,
                    is_reliable=is_reliable,
                )
            )

    return results
