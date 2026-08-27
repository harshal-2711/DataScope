"""Classifies every column of a DataFrame into a semantic role.

This is what lets Phase 3 generate visualizations without a human picking
axes/columns: the recommendation engine only needs to ask "give me the
numeric columns" or "give me the low-cardinality categorical columns" and
build charts from there.

Roles:
    numeric        -- continuous/discrete quantities. Usable as a measure
                       (bar/line aggregation target) or for histograms and
                       scatter plots.
    categorical     -- text/bool-ish columns with a manageable number of
                       distinct values. Usable as a grouping dimension.
    datetime        -- parses as dates/timestamps. Usable as a time axis.
    boolean         -- true/false columns. Treated as a special case of
                       categorical (always exactly 2 groups) by callers.
    identifier      -- near-unique per row (ids, uuids, row numbers). Never
                       charted directly — grouping or plotting one point per
                       row is not a meaningful visualization.
    high_cardinality-- text column with too many distinct values to chart
                       legibly (e.g. free-text notes, names) but not unique
                       enough to be an identifier. Excluded from charts.
    ignore          -- entirely null, or constant (a single distinct value
                       repeated for every row) -- carries no information to
                       visualize.

Every column receives exactly one role. Nothing is silently dropped from
the profile itself (that was a Phase 3 bug: categorical columns vanishing
before the recommendation engine ever saw them) -- it's the recommendation
engine's job to decide which roles are chart-worthy, not the profiler's.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd
from pandas.api import types as pdt

from app.core.config import settings

ColumnRole = Literal[
    "numeric",
    "categorical",
    "datetime",
    "boolean",
    "identifier",
    "high_cardinality",
    "ignore",
]

_IDENTIFIER_NAME_HINTS = ("id", "uuid", "guid", "key", "code", "pk")


@dataclass
class ColumnProfile:
    name: str
    role: ColumnRole
    dtype: str
    non_null_count: int
    null_count: int
    distinct_count: int
    reason: str  # short human-readable justification, useful for debugging/UI


def _looks_like_identifier_name(column_name: str) -> bool:
    lowered = column_name.strip().lower().replace(" ", "_")
    if lowered in {"id", "uuid", "guid", "index", "idx"}:
        return True
    return any(
        lowered == hint or lowered.endswith(f"_{hint}") or lowered.startswith(f"{hint}_")
        for hint in _IDENTIFIER_NAME_HINTS
    )


def _parseable_datetime_ratio(series: pd.Series) -> float:
    non_null = series.dropna()
    if non_null.empty:
        return 0.0
    parsed = pd.to_datetime(non_null, errors="coerce", format="mixed")
    return float(parsed.notna().mean())


def _looks_boolean(series: pd.Series) -> bool:
    if pdt.is_bool_dtype(series):
        return True
    non_null = series.dropna()
    if non_null.empty:
        return False
    distinct_values = {
        str(v).strip().lower() for v in pd.unique(non_null)
    }
    boolean_pairs = [
        {"true", "false"},
        {"yes", "no"},
        {"y", "n"},
        {"0", "1"},
        {"0.0", "1.0"},
    ]
    return distinct_values in boolean_pairs


def profile_column(series: pd.Series, row_count: int) -> ColumnProfile:
    name = str(series.name)
    dtype_str = str(series.dtype)
    non_null_count = int(series.notna().sum())
    null_count = int(row_count - non_null_count)
    distinct_count = int(series.nunique(dropna=True))

    if non_null_count == 0:
        return ColumnProfile(
            name, "ignore", dtype_str, non_null_count, null_count, distinct_count,
            "column is entirely null",
        )

    if distinct_count <= 1:
        return ColumnProfile(
            name, "ignore", dtype_str, non_null_count, null_count, distinct_count,
            "column has a single constant value",
        )

    uniqueness_ratio = distinct_count / non_null_count

    if _looks_boolean(series):
        return ColumnProfile(
            name, "boolean", dtype_str, non_null_count, null_count, distinct_count,
            "exactly two distinct boolean-like values",
        )

    if pdt.is_datetime64_any_dtype(series):
        return ColumnProfile(
            name, "datetime", dtype_str, non_null_count, null_count, distinct_count,
            "native datetime dtype",
        )

    if pdt.is_numeric_dtype(series):
        # Integer columns named like a key/reference (customer_id, sku_code)
        # are references, not quantities -- averaging or summing "id" is
        # never a meaningful chart, regardless of how often values repeat.
        if pdt.is_integer_dtype(series) and _looks_like_identifier_name(name):
            return ColumnProfile(
                name, "identifier", dtype_str, non_null_count, null_count, distinct_count,
                "integer column with an id/key-like name (treated as a reference, not a measure)",
            )
        # Only integer columns fall through to the generic near-unique ->
        # identifier heuristic. Continuous float measures (revenue, price,
        # temperature...) are *expected* to be nearly all-unique and must
        # not be excluded from charting just because few rows tie.
        if (
            pdt.is_integer_dtype(series)
            and uniqueness_ratio >= settings.IDENTIFIER_UNIQUENESS_RATIO
            and non_null_count > 20
        ):
            return ColumnProfile(
                name, "identifier", dtype_str, non_null_count, null_count, distinct_count,
                "near-unique integer column (likely a row identifier)",
            )
        return ColumnProfile(
            name, "numeric", dtype_str, non_null_count, null_count, distinct_count,
            "numeric dtype",
        )

    # Remaining candidates: object/string/category dtype. Check datetime
    # BEFORE the generic uniqueness-based identifier catch-all below --
    # a timestamp column is *expected* to be near-unique per row, and that
    # must not cause it to be misclassified as a free-form identifier.
    if non_null_count >= 5 and _parseable_datetime_ratio(series) >= settings.MIN_DATETIME_PARSE_RATIO:
        return ColumnProfile(
            name, "datetime", dtype_str, non_null_count, null_count, distinct_count,
            "text values parse as dates",
        )

    if _looks_like_identifier_name(name) and uniqueness_ratio >= settings.IDENTIFIER_UNIQUENESS_RATIO:
        return ColumnProfile(
            name, "identifier", dtype_str, non_null_count, null_count, distinct_count,
            "near-unique text column with an id-like name",
        )

    if uniqueness_ratio >= settings.IDENTIFIER_UNIQUENESS_RATIO and non_null_count > 20:
        return ColumnProfile(
            name, "identifier", dtype_str, non_null_count, null_count, distinct_count,
            "near-unique values (likely a free-form identifier)",
        )

    if distinct_count > settings.MAX_CATEGORICAL_CARDINALITY:
        return ColumnProfile(
            name, "high_cardinality", dtype_str, non_null_count, null_count, distinct_count,
            f"too many distinct values ({distinct_count}) to chart legibly",
        )

    return ColumnProfile(
        name, "categorical", dtype_str, non_null_count, null_count, distinct_count,
        "manageable number of distinct text values",
    )


def profile_dataset(df: pd.DataFrame) -> list[ColumnProfile]:
    """Profile every column in the DataFrame. Order matches df.columns."""
    row_count = len(df)
    return [profile_column(df[col], row_count) for col in df.columns]
