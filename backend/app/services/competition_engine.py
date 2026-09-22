"""Universal, domain-aware Competition Intelligence Engine for DataScope.

Analyzes internal dataset distributions, segment rankings, comparative performance gaps,
and longitudinal growth differences across categorical entities (e.g. Products, Brands,
Teams, Suppliers, Departments, Categories, Regions) without inventing external data
or claiming unsupported market positions.
"""
from __future__ import annotations

import logging
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

# Keywords for ranking categorical comparison dimensions per domain
_DIMENSION_DOMAIN_KEYWORDS = {
    "ecommerce": [
        "product", "category", "sub_category", "brand", "item", "sku",
        "segment", "channel", "region", "vendor", "seller", "store",
    ],
    "finance": [
        "company", "ticker", "entity", "institution", "asset", "portfolio",
        "sector", "industry", "segment", "department", "cost_center", "region",
    ],
    "sports_cricket": [
        "team", "player", "batsman", "bowler", "country", "franchise", "venue",
    ],
    "people_hr": [
        "department", "job_role", "role", "division", "team", "position",
        "branch", "location", "education_field", "business_unit",
    ],
    "healthcare": [
        "department", "facility", "hospital", "clinic", "ward", "physician",
        "specialty", "diagnosis", "procedure",
    ],
    "procurement": [
        "supplier", "vendor", "bidder", "contractor", "procuring_entity",
        "buyer", "item_category", "procurement_category", "category",
    ],
    "education": [
        "school", "department", "course", "subject", "grade", "faculty", "program",
    ],
    "entertainment": [
        "studio", "genre", "director", "platform", "distributor", "artist", "channel",
    ],
    "social_media": [
        "platform", "campaign", "channel", "creator", "content_type", "account",
    ],
}

# Keywords for ranking numeric metrics per domain
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
        ("discount", "mean", "percentage"),
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
        ("cash_flow", "sum", "currency"),
        ("roi", "mean", "percentage"),
        ("growth", "mean", "percentage"),
    ],
    "sports_cricket": [
        ("runs", "sum", "number"),
        ("points", "sum", "number"),
        ("wickets", "sum", "number"),
        ("score", "sum", "number"),
        ("strike_rate", "mean", "score"),
        ("economy", "mean", "score"),
        ("average", "mean", "score"),
        ("matches", "sum", "number"),
    ],
    "people_hr": [
        ("salary", "mean", "currency"),
        ("compensation", "mean", "currency"),
        ("monthly_income", "mean", "currency"),
        ("hourly_rate", "mean", "currency"),
        ("performance_rating", "mean", "score"),
        ("tenure", "mean", "duration"),
        ("years_at_company", "mean", "duration"),
        ("training_hours", "mean", "duration"),
    ],
    "healthcare": [
        ("patient_count", "sum", "number"),
        ("admissions", "sum", "number"),
        ("billing_amount", "sum", "currency"),
        ("cost", "sum", "currency"),
        ("length_of_stay", "mean", "duration"),
        ("satisfaction", "mean", "score"),
    ],
    "procurement": [
        ("tender_value", "sum", "currency"),
        ("contract_value", "sum", "currency"),
        ("award_value", "sum", "currency"),
        ("amount", "sum", "currency"),
        ("spend", "sum", "currency"),
        ("duration_in_days", "mean", "duration"),
        ("bidders", "mean", "number"),
    ],
    "education": [
        ("score", "mean", "score"),
        ("grade", "mean", "score"),
        ("gpa", "mean", "score"),
        ("attendance", "mean", "percentage"),
        ("tuition", "sum", "currency"),
    ],
    "entertainment": [
        ("box_office", "sum", "currency"),
        ("revenue", "sum", "currency"),
        ("streams", "sum", "quantity"),
        ("views", "sum", "quantity"),
        ("rating", "mean", "score"),
        ("budget", "sum", "currency"),
    ],
    "social_media": [
        ("impressions", "sum", "quantity"),
        ("reach", "sum", "quantity"),
        ("engagement", "sum", "quantity"),
        ("clicks", "sum", "quantity"),
        ("ctr", "mean", "percentage"),
        ("spend", "sum", "currency"),
    ],
}


