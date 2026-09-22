"""Market-Based Competition Intelligence Engine for DataScope.

Analyzes external market competition, competitor comparisons, market gaps,
and evidence-backed strategic recommendations from verified competitor datasets.
Never misclassifies internal transaction columns (such as Customer Login Type,
Device Type, Product Categories) as market competitors.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from app.schemas.domain_blueprint import (
    CompetitionIntelligenceResponse,
    CompetitorEntitySchema,
    CompetitionTimeComparisonSchema,
    DomainIdentitySchema,
    MarketBenchmarkPreviewResponse,
    MarketGapSchema,
    MarketOverviewSchema,
    MarketStrategyRecommendationSchema,
)
from app.services.column_formatter import format_metric_display, humanize_column_name
from app.services.column_profiler import ColumnProfile, profile_dataset

logger = logging.getLogger("datascope.services.competition_engine")

# Blacklist of internal transaction/customer terms that MUST NEVER be treated as market competitors
_INTERNAL_TRANSACTION_TERMS = {
    "login", "customer_login", "customer_login_type", "login_type", "user_type",
    "customer_type", "member", "membership", "membership_status", "auth", "account_type",
    "device", "device_type", "browser", "os", "platform", "client", "client_type",
    "gender", "sex", "age", "age_group", "marital", "marital_status", "education",
    "region", "country", "city", "state", "zone", "zip", "zip_code", "postal", "postal_code",
    "area", "location", "territory", "province", "district",
    "payment", "payment_method", "payment_type", "card_type", "shipping", "ship_mode",
    "shipping_mode", "delivery_type", "fulfillment_type", "order_status", "status",
    "stage", "priority", "aging", "delay", "order_id", "customer_id", "customer_name",
    "rating_category", "sentiment", "feedback", "category", "sub_category", "product_name",
    "product", "item_name", "sku",
}

# Explicit whitelist of column terms that represent external market competitors / peer companies
_MARKET_COMPETITOR_TERMS = [
    "competitor", "competitor_name", "competitors", "peer_company", "peer_firm",
    "rival", "rival_company", "market_competitor", "market_player", "competing_firm",
    "peer_brand", "brand_competitor", "company_name", "company", "firm", "enterprise",
]

# Required market fields specifications for user guidance
REQUIRED_MARKET_FIELDS_GUIDE = [
    {
        "field_name": "competitor_name / company",
        "description": "Name of each competing company, firm, or brand in the market.",
        "example": "Apex Corp, Nexus Ltd, Zenith Inc",
        "required": True,
    },
    {
        "field_name": "revenue / sales",
        "description": "Total revenue or reported turnover for each competitor.",
        "example": "$4,500,000, $3,200,000",
        "required": True,
    },
    {
        "field_name": "profit / net_income",
        "description": "Reported operating profit or net income for margin calculation.",
        "example": "$650,000, $420,000",
        "required": False,
    },
    {
        "field_name": "market_share_pct",
        "description": "Reported market share percentage (if available from market research).",
        "example": "34.5%, 22.0%",
        "required": False,
    },
    {
        "field_name": "growth_rate_pct / period",
        "description": "Year-over-year growth rate or historical periods for trend comparison.",
        "example": "+14.2%, -3.5% or 2023-Q1..2024-Q4",
        "required": False,
    },
    {
        "field_name": "price / price_index",
        "description": "Average selling price or benchmark pricing index against market average.",
        "example": "$129.99, 105.2 index",
        "required": False,
    },
]


def validate_and_preview_benchmark(df: pd.DataFrame, filename: str) -> MarketBenchmarkPreviewResponse:
    """Validate an uploaded market benchmark dataset (CSV/XLSX/JSON) and return preview & quality warnings."""
    if df is None or df.empty:
        return MarketBenchmarkPreviewResponse(
            is_valid=False,
            filename=filename,
            company_count=0,
            companies_sample=[],
            industry=None,
            reporting_period=None,
            detected_fields=[],
            missing_required_fields=["competitor_name / company (Required)", "revenue / sales (Required)"],
            missing_optional_fields=["profit / net_income", "market_share_pct", "growth_rate_pct", "period", "price"],
            warnings=["The uploaded file contains no rows or records."],
            sample_records=[],
            validation_summary="Validation failed: The dataset is empty.",
        )

    comp_col = None
    rev_col = None
    profit_col = None
    share_col = None
    growth_col = None
    period_col = None
    industry_col = None
    price_col = None

    for col in df.columns:
        col_norm = str(col).strip().lower().replace("-", "_").replace(" ", "_")
        
        # Check competitor
        if not comp_col:
            for term in _MARKET_COMPETITOR_TERMS:
                if col_norm == term or col_norm == f"{term}_name" or col_norm == f"name_{term}" or f"_{term}_" in f"_{col_norm}_":
                    comp_col = col
                    break

        # Revenue
        if not rev_col and any(term in col_norm for term in ["revenue", "sales", "turnover", "income", "spend", "value"]):
            if pd.to_numeric(df[col], errors="coerce").notna().sum() > 0:
                rev_col = col

        # Profit
        if not profit_col and any(term in col_norm for term in ["profit", "net_profit", "operating_profit", "earnings"]):
            if pd.to_numeric(df[col], errors="coerce").notna().sum() > 0:
                profit_col = col

        # Share
        if not share_col and any(term in col_norm for term in ["market_share", "share_pct", "share", "market_pct"]):
            if pd.to_numeric(df[col], errors="coerce").notna().sum() > 0:
                share_col = col

        # Growth
        if not growth_col and any(term in col_norm for term in ["growth", "growth_rate", "yoy_growth", "cagr"]):
            if pd.to_numeric(df[col], errors="coerce").notna().sum() > 0:
                growth_col = col

        # Period / Date
        if not period_col and any(term in col_norm for term in ["period", "date", "year", "quarter", "month", "time"]):
            period_col = col

        # Industry
        if not industry_col and any(term in col_norm for term in ["industry", "market", "sector", "domain"]):
            industry_col = col

        # Price
        if not price_col and any(term in col_norm for term in ["price", "avg_price", "pricing", "unit_price", "price_index"]):
            if pd.to_numeric(df[col], errors="coerce").notna().sum() > 0:
                price_col = col

    detected = []
    missing_req = []
    missing_opt = []
    warnings = []

    if comp_col:
        detected.append(f"Company/Competitor: '{comp_col}'")
    else:
        missing_req.append("competitor_name / company (Required)")

    if rev_col:
        detected.append(f"Revenue/Sales: '{rev_col}'")
    else:
        missing_req.append("revenue / sales (Required)")

    if profit_col:
        detected.append(f"Profit/Net Income: '{profit_col}'")
    else:
        missing_opt.append("profit / net_income")

    if share_col:
        detected.append(f"Market Share %: '{share_col}'")
    else:
        missing_opt.append("market_share_pct")

    if growth_col:
        detected.append(f"Growth Rate %: '{growth_col}'")
    else:
        missing_opt.append("growth_rate_pct")

    if period_col:
        detected.append(f"Period/Date: '{period_col}'")
    else:
        missing_opt.append("period / date")

    if industry_col:
        detected.append(f"Industry: '{industry_col}'")
    else:
        missing_opt.append("industry")

    if price_col:
        detected.append(f"Price/Index: '{price_col}'")
    else:
        missing_opt.append("price / price_index")

    company_count = 0
    companies_sample = []
    if comp_col:
        unique_companies = [str(x) for x in df[comp_col].dropna().unique().tolist() if str(x).strip()]
        company_count = len(unique_companies)
        companies_sample = unique_companies[:6]
        
        if company_count < 2:
            warnings.append(f"Only {company_count} distinct company found. Meaningful market comparison requires at least 2 distinct companies.")

        if not period_col and df[comp_col].duplicated().sum() > 0:
            dup_count = int(df[comp_col].duplicated().sum())
            warnings.append(f"Detected {dup_count} duplicate company rows without a period column. Values will be aggregated per company.")

        null_comps = int(df[comp_col].isna().sum())
        if null_comps > 0:
            warnings.append(f"Found {null_comps} rows with missing or blank company names.")

    if rev_col:
        rev_numeric = pd.to_numeric(df[rev_col], errors="coerce")
        null_rev = int(rev_numeric.isna().sum())
        if null_rev > 0:
            warnings.append(f"Found {null_rev} rows with non-numeric or missing revenue values.")
        if (rev_numeric < 0).any():
            neg_count = int((rev_numeric < 0).sum())
            warnings.append(f"Found {neg_count} rows with negative revenue values.")

    industry_str = None
    if industry_col:
        mode_val = df[industry_col].dropna().mode()
        if not mode_val.empty:
            industry_str = str(mode_val.iloc[0])

    period_str = None
    if period_col:
        try:
            non_null_p = df[period_col].dropna().astype(str)
            if len(non_null_p) > 0:
                period_str = f"{non_null_p.min()} - {non_null_p.max()}"
        except Exception:
            pass

    sample_df = df.head(5).copy()
    sample_records = sample_df.where(pd.notnull(sample_df), None).to_dict(orient="records")

    is_valid = bool(comp_col and rev_col and company_count >= 2)
    if is_valid:
        validation_summary = f"Verified market benchmark dataset containing {company_count} companies with {len(detected)} detected metric fields."
    else:
        validation_summary = f"Validation incomplete: {', '.join(missing_req) if missing_req else 'At least 2 distinct companies required'}."

    return MarketBenchmarkPreviewResponse(
        is_valid=is_valid,
        filename=filename,
        company_count=company_count,
        companies_sample=companies_sample,
        industry=industry_str,
        reporting_period=period_str,
        detected_fields=detected,
        missing_required_fields=missing_req,
        missing_optional_fields=missing_opt,
        warnings=warnings,
        sample_records=sample_records,
        validation_summary=validation_summary,
    )


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

    date_keywords = ["date", "time", "timestamp", "period", "day", "month", "year", "quarter"]
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


def _is_market_competitor_column(col_name: str, profile: ColumnProfile, row_count: int) -> bool:
    """Strictly verify if a column represents genuine external market competitors."""
    norm = col_name.strip().lower().replace("-", "_").replace(" ", "_")
    
    # Reject internal transaction patterns
    if norm in _INTERNAL_TRANSACTION_TERMS:
        return False
    for rej in _INTERNAL_TRANSACTION_TERMS:
        if rej in norm:
            return False

    # Check whitelist first
    is_whitelist_match = False
    for term in _MARKET_COMPETITOR_TERMS:
        if norm == term or norm == f"{term}_name" or norm == f"name_{term}" or f"_{term}_" in f"_{norm}_":
            is_whitelist_match = True
            break

    if not is_whitelist_match:
        return False

    # If it is a whitelist match, don't allow pure numeric or datetime types
    if profile.role in ("datetime", "numeric"):
        return False

    # High-cardinality guard (e.g. unique user identifiers)
    distinct_count = profile.distinct_count
    if distinct_count > 100:
        return False
    if row_count > 10 and (distinct_count / row_count) > 0.95:
        return False

    return True


def _find_numeric_metric(df: pd.DataFrame, profiles: List[ColumnProfile], keywords: List[str]) -> Optional[str]:
    """Look for a specific continuous numeric metric matching keywords."""
    profile_map = {p.name: p for p in profiles}
    for col in df.columns:
        if col not in profile_map:
            continue
        p = profile_map[col]
        if p.role != "numeric":
            continue
        col_lower = col.lower()
        if any(kw in col_lower for kw in keywords):
            return col
    return None


def compute_competition_intelligence(
    df: pd.DataFrame,
    dataset_id: str,
    profiles: List[ColumnProfile],
    domain: DomainIdentitySchema,
    dataset_currency: Optional[str] = None,
    benchmark_df: Optional[pd.DataFrame] = None,
    benchmark_filename: Optional[str] = None,
) -> CompetitionIntelligenceResponse:
    """Market-Oriented Competition Intelligence Engine."""
    has_benchmark = benchmark_df is not None and not benchmark_df.empty
    target_df = benchmark_df if has_benchmark else df
    target_profiles = profile_dataset(target_df) if has_benchmark else profiles

    if target_df is None or target_df.empty:
        return CompetitionIntelligenceResponse(
            dataset_id=dataset_id,
            is_available=False,
            market_data_status="insufficient_data",
            status_title="Market competition analysis is not available yet.",
            unavailable_reason="Dataset is empty or contains 0 records.",
            summary_statement="Your current dataset contains no records to analyze.",
            missing_requirements=[
                "Upload a dataset containing verified competitor entities and comparable market metrics.",
            ],
            required_market_fields=REQUIRED_MARKET_FIELDS_GUIDE,
            market_limitations=["0 records available."],
        )

    domain_id = domain.domain_id if domain else "general"
    domain_name = domain.name if domain else "General Market Analytics"
    row_count = len(target_df)
    profile_map = {p.name: p for p in target_profiles}

    # 1. Gate: Verify if target dataset contains external market competitor columns
    competitor_col = None
    for col in target_df.columns:
        if col not in profile_map:
            continue
        p = profile_map[col]
        if _is_market_competitor_column(col, p, row_count):
            competitor_col = col
            break

    # If NO verified market competitor column exists (e.g. internal sales dataset):
    if not competitor_col:
        return CompetitionIntelligenceResponse(
            dataset_id=dataset_id,
            is_available=False,
            market_data_status="market_data_absent",
            status_title="Market competition analysis is not available yet.",
            unavailable_reason="Your current dataset contains internal transaction data, but no verified competitor or market benchmark data.",
            summary_statement="Your current dataset contains internal transaction data, but no verified competitor or market benchmark data. Upload a market benchmark dataset containing competitor entities and comparable metrics to enable this analysis.",
            missing_requirements=[
                "Competitor or Company column (e.g., 'Competitor', 'Company', 'Peer Brand')",
                "Comparable performance metrics (e.g., 'Revenue', 'Profit Margin', 'Market Share', 'Growth Rate')",
                "External market scope or competitor-level reporting periods",
            ],
            required_market_fields=REQUIRED_MARKET_FIELDS_GUIDE,
            domain_id=domain_id,
            domain_name=domain_name,
            currency_symbol=dataset_currency,
            has_external_benchmark=False,
            benchmark_filename=None,
            market_limitations=[
                "Internal Transaction Data Only: The active file tracks internal orders and customer transactions, not external market competitor disclosures.",
                "Excluded Categories: Customer Login Type, Device Type, Demographics, and Order IDs represent internal operations and are excluded from market competitor analysis.",
            ],
            methodology_notes=[
                "Market Gating Active: DataScope strictly validates that datasets contain external competitor firms before computing market share or competitor gap dashboards.",
            ],
            analyzed_at=datetime.now(timezone.utc).isoformat(),
        )

    # 2. Market Data Detected -> Extract Metrics
    rev_col = _find_numeric_metric(target_df, target_profiles, ["revenue", "sales", "turnover", "income", "spend", "value"])
    profit_col = _find_numeric_metric(target_df, target_profiles, ["profit", "net_profit", "operating_profit", "earnings"])
    share_col = _find_numeric_metric(target_df, target_profiles, ["market_share", "share_pct", "share", "market_pct"])
    growth_col = _find_numeric_metric(target_df, target_profiles, ["growth", "growth_rate", "yoy_growth", "cagr"])
    price_col = _find_numeric_metric(target_df, target_profiles, ["price", "avg_price", "pricing", "unit_price", "price_index"])
    units_col = _find_numeric_metric(target_df, target_profiles, ["units", "quantity", "units_sold", "volume"])

    comp_series = target_df[competitor_col].fillna("(Unknown Competitor)").astype(str)
    unique_competitors = target_df[competitor_col].dropna().unique()
    total_competitors = len(unique_competitors)

    if total_competitors < 2:
        return CompetitionIntelligenceResponse(
            dataset_id=dataset_id,
            is_available=False,
            market_data_status="insufficient_data",
            status_title="Market competition analysis is not available yet.",
            unavailable_reason=f"The competitor column '{humanize_column_name(competitor_col)}' contains fewer than 2 distinct competitors.",
            summary_statement="At least 2 distinct competitor entities are required for comparative market analysis.",
            missing_requirements=["Multiple competitor entities in the market dataset."],
            required_market_fields=REQUIRED_MARKET_FIELDS_GUIDE,
            has_external_benchmark=has_benchmark,
            benchmark_filename=benchmark_filename,
        )

    # Primary comparison metric
    primary_metric_col = rev_col or units_col or profit_col or "record_count"
    primary_metric_label = humanize_column_name(primary_metric_col) if primary_metric_col != "record_count" else "Reported Records"

    # Aggregate by Competitor
    competitors: List[CompetitorEntitySchema] = []
    
    # Compute totals
    comp_groups = target_df.groupby(comp_series)
    rev_by_comp = comp_groups[rev_col].sum() if rev_col else pd.Series(0.0, index=comp_groups.groups.keys())
    profit_by_comp = comp_groups[profit_col].sum() if profit_col else pd.Series(0.0, index=comp_groups.groups.keys())
    units_by_comp = comp_groups[units_col].sum() if units_col else pd.Series(0.0, index=comp_groups.groups.keys())
    growth_by_comp = comp_groups[growth_col].mean() if growth_col else None
    price_by_comp = comp_groups[price_col].mean() if price_col else None
    explicit_share = comp_groups[share_col].mean() if share_col else None

    total_market_rev = float(rev_by_comp.sum()) if rev_col and rev_by_comp.sum() > 0 else None
    
    # Sort competitors by primary metric (revenue or units or count)
    sort_series = rev_by_comp if rev_col else (units_by_comp if units_col else comp_groups.size())
    sorted_comp_names = sort_series.sort_values(ascending=False).index.tolist()

    for rank, comp_name in enumerate(sorted_comp_names, start=1):
        c_rev = float(rev_by_comp.get(comp_name, 0.0)) if rev_col else None
        c_profit = float(profit_by_comp.get(comp_name, 0.0)) if profit_col else None
        c_units = float(units_by_comp.get(comp_name, 0.0)) if units_col else None
        c_growth = float(growth_by_comp.get(comp_name, 0.0)) if growth_by_comp is not None else None
        c_price = float(price_by_comp.get(comp_name, 0.0)) if price_by_comp is not None else None
        
        # Margin
        margin_pct = round((c_profit / c_rev) * 100, 1) if (c_profit is not None and c_rev and c_rev > 0) else None
        
        # Share
        if explicit_share is not None and comp_name in explicit_share:
            share_pct = round(float(explicit_share[comp_name]), 1)
        elif total_market_rev and c_rev:
            share_pct = round((c_rev / total_market_rev) * 100, 1)
        else:
            share_pct = None

        rev_fmt = format_metric_display(c_rev, unit=dataset_currency, semantic_type="currency") if c_rev is not None else None
        profit_fmt = format_metric_display(c_profit, unit=dataset_currency, semantic_type="currency") if c_profit is not None else None
        units_fmt = format_metric_display(c_units, unit=None, semantic_type="quantity") if c_units is not None else None
        price_fmt = format_metric_display(c_price, unit=dataset_currency, semantic_type="currency") if c_price is not None else None

        competitors.append(
            CompetitorEntitySchema(
                rank=rank,
                name=comp_name,
                revenue=round(c_rev, 2) if c_rev is not None else None,
                revenue_formatted=rev_fmt,
                profit=round(c_profit, 2) if c_profit is not None else None,
                profit_formatted=profit_fmt,
                profit_margin_pct=margin_pct,
                market_share_pct=share_pct,
                units_sold=round(c_units, 2) if c_units is not None else None,
                units_sold_formatted=units_fmt,
                growth_rate_pct=round(c_growth, 1) if c_growth is not None else None,
                pricing_index=round(c_price, 2) if c_price is not None else None,
                pricing_index_formatted=price_fmt,
                records_count=int(comp_groups.size().get(comp_name, 0)),
                status_label="Reported Competitor",
            )
        )

    leader_comp = competitors[0]
    trailing_comp = competitors[-1]
    avg_rev = float(rev_by_comp.mean()) if rev_col else None
    avg_rev_fmt = format_metric_display(avg_rev, unit=dataset_currency, semantic_type="currency") if avg_rev is not None else None
    tot_rev_fmt = format_metric_display(total_market_rev, unit=dataset_currency, semantic_type="currency") if total_market_rev is not None else None

    # Overview
    overview = MarketOverviewSchema(
        industry_market_name=domain_name,
        competitor_column=competitor_col,
        competitor_column_label=humanize_column_name(competitor_col),
        total_competitors_tracked=total_competitors,
        total_reported_market_revenue=round(total_market_rev, 2) if total_market_rev else None,
        total_reported_market_revenue_formatted=tot_rev_fmt,
        data_coverage_description=f"Tracked {total_competitors} reported competitors in this market dataset.",
        top_competitor_name=leader_comp.name,
        top_competitor_metric_value=leader_comp.revenue or leader_comp.units_sold or 0.0,
        top_competitor_metric_formatted=leader_comp.revenue_formatted or leader_comp.units_sold_formatted or str(leader_comp.records_count),
        benchmark_average_revenue=round(avg_rev, 2) if avg_rev else None,
        benchmark_average_revenue_formatted=avg_rev_fmt,
        primary_metric=primary_metric_col,
        primary_metric_label=primary_metric_label,
        summary_statement=(
            f"Compared {total_competitors} reported competitors in {domain_name}. "
            f"'{leader_comp.name}' holds the highest reported {primary_metric_label.lower()} "
            f"({leader_comp.revenue_formatted or leader_comp.units_sold_formatted or str(leader_comp.records_count)})"
            + (f" representing {leader_comp.market_share_pct}% of tracked volume" if leader_comp.market_share_pct else "")
            + f", compared to '{trailing_comp.name}' ({trailing_comp.revenue_formatted or trailing_comp.units_sold_formatted or str(trailing_comp.records_count)})."
        ),
    )

    # 3. Build Factual Competitive Gaps
    market_gaps: List[MarketGapSchema] = []
    
    # Revenue Gap (Leader vs Trailing)
    if rev_col and leader_comp.revenue and trailing_comp.revenue is not None:
        rev_gap = round(leader_comp.revenue - trailing_comp.revenue, 2)
        rev_gap_fmt = format_metric_display(rev_gap, unit=dataset_currency, semantic_type="currency")
        pct_diff = round(((leader_comp.revenue - trailing_comp.revenue) / abs(trailing_comp.revenue)) * 100, 1) if trailing_comp.revenue != 0 else 100.0
        
        market_gaps.append(
            MarketGapSchema(
                title=f"Reported Revenue Gap: '{leader_comp.name}' vs '{trailing_comp.name}'",
                gap_type="revenue_gap",
                metric_name=primary_metric_label,
                leader_entity=leader_comp.name,
                trailing_entity=trailing_comp.name,
                absolute_difference=rev_gap,
                formatted_difference=rev_gap_fmt,
                pct_difference=pct_diff,
                factual_statement=(
                    f"'{leader_comp.name}' reported {leader_comp.revenue_formatted} in revenue, "
                    f"which is {rev_gap_fmt} (+{pct_diff}%) higher than '{trailing_comp.name}' ({trailing_comp.revenue_formatted})."
                ),
                evidence=f"Leader: {leader_comp.revenue_formatted} | Lowest: {trailing_comp.revenue_formatted} | Delta: {rev_gap_fmt}",
            )
        )

    # Profit Margin Gap
    if profit_col and len(competitors) >= 2:
        valid_margins = [c for c in competitors if c.profit_margin_pct is not None]
        if len(valid_margins) >= 2:
            highest_margin_comp = max(valid_margins, key=lambda x: x.profit_margin_pct or -999)
            lowest_margin_comp = min(valid_margins, key=lambda x: x.profit_margin_pct or 999)
            margin_gap = round((highest_margin_comp.profit_margin_pct or 0.0) - (lowest_margin_comp.profit_margin_pct or 0.0), 1)
            
            market_gaps.append(
                MarketGapSchema(
                    title=f"Operating Profit Margin Gap: '{highest_margin_comp.name}' vs '{lowest_margin_comp.name}'",
                    gap_type="margin_gap",
                    metric_name="Profit Margin %",
                    leader_entity=highest_margin_comp.name,
                    trailing_entity=lowest_margin_comp.name,
                    absolute_difference=margin_gap,
                    formatted_difference=f"{margin_gap:+.1f}% pts",
                    pct_difference=margin_gap,
                    factual_statement=(
                        f"'{highest_margin_comp.name}' achieved a profit margin of {highest_margin_comp.profit_margin_pct}%, "
                        f"leading '{lowest_margin_comp.name}' ({lowest_margin_comp.profit_margin_pct}%) by {margin_gap:.1f} percentage points."
                    ),
                    evidence=f"Highest Margin: {highest_margin_comp.profit_margin_pct}% | Lowest Margin: {lowest_margin_comp.profit_margin_pct}%",
                )
            )

    # 4. Strategic Recommendations / Actionable Opportunities
    strategic_recs: List[MarketStrategyRecommendationSchema] = []

    if rev_col and leader_comp.revenue and len(competitors) >= 2:
        strategic_recs.append(
            MarketStrategyRecommendationSchema(
                title="Evaluate Revenue Growth Opportunities Against Market Leader",
                category="growth_expansion",
                priority="high",
                metric=primary_metric_label,
                comparison=f"Leader '{leader_comp.name}' generated {leader_comp.revenue_formatted} vs cohort average of {avg_rev_fmt}.",
                evidence=f"Leader revenue: {leader_comp.revenue_formatted} ({leader_comp.market_share_pct or 'N/A'}% reported share).",
                suggested_investigation="Review product lines, regional distribution, and sales channel mix to identify specific volume or expansion gaps.",
                limitation="External market factors not captured in this dataset (e.g. ad spend, offline channels) may influence competitor revenue.",
            )
        )

    if profit_col and len(competitors) >= 2 and any(c.profit_margin_pct is not None for c in competitors):
        strategic_recs.append(
            MarketStrategyRecommendationSchema(
                title="Investigate Cost Structure & Operational Margins",
                category="cost_efficiency",
                priority="medium",
                metric="Operating Margin",
                comparison="Differences observed in reported competitor profit margins across the dataset.",
                evidence="Competitor margins range across reported entities.",
                suggested_investigation="Analyze COGS, supplier contracts, discounting policies, and fulfillment overhead to improve operational margin efficiency.",
                limitation="Competitor cost accounting methodologies may vary.",
            )
        )

    # 5. Time-Series Comparison (if date column exists)
    time_comparison = None
    date_col = _find_date_column(target_df, target_profiles)
    if date_col and rev_col:
        try:
            parsed_dates = pd.to_datetime(target_df[date_col], errors="coerce")
            valid_mask = parsed_dates.notna()
            if valid_mask.sum() >= 6:
                df_timed = target_df[valid_mask].copy()
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
                    top_names = [c.name for c in competitors[:5]]
                    df_top = df_timed[df_timed[competitor_col].astype(str).isin(top_names)]
                    p_agg = df_top.groupby(["_period", df_top[competitor_col].astype(str)])[rev_col].sum().unstack(fill_value=0.0)

                    segment_series = []
                    growth_rates = {}
                    for c_name in top_names:
                        if c_name in p_agg.columns:
                            vals = [round(float(v), 2) for v in p_agg[c_name].values]
                            segment_series.append({"segment": c_name, "values": vals})
                            non_zeros = [(idx, v) for idx, v in enumerate(vals) if v > 0]
                            if len(non_zeros) >= 2:
                                first_val = non_zeros[0][1]
                                last_val = non_zeros[-1][1]
                                gr = round(((last_val - first_val) / first_val) * 100, 1)
                                growth_rates[c_name] = gr

                    fastest = max(growth_rates.items(), key=lambda x: x[1]) if growth_rates else None
                    slowest = min(growth_rates.items(), key=lambda x: x[1]) if growth_rates else None
                    
                    time_comparison = CompetitionTimeComparisonSchema(
                        is_available=True,
                        time_column=date_col,
                        granularity=gran,
                        period_labels=periods,
                        segment_series=segment_series,
                        fastest_growing=fastest[0] if fastest else None,
                        fastest_growing_rate=fastest[1] if fastest else None,
                        most_declining=slowest[0] if slowest else None,
                        most_declining_rate=slowest[1] if slowest else None,
                        summary=f"Tracked competitor revenue over {len(periods)} {gran.lower()} periods.",
                    )
        except Exception as e:
            logger.debug("Competitor time comparison encountered error: %s", e)
            time_comparison = None

    if not time_comparison:
        time_comparison = CompetitionTimeComparisonSchema(
            is_available=False,
            summary="Period-over-period market growth analysis is unavailable (no chronological date column detected).",
        )

    limitations = [
        "Tracked Competitors Only: Market share and volume rankings reflect only the competitors included in this uploaded dataset.",
        "Internal Data Consistency: Figures are based strictly on reported values and do not constitute certified global market audits.",
        "No Causal Guarantees: Strategic recommendations highlight observed metric gaps; business improvements require holistic market investigation.",
    ]

    methodology = [
        f"Competitor Entity: '{competitor_col}' ({humanize_column_name(competitor_col)}) with {total_competitors} distinct market entities.",
        f"Primary Measure: '{primary_metric_col}' ({primary_metric_label}).",
        "Market Share Calculation: Computed as (Competitor Revenue / Total Tracked Market Revenue) * 100.",
    ]

    return CompetitionIntelligenceResponse(
        dataset_id=dataset_id,
        is_available=True,
        market_data_status="market_data_detected",
        status_title="Market Competition Analysis",
        domain_id=domain_id,
        domain_name=domain_name,
        currency_symbol=dataset_currency,
        has_external_benchmark=has_benchmark,
        benchmark_filename=benchmark_filename,
        overview=overview,
        competitors=competitors,
        market_gaps=market_gaps,
        strategic_recommendations=strategic_recs,
        time_comparison=time_comparison,
        missing_requirements=[],
        required_market_fields=REQUIRED_MARKET_FIELDS_GUIDE,
        market_limitations=limitations,
        methodology_notes=methodology,
        analyzed_at=datetime.now(timezone.utc).isoformat(),
    )
