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

Every candidate chart is scored, then a diversity-aware selection picks
the final set (round-robins across chart types rather than always taking
the single highest-scoring type).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Tuple

import numpy as np
import pandas as pd

from app.core.config import settings
from app.services.column_profiler import ColumnProfile, profile_dataset
from app.services.semantic_rules import (
    dimension_importance,
    metric_importance,
    prettify,
)

ChartType = Literal["bar", "line", "pie", "histogram", "scatter"]

_SUM_NAME_HINTS = (
    "count", "quantity", "qty", "total", "sum", "amount", "revenue",
    "sales", "units", "volume", "spend", "cost",
)

# How many of the top-scored dimensions/metrics are even considered for
# combination charts. This is what stops "Customer_Login_type" (or any
# other low-signal column) from being charted just because it happens to
# exist -- only the strongest few candidates by business relevance get
# paired up at all.
TOP_K_DIMENSIONS = 4
TOP_K_METRICS = 4
TOP_K_HIGH_CARDINALITY_DIMENSIONS = 2
TOP_N_HIGH_CARDINALITY_CATEGORIES = 10
MIN_DIMENSION_SCORE_FOR_HIGH_CARDINALITY = 2.0  # e.g. "Product" qualifies, a random free-text column does not
SCATTER_MIN_CORRELATION = 0.3
SCATTER_MIN_CORRELATION_BOTH_IMPORTANT = 0.15
# An "Other" bucket that would outweigh the largest individual category
# hides more than it reveals -- in that case we show more individual
# categories instead of folding into Other (see _rank_or_fold below).
MAX_CATEGORIES_HARD_CAP = 20


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
    # Raw (non-prettified) column names backing this chart, when it's a
    # dimension/metric breakdown -- lets the frontend request a genuine,
    # data-driven drill-down for a clicked category without guessing which
    # original column produced a prettified label like "Sub Category".
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
    """Heuristic: does this numeric column read as a total (sum) or a
    typical value (mean)? 'revenue'/'quantity' -> sum, 'rating'/'price' ->
    mean. Defaults to mean, the safer choice for an unknown quantity."""
    lowered = column_name.lower()
    return "sum" if any(hint in lowered for hint in _SUM_NAME_HINTS) else "mean"


def _fold_into_other(
    series: pd.Series, max_categories: int
) -> Tuple[pd.Series, bool]:
    """Keep the top categories of an already-sorted (descending) series.

    Returns (shown_series, was_folded). Folding the remainder into a single
    "Other" bucket is only useful when that bucket is a minor, honestly-
    labeled remainder -- if "Other" would outweigh the largest individual
    category (or even come close), it hides more signal than it saves
    space, so instead we just show more individual categories (up to a
    hard cap) with no "Other" bucket at all.
    """
    if len(series) <= max_categories:
        return series, False

    kept = series.iloc[:max_categories]
    other_total = series.iloc[max_categories:].sum()
    largest_individual = float(kept.iloc[0])

    if other_total <= largest_individual:
        # "Other" is a believable remainder, not a hidden majority.
        return pd.concat([kept, pd.Series({"Other": other_total})]), True

    # "Other" would dominate or rival the top category -- prefer showing
    # more real categories over one misleading catch-all bucket.
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
    pretty_col = prettify(col)
    coverage_note = ""
    if not folded and len(shown) < total_categories:
        coverage_note = f" Showing the top {len(shown)} of {total_categories} values."
    # Spread across values (not all-equal) makes a count breakdown more
    # informative -> higher score. Business-relevant dimensions (Category,
    # Product, ...) are weighted up; low-signal ones (login_type,
    # session_id, ...) are weighted down rather than excluded outright.
    spread = float(counts.std()) / (float(counts.mean()) + 1e-9) if len(counts) > 1 else 0.0
    score = (3.5 + min(spread, 2.0)) * dim_score
    return ChartSpec(
        id=chart_id,
        chart_type="bar",
        title=f"{pretty_col} Breakdown",
        description=f"Number of rows for each value of '{pretty_col}'.{coverage_note}",
        x_label=pretty_col,
        y_label="Count",
        data=data,
        score=score,
        dimension_column=col,
    )