def _is_valid_comparison_dimension(col_name: str, profile: ColumnProfile, row_count: int) -> bool:
    """Check if a column is suitable as a categorical comparison dimension."""
    # Must be categorical or boolean role (or low-cardinality text)
    if profile.role in ("datetime", "numeric", "ignore"):
        return False
    
    # Exclude obvious row IDs
    if profile.role == "identifier":
        return False
    
    # Must have between 2 and 150 unique categories
    distinct_count = profile.distinct_count
    if distinct_count < 2 or distinct_count > 150:
        return False
    
    if row_count > 10 and (distinct_count / row_count) > 0.95:
        return False
    
    col_lower = col_name.lower()
    if col_lower in ("id", "uuid", "guid", "row_id", "index", "hash") or (col_lower.endswith("_id") and distinct_count > 50):
        return False
        
    return True


def _find_candidate_dimensions(
    df: pd.DataFrame,
    profiles: List[ColumnProfile],
    domain: DomainIdentitySchema,
) -> List[str]:
    """Find and rank all suitable categorical comparison dimensions."""
    profile_map = {p.name: p for p in profiles}
    candidates = []
    
    row_count = len(df)
    domain_id = domain.domain_id if domain else "general"
    domain_kw = _DIMENSION_DOMAIN_KEYWORDS.get(domain_id, [])
    general_kw = ["category", "type", "segment", "group", "class", "name", "brand", "model", "region", "team"]

    for col in df.columns:
        if col not in profile_map:
            continue
        p = profile_map[col]
        if not _is_valid_comparison_dimension(col, p, row_count):
            continue

        col_lower = col.lower()
        score = 10.0
        
        # Domain keyword boost
        for idx, kw in enumerate(domain_kw):
            if kw in col_lower:
                score += 50.0 - (idx * 2)
                break
                
        # General comparison keyword boost
        for kw in general_kw:
            if kw in col_lower:
                score += 15.0
                break
                
        # Ideal cardinality (3 to 30 categories) gets highest utility
        if 3 <= p.distinct_count <= 30:
            score += 20.0
        elif 2 <= p.distinct_count <= 50:
            score += 10.0
            
        candidates.append((col, score))
        
    # Sort by score descending
    candidates.sort(key=lambda x: x[1], reverse=True)
    return [c[0] for c in candidates]


