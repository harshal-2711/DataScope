"""Universal, domain-aware Competition Intelligence Engine for DataScope.

Strictly validates competitive entities (Company, Brand, Competitor, Manufacturer,
Product Brand, Supplier, Team). Never misclassifies arbitrary dataset categories
such as Customer Login Type, Device Type, Demographics, or Regions as competitors.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from app.schemas.domain_blueprint import (
    CompetitionGapSchema,
    CompetitionIntelligenceResponse,
    CompetitionOverviewSchema,
    CompetitionSegmentSchema,
    CompetitionTimeComparisonSchema,
    DomainIdentitySchema,
)
from app.services.column_formatter import format_metric_display, humanize_column_name
from app.services.column_profiler import ColumnProfile

logger = logging.getLogger("datascope.services.competition_engine")

# Strict blacklist of categorical patterns that MUST NEVER be classified as competitors
_REJECTED_CATEGORY_TERMS = {
    # Customer / User classification
    "login", "customer_login", "customer_login_type", "login_type", "user_type",
    "customer_type", "member", "membership", "membership_status", "auth", "account_type",
    # Device / Technical environment
    "device", "device_type", "browser", "os", "platform", "client", "client_type",
    "ip", "user_agent", "screen_resolution", "channel",
    # Demographics & Personal Attributes
    "gender", "sex", "age", "age_group", "marital", "marital_status", "education",
    "education_level", "ethnicity", "nationality", "occupation",
    # Geography / Locations (descriptive distributions, not competing firms)
    "region", "country", "city", "state", "zone", "zip", "zip_code", "postal", "postal_code",
    "area", "location", "territory", "province", "district",
    # Transactional attributes / Logistics
    "payment", "payment_method", "payment_type", "card_type", "shipping", "ship_mode",
    "shipping_mode", "delivery_type", "fulfillment_type", "order_status", "status",
    "stage", "priority", "aging", "delay",
    # Feedback & Ratings categories
    "rating_category", "sentiment", "feedback", "feedback_type", "survey_response",
}

# Whitelist of valid competitive entity keywords per domain
_VALID_ENTITY_RULES = [
    # (Entity Type Label, Keyword list, Domain list or None for any)
    ("Company", ["company", "competitor", "firm", "enterprise", "business_name", "organization", "agency", "ticker", "institution"], None),
    ("Brand", ["brand", "brand_name", "manufacturer", "make", "publisher", "record_label", "studio", "product_brand"], None),
    ("Product", ["product_name", "product", "model_name", "model", "item_name", "sku_name", "car_model", "track_name", "movie_title"], None),
    ("Supplier", ["supplier", "vendor", "contractor", "bidder"], ["procurement", "supply_chain", "operations"]),
    ("Team", ["team", "franchise", "club", "country", "player", "batsman", "bowler"], ["sports", "sports_cricket"]),
]

# Keywords for ranking numeric comparison metrics
_METRIC_DOMAIN_KEYWORDS = {
    "ecommerce": [
        ("profit", "sum", "currency"),
        ("revenue", "sum", "currency"),
        ("sales", "sum", "currency"),
        ("amount", "sum", "currency"),
        ("spend", "sum", "currency"),
        ("quantity", "sum", "quantity"),
        ("units", "sum", "quantity"),
        ("orders", "sum", "count"),
        ("margin", "mean", "percentage"),
    ],
    "finance": [
        ("net_profit", "sum", "currency"),
        ("profit", "sum", "currency"),
        ("revenue", "sum", "currency"),
        ("income", "sum", "currency"),
        ("operating_expense", "sum", "currency"),
        ("expense", "sum", "currency"),
        ("cost", "sum", "currency"),
        ("assets", "sum", "currency"),
        ("roi", "mean", "percentage"),
        ("growth", "mean", "percentage"),
    ],
    "sports_cricket": [
        ("runs", "sum", "number"),
        ("points", "sum", "number"),
        ("wickets", "sum", "number"),
        ("score", "sum", "number"),
        ("strike_rate", "mean", "score"),
        ("matches", "sum", "number"),
    ],
    "people_hr": [
        ("salary", "mean", "currency"),
        ("compensation", "mean", "currency"),
        ("monthly_income", "mean", "currency"),
        ("performance_rating", "mean", "score"),
        ("tenure", "mean", "duration"),
    ],
    "healthcare": [
        ("patient_count", "sum", "number"),
        ("admissions", "sum", "number"),
        ("billing_amount", "sum", "currency"),
        ("cost", "sum", "currency"),
        ("length_of_stay", "mean", "duration"),
    ],
    "procurement": [
        ("tender_value", "sum", "currency"),
        ("contract_value", "sum", "currency"),
        ("award_value", "sum", "currency"),
        ("amount", "sum", "currency"),
        ("spend", "sum", "currency"),
        ("duration_in_days", "mean", "duration"),
    ],
}


def _find_date_column(df: pd.DataFrame, profiles: List[ColumnProfile]) -> Optional[str]:
    """Identify the most reliable datetime column in the dataset."""
    for p in profiles:
        if getattr(p, "role", None) in ("datetime", "time", "date") and p.name in df.columns:
            return p.name
        if getattr(p, "inferred_type", None) in ("Date", "Timestamp") and p.name in df.columns:
            return p.name

    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            return col

    date_keywords = ["date", "time", "timestamp", "period", "day", "month", "year", "order_date", "transaction_date"]
    for col in df.columns:
        col_lower = str(col).lower()
        if any(kw in col_lower for kw in date_keywords):
            try:
                sample = df[col].dropna().head(20)
                if len(sample) >= 3:
                    pd.to_datetime(sample, errors="raise")
                    return col
            except Exception:
                continue

    return None


def _is_rejected_category(col_name: str) -> bool:
    """Check if a column is an invalid, non-competitive category (e.g. Login Type, Device Type)."""
    norm = col_name.strip().lower().replace("-", "_").replace(" ", "_")
    parts = set(norm.split("_"))
    
    # Direct match or substring in blacklist
    if norm in _REJECTED_CATEGORY_TERMS:
        return True
        
    for rej in _REJECTED_CATEGORY_TERMS:
        if rej in norm:
            return True
            
    return False


def _detect_valid_competitive_entity(
    col_name: str,
    profile: ColumnProfile,
    row_count: int,
    domain_id: str,
) -> Optional[Tuple[str, float]]:
    """Strictly evaluate whether a column is a genuine competitive entity (Brand, Company, Team, etc.).
    Returns (EntityTypeLabel, score) or None if not a valid competitive entity.
    """
    if profile.role in ("datetime", "numeric", "ignore", "identifier"):
        return False
        
    # Check strict rejection list first
    if _is_rejected_category(col_name):
        return None
        
    # Cardinality constraints: must have between 2 and 150 discrete entities
    distinct_count = profile.distinct_count
    if distinct_count < 2 or distinct_count > 150:
        return None
        
    if row_count > 10 and (distinct_count / row_count) > 0.95:
        return None

    norm = col_name.strip().lower().replace("-", "_").replace(" ", "_")
    
    # Match against valid entity rules
    for entity_label, keywords, allowed_domains in _VALID_ENTITY_RULES:
        if allowed_domains and domain_id not in allowed_domains:
            continue
            
        for kw in keywords:
            # Exact match or compound match (e.g. 'product_brand', 'company_name', 'competitor_id')
            if norm == kw or norm == f"{kw}_name" or norm == f"name_{kw}" or f"_{kw}_" in f"_{norm}_":
                score = 100.0
                if 3 <= distinct_count <= 40:
                    score += 20.0
                return (entity_label, score)

    return None


def _find_candidate_metrics(
    df: pd.DataFrame,
    profiles: List[ColumnProfile],
    domain: DomainIdentitySchema,
) -> List[Tuple[str, str, str]]:
    """Find and rank all suitable continuous numeric comparison metrics."""
    profile_map = {p.name: p for p in profiles}
    candidates = []
    
    domain_id = domain.domain_id if domain else "general"
    domain_kw = _METRIC_DOMAIN_KEYWORDS.get(domain_id, [])

    for col in df.columns:
        if col not in profile_map:
            continue
        p = profile_map[col]
        if p.role != "numeric":
            continue
            
        if p.distinct_count <= 1:
            continue
            
        col_lower = col.lower()
        score = 10.0
        agg_method = "sum"
        sem_type = "number"
        
        # Determine semantic type & aggregation method
        if "profit" in col_lower or "revenue" in col_lower or "sales" in col_lower or "price" in col_lower or "cost" in col_lower or "spend" in col_lower or "amount" in col_lower or "salary" in col_lower:
            sem_type = "currency"
            agg_method = "sum" if "salary" not in col_lower else "mean"
        elif "rate" in col_lower or "pct" in col_lower or "percent" in col_lower or "ratio" in col_lower or "margin" in col_lower:
            agg_method = "mean"
            sem_type = "percentage"
        elif "avg" in col_lower or "rating" in col_lower or "score" in col_lower:
            agg_method = "mean"
            sem_type = "score"
        elif "duration" in col_lower or "days" in col_lower or "hours" in col_lower:
            agg_method = "mean"
            sem_type = "duration"
        elif "units" in col_lower or "quantity" in col_lower or "qty" in col_lower:
            sem_type = "quantity"
            agg_method = "sum"

        # Domain keywords matching
        matched_domain = False
        for idx, (kw, def_agg, def_sem) in enumerate(domain_kw):
            if kw in col_lower:
                score += 50.0 - (idx * 2)
                agg_method = def_agg
                sem_type = def_sem
                matched_domain = True
                break
                
        if not matched_domain:
            if "profit" in col_lower or "revenue" in col_lower or "sales" in col_lower or "spend" in col_lower or "cost" in col_lower:
                score += 35.0
            elif "units" in col_lower or "quantity" in col_lower or "runs" in col_lower or "points" in col_lower:
                score += 25.0
            else:
                score += 15.0

        candidates.append(((col, agg_method, sem_type), score))
        
    candidates.sort(key=lambda x: x[1], reverse=True)
    return [c[0] for c in candidates]


def compute_competition_intelligence(
    df: pd.DataFrame,
    dataset_id: str,
    profiles: List[ColumnProfile],
    domain: DomainIdentitySchema,
    dataset_currency: Optional[str] = None,
) -> CompetitionIntelligenceResponse:
    """Universal, domain-aware calculation of competition intelligence with strict entity verification."""
    if df is None or df.empty:
        return CompetitionIntelligenceResponse(
            dataset_id=dataset_id,
            is_available=False,
            competition_mode="unavailable",
            mode_label="Competition Analysis Unavailable",
            unavailable_reason="External competition analysis is unavailable for this dataset.",
            summary_statement="This dataset does not contain verified company, brand or competitor information. We cannot compare your business with other companies using this data alone.",
            missing_requirements=[
                "Company or Brand column (e.g., 'Brand', 'Company', 'Competitor', 'Manufacturer', or 'Product Brand')",
                "Comparable performance metrics (e.g., 'Revenue', 'Profit', 'Units Sold', 'Market Share')",
                "Optional external competitor data or industry benchmarks",
            ],
            required_data_guide=[
                "To enable Dataset-Based Benchmarking, upload a dataset with a verified 'Brand', 'Company', 'Manufacturer', or 'Product' column.",
                "For multi-firm competitive intelligence, include records for peer competitors with corresponding performance measures.",
            ],
            data_limitations=["Dataset contains 0 records."],
        )

    domain_id = domain.domain_id if domain else "general"
    row_count = len(df)
    profile_map = {p.name: p for p in profiles}

    # 1. Gate: Strictly discover valid competitive entity columns
    candidate_entities: List[Tuple[str, str, float]] = []
    for col in df.columns:
        if col not in profile_map:
            continue
        p = profile_map[col]
        entity_res = _detect_valid_competitive_entity(col, p, row_count, domain_id)
        if entity_res:
            entity_label, score = entity_res
            candidate_entities.append((col, entity_label, score))

    # Sort candidate entities by score
    candidate_entities.sort(key=lambda x: x[2], reverse=True)

    # If NO genuine competitive entity is present, return the UNAVAILABLE / SETUP STATE
    if not candidate_entities:
        return CompetitionIntelligenceResponse(
            dataset_id=dataset_id,
            is_available=False,
            competition_mode="unavailable",
            mode_label="Competition Analysis Unavailable",
            entity_type=None,
            unavailable_reason="External competition analysis is unavailable for this dataset.",
            summary_statement="This dataset does not contain verified company, brand or competitor information. We cannot compare your business with other companies using this data alone.",
            missing_requirements=[
                "Company or Brand column (e.g., 'Brand', 'Company', 'Competitor', 'Manufacturer', or 'Product Brand')",
                "Comparable performance metrics (e.g., 'Revenue', 'Profit', 'Units Sold', 'Market Share')",
                "Optional external competitor data or industry benchmarks",
            ],
            required_data_guide=[
                "To enable Dataset-Based Benchmarking, upload a dataset with a verified 'Brand', 'Company', 'Manufacturer', or 'Product' column.",
                "For multi-firm competitive intelligence, include records for peer competitors with corresponding performance measures.",
                "Note: Operational attributes (such as Customer Login Type, Device Type, Demographics, or Regions) represent internal distributions and are excluded from competitive entity benchmarking.",
            ],
            domain_id=domain_id,
            domain_name=domain.name if domain else "General Analytics",
            currency_symbol=dataset_currency,
            data_limitations=[
                "No verified company, brand, or competitor entity column was detected.",
                "Internal operational distributions (e.g., customer login types, device types) are not evaluated as competitive market entities.",
            ],
            methodology_notes=[
                "Entity Verification: Strict entity gating is applied to ensure only genuine commercial brands, firms, suppliers, or teams are benchmarked.",
            ],
            analyzed_at=datetime.now(timezone.utc).isoformat(),
        )

    # 2. Mode A: Genuine Entity Detected -> Compute Dataset-Based Benchmarking
    selected_dimension, entity_type_label, _ = candidate_entities[0]
    available_dimensions = [c[0] for c in candidate_entities[:5]]

    # 3. Identify Candidate Numeric Metrics
    metrics = _find_candidate_metrics(df, profiles, domain)
    if not metrics:
        selected_metric = "record_count"
        selected_metric_label = "Observation Count"
        agg_method = "count"
        sem_type = "count"
        available_metrics = ["record_count"]
    else:
        selected_metric_tuple = metrics[0]
        selected_metric = selected_metric_tuple[0]
        agg_method = selected_metric_tuple[1]
        sem_type = selected_metric_tuple[2]
        selected_metric_label = humanize_column_name(selected_metric)
        available_metrics = [m[0] for m in metrics[:8]]

    # 4. Perform Grouped Aggregation
    dim_series = df[selected_dimension].fillna("(Unspecified)").astype(str)
    
    if agg_method == "count":
        agg_res = df.groupby(dim_series).size().rename("val").reset_index()
    elif agg_method == "mean":
        numeric_series = pd.to_numeric(df[selected_metric], errors="coerce")
        agg_res = df.assign(_metric_val=numeric_series).groupby(dim_series)["_metric_val"].mean().dropna().rename("val").reset_index()
    else:  # sum
        numeric_series = pd.to_numeric(df[selected_metric], errors="coerce").fillna(0.0)
        agg_res = df.assign(_metric_val=numeric_series).groupby(dim_series)["_metric_val"].sum().rename("val").reset_index()

    row_counts = df.groupby(dim_series).size().to_dict()

    if agg_res.empty or len(agg_res) < 2:
        return CompetitionIntelligenceResponse(
            dataset_id=dataset_id,
            is_available=False,
            competition_mode="unavailable",
            mode_label="Competition Analysis Unavailable",
            unavailable_reason="External competition analysis is unavailable for this dataset.",
            summary_statement=f"The detected entity column '{humanize_column_name(selected_dimension)}' has fewer than 2 populated entities for comparative benchmarking.",
            missing_requirements=["At least 2 distinct populated entities in the dataset."],
        )

    # Sort descending
    agg_res = agg_res.sort_values(by="val", ascending=False).reset_index(drop=True)
    total_segments = len(agg_res)
    
    total_sum = agg_res["val"].sum() if agg_res["val"].sum() > 0 and (agg_res["val"] >= 0).all() else None
    benchmark_avg = float(agg_res["val"].mean())
    benchmark_med = float(agg_res["val"].median())

    # Build Segments List
    segments: List[CompetitionSegmentSchema] = []
    for rank, row in enumerate(agg_res.head(50).itertuples(), start=1):
        seg_name = str(getattr(row, selected_dimension))
        seg_val = float(getattr(row, "val"))
        seg_rc = int(row_counts.get(seg_name, 0))
        
        share_pct = round((seg_val / total_sum) * 100, 2) if total_sum and total_sum > 0 else None
        
        if rank == 1:
            status = "top"
        elif rank == total_segments:
            status = "bottom"
        elif seg_val >= benchmark_avg:
            status = "above_average"
        elif seg_val < benchmark_avg:
            status = "below_average"
        else:
            status = "average"
            
        unit_str = dataset_currency if sem_type == "currency" else ("%" if sem_type == "percentage" else None)
        fmt_val = format_metric_display(seg_val, unit=unit_str, semantic_type=sem_type)

        segments.append(
            CompetitionSegmentSchema(
                rank=rank,
                name=seg_name,
                value=round(seg_val, 2),
                formatted_value=fmt_val,
                share_pct=share_pct,
                record_count=seg_rc,
                status=status,
            )
        )

    top_seg = segments[0]
    bottom_seg = segments[-1]
    
    top_val = top_seg.value
    bottom_val = bottom_seg.value
    
    abs_gap = round(top_val - bottom_val, 2)
    if bottom_val != 0:
        ratio = round(top_val / bottom_val, 2) if (top_val >= 0 and bottom_val > 0) else round(abs(top_val - bottom_val) / abs(bottom_val) + 1.0, 2)
        pct_diff = round(((top_val - bottom_val) / abs(bottom_val)) * 100, 1)
    else:
        ratio = round(top_val, 2)
        pct_diff = 100.0

    unit_str = dataset_currency if sem_type == "currency" else ("%" if sem_type == "percentage" else None)
    top_fmt = format_metric_display(top_val, unit=unit_str, semantic_type=sem_type)
    bottom_fmt = format_metric_display(bottom_val, unit=unit_str, semantic_type=sem_type)
    avg_fmt = format_metric_display(benchmark_avg, unit=unit_str, semantic_type=sem_type)
    med_fmt = format_metric_display(benchmark_med, unit=unit_str, semantic_type=sem_type)
    gap_fmt = format_metric_display(abs_gap, unit=unit_str, semantic_type=sem_type)

    dim_label = humanize_column_name(selected_dimension)
    
    # Neutral, evidence-based summary statement
    summary_stmt = (
        f"Compared {total_segments} {entity_type_label.lower()} entities in this dataset on {selected_metric_label}. "
        f"'{top_seg.name}' recorded the highest observed value with {top_fmt}"
        + (f" ({top_seg.share_pct}% share)" if top_seg.share_pct else "")
        + f", while '{bottom_seg.name}' recorded {bottom_fmt} (difference of {gap_fmt})."
    )

    overview = CompetitionOverviewSchema(
        comparison_dimension=selected_dimension,
        comparison_dimension_label=dim_label,
        entity_type_label=entity_type_label,
        available_dimensions=available_dimensions,
        primary_metric=selected_metric,
        primary_metric_label=selected_metric_label,
        available_metrics=available_metrics,
        aggregation_method=agg_method,
        total_segments=total_segments,
        top_segment_name=top_seg.name,
        top_segment_value=top_val,
        top_segment_formatted=top_fmt,
        bottom_segment_name=bottom_seg.name,
        bottom_segment_value=bottom_val,
        bottom_segment_formatted=bottom_fmt,
        benchmark_average=round(benchmark_avg, 2),
        benchmark_average_formatted=avg_fmt,
        benchmark_median=round(benchmark_med, 2),
        benchmark_median_formatted=med_fmt,
        performance_spread_ratio=ratio,
        summary_statement=summary_stmt,
    )

    # 5. Build Measurable Performance Gaps with Careful, Objective Language
    gaps: List[CompetitionGapSchema] = []
    
    # Gap 1: High vs Low
    gaps.append(
        CompetitionGapSchema(
            title=f"Performance Difference: '{top_seg.name}' vs '{bottom_seg.name}'",
            gap_type="top_vs_bottom",
            segment_a=top_seg.name,
            segment_b=bottom_seg.name,
            absolute_gap=abs_gap,
            formatted_absolute_gap=gap_fmt,
            ratio=ratio,
            pct_difference=pct_diff,
            explanation=(
                f"'{top_seg.name}' recorded a higher value ({top_fmt}) than '{bottom_seg.name}' ({bottom_fmt}) "
                f"for {selected_metric_label}, resulting in a measurable difference of {gap_fmt}."
            ),
            evidence=f"Highest: {top_fmt} | Lowest: {bottom_fmt} | Absolute Delta: {gap_fmt} ({pct_diff:+.1f}%)",
        )
    )

    # Gap 2: High vs Cohort Average
    avg_gap = round(top_val - benchmark_avg, 2)
    avg_gap_fmt = format_metric_display(avg_gap, unit=unit_str, semantic_type=sem_type)
    avg_pct_diff = round(((top_val - benchmark_avg) / abs(benchmark_avg)) * 100, 1) if benchmark_avg != 0 else 0.0
    gaps.append(
        CompetitionGapSchema(
            title=f"Cohort Average Comparison: '{top_seg.name}' vs Mean",
            gap_type="top_vs_average",
            segment_a=top_seg.name,
            segment_b=f"Cohort Average ({total_segments} entities)",
            absolute_gap=avg_gap,
            formatted_absolute_gap=avg_gap_fmt,
            ratio=round(top_val / benchmark_avg, 2) if benchmark_avg > 0 else 1.0,
            pct_difference=avg_pct_diff,
            explanation=(
                f"'{top_seg.name}' recorded {top_fmt}, which is {avg_gap_fmt} ({avg_pct_diff:+.1f}%) above "
                f"the dataset cohort mean of {avg_fmt}."
            ),
            evidence=f"Lead Entity: {top_fmt} | Cohort Mean: {avg_fmt} | Variance: {avg_gap_fmt}",
        )
    )

    # 6. Objective Areas of Strength & Improvement
    areas_of_strength = [
        f"'{top_seg.name}' registered the highest recorded {selected_metric_label} ({top_fmt}) among all {total_segments} compared {entity_type_label.lower()} entities.",
    ]
    if len(segments) >= 2:
        areas_of_strength.append(
            f"Top 2 {entity_type_label.lower()} entities ('{segments[0].name}' and '{segments[1].name}') account for the majority of total observed {selected_metric_label}."
        )

    areas_for_improvement = [
        f"Trailing entity '{bottom_seg.name}' registered {bottom_fmt}, lagging the cohort average ({avg_fmt}) by {format_metric_display(abs(bottom_val - benchmark_avg), unit=unit_str, semantic_type=sem_type)}.",
        f"Examine underlying operational factors contributing to the {ratio}x performance variance between top and bottom {entity_type_label.lower()} entities.",
    ]

    # 7. Time-Based Longitudinal Comparison (if date column exists)
    time_comparison = None
    date_col = _find_date_column(df, profiles)
    if date_col and agg_method != "count":
        try:
            parsed_dates = pd.to_datetime(df[date_col], errors="coerce")
            valid_mask = parsed_dates.notna()
            if valid_mask.sum() >= 10:
                df_timed = df[valid_mask].copy()
                df_timed["_parsed_date"] = parsed_dates[valid_mask]
                
                date_span_days = (df_timed["_parsed_date"].max() - df_timed["_parsed_date"].min()).days
                if date_span_days > 730:
                    df_timed["_period"] = df_timed["_parsed_date"].dt.to_period("Y").astype(str)
                    gran = "Yearly"
                elif date_span_days > 60:
                    df_timed["_period"] = df_timed["_parsed_date"].dt.to_period("M").astype(str)
                    gran = "Monthly"
                else:
                    df_timed["_period"] = df_timed["_parsed_date"].dt.to_period("W").astype(str)
                    gran = "Weekly"
                    
                periods = sorted(df_timed["_period"].unique())
                if len(periods) >= 2:
                    top_5_names = [s.name for s in segments[:5]]
                    df_top5 = df_timed[df_timed[selected_dimension].astype(str).isin(top_5_names)]
                    
                    if agg_method == "mean":
                        p_agg = df_top5.groupby(["_period", df_top5[selected_dimension].astype(str)])[selected_metric].mean().unstack(fill_value=0.0)
                    else:
                        p_agg = df_top5.groupby(["_period", df_top5[selected_dimension].astype(str)])[selected_metric].sum().unstack(fill_value=0.0)

                    segment_series = []
                    growth_rates = {}
                    for s_name in top_5_names:
                        if s_name in p_agg.columns:
                            vals = [round(float(v), 2) for v in p_agg[s_name].values]
                            segment_series.append({"segment": s_name, "values": vals})
                            
                            non_zeros = [(idx, v) for idx, v in enumerate(vals) if v > 0]
                            if len(non_zeros) >= 2:
                                first_val = non_zeros[0][1]
                                last_val = non_zeros[-1][1]
                                gr = round(((last_val - first_val) / first_val) * 100, 1)
                                growth_rates[s_name] = gr

                    fastest_seg = max(growth_rates.items(), key=lambda x: x[1]) if growth_rates else None
                    slowest_seg = min(growth_rates.items(), key=lambda x: x[1]) if growth_rates else None
                    
                    time_summary = (
                        f"Tracked longitudinal trajectory for top {entity_type_label.lower()} entities across {len(periods)} {gran.lower()} periods. "
                        + (f"'{fastest_seg[0]}' exhibited the fastest growth ({fastest_seg[1]:+.1f}%)." if fastest_seg else "")
                    )

                    time_comparison = CompetitionTimeComparisonSchema(
                        is_available=True,
                        time_column=date_col,
                        granularity=gran,
                        period_labels=periods,
                        segment_series=segment_series,
                        fastest_growing=fastest_seg[0] if fastest_seg else None,
                        fastest_growing_rate=fastest_seg[1] if fastest_seg else None,
                        most_declining=slowest_seg[0] if slowest_seg else None,
                        most_declining_rate=slowest_seg[1] if slowest_seg else None,
                        summary=time_summary,
                    )
        except Exception as e:
            logger.debug("Time-based competitive comparison encountered non-fatal error: %s", e)
            time_comparison = None

    if not time_comparison:
        time_comparison = CompetitionTimeComparisonSchema(
            is_available=False,
            summary="Longitudinal trajectory unavailable (no chronological date column detected). Analysis reflects cross-sectional benchmarking.",
        )

    limitations = [
        "Dataset-Based Benchmarking Only: Comparisons reflect relative values exclusively within the uploaded dataset and do not represent external market share or industry totals.",
        "Sample Representation: Aggregates depend on the completeness of entity records in this specific file.",
        "Neutral Measurement: High or low recorded values reflect observed numbers and do not imply external market leadership or customer preference without verified source data.",
    ]

    methodology = [
        f"Benchmarked Entity: '{selected_dimension}' ({dim_label}) with {total_segments} discrete {entity_type_label.lower()} entities.",
        f"Compared Metric: '{selected_metric}' ({selected_metric_label}) aggregated via {agg_method.upper()}.",
        "Entity Verification: Validated as a commercial brand/company/entity column before comparison.",
    ]

    return CompetitionIntelligenceResponse(
        dataset_id=dataset_id,
        is_available=True,
        competition_mode="internal_benchmarking",
        mode_label="Dataset-Based Benchmarking",
        entity_type=entity_type_label,
        domain_id=domain_id,
        domain_name=domain.name if domain else "General Analytics",
        currency_symbol=dataset_currency,
        overview=overview,
        segments=segments,
        gaps=gaps,
        areas_of_strength=areas_of_strength,
        areas_for_improvement=areas_for_improvement,
        time_comparison=time_comparison,
        data_limitations=limitations,
        methodology_notes=methodology,
        analyzed_at=datetime.now(timezone.utc).isoformat(),
    )