def _category_proportion_pie(
    df: pd.DataFrame, col: str, chart_id: str, dim_score: float
) -> ChartSpec:
    counts = df[col].value_counts(dropna=True).sort_values(ascending=False)
    counts.index = counts.index.map(str)
    data = [{"x": str(idx), "y": _clean(val)} for idx, val in counts.items()]
    pretty_col = prettify(col)
    return ChartSpec(
        id=chart_id,
        chart_type="pie",
        title=f"Share by {pretty_col}",
        description=f"Proportion of rows in each category of '{pretty_col}'.",
        x_label=pretty_col,
        y_label="Count",
        data=data,
        score=3.0 * dim_score,
        dimension_column=col,
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
            coverage_note = f" Showing the top {len(shown)} of {total_categories} values."
    elif agg == "sum":
        shown, folded = _fold_into_other(grouped, limit)
        if not folded and len(shown) < total_categories:
            coverage_note = f" Showing the top {len(shown)} of {total_categories} values."
    else:
        shown = grouped.iloc[:limit]
        if len(shown) < total_categories:
            coverage_note = f" Showing the top {len(shown)} of {total_categories} values."
    data = [{"x": str(idx), "y": _clean(val)} for idx, val in shown.items()]
    agg_label = "Total" if agg == "sum" else "Average"
    pretty_metric = prettify(num_col)
    pretty_dim = prettify(cat_col)
    cv = float(grouped.std()) / (abs(float(grouped.mean())) + 1e-9)
    # Business relevance (both the metric and the dimension being
    # recognized as meaningful) dominates the score -- a statistically
    # "spread out" but low-relevance pairing (e.g. Discount by
    # Customer_Login_type) should rank below a meaningful one even with a
    # smaller coefficient of variation.
    score = (4.0 + min(cv, 3.0)) * dim_score * met_score
    title_suffix = " (Top 10)" if top_n_only else ""
    return ChartSpec(
        id=chart_id,
        chart_type="bar",
        title=f"{agg_label} {pretty_metric} by {pretty_dim}{title_suffix}",
        description=f"{agg_label} of '{pretty_metric}' grouped by '{pretty_dim}'.{coverage_note}",
        x_label=pretty_dim,
        y_label=f"{agg_label} {pretty_metric}",
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
        # Explicit, human-readable bin boundaries (never scientific
        # notation) -- rounded to a sensible precision for the value range
        # rather than the raw float repr.
        decimals = 0 if (hi - edges[0]) >= 10 else 2
        label = f"{lo:,.{decimals}f}\u2013{hi:,.{decimals}f}"
        pct = round(100 * int(counts[i]) / total, 1) if total else 0.0
        data.append(
            {"x": label, "y": int(counts[i]), "range_low": round(lo, 4),
             "range_high": round(hi, 4), "percent": pct}
        )
    pretty_col = prettify(col)
    lowered = col.lower()
    # A business-readable title/description tied to what the metric
    # actually represents, rather than a generic "X Distribution" label
    # that requires the reader to already know what a histogram is.
    if any(h in lowered for h in ("sales", "revenue", "amount", "price", "value", "total")):
        title = f"{pretty_col} Distribution"
        x_axis_label = f"{pretty_col} Range"
        subject = "transaction"
    elif any(h in lowered for h in ("quantity", "qty", "units")):
        title = f"{pretty_col} Distribution"
        x_axis_label = f"{pretty_col} Range"
        subject = "order"
    else:
        title = f"{pretty_col} Distribution"
        x_axis_label = f"{pretty_col} Range"
        subject = "row"
    description = (
        f"Shows how frequently {subject}s fall within different '{pretty_col}' "
        f"ranges, helping identify typical values, concentration, and unusually "
        f"high or low outliers."
    )
    # Skewness (very unequal bins) is more visually interesting than a flat
    # uniform spread, but any real spread beats a near-constant column.
    score = (3.5 + min(float(np.std(counts)) / (float(np.mean(counts)) + 1e-9), 2.0)) * met_score
    return ChartSpec(
        id=chart_id,
        chart_type="histogram",
        title=title,
        description=description,
        x_label=x_axis_label,
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
        freq, label = "MS", "month"
    elif span_days > 90:
        freq, label = "W", "week"
    else:
        freq, label = "D", "day"

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
    agg_label = "Total" if agg == "sum" else "Average"
    pretty_metric = prettify(num_col)
    cv = float(grouped.std()) / (abs(float(grouped.mean())) + 1e-9)
    # Time trends are generally high-value, and doubly so for a recognized
    # business metric (Sales/Profit/Quantity over time beats an obscure
    # numeric column over time).
    score = (5.0 + min(cv, 3.0)) * met_score
    return ChartSpec(
        id=chart_id,
        chart_type="line",
        title=f"{pretty_metric} Over Time",
        description=f"{agg_label} of '{pretty_metric}' by {prettify(date_col)}, bucketed by {label}.",
        x_label=prettify(date_col),
        y_label=f"{agg_label} {pretty_metric}",
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

    # A scatter plot is only analytically meaningful when either (a) both
    # columns are recognized, important business metrics -- "Sales vs
    # Profit" earns its place even at a modest correlation -- or (b) the
    # correlation itself is strong enough to be interesting regardless of
    # what the columns are named ("Profit vs Shipping_Cost" needs to prove
    # itself statistically since neither is a clear analytical pairing by
    # name alone).
    both_important = met_score_x >= 2.0 and met_score_y >= 2.0
    min_corr = SCATTER_MIN_CORRELATION_BOTH_IMPORTANT if both_important else SCATTER_MIN_CORRELATION
    if abs(float(corr)) < min_corr:
        return None

    sample = pair if len(pair) <= settings.SCATTER_MAX_POINTS else pair.sample(
        settings.SCATTER_MAX_POINTS, random_state=0
    )
    data = []
    for idx, row in sample.iterrows():
        point = {"x": _clean(row[col_x]), "y": _clean(row[col_y])}
        point["id"] = str(row[id_col]) if id_col else f"Row {idx}"
        data.append(point)

    pretty_x, pretty_y = prettify(col_x), prettify(col_y)
    score = (3.0 + min(abs(float(corr)) * 6, 6.0)) * ((met_score_x + met_score_y) / 2)
    strength = (
        "strong" if abs(corr) >= 0.6 else "moderate" if abs(corr) >= 0.3 else "weak"
    )
    direction_word = "Positive" if corr > 0 else "Negative"
    relationship_label = (
        "No Clear Relationship" if abs(corr) < 0.15
        else f"{strength.capitalize()} {direction_word} Relationship"
    )
    if abs(corr) < 0.15:
        interpretation = f"'{pretty_x}' and '{pretty_y}' show little to no linear relationship in this data."
    else:
        direction = "higher" if corr > 0 else "lower"
        interpretation = (
            f"Higher {pretty_x.lower()} generally corresponds to {direction} "
            f"{pretty_y.lower()} in this data (correlation, not causation)."
        )
    return ChartSpec(
        id=chart_id,
        chart_type="scatter",
        title=f"{pretty_x} vs {pretty_y}",
        description=(
            f"Shows the relationship between '{pretty_x}' and '{pretty_y}' across "
            f"all rows. Correlation: {corr:.2f} ({relationship_label}). {interpretation}"
        ),
        x_label=pretty_x,
        y_label=pretty_y,
        data=data,
        score=score,
    )


def _select_diverse(candidates: List[ChartSpec], max_charts: int) -> List[ChartSpec]:
    """Greedy, globally score-ranked selection with a per-type cap.

    A pure "take the top N by score" would often be dominated by one chart
    type (bar breakdowns tend to outnumber everything else). A pure
    round-robin (1 pick per type per round) goes too far the other way and
    can crowd out a highly-relevant chart (e.g. "Sales by Category") in
    favor of a much weaker one just because its type's turn came up. This
    strikes a middle ground: process candidates in score order and take
    each one unless its type has already hit its cap, so strong candidates
    of the dominant type still fill most of the slots, while weaker types
    are still guaranteed a little representation for visual diversity.
    """
    per_type_cap = {
        "bar": 4,
        "line": 2,
        "scatter": 2,
        "histogram": 2,
        "pie": 1,
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
    """Business-relevance ranking of a dataset's columns, shared by the
    overview recommendation engine and the drill-down endpoint so both
    agree on what "the important metrics/dimensions" are."""

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


def generate_recommendations(df: pd.DataFrame) -> List[ChartSpec]:
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

    # 1) Category counts -- generated for the top-ranked groupable columns,
    #    independently of whether a numeric measure exists, so a
    #    categorical-only dataset still gets useful charts.
    for col in top_dimensions:
        dim_score = dimension_importance(col)
        candidates.append(_category_counts_chart(df, col, next_id(), dim_score))
        distinct = df[col].nunique(dropna=True)
        if distinct <= settings.PIE_CHART_MAX_CATEGORIES:
            candidates.append(_category_proportion_pie(df, col, next_id(), dim_score))

    # 2) Categorical x numeric measure breakdowns, restricted to the
    #    top-ranked dimensions and metrics so the result is "Sales by
    #    Category" / "Profit by Category", not every possible pairing.
    for cat_col in top_dimensions:
        dim_score = dimension_importance(cat_col)
        for num_col in top_metrics:
            met_score = metric_importance(num_col)
            spec = _categorical_measure_bar(
                df, cat_col, num_col, next_id(), dim_score, met_score
            )
            if spec is not None:
                candidates.append(spec)

    # 2b) "Top N Product"-style breakdowns for important-but-high-cardinality
    #     dimensions (Product, SKU...) paired with the top metrics only.
    #     See _fold_into_other()/_categorical_measure_bar(): these never
    #     fold into a dominating "Other" bucket, so the real top values
    #     stay visible and drillable rather than hidden behind an average.
    for cat_col in important_hc_dims:
        dim_score = dimension_importance(cat_col)
        for num_col in top_metrics[:2]:
            met_score = metric_importance(num_col)
            spec = _categorical_measure_bar(
                df, cat_col, num_col, next_id(), dim_score, met_score, top_n_only=True
            )
            if spec is not None:
                candidates.append(spec)

    # 3) Numeric distributions for the top-ranked metrics only.
    for col in top_metrics:
        spec = _histogram(df, col, next_id(), metric_importance(col))
        if spec is not None:
            candidates.append(spec)

    # 4) Time series: date column x top-ranked numeric measures.
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

    # 5) Scatter plots for the most correlated numeric pairs among the
    #    top-ranked metrics -- see _scatter() for the relevance gate that
    #    keeps "Sales vs Profit" while filtering out weakly-related pairs
    #    like "Profit vs Shipping_Cost" unless the correlation earns it.
    #    Points are labeled with the top dimension (e.g. Product) when one
    #    exists, so tooltips identify an entity rather than an anonymous dot.
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
    """Derive a small set of headline KPIs from the dataset's own top
    metrics -- never invented, never hard-coded to e-commerce field names.
    Each KPI carries a `kind` the frontend uses to pick an icon/accent
    color (falls back to a generic style for anything it doesn't recognize).
    """
    if ranking is None:
        ranking = rank_columns(df)

    kpis: List[Dict[str, Any]] = []
    row_count = int(len(df))

    for col in ranking.top_metrics[:4]:
        agg = _pick_aggregation(col)
        series = df[col].dropna()
        if series.empty:
            continue
        value = float(series.sum()) if agg == "sum" else float(series.mean())
        label = f"Total {prettify(col)}" if agg == "sum" else f"Average {prettify(col)}"
        kpis.append({
            "label": label,
            "value": round(value, 2),
            "kind": _kpi_kind(col),
            "format": "number",
        })

    # A generic "how many records/orders" KPI -- labeled "Total Orders"
    # only if the dataset actually looks order/transaction-shaped by name,
    # otherwise the honest generic label "Total Rows".
    looks_order_shaped = any(
        any(hint in c.lower() for hint in _ORDER_NAME_HINTS) for c in df.columns
    )
    kpis.append({
        "label": "Total Orders" if looks_order_shaped else "Total Rows",
        "value": row_count,
        "kind": "orders",
        "format": "count",
    })

    # Average order value: total of the top "sum" metric / row count, only
    # when that metric is a real total (sum aggregation) -- averaging an
    # already-averaged metric per row would be meaningless.
    for col in ranking.top_metrics:
        if _pick_aggregation(col) == "sum" and row_count > 0:
            total = float(df[col].dropna().sum())
            kpis.append({
                "label": f"Average {prettify(col)} per Row",
                "value": round(total / row_count, 2),
                "kind": "average",
                "format": "number",
            })
            break

    return kpis[:5]


def _kpi_kind(column_name: str) -> str:
    lowered = column_name.lower()
    if any(h in lowered for h in ("profit", "margin", "income", "earning")):
        return "profit"
    if any(h in lowered for h in ("sales", "revenue")):
        return "sales"
    if any(h in lowered for h in ("quantity", "qty", "units")):
        return "quantity"
    if any(h in lowered for h in ("discount",)):
        return "discount"
    return "generic"


# --- Drill-down --------------------------------------------------------------

def generate_drilldown(
    df: pd.DataFrame,
    filters: List[Tuple[str, str]],
    ranking: Optional[ColumnRanking] = None,
) -> Optional[Dict[str, Any]]:
    """Data-driven drill-down for one or more stacked (dimension, value)
    filters -- e.g. [('Category', 'Clothing'), ('Product', 'T-Shirts')] for
    a second-level drill into Product within an already-selected Category.

    Generic: works for any categorical column(s)/value(s) that exist in the
    dataset, in any order, never hard-coded to a specific dimension name.
    The *last* filter in the list is treated as "the current level" for the
    response's dimension/value/label fields; earlier filters just narrow
    the base data before that level is computed.
    """
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
            spec.title = f"{current_value} \u2014 {prettify(primary_metric)} Over Time"
            trend_chart = spec.to_dict()

    # A meaningful secondary breakdown must use a dimension not already
    # pinned by one of the active filters -- otherwise every value in it
    # would trivially be 100% of the subset, which is not analytically
    # useful and would make a nonsensical drill-down target.
    secondary_chart = None
    secondary_dimension_column = None
    candidate_dims = [d for d in ranking.top_dimensions if d not in filtered_dims]
    if not candidate_dims:
        candidate_dims = [
            d for d in ranking.important_hc_dimensions if d not in filtered_dims
        ]
    if candidate_dims and ranking.top_metrics:
        second_dim = candidate_dims[0]
        primary_metric = ranking.top_metrics[0]
        # Only offer a further drill-down level if the subset actually has
        # more than one distinct value left in that dimension -- drilling
        # into a dimension with a single remaining value is a dead end.
        if subset[second_dim].nunique(dropna=True) > 1:
            spec = _categorical_measure_bar(
                subset, second_dim, primary_metric, "drilldown_secondary",
                dimension_importance(second_dim), metric_importance(primary_metric),
            )
            if spec is not None:
                spec.title = f"{current_value} by {prettify(second_dim)}"
                secondary_chart = spec.to_dict()
                secondary_dimension_column = second_dim

    return {
        "dimension": current_dim,
        "dimension_label": prettify(current_dim),
        "value": str(current_value),
        "row_count": int(len(subset)),
        "kpis": kpis,
        "trend_chart": trend_chart,
        "secondary_chart": secondary_chart,
        # Lets the frontend know whether the secondary chart's bars are
        # themselves drillable into a further (third) level -- omitted
        # gracefully (None) when no further meaningful dimension exists,
        # per "don't invent a level that isn't there".
        "secondary_dimension": secondary_dimension_column,
        "applied_filters": [{"dimension": d, "value": v} for d, v in filters],
    }