def _find_candidate_metrics(
    df: pd.DataFrame,
    profiles: List[ColumnProfile],
    domain: DomainIdentitySchema,
) -> List[Tuple[str, str, str]]:
    """Find and rank all suitable continuous numeric comparison metrics.
    Returns: List of (col_name, aggregation_method, semantic_type)
    """
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
            
        # Ignore constant columns
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
    """Universal, domain-aware calculation of segment competition, rankings, and performance gaps."""
    if df is None or df.empty:
        return CompetitionIntelligenceResponse(
            dataset_id=dataset_id,
            is_available=False,
            unavailable_reason="Competitive comparison cannot be reliably calculated from this dataset.",
            missing_requirements=["Dataset is empty or contains 0 records."],
            data_limitations=["No records available for analysis."],
        )

    # 1. Identify Candidate Comparison Dimensions
    dimensions = _find_candidate_dimensions(df, profiles, domain)
    if not dimensions:
        return CompetitionIntelligenceResponse(
            dataset_id=dataset_id,
            is_available=False,
            unavailable_reason="Competitive comparison cannot be reliably calculated from this dataset.",
            missing_requirements=[
                "At least one categorical comparison dimension (e.g. Product, Brand, Company, Team, Department, Category, Supplier) with 2 or more distinct segments.",
            ],
            data_limitations=[
                "No categorical entity or segment columns with sufficient distinct values (>= 2) were detected in the dataset.",
                "Pure unique ID columns and uniform single-value columns are excluded from competitive grouping.",
            ],
        )

    selected_dimension = dimensions[0]
    available_dimensions = dimensions[:8]

    # 2. Identify Candidate Numeric Metrics
    metrics = _find_candidate_metrics(df, profiles, domain)
    if not metrics:
        # Fallback to record count aggregation if no numeric metric exists
        selected_metric = "record_count"
        selected_metric_label = "Record Count"
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

    # 3. Perform Grouped Aggregation
    dim_series = df[selected_dimension].fillna("(Unspecified)").astype(str)
    
    if agg_method == "count":
        agg_res = df.groupby(dim_series).size().rename("val").reset_index()
    elif agg_method == "mean":
        numeric_series = pd.to_numeric(df[selected_metric], errors="coerce")
        agg_res = df.assign(_metric_val=numeric_series).groupby(dim_series)["_metric_val"].mean().dropna().rename("val").reset_index()
    else:  # sum
        numeric_series = pd.to_numeric(df[selected_metric], errors="coerce").fillna(0.0)
        agg_res = df.assign(_metric_val=numeric_series).groupby(dim_series)["_metric_val"].sum().rename("val").reset_index()

    # Count of rows per segment
    row_counts = df.groupby(dim_series).size().to_dict()

    if agg_res.empty or len(agg_res) < 2:
        return CompetitionIntelligenceResponse(
            dataset_id=dataset_id,
            is_available=False,
            unavailable_reason="Competitive comparison cannot be reliably calculated from this dataset.",
            missing_requirements=[
                f"Selected dimension '{humanize_column_name(selected_dimension)}' has fewer than 2 valid populated segments after filtering missing values."
            ],
            data_limitations=["Insufficient populated groups for relative comparison."],
        )

    # Sort segments descending by value
    agg_res = agg_res.sort_values(by="val", ascending=False).reset_index(drop=True)
    total_segments = len(agg_res)
    
    total_sum = agg_res["val"].sum() if agg_res["val"].sum() > 0 and (agg_res["val"] >= 0).all() else None
    benchmark_avg = float(agg_res["val"].mean())
    benchmark_med = float(agg_res["val"].median())

    # Build Segment List (limit to top 50 to maintain performance)
    segments: List[CompetitionSegmentSchema] = []
    for rank, row in enumerate(agg_res.head(50).itertuples(), start=1):
        seg_name = str(getattr(row, selected_dimension))
        seg_val = float(getattr(row, "val"))
        seg_rc = int(row_counts.get(seg_name, 0))
        
        share_pct = round((seg_val / total_sum) * 100, 2) if total_sum and total_sum > 0 else None
        
        # Determine status
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

    # 4. Calculate Key Gaps & Overview Benchmarks
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
    
    summary_stmt = (
        f"Compared {total_segments} {dim_label.lower()} segments on {selected_metric_label}. "
        f"'{top_seg.name}' leads with {top_fmt}"
        + (f" ({top_seg.share_pct}% share)" if top_seg.share_pct else "")
        + f", outperforming '{bottom_seg.name}' ({bottom_fmt}) by {gap_fmt}."
    )

    overview = CompetitionOverviewSchema(
        comparison_dimension=selected_dimension,
        comparison_dimension_label=dim_label,
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

    # 5. Build Key Performance Gaps
    gaps: List[CompetitionGapSchema] = []
    
    # Gap 1: Top vs Bottom
    gaps.append(
        CompetitionGapSchema(
            title=f"Head-to-Head Performance Gap: '{top_seg.name}' vs '{bottom_seg.name}'",
            gap_type="top_vs_bottom",
            segment_a=top_seg.name,
            segment_b=bottom_seg.name,
            absolute_gap=abs_gap,
            formatted_absolute_gap=gap_fmt,
            ratio=ratio,
            pct_difference=pct_diff,
            explanation=(
                f"'{top_seg.name}' registered the highest observed {selected_metric_label} ({top_fmt}), "
                f"which is {ratio}x the lowest recorded segment '{bottom_seg.name}' ({bottom_fmt})."
            ),
            evidence=f"Highest: {top_fmt} | Lowest: {bottom_fmt} | Absolute difference: {gap_fmt} ({pct_diff:+.1f}%)",
        )
    )

    # Gap 2: Top vs Benchmark Average
    avg_gap = round(top_val - benchmark_avg, 2)
    avg_gap_fmt = format_metric_display(avg_gap, unit=unit_str, semantic_type=sem_type)
    avg_pct_diff = round(((top_val - benchmark_avg) / abs(benchmark_avg)) * 100, 1) if benchmark_avg != 0 else 0.0
    gaps.append(
        CompetitionGapSchema(
            title=f"Benchmark Premium: '{top_seg.name}' vs Cohort Average",
            gap_type="top_vs_average",
            segment_a=top_seg.name,
            segment_b=f"Cohort Average ({total_segments} segments)",
            absolute_gap=avg_gap,
            formatted_absolute_gap=avg_gap_fmt,
            ratio=round(top_val / benchmark_avg, 2) if benchmark_avg > 0 else 1.0,
            pct_difference=avg_pct_diff,
            explanation=(
                f"The top-ranking segment '{top_seg.name}' exceeds the overall segment cohort average of {avg_fmt} "
                f"by {avg_gap_fmt} ({avg_pct_diff:+.1f}% above cohort mean)."
            ),
            evidence=f"Leader: {top_fmt} | Cohort Mean: {avg_fmt} | Benchmark delta: {avg_gap_fmt}",
        )
    )

    # Gap 3: Leader Concentration / Dominance (if top segment has > 2x #2 or significant share)
    if len(segments) >= 2:
        second_seg = segments[1]
        second_val = second_seg.value
        second_fmt = format_metric_display(second_val, unit=unit_str, semantic_type=sem_type)
        lead_delta = round(top_val - second_val, 2)
        lead_delta_fmt = format_metric_display(lead_delta, unit=unit_str, semantic_type=sem_type)
        lead_pct = round(((top_val - second_val) / abs(second_val)) * 100, 1) if second_val != 0 else 0.0
        
        gaps.append(
            CompetitionGapSchema(
                title=f"Leader Separation: '{top_seg.name}' vs Runner-Up '{second_seg.name}'",
                gap_type="leader_dominance",
                segment_a=top_seg.name,
                segment_b=second_seg.name,
                absolute_gap=lead_delta,
                formatted_absolute_gap=lead_delta_fmt,
                ratio=round(top_val / second_val, 2) if second_val > 0 else 1.0,
                pct_difference=lead_pct,
                explanation=(
                    f"'{top_seg.name}' outperforms the second-ranked segment '{second_seg.name}' by "
                    f"{lead_delta_fmt} (+{lead_pct:.1f}%)."
                ),
                evidence=f"Rank #1: {top_fmt} | Rank #2: {second_fmt} | Margin: {lead_delta_fmt}",
            )
        )

    # 6. Time-Based Longitudinal Comparison (if date column exists)
    time_comparison = None
    date_col = _find_date_column(df, profiles)
    if date_col and agg_method != "count":
        try:
            parsed_dates = pd.to_datetime(df[date_col], errors="coerce")
            valid_mask = parsed_dates.notna()
            if valid_mask.sum() >= 10:
                df_timed = df[valid_mask].copy()
                df_timed["_parsed_date"] = parsed_dates[valid_mask]
                
                # Check date range to choose monthly or yearly granularity
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
                            
                            # Growth from first valid period to last period
                            non_zeros = [(idx, v) for idx, v in enumerate(vals) if v > 0]
                            if len(non_zeros) >= 2:
                                first_val = non_zeros[0][1]
                                last_val = non_zeros[-1][1]
                                gr = round(((last_val - first_val) / first_val) * 100, 1)
                                growth_rates[s_name] = gr

                    fastest_seg = max(growth_rates.items(), key=lambda x: x[1]) if growth_rates else None
                    slowest_seg = min(growth_rates.items(), key=lambda x: x[1]) if growth_rates else None
                    
                    time_summary = (
                        f"Tracked longitudinal trajectory for top segments across {len(periods)} {gran.lower()} periods. "
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
            summary="Longitudinal time-series trajectory is unavailable (no suitable chronological timestamp column detected). Analysis reflects cross-sectional comparison.",
        )

    # 7. Data Limitations & Methodology Notes
    limitations = [
        "Internal Cohort Only: Comparisons reflect relative rankings solely within the provided dataset and do not represent external market share or industry benchmarks.",
        "Sample Size Variation: Segment aggregates may be influenced by uneven record distributions across categories.",
        "Aggregation Basis: Rankings are computed strictly on the selected metric and do not account for external unmeasured variables.",
    ]

    methodology = [
        f"Grouping Dimension: '{selected_dimension}' ({dim_label}) with {total_segments} discrete categories.",
        f"Selected Metric: '{selected_metric}' ({selected_metric_label}) aggregated via {agg_method.upper()}.",
        "Missing / Null Values: Records with missing segment keys are attributed to '(Unspecified)' or filtered.",
        "Precision & Rounding: All percentages and financial figures are rounded for human-readable presentation.",
    ]

    return CompetitionIntelligenceResponse(
        dataset_id=dataset_id,
        is_available=True,
        domain_id=domain.domain_id if domain else "general",
        domain_name=domain.name if domain else "General Analytics",
        currency_symbol=dataset_currency,
        overview=overview,
        segments=segments,
        gaps=gaps,
        time_comparison=time_comparison,
        data_limitations=limitations,
        methodology_notes=methodology,
        analyzed_at=datetime.now(timezone.utc).isoformat(),
    )
