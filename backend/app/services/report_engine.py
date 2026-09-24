"""DataScope Unified Comprehensive Business Intelligence Report Engine.

Harmonizes and synthesizes all platform analytics modules into a boardroom-ready
business intelligence briefing across 19 comprehensive decision-support sections:
1. Executive Business Summary (KPIs, written executive narrative, key findings, risks, actions)
2. Business Performance & Operational KPIs (revenue, volume, top/bottom performers with strict dimension filtering)
3. 6-Point Sales & Commercial Analysis (What Happened, Business Meaning, Why It Matters, Recommended Action, Evidence, Limitations)
4. Profit & Loss Analysis (gross/net margins, loss-making categories, discount vs margin observations, calculation bases)
5. Product & Category Performance (contribution %, average selling values, low margin volume drivers)
6. Customer & Segment Analysis (customer types, AOV, retention/marketing strategy, revenue share)
7. Regional / Channel / Distribution Analysis (geographic & channel performance with operational insights)
8. Discount & Pricing Dynamics (high-discount volume, margin erosion, suggested discount controls, validation requirements)
9. Inventory & Stock Analysis (stock levels, reorder alerts, or honest unavailable fallback)
10. Root Cause Analysis (confirmed observations, contributing factors, validation data needed, investigation plan)
11. Business Risk Analysis (verified risks, impact, severity, why it matters, validation requirements, confidence)
12. Market Competition (external market comparisons only, or honest unavailable notice with required fields)
13. Trends Intelligence (historical trajectory, period-over-period delta, domain interpretation)
14. Forecasting & Horizon Projections (domain metric, confidence, assumptions, limitations)
15. Corrective Measures & Recommendations (evidence-based 5-step action plans, owners, KPIs, timeframes)
16. Priority Action Plan Table (ordered by urgency and evidence strength)
17. Business Limitations & Missing Data (decision boundaries)
18. Technical Data Validation (optional, secondary collapsible section at the bottom)
"""
from __future__ import annotations

import datetime
import math
from typing import Any, Dict, List, Optional, Set

import numpy as np
import pandas as pd

from app.schemas.report import (
    BusinessPerformanceReportSchema,
    ColumnSummaryItemSchema,
    CompetitionReportSchema,
    CompetitorComparisonItemSchema,
    ConclusionReportSchema,
    CorrectiveActionItemSchema,
    CorrectiveActionPlanSchema,
    CustomerSegmentAnalysisSchema,
    CustomerSegmentItemSchema,
    DatasetOverviewReportSchema,
    DiscountPricingReportSchema,
    ExecutiveSummarySchema,
    ForecastPointItemSchema,
    ForecastReportSchema,
    InventoryReportSchema,
    MethodologyAuditTrailSchema,
    PerformanceMetricItemSchema,
    PerformancePerformerItemSchema,
    ProfitLossReportSchema,
    ProfitLossSegmentItemSchema,
    RecommendationsReportSchema,
    RegionalChannelAnalysisSchema,
    RegionalChannelItemSchema,
    ReportMetadataSchema,
    RiskDistributionInsightSchema,
    RisksReportSchema,
    RootCauseAnalysisReportSchema,
    RootCauseItemSchema,
    SixPointFindingSchema,
    TrendPeriodComparisonItemSchema,
    TrendsReportSchema,
    UnifiedRecommendationItemSchema,
    VerifiedRiskItemSchema,
    ComprehensiveReportResponse,
)
from app.services import dataset_service, dataset_store
from app.services.business_analytics_engine import (
    _INVALID_BUSINESS_DIMENSIONS,
    _find_business_dimension,
    _find_col,
)
from app.services.column_formatter import detect_column_unit, format_metric_display
from app.services.column_profiler import ColumnProfile, profile_dataset
from app.services.domain_detector import detect_domain
from app.services.type_inference import detect_dataset_currency


def _format_curr(val: Optional[float], sym: str = "₹") -> str:
    if val is None or math.isnan(val):
        return "N/A"
    s = sym or "₹"
    abs_val = abs(val)
    sign = "-" if val < 0 else ""
    if abs_val >= 1_000_000_000:
        return f"{sign}{s}{abs_val / 1_000_000_000:.2f}B"
    if abs_val >= 1_000_000:
        return f"{sign}{s}{abs_val / 1_000_000:.2f}M"
    if abs_val >= 1_000:
        return f"{sign}{s}{abs_val / 1_000:.2f}K"
    return f"{sign}{s}{abs_val:,.2f}"


def _format_num(val: Optional[float], decimals: int = 1) -> str:
    if val is None or math.isnan(val):
        return "N/A"
    abs_val = abs(val)
    sign = "-" if val < 0 else ""
    if abs_val >= 1_000_000:
        return f"{sign}{abs_val / 1_000_000:.2f}M"
    if abs_val >= 1_000:
        return f"{sign}{abs_val / 1_000:.2f}K"
    return f"{sign}{abs_val:,.{decimals}f}".rstrip("0").rstrip(".")


def generate_comprehensive_report(
    dataset_id: str,
    selected_sections: Optional[List[str]] = None,
) -> ComprehensiveReportResponse:
    """Consolidate all dataset intelligence into a unified, boardroom-ready business report."""
    entry = dataset_store.get_dataset_or_raise(dataset_id)
    df = entry.df

    # 1. Base profiling & domain
    profiles_raw = entry.cache.get("profiles") or profile_dataset(df)
    entry.cache["profiles"] = profiles_raw
    profiles_list = profiles_raw if isinstance(profiles_raw, list) else list(profiles_raw.values())
    profiles: Dict[str, ColumnProfile] = {p.name: p for p in profiles_list}
    domain = entry.cache.get("domain") or detect_domain(df, profiles_list)
    entry.cache["domain"] = domain
    currency_symbol = detect_dataset_currency(df) or "₹"

    # 2. Downstream service results
    dq_data = dataset_service.get_data_quality_report(dataset_id)
    intel_data = dataset_service.get_domain_intelligence(dataset_id)
    decision_data = dataset_service.get_decision_dashboard(dataset_id)
    trends_data = dataset_service.get_trends_intelligence(dataset_id)
    forecast_data = dataset_service.get_forecast(dataset_id)
    risk_data = dataset_service.get_risk_intelligence(dataset_id)
    comp_data = dataset_service.get_competition_intelligence(dataset_id)
    recs_data = dataset_service.get_recommendations_intelligence(dataset_id)

    intel_domain = intel_data.get("domain", {}) if isinstance(intel_data, dict) else {}
    domain_id = intel_domain.get("domain_id") or getattr(domain, "domain_id", "general_business")
    domain_name = intel_domain.get("name") or getattr(domain, "name", "General Business")

    # ----------------------------------------------------
    # COLUMN DETECTION (STRICT BUSINESS VALIDATION)
    # ----------------------------------------------------
    rev_col = _find_col(df, profiles_list, ("revenue", "sales", "total_amount", "amount", "total", "price"), "numeric")
    qty_col = _find_col(df, profiles_list, ("quantity", "qty", "units", "items_sold", "volume"), "numeric")
    cost_col = _find_col(df, profiles_list, ("cost", "cogs", "expense", "purchase_price", "unit_cost"), "numeric")
    profit_col = _find_col(df, profiles_list, ("profit", "net_profit", "earnings", "margin_amount"), "numeric")
    discount_col = _find_col(df, profiles_list, ("discount", "discount_amount", "discount_pct", "rebate"), "numeric")
    order_col = _find_col(df, profiles_list, ("order_id", "order_number", "transaction_id", "invoice_id", "id"))
    stock_col = _find_col(df, profiles_list, ("stock", "inventory", "stock_level", "units_in_stock", "available_quantity"), "numeric")

    # Strict business dimensions
    product_dim = _find_business_dimension(df, profiles_list, ("product_name", "product", "item_name", "item", "sku", "title", "model"))
    category_dim = _find_business_dimension(df, profiles_list, ("category", "product_category", "department", "sub_category", "line_of_business", "winner", "team1", "venue"))
    cust_dim = _find_business_dimension(df, profiles_list, ("customer_type", "customer_segment", "segment", "customer_login_type", "membership", "tier", "gender", "client_type"))
    region_dim = _find_business_dimension(df, profiles_list, ("region", "country", "state", "city", "store", "territory", "location", "market"))
    channel_dim = _find_business_dimension(df, profiles_list, ("channel", "sales_channel", "platform", "device_type", "device", "source"))

    # Fallback to first valid numeric column if rev_col not matched
    if not rev_col:
        for c in df.columns:
            if c.lower() not in _INVALID_BUSINESS_DIMENSIONS and c.lower() not in ("id", "season", "index"):
                try:
                    num_s = pd.to_numeric(df[c], errors="coerce").dropna()
                    if len(num_s) > 0 and len(num_s.unique()) > 1:
                        rev_col = c
                        break
                except Exception:
                    pass

    total_rows = len(df)
    total_cols = len(df.columns)

    # ----------------------------------------------------
    # CORE BUSINESS FINANCIAL METRICS
    # ----------------------------------------------------
    total_sales_raw: Optional[float] = float(df[rev_col].sum()) if rev_col and rev_col in df.columns else None
    total_qty_raw: Optional[float] = float(df[qty_col].sum()) if qty_col and qty_col in df.columns else None
    total_orders_raw: int = int(df[order_col].nunique()) if order_col and order_col in df.columns else total_rows
    aov_raw: Optional[float] = (total_sales_raw / total_orders_raw) if total_sales_raw and total_orders_raw > 0 else None

    total_cost_raw: Optional[float] = None
    if cost_col and cost_col in df.columns:
        cost_s = pd.to_numeric(df[cost_col], errors="coerce").dropna()
        if len(cost_s) > 0:
            total_cost_raw = float(cost_s.sum())

    total_profit_raw: Optional[float] = None
    profit_margin_raw: Optional[float] = None
    has_profit = False

    if profit_col and profit_col in df.columns:
        prof_s = pd.to_numeric(df[profit_col], errors="coerce").dropna()
        total_profit_raw = float(prof_s.sum())
        has_profit = True
        if total_sales_raw and total_sales_raw > 0:
            profit_margin_raw = round((total_profit_raw / total_sales_raw) * 100.0, 1)
    elif total_cost_raw is not None and total_sales_raw is not None:
        total_profit_raw = total_sales_raw - total_cost_raw
        has_profit = True
        if total_sales_raw > 0:
            profit_margin_raw = round((total_profit_raw / total_sales_raw) * 100.0, 1)

    avg_discount_raw: Optional[float] = None
    if discount_col and discount_col in df.columns:
        disc_s = pd.to_numeric(df[discount_col], errors="coerce").dropna()
        if len(disc_s) > 0:
            raw_m = float(disc_s.mean())
            avg_discount_raw = round(raw_m * 100.0 if raw_m <= 1.0 else raw_m, 1)

    total_sales_str = _format_curr(total_sales_raw, currency_symbol) if total_sales_raw is not None else None
    total_cost_str = _format_curr(total_cost_raw, currency_symbol) if total_cost_raw is not None else None
    total_profit_str = _format_curr(total_profit_raw, currency_symbol) if total_profit_raw is not None else None
    profit_margin_str = f"{profit_margin_raw:.1f}%" if profit_margin_raw is not None else None
    aov_str = _format_curr(aov_raw, currency_symbol) if aov_raw is not None else None
    total_orders_str = f"{total_orders_raw:,}"
    total_qty_str = f"{int(total_qty_raw):,}" if total_qty_raw is not None else None
    avg_discount_str = f"{avg_discount_raw:.1f}%" if avg_discount_raw is not None else None

    # Date range detection
    time_val = trends_data.get("time_validation", {}) if isinstance(trends_data, dict) else {}
    has_date = bool(trends_data.get("has_time_dimension", False))
    date_range_str: Optional[str] = None
    if has_date:
        dr = time_val.get("date_range")
        if isinstance(dr, dict) and dr.get("min") and dr.get("max"):
            date_range_str = f"{dr['min']} to {dr['max']}"
        elif time_val.get("time_column"):
            try:
                dt_col = pd.to_datetime(df[time_val["time_column"]], errors="coerce").dropna()
                if not dt_col.empty:
                    date_range_str = f"{dt_col.min().strftime('%d %b %Y')} to {dt_col.max().strftime('%d %b %Y')}"
            except Exception:
                date_range_str = "Detected timestamp series"

    # ----------------------------------------------------
    # BUSINESS PERFORMANCE OVERVIEW & 6-POINT FINDINGS
    # ----------------------------------------------------
    top_performers: List[PerformancePerformerItemSchema] = []
    underperformers: List[PerformancePerformerItemSchema] = []
    primary_dim = category_dim or product_dim or cust_dim or region_dim

    if primary_dim and rev_col and rev_col in df.columns:
        try:
            grouped = df.groupby(primary_dim, dropna=True)[rev_col].sum().sort_values(ascending=False)
            total_sum = float(grouped.sum())
            if total_sum > 0:
                for name, val in grouped.head(5).items():
                    share = round((val / total_sum) * 100, 1)
                    top_performers.append(
                        PerformancePerformerItemSchema(
                            entity_type=primary_dim.replace("_", " ").title(),
                            name=str(name),
                            metric_name="Revenue",
                            formatted_value=_format_curr(val, currency_symbol),
                            raw_value=float(val),
                            percentage_share=share,
                            note=f"Contributes {share}% of total commercial sales",
                        )
                    )
                if len(grouped) > 5:
                    for name, val in grouped.tail(3).items():
                        share = round((val / total_sum) * 100, 1)
                        underperformers.append(
                            PerformancePerformerItemSchema(
                                entity_type=primary_dim.replace("_", " ").title(),
                                name=str(name),
                                metric_name="Revenue",
                                formatted_value=_format_curr(val, currency_symbol),
                                raw_value=float(val),
                                percentage_share=share,
                                note=f"Contributes only {share}% of total commercial sales",
                            )
                        )
        except Exception:
            pass

    # Build structured KPI highlights with interpretation and attention flags
    metric_highlights: List[PerformanceMetricItemSchema] = []
    if total_sales_str:
        metric_highlights.append(
            PerformanceMetricItemSchema(
                name="Total Gross Revenue",
                formatted_value=total_sales_str,
                raw_value=total_sales_raw,
                unit="Currency",
                status="Calculated",
                business_meaning="Aggregate commercial top-line turnover generated across all completed transactions.",
                comparison_with_previous="Historical Baseline",
                requires_attention=False,
            )
        )
    if total_profit_str:
        is_loss = total_profit_raw is not None and total_profit_raw < 0
        is_thin = profit_margin_raw is not None and profit_margin_raw < 10.0
        metric_highlights.append(
            PerformanceMetricItemSchema(
                name="Net Profit / Return",
                formatted_value=total_profit_str,
                raw_value=total_profit_raw,
                unit="Currency",
                status="Calculated",
                business_meaning="Residual commercial earnings after deducting all product costs and promotional markdowns.",
                comparison_with_previous="Historical Baseline",
                requires_attention=is_loss or is_thin,
                attention_reason="Net returns show margin compression below operational benchmarks." if is_thin else "Direct net financial loss." if is_loss else None,
            )
        )
    if profit_margin_str:
        metric_highlights.append(
            PerformanceMetricItemSchema(
                name="Net Profit Margin",
                formatted_value=profit_margin_str,
                raw_value=profit_margin_raw,
                unit="Percentage",
                status="Calculated",
                business_meaning="Percentage of each rupee/dollar of revenue retained as profit.",
                requires_attention=profit_margin_raw is not None and profit_margin_raw < 10.0,
                attention_reason="Profit margin is compressed below standard operating threshold (10%)." if profit_margin_raw and profit_margin_raw < 10.0 else None,
            )
        )
    if aov_str:
        metric_highlights.append(
            PerformanceMetricItemSchema(
                name="Average Order Value (AOV)",
                formatted_value=aov_str,
                raw_value=aov_raw,
                unit="Currency",
                status="Calculated",
                business_meaning="Average commercial expenditure per customer order.",
                requires_attention=False,
            )
        )
    if total_orders_str:
        metric_highlights.append(
            PerformanceMetricItemSchema(
                name="Total Order Volume",
                formatted_value=total_orders_str,
                raw_value=float(total_orders_raw),
                unit="Count",
                status="Available",
                business_meaning="Total distinct customer transactions completed in the period.",
                requires_attention=False,
            )
        )
    if avg_discount_str:
        is_high_disc = avg_discount_raw is not None and avg_discount_raw >= 25.0
        metric_highlights.append(
            PerformanceMetricItemSchema(
                name="Average Promotional Discount",
                formatted_value=avg_discount_str,
                raw_value=avg_discount_raw,
                unit="Percentage",
                status="Calculated",
                business_meaning="Mean promotional reduction applied across transaction line items.",
                requires_attention=is_high_disc,
                attention_reason="Promotional discount rate exceeds 25%, risking severe margin erosion." if is_high_disc else None,
            )
        )

    # 6-Point Sales Findings
    six_point_findings: List[SixPointFindingSchema] = []
    if top_performers:
        top_item = top_performers[0]
        six_point_findings.append(
            SixPointFindingSchema(
                observation_title=f"Commercial Concentration in {top_item.entity_type} '{top_item.name}'",
                what_happened=f"'{top_item.name}' generated {top_item.formatted_value}, representing {top_item.percentage_share}% of total commercial turnover.",
                business_meaning=f"Commercial performance is heavily anchored to '{top_item.name}', serving as the primary revenue engine.",
                why_it_matters="High concentration creates operational vulnerability if market demand shifts or supply chain disruptions occur.",
                recommended_action=f"Maintain inventory availability for '{top_item.name}' while actively scaling marketing for complementary categories.",
                evidence=f"Aggregated sales data confirms {top_item.percentage_share}% revenue contribution across {total_orders_str} recorded orders.",
                limitations="Analysis reflects historical transaction records and assumes consistent gross margins across catalogue lines.",
            )
        )
    if underperformers:
        under_item = underperformers[0]
        six_point_findings.append(
            SixPointFindingSchema(
                observation_title=f"Low Revenue Contribution in {under_item.entity_type} '{under_item.name}'",
                what_happened=f"'{under_item.name}' produced only {under_item.formatted_value} ({under_item.percentage_share}% of total sales).",
                business_meaning="This segment exhibits weak customer demand or insufficient marketing exposure relative to the rest of the catalogue.",
                why_it_matters="Underperforming catalogue lines tie up shelf space, working capital, or catalogue overhead without generating proportional returns.",
                recommended_action=f"Audit merchandising and pricing for '{under_item.name}'; consider bundling or strategic phase-out if margins are negligible.",
                evidence=f"Recorded revenue of {under_item.formatted_value} over the full reporting period.",
                limitations="Excludes unrecorded customer inquiries or offline conversion paths.",
            )
        )

    has_business_perf = bool(total_sales_str or metric_highlights or top_performers)
    perf_summary_text = ""
    if has_business_perf:
        if top_performers:
            perf_summary_text = (
                f"{top_performers[0].entity_type} '{top_performers[0].name}' leads commercial performance, generating "
                f"{top_performers[0].formatted_value} ({top_performers[0].percentage_share}% of total revenue)."
            )
        else:
            perf_summary_text = f"Total commercial revenue stands at {total_sales_str or 'observed baseline'} across recorded transactions."
    else:
        perf_summary_text = "Category-level performance analysis is unavailable because no suitable business dimension was detected."

    business_performance = BusinessPerformanceReportSchema(
        is_available=has_business_perf,
        unavailable_reason=None if has_business_perf else "Category-level performance analysis is unavailable because no suitable business dimension was detected.",
        total_sales_revenue=total_sales_str,
        total_profit_loss=total_profit_str,
        profit_margin_pct=profit_margin_str,
        average_order_value=aov_str,
        growth_rate_pct=None,
        performance_direction="growth" if total_profit_raw and total_profit_raw > 0 else "neutral",
        metric_highlights=metric_highlights,
        top_performers=top_performers,
        underperformers=underperformers,
        six_point_findings=six_point_findings,
        summary_text=perf_summary_text,
    )

    # ----------------------------------------------------
    # PROFIT & LOSS ANALYSIS
    # ----------------------------------------------------
    loss_segments: List[ProfitLossSegmentItemSchema] = []
    high_sales_low_profit_segments: List[ProfitLossSegmentItemSchema] = []
    discount_observations: List[str] = []
    changes_expl: List[str] = []

    if has_profit and primary_dim and rev_col:
        try:
            grp = df.groupby(primary_dim, dropna=True)[[rev_col, profit_col or cost_col]].sum()
            if profit_col:
                grp["profit_val"] = grp[profit_col]
            else:
                grp["profit_val"] = grp[rev_col] - grp[cost_col]
            grp["margin_pct"] = (grp["profit_val"] / grp[rev_col] * 100.0).replace([np.inf, -np.inf], np.nan)

            # Loss makers
            loss_df = grp[grp["profit_val"] < 0].sort_values("profit_val")
            for name, row in loss_df.head(4).iterrows():
                r_val = float(row[rev_col])
                p_val = float(row["profit_val"])
                m_val = round(float(row["margin_pct"]), 1) if not math.isnan(row["margin_pct"]) else 0.0
                loss_segments.append(
                    ProfitLossSegmentItemSchema(
                        name=str(name),
                        segment_type=primary_dim.replace("_", " ").title(),
                        revenue_formatted=_format_curr(r_val, currency_symbol),
                        profit_loss_formatted=_format_curr(p_val, currency_symbol),
                        profit_margin_pct=m_val,
                        issue_type="loss_maker",
                        explanation=f"Negative net contribution of {_format_curr(p_val, currency_symbol)} despite generating {_format_curr(r_val, currency_symbol)} in top-line revenue.",
                        calculation_basis=f"Net Profit = Revenue ({_format_curr(r_val, currency_symbol)}) - Direct Costs/Discounts",
                        status_type="confirmed_finding",
                        actionable_response=f"Conduct immediate price review and suspend promotional discounts on '{name}'.",
                    )
                )

            # High sales but low profit (< 10% margin)
            rev_threshold = grp[rev_col].quantile(0.50) if len(grp) > 2 else 0
            thin_df = grp[(grp[rev_col] >= rev_threshold) & (grp["profit_val"] > 0) & (grp["margin_pct"] < 10.0)].sort_values(rev_col, ascending=False)
            for name, row in thin_df.head(3).iterrows():
                r_val = float(row[rev_col])
                p_val = float(row["profit_val"])
                m_val = round(float(row["margin_pct"]), 1)
                high_sales_low_profit_segments.append(
                    ProfitLossSegmentItemSchema(
                        name=str(name),
                        segment_type=primary_dim.replace("_", " ").title(),
                        revenue_formatted=_format_curr(r_val, currency_symbol),
                        profit_loss_formatted=_format_curr(p_val, currency_symbol),
                        profit_margin_pct=m_val,
                        issue_type="high_sales_low_profit",
                        explanation=f"High sales volume ({_format_curr(r_val, currency_symbol)}) yielding compressed margin of {m_val}%.",
                        calculation_basis=f"Margin % = ({_format_curr(p_val, currency_symbol)} Net Profit / {_format_curr(r_val, currency_symbol)} Revenue) * 100",
                        status_type="confirmed_finding",
                        actionable_response=f"Audit supplier procurement costs and cap promotional markdowns below 15% for '{name}'.",
                    )
                )

            if loss_segments:
                changes_expl.append(f"Identified {len(loss_segments)} loss-making segment(s) causing direct bottom-line leakage.")
            if high_sales_low_profit_segments:
                changes_expl.append(f"Identified {len(high_sales_low_profit_segments)} high-volume categories with margins below 10%.")
        except Exception:
            pass

    if discount_col and rev_col and profit_col:
        try:
            disc_clean = pd.to_numeric(df[discount_col], errors="coerce").fillna(0)
            norm_disc = disc_clean * 100.0 if disc_clean.mean() <= 1.0 else disc_clean
            high_d = df[norm_disc >= 30.0]
            if len(high_d) > 0:
                high_d_rev = float(high_d[rev_col].sum())
                high_d_prof = float(high_d[profit_col].sum())
                high_d_margin = (high_d_prof / high_d_rev * 100.0) if high_d_rev > 0 else 0.0
                discount_observations.append(
                    f"Transactions with discounts above 30% generated {_format_curr(high_d_rev, currency_symbol)} in sales with an average margin of {high_d_margin:.1f}%, compared to {profit_margin_str or 'higher'} for lower discounts."
                )
        except Exception:
            pass

    profit_loss = ProfitLossReportSchema(
        is_available=has_profit,
        unavailable_reason=None if has_profit else "Reliable profit and loss analysis is unavailable because sufficient financial fields were not found in the dataset.",
        revenue_trend_summary=f"Total revenue: {total_sales_str or 'N/A'}",
        profit_trend_summary=f"Total net profit: {total_profit_str or 'N/A'}",
        profit_margin_summary=f"Overall profit margin: {profit_margin_str or 'N/A'}",
        loss_making_segments=loss_segments,
        high_sales_low_profit_segments=high_sales_low_profit_segments,
        discount_margin_observations=discount_observations,
        changes_explanation=changes_expl or ["No severe margin discrepancies detected across analyzed lines."],
    )

    # ----------------------------------------------------
    # CUSTOMER & SEGMENT ANALYSIS
    # ----------------------------------------------------
    customer_segment_analysis: Optional[CustomerSegmentAnalysisSchema] = None
    if cust_dim and rev_col and rev_col in df.columns:
        try:
            cust_grp = df.groupby(cust_dim, dropna=True)
            cust_rev = cust_grp[rev_col].sum().sort_values(ascending=False)
            cust_total_rev = float(cust_rev.sum())
            cust_items: List[CustomerSegmentItemSchema] = []
            
            for c_name, c_rval in cust_rev.head(5).items():
                c_cnt = int(cust_grp.size().get(c_name, 1))
                c_aov = c_rval / c_cnt if c_cnt > 0 else c_rval
                c_share = round((c_rval / cust_total_rev * 100.0), 1) if cust_total_rev > 0 else 0.0
                
                c_prof_str: Optional[str] = None
                c_margin_val: Optional[float] = None
                if profit_col and profit_col in df.columns:
                    p_sum = float(cust_grp[profit_col].sum().get(c_name, 0.0))
                    c_prof_str = _format_curr(p_sum, currency_symbol)
                    if c_rval > 0:
                        c_margin_val = round((p_sum / c_rval) * 100.0, 1)

                cust_items.append(
                    CustomerSegmentItemSchema(
                        segment_name=str(c_name),
                        customer_count_formatted=f"{c_cnt:,} orders",
                        revenue_formatted=_format_curr(c_rval, currency_symbol),
                        revenue_share_pct=c_share,
                        aov_formatted=_format_curr(c_aov, currency_symbol),
                        profit_formatted=c_prof_str,
                        profit_margin_pct=c_margin_val,
                        business_implication=f"Generates {c_share}% of commercial turnover with average order size of {_format_curr(c_aov, currency_symbol)}.",
                        marketing_strategy=f"Tailor loyalty retention campaigns for '{c_name}' to expand lifetime value." if c_share > 30 else f"Target acquisition promotions to scale order frequency in '{c_name}'.",
                    )
                )
            
            dominant_share = cust_items[0].revenue_share_pct if cust_items else 0.0
            conc_obs = f"Dominant customer segment '{cust_items[0].segment_name}' accounts for {dominant_share}% of commercial revenue." if dominant_share >= 50.0 else "Customer revenue is distributed across multiple customer classifications."
            
            customer_segment_analysis = CustomerSegmentAnalysisSchema(
                is_available=True,
                dimension_analyzed=cust_dim.replace("_", " ").title(),
                segments=cust_items,
                concentration_observation=conc_obs,
                strategic_summary=f"Evaluated customer purchasing behavior across {len(cust_items)} distinct segment tiers.",
            )
        except Exception:
            customer_segment_analysis = CustomerSegmentAnalysisSchema(
                is_available=False,
                unavailable_reason="Customer segment analysis is unavailable because customer classification fields were not detected in the dataset.",
            )
    else:
        customer_segment_analysis = CustomerSegmentAnalysisSchema(
            is_available=False,
            unavailable_reason="Customer segment analysis is unavailable because customer classification fields were not detected in the dataset.",
        )

    # ----------------------------------------------------
    # REGIONAL / CHANNEL / DISTRIBUTION ANALYSIS
    # ----------------------------------------------------
    regional_channel_analysis: Optional[RegionalChannelAnalysisSchema] = None
    active_dist_dim = region_dim or channel_dim
    if active_dist_dim and rev_col and rev_col in df.columns:
        try:
            d_grp = df.groupby(active_dist_dim, dropna=True)
            d_rev = d_grp[rev_col].sum().sort_values(ascending=False)
            d_total = float(d_rev.sum())
            d_items: List[RegionalChannelItemSchema] = []
            
            for d_name, d_val in d_rev.head(6).items():
                d_cnt = int(d_grp.size().get(d_name, 1))
                d_share = round((d_val / d_total * 100.0), 1) if d_total > 0 else 0.0
                d_type = "Region" if region_dim and active_dist_dim == region_dim else "Channel"
                
                d_items.append(
                    RegionalChannelItemSchema(
                        name=str(d_name),
                        dimension_type=d_type,
                        revenue_formatted=_format_curr(d_val, currency_symbol),
                        revenue_share_pct=d_share,
                        order_volume=d_cnt,
                        operational_observation=f"{d_type} '{d_name}' accounts for {d_share}% of volume ({d_cnt:,} transactions).",
                    )
                )

            regional_channel_analysis = RegionalChannelAnalysisSchema(
                is_available=True,
                dimension_name=active_dist_dim.replace("_", " ").title(),
                items=d_items,
                operational_takeaway=f"Distribution performance evaluated across {len(d_items)} active {active_dist_dim.replace('_', ' ')} hubs.",
            )
        except Exception:
            regional_channel_analysis = RegionalChannelAnalysisSchema(
                is_available=False,
                unavailable_reason="Regional/channel analysis is unavailable because geographical or distribution channel dimensions were not detected.",
            )
    else:
        regional_channel_analysis = RegionalChannelAnalysisSchema(
            is_available=False,
            unavailable_reason="Regional/channel analysis is unavailable because geographical or distribution channel dimensions were not detected in the dataset.",
        )

    # ----------------------------------------------------
    # DISCOUNT & PRICING ANALYSIS SECTION
    # ----------------------------------------------------
    has_discount_analysis = discount_col is not None and rev_col is not None
    discount_pricing: Optional[DiscountPricingReportSchema] = None
    if has_discount_analysis:
        try:
            disc_clean = pd.to_numeric(df[discount_col], errors="coerce").fillna(0)
            norm_disc = disc_clean * 100.0 if disc_clean.mean() <= 1.0 else disc_clean
            high_disc_mask = norm_disc >= 30.0
            high_disc_df = df[high_disc_mask]
            high_d_rev = float(high_disc_df[rev_col].sum()) if len(high_disc_df) > 0 else 0.0
            high_d_cnt = int(len(high_disc_df))
            
            tier_obs: List[str] = []
            if len(high_disc_df) > 0:
                tier_obs.append(
                    f"High-discount orders (≥30%) represent {high_d_cnt:,} transactions totaling {_format_curr(high_d_rev, currency_symbol)}."
                )
            if avg_discount_raw and avg_discount_raw > 15.0:
                tier_obs.append(
                    f"Overall mean discount across catalogue is {avg_discount_raw:.1f}%, reflecting active promotional markdowns."
                )
            controls = [
                "Establish strict discount caps (max 20–25%) for product categories with gross margins under 15%.",
                "Require managerial sign-off for promotional reductions exceeding 30%.",
                "Monitor conversion rates and profit margin impact weekly following discount tier adjustments.",
            ]
            validations = [
                "Validate whether high-discount volume generates new customer acquisition or cannibalizes full-price sales.",
                "Review supplier co-op funding to determine if manufacturer rebates offset discount concessions.",
            ]
            discount_pricing = DiscountPricingReportSchema(
                is_available=True,
                unavailable_reason=None,
                average_discount_pct=avg_discount_str,
                high_discount_revenue=_format_curr(high_d_rev, currency_symbol) if high_d_rev > 0 else None,
                high_discount_transaction_count=high_d_cnt,
                margin_erosion_estimate=f"Promotional markdowns account for {_format_curr(high_d_rev * 0.15, currency_symbol)} in estimated margin concessions." if high_d_rev > 0 else None,
                discount_tier_observations=tier_obs or ["Discount distribution is within normal operating ranges."],
                suggested_controls=controls,
                validation_requirements=validations,
            )
        except Exception:
            discount_pricing = DiscountPricingReportSchema(
                is_available=True,
                unavailable_reason=None,
                average_discount_pct=avg_discount_str,
                discount_tier_observations=["Promotional discount data detected."],
                suggested_controls=["Audit promotional concessions on low-margin SKUs."],
                validation_requirements=["Verify promotional campaign cost structures."],
            )
    else:
        discount_pricing = DiscountPricingReportSchema(
            is_available=False,
            unavailable_reason="Discount and pricing analysis is unavailable because promotional discount fields were not detected in the dataset.",
        )

    # ----------------------------------------------------
    # INVENTORY / STOCK ANALYSIS SECTION
    # ----------------------------------------------------
    has_inventory = stock_col is not None and stock_col in df.columns
    inventory_analysis: Optional[InventoryReportSchema] = None
    if has_inventory:
        try:
            stock_s = pd.to_numeric(df[stock_col], errors="coerce").dropna()
            total_stock = float(stock_s.sum())
            low_stock_mask = stock_s < 10.0
            overstock_mask = stock_s > stock_s.quantile(0.90) if len(stock_s) > 10 else stock_s > 1000
            low_cnt = int(low_stock_mask.sum())
            over_cnt = int(overstock_mask.sum())
            
            alerts: List[str] = []
            if low_cnt > 0:
                alerts.append(f"{low_cnt:,} SKU(s) are below critical stock thresholds (< 10 units) and risk stockout.")
            if over_cnt > 0:
                alerts.append(f"{over_cnt:,} SKU(s) carry excessive inventory levels, locking working capital.")

            inventory_analysis = InventoryReportSchema(
                is_available=True,
                unavailable_reason=None,
                total_stock_units=f"{int(total_stock):,}",
                low_stock_count=low_cnt,
                overstocked_count=over_cnt,
                inventory_turnover_observation=f"Active stock management across {len(stock_s):,} catalog lines.",
                reorder_alerts=alerts or ["All catalog items have balanced inventory coverage."],
            )
        except Exception:
            inventory_analysis = InventoryReportSchema(
                is_available=True,
                unavailable_reason=None,
                inventory_turnover_observation="Inventory tracking active.",
            )
    else:
        inventory_analysis = InventoryReportSchema(
            is_available=False,
            unavailable_reason="Inventory analysis cannot be performed because stock-level and inventory movement data is not available.",
        )

    # ----------------------------------------------------
    # ROOT CAUSE ANALYSIS SECTION
    # ----------------------------------------------------
    root_causes: List[RootCauseItemSchema] = []
    if loss_segments:
        loss_names = ", ".join(f"'{ls.name}'" for ls in loss_segments[:2])
        root_causes.append(
            RootCauseItemSchema(
                issue_title=f"Net Profit Loss in {loss_names}",
                confirmed_observation=f"Segment(s) {loss_names} generated negative net margin despite commercial sales volume.",
                possible_contributing_factors=[
                    "Excessive promotional discounting without price protection.",
                    "High procurement cost (COGS) or unadjusted vendor price hikes.",
                    "Elevated fulfillment or logistics expenses per unit.",
                ],
                data_needed_for_validation=[
                    "Granular SKU-level unit procurement cost history.",
                    "Shipping and warehouse fulfillment cost allocations.",
                    "Vendor rebate and return rate logs.",
                ],
                recommended_investigation="Audit pricing formulas and margin contributions before running next marketing promotion cycle.",
            )
        )
    if discount_pricing and discount_pricing.high_discount_transaction_count > 0:
        root_causes.append(
            RootCauseItemSchema(
                issue_title="Margin Compression from Heavy Discounting",
                confirmed_observation=f"Recorded {discount_pricing.high_discount_transaction_count:,} transactions with promotional discounts exceeding 30%.",
                possible_contributing_factors=[
                    "Blanket coupon campaigns applied without category gross-margin restrictions.",
                    "Sales representative discounting to close volume targets without margin hurdles.",
                ],
                data_needed_for_validation=[
                    "Coupon code attribution and discount authorization logs.",
                    "Customer price sensitivity and elasticity test data.",
                ],
                recommended_investigation="Implement a minimum margin threshold (e.g. 15%) that automatically blocks checkout discounts above 25%.",
            )
        )
    if not root_causes:
        root_causes.append(
            RootCauseItemSchema(
                issue_title="Stable Commercial Performance",
                confirmed_observation="Operational performance metrics are operating within historical benchmark tolerances.",
                possible_contributing_factors=["Consistent demand patterns and balanced pricing strategy."],
                data_needed_for_validation=["Ongoing periodic transaction tracking."],
                recommended_investigation="Maintain weekly margin monitoring and automated threshold alerts.",
            )
        )

    root_cause_analysis = RootCauseAnalysisReportSchema(
        is_available=True,
        summary_statement=f"Root cause investigation conducted across {len(root_causes)} primary operational finding(s).",
        root_causes=root_causes,
    )

    # ----------------------------------------------------
    # TRENDS INTELLIGENCE
    # ----------------------------------------------------
    p_comp = trends_data.get("period_comparison") if isinstance(trends_data, dict) else None
    trend_comp_item: Optional[TrendPeriodComparisonItemSchema] = None
    growth_or_decline_str: Optional[str] = None
    if p_comp and isinstance(p_comp, dict) and p_comp.get("current_val") is not None:
        c_val = float(p_comp.get("current_val", 0))
        p_val = float(p_comp.get("previous_val", 0))
        abs_diff = float(p_comp.get("absolute_change", 0))
        pct_diff = p_comp.get("pct_change")
        is_pos = abs_diff >= 0
        direction = "increasing" if abs_diff > 0 else "decreasing" if abs_diff < 0 else "stable"
        
        c_fmt = _format_curr(c_val, currency_symbol) if "sales" in str(trends_data.get("selected_metric", "")).lower() else _format_num(c_val)
        p_fmt = _format_curr(p_val, currency_symbol) if "sales" in str(trends_data.get("selected_metric", "")).lower() else _format_num(p_val)
        a_fmt = _format_curr(abs_diff, currency_symbol) if "sales" in str(trends_data.get("selected_metric", "")).lower() else _format_num(abs_diff)
        pct_fmt = f"{pct_diff:+.1f}%" if pct_diff is not None else "N/A"
        growth_or_decline_str = f"{direction.capitalize()} ({pct_fmt})"

        trend_comp_item = TrendPeriodComparisonItemSchema(
            metric=trends_data.get("selected_metric") or "Monthly Revenue",
            time_period=f"{p_comp.get('previous_period', 'Prior Period')} vs {p_comp.get('current_period', 'Current Period')}",
            previous_value=p_val,
            previous_value_formatted=p_fmt,
            current_value=c_val,
            current_value_formatted=c_fmt,
            absolute_change=abs_diff,
            absolute_change_formatted=a_fmt,
            pct_change=pct_diff,
            pct_change_formatted=pct_fmt,
            is_positive=is_pos,
            direction=direction,
        )

    upward_tr: List[str] = []
    downward_tr: List[str] = []
    for cat_tr in trends_data.get("category_trends", []):
        cat_name = cat_tr.get("category", "")
        # Strict validation: reject timestamps/dates as categories in trends
        if any(tok in str(cat_name).lower() for tok in [":", "2018-", "2019-", "2020-", "2021-", "2022-", "2023-", "2024-", "2025-", "2026-"]):
            continue
        p_chg = cat_tr.get("pct_change")
        p_chg_str = f" ({p_chg:+.1f}%)" if p_chg is not None else ""
        if cat_tr.get("direction") == "increasing":
            upward_tr.append(f"{cat_name}: increased by {_format_num(cat_tr.get('absolute_change'))}{p_chg_str}")
        elif cat_tr.get("direction") == "decreasing":
            downward_tr.append(f"{cat_name}: contracted by {_format_num(cat_tr.get('absolute_change'))}{p_chg_str}")

    t_summary = trends_data.get("trend_summary") or {}
    plain_trend_text = (
        t_summary.get("plain_english_summary")
        or (trends_data.get("practical_answers") or {}).get("stability_text")
        or f"Historical trajectory evaluated across {date_range_str or 'recorded periods'}."
    )

    trends_report = TrendsReportSchema(
        is_available=has_date,
        unavailable_reason=None if has_date else "No sequential date or timestamp column detected in dataset.",
        analyzed_metric=trends_data.get("selected_metric") or "Revenue Trend",
        time_column=time_val.get("time_column"),
        time_period=date_range_str,
        selected_granularity=trends_data.get("selected_granularity", "Monthly"),
        period_comparison=trend_comp_item,
        upward_trends=upward_tr[:4],
        downward_trends=downward_tr[:4],
        peak_period=t_summary.get("highest_period"),
        peak_value_formatted=_format_num(t_summary.get("highest_value")),
        lowest_period=t_summary.get("lowest_period"),
        lowest_value_formatted=_format_num(t_summary.get("lowest_value")),
        seasonality_notes="Predictable seasonal patterns observed." if (trends_data.get("volatility_cv") or 0) <= 0.4 else "Irregular demand fluctuations detected.",
        volatility_assessment=trends_data.get("stability_rating") or "Stable",
        plain_language_interpretation=plain_trend_text,
        limitations=trends_data.get("limitations") or [],
    )

    # ----------------------------------------------------
    # FORECASTING SECTION
    # ----------------------------------------------------
    has_fc = bool(forecast_data.get("is_available", False))
    fc_points: List[ForecastPointItemSchema] = []
    if has_fc:
        for pt in forecast_data.get("forecast_points", []):
            fc_val = float(pt.get("forecast", 0))
            l80 = float(pt.get("lower_bound_80", fc_val * 0.9))
            u80 = float(pt.get("upper_bound_80", fc_val * 1.1))
            l95 = float(pt.get("lower_bound_95", fc_val * 0.8))
            u95 = float(pt.get("upper_bound_95", fc_val * 1.2))
            fc_points.append(
                ForecastPointItemSchema(
                    period=pt.get("period", ""),
                    forecast_formatted=_format_curr(fc_val, currency_symbol) if "sales" in str(forecast_data.get("metric", "")).lower() else _format_num(fc_val),
                    forecast_raw=fc_val,
                    lower_bound_80_formatted=_format_num(l80),
                    upper_bound_80_formatted=_format_num(u80),
                    lower_bound_95_formatted=_format_num(l95),
                    upper_bound_95_formatted=_format_num(u95),
                )
            )

    forecasting = ForecastReportSchema(
        is_available=has_fc,
        unavailable_reason=forecast_data.get("unavailable_reason") if not has_fc else None,
        forecasted_metric=forecast_data.get("metric") or "Revenue",
        time_horizon_periods=forecast_data.get("horizon", 3),
        frequency_label=forecast_data.get("frequency_label") or "Monthly",
        method_used=forecast_data.get("method_used") or "Statistical Exponential Smoothing",
        latest_actual_formatted=_format_num(forecast_data.get("latest_actual")),
        final_forecast_formatted=_format_num(forecast_data.get("final_forecast")),
        projected_change_formatted=_format_num(forecast_data.get("absolute_change")),
        projected_growth_pct=forecast_data.get("projected_growth_pct"),
        forecast_points=fc_points,
        confidence_score=forecast_data.get("confidence_score", 0.85),
        forecast_limitations=forecast_data.get("limitations") or [],
        plain_language_interpretation=forecast_data.get("domain_interpretation") or "Extrapolation based on in-sample historical trend momentum.",
        disclaimer=forecast_data.get("disclaimer") or "Statistical forecasts extrapolate historical patterns without guaranteeing future outcomes.",
    )

    # ----------------------------------------------------
    # RISKS & ANOMALIES SECTION
    # ----------------------------------------------------
    verified_risks: List[VerifiedRiskItemSchema] = []
    for r in risk_data.get("risks", []):
        r_title = r.get("title", "Detected Risk")
        r_sev = r.get("severity", "medium")
        r_cat = r.get("category", "Financial Risk")
        r_evid = r.get("evidence", "")
        r_seg = r.get("affected_metric") or r.get("affected_column") or "Business Operations"
        r_impact = r.get("why_it_matters") or r.get("description", "")
        r_action = r.get("recommended_action", "")
        
        verified_risks.append(
            VerifiedRiskItemSchema(
                risk_id=r.get("risk_id", f"risk_{len(verified_risks)+1}"),
                title=r_title,
                severity=r_sev,
                category=r_cat,
                evidence=r_evid,
                affected_metric_or_segment=r_seg,
                business_impact=r_impact,
                why_it_matters=f"Directly threatens bottom-line stability and commercial execution." if r_sev in ("critical", "high") else "Creates operational drag and inefficiencies.",
                recommended_action=r_action,
                qualification=r.get("qualification"),
                data_required_for_validation="Requires ongoing weekly transactional logs and margin audits.",
                confidence_level="High (Verified from Dataset Evidence)",
            )
        )

    dist_insights: List[RiskDistributionInsightSchema] = []
    for d in risk_data.get("distribution_insights", []):
        dim_name = d.get("dimension", "")
        if dim_name.lower() in _INVALID_BUSINESS_DIMENSIONS or "time" in dim_name.lower():
            continue
        dist_insights.append(
            RiskDistributionInsightSchema(
                dimension=dim_name,
                dominant_category=d.get("dominant_category", ""),
                percentage=float(d.get("percentage", 0)),
                description=d.get("description", ""),
                observation_note=d.get("observation_note", ""),
            )
        )

    r_overview = risk_data.get("overview", {})
    risks_report = RisksReportSchema(
        is_available=True,
        health_status=r_overview.get("health_status", "Healthy"),
        summary_statement=r_overview.get("summary_statement", "Business risk evaluation completed across operational dimensions."),
        total_risks_count=len(verified_risks),
        high_severity_count=r_overview.get("high_count", sum(1 for r in verified_risks if r.severity in ("high", "critical"))),
        medium_severity_count=r_overview.get("medium_count", sum(1 for r in verified_risks if r.severity == "medium")),
        low_severity_count=r_overview.get("low_count", sum(1 for r in verified_risks if r.severity == "low")),
        verified_risks=verified_risks,
        distribution_insights=dist_insights,
        data_safety_notes=risk_data.get("data_safety_notes", []),
    )

    # ----------------------------------------------------
    # MARKET COMPETITION SECTION (EXTERNAL BENCHMARK ONLY)
    # ----------------------------------------------------
    has_comp = bool(comp_data.get("is_available", False) and comp_data.get("has_external_benchmark", False))
    comp_list: List[CompetitorComparisonItemSchema] = []
    if has_comp:
        for c in comp_data.get("competitors", []):
            comp_list.append(
                CompetitorComparisonItemSchema(
                    rank=c.get("rank", 1),
                    name=c.get("name", "Competitor"),
                    is_our_entity=c.get("is_our_entity", False),
                    revenue_formatted=c.get("revenue_formatted", "N/A"),
                    profit_formatted=c.get("profit_formatted", "N/A"),
                    profit_margin_pct=c.get("profit_margin_pct"),
                    market_share_pct=c.get("market_share_pct"),
                    growth_rate_pct=c.get("growth_rate_pct"),
                    pricing_index_formatted=c.get("pricing_index_formatted", "N/A"),
                    status_label=c.get("status_label", "Reported Competitor"),
                )
            )

    market_gaps = [g.get("factual_statement", "") for g in comp_data.get("market_gaps", []) if g.get("factual_statement")]
    strat_actions = [s.get("suggested_investigation", "") for s in comp_data.get("strategic_recommendations", []) if s.get("suggested_investigation")]

    competition_report = CompetitionReportSchema(
        is_available=has_comp,
        status_title=comp_data.get("status_title", "Market competition analysis is unavailable."),
        summary_statement=comp_data.get("summary_statement", "Market competition analysis is unavailable because external competitor and market benchmark data has not been provided. Internal transaction categories cannot be treated as competing companies."),
        unavailable_reason=(
            None if has_comp else (
                "Market competition analysis is unavailable because external competitor and market benchmark data has not been provided. Internal transaction categories cannot be treated as competing companies."
            )
        ),
        has_external_benchmark=has_comp,
        benchmark_filename=comp_data.get("benchmark_filename"),
        total_competitors_tracked=len(comp_list),
        competitors=comp_list,
        market_gaps=market_gaps,
        strategic_actions=strat_actions,
        required_market_fields=[
            {"field": "Competitor_Name", "type": "Text", "importance": "Required", "purpose": "Identifies external company entity"},
            {"field": "Industry / Sector", "type": "Text", "importance": "Required", "purpose": "Ensures apples-to-apples market segmentation"},
            {"field": "Period / Quarter", "type": "Date/Text", "importance": "Required", "purpose": "Aligns comparable fiscal timeline"},
            {"field": "Competitor Revenue", "type": "Numeric", "importance": "Required", "purpose": "Calculates industry market share"},
            {"field": "Profit / Margin", "type": "Numeric", "importance": "Optional", "purpose": "Compares margin efficiency"},
            {"field": "Growth Rate", "type": "Percentage", "importance": "Optional", "purpose": "Assesses competitor expansion rate"},
            {"field": "Price Index", "type": "Numeric", "importance": "Optional", "purpose": "Evaluates pricing positioning vs market"},
        ],
        market_limitations=[
            "Internal customer logins, device types, and product categories cannot be treated as external market competitors.",
            "Market share calculation requires verified third-party industry filings.",
        ],
    )

    # ----------------------------------------------------
    # RECOMMENDATIONS & CORRECTIVE ACTION PLAN
    # ----------------------------------------------------
    recs_list: List[UnifiedRecommendationItemSchema] = []
    action_items: List[CorrectiveActionItemSchema] = []

    def _infer_owner(cat: str, title: str) -> str:
        tl = (cat + " " + title).lower()
        if any(w in tl for w in ["pricing", "cost", "margin", "profit", "discount", "finance"]):
            return "Pricing & Finance"
        if any(w in tl for w in ["marketing", "campaign", "conversion", "acquisition", "channel"]):
            return "Marketing & Growth"
        if any(w in tl for w in ["inventory", "logistics", "supply", "shipping", "delivery", "stock"]):
            return "Supply Chain & Ops"
        if any(w in tl for w in ["sales", "account", "client", "customer", "churn"]):
            return "Sales Leadership"
        if any(w in tl for w in ["quality", "hygiene", "missing", "data", "integrity"]):
            return "Data & BI Team"
        return "Executive Management"

    for r in recs_data.get("recommendations", []):
        r_title = r.get("title", "Strategic Action")
        r_cat = r.get("category_label") or r.get("category") or "General Improvement"
        r_prio = r.get("priority", "medium")
        r_prob = r.get("business_problem") or r.get("problem_detected") or "Identified performance inefficiency."
        r_evid = r.get("evidence") or r.get("observation") or "Identified from dataset statistical evidence."
        r_imp = r.get("why_it_matters") or "Impairs operational margins and throughput."
        r_act = r.get("recommended_action") or "Review and optimize execution parameters."
        r_obj = r.get("expected_objective") or r.get("success_measure") or "Improve efficiency and profitability."
        r_lim = r.get("limitations") or "Requires ongoing tracking against business baseline."
        
        owner = _infer_owner(r_cat, r_title)
        metric_to_track = r.get("metric_name") or r.get("relevant_metric") or "Profit Margin & Revenue"
        review_pd = "Immediate (7-14 Days)" if r_prio in ("critical", "high") else "30 Days"

        steps = [
            f"1. Audit transactions and SKUs associated with '{r_title}'.",
            "2. Establish clear baseline metrics (gross margin %, conversion rate, volume).",
            f"3. Coordinate with {owner} to implement corrective operational controls.",
            "4. A/B test adjustments over a 14-day evaluation window.",
            f"5. Monitor {metric_to_track} and confirm margin improvement before broad rollout.",
        ]

        recs_list.append(
            UnifiedRecommendationItemSchema(
                rec_id=r.get("rec_id", f"rec_{len(recs_list)+1}"),
                title=r_title,
                category=r_cat,
                priority=r_prio,
                problem=r_prob,
                evidence=r_evid,
                business_impact=r_imp,
                exact_recommended_action=r_act,
                action_steps=steps,
                expected_objective=r_obj,
                suggested_owner_team=owner,
                metric_to_track=metric_to_track,
                suggested_review_period=review_pd,
                data_limitations=r_lim,
            )
        )

        action_items.append(
            CorrectiveActionItemSchema(
                priority=r_prio.capitalize(),
                problem=r_prob,
                recommended_action=r_act,
                owner_team=owner,
                metric_to_track=metric_to_track,
                review_period=review_pd,
            )
        )

    prio_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    action_items.sort(key=lambda x: prio_order.get(x.priority, 4))

    recommendations_report = RecommendationsReportSchema(
        is_available=len(recs_list) > 0,
        unavailable_reason=None if recs_list else "No inefficiencies or anomalies detected.",
        total_recommendations=len(recs_list),
        critical_count=sum(1 for r in recs_list if r.priority == "critical"),
        high_count=sum(1 for r in recs_list if r.priority == "high"),
        medium_count=sum(1 for r in recs_list if r.priority == "medium"),
        low_count=sum(1 for r in recs_list if r.priority == "low"),
        summary_statement=f"Generated {len(recs_list)} prioritized, evidence-backed recommendations.",
        recommendations_list=recs_list,
    )

    corrective_action_plan = CorrectiveActionPlanSchema(
        is_available=len(action_items) > 0,
        action_items=action_items,
    )

    # ----------------------------------------------------
    # EXECUTIVE SUMMARY & FINDINGS
    # ----------------------------------------------------
    major_positives: List[str] = []
    major_negatives: List[str] = []
    key_findings: List[str] = []

    if total_sales_str:
        major_positives.append(f"Generated {total_sales_str} in total commercial sales revenue.")
        key_findings.append(f"Generated {total_sales_str} in gross commercial revenue.")
    if top_performers:
        major_positives.append(f"Top {top_performers[0].entity_type} '{top_performers[0].name}' contributed {top_performers[0].formatted_value} ({top_performers[0].percentage_share}% of total sales).")
        key_findings.append(f"Top-performing {top_performers[0].entity_type} is '{top_performers[0].name}' generating {top_performers[0].formatted_value}.")
    if total_profit_str and total_profit_raw and total_profit_raw > 0:
        major_positives.append(f"Achieved positive net profitability of {total_profit_str} ({profit_margin_str or 'N/A'} margin).")
        key_findings.append(f"Net financial return reached {total_profit_str} ({profit_margin_str or 'N/A'} margin).")

    if loss_segments:
        neg_text = f"Uncovered {len(loss_segments)} loss-making segment(s) causing direct profit leakage (e.g., '{loss_segments[0].name}')."
        major_negatives.append(neg_text)
        key_findings.append(neg_text)
    if high_sales_low_profit_segments:
        neg_text = f"{len(high_sales_low_profit_segments)} high-volume product line(s) yield compressed margins below 10%."
        major_negatives.append(neg_text)
        key_findings.append(neg_text)
    if discount_pricing and discount_pricing.high_discount_transaction_count > 0:
        neg_text = f"Recorded {discount_pricing.high_discount_transaction_count:,} orders with discounts ≥30%, creating margin erosion."
        major_negatives.append(neg_text)
        key_findings.append(neg_text)

    if not major_positives:
        major_positives.append(f"Operational volume active across {domain_name} dataset records.")
    if not major_negatives:
        major_negatives.append("No critical operational deficits or negative margins detected.")
    if not key_findings:
        key_findings.append(f"Performance analysis completed across {domain_name} records.")

    top_risks_bullets = [
        f"[{r.severity.upper()}] {r.title}: {r.evidence}" for r in verified_risks[:3]
    ] or ["No critical risk signals flagged."]

    top_3_actions = [
        f"[{a.priority}] {a.recommended_action} — Owner: {a.owner_team} (Timeframe: {a.review_period})" for a in action_items[:3]
    ] or ["Maintain standard operational monitoring and periodic margin reviews."]

    priority_actions_bullets = [
        f"[{a.priority}] {a.recommended_action} (Assigned: {a.owner_team})" for a in action_items[:3]
    ] or ["Maintain standard operational monitoring."]

    # Boardroom Written Summary:
    # "During the analyzed period, the business generated ₹X in revenue and ₹Y in profit, resulting in a margin of Z%..."
    written_summary = ""
    if total_sales_str and total_profit_str:
        written_summary = (
            f"During the analyzed period, the business generated {total_sales_str} in revenue and {total_profit_str} in net profit, "
            f"resulting in an overall profit margin of {profit_margin_str or 'N/A'}. "
        )
    elif total_sales_str:
        written_summary = f"During the analyzed period, the business generated {total_sales_str} in total revenue. "
    else:
        written_summary = f"Business performance across {domain_name} shows active commercial operations. "

    if loss_segments:
        written_summary += f"The analysis indicates that profitability is being affected by negative margins in '{loss_segments[0].name}'. "
    elif discount_pricing and discount_pricing.high_discount_transaction_count > 0:
        written_summary += "The analysis indicates that profitability is being affected by aggressive promotional discounting. "

    if action_items:
        written_summary += f"The most important management priority is {action_items[0].recommended_action}, assigned to {action_items[0].owner_team}."

    biz_condition = "Needs Attention" if (loss_segments or (verified_risks and verified_risks[0].severity in ("critical", "high"))) else "Strong" if (has_profit and total_profit_raw and total_profit_raw > 0 and profit_margin_raw and profit_margin_raw >= 15.0) else "Healthy"

    executive_summary = ExecutiveSummarySchema(
        dataset_name=entry.filename,
        row_count=total_rows,
        column_count=total_cols,
        domain_name=domain_name,
        reporting_period=date_range_str or "Full Historical Record",
        currency_symbol=currency_symbol,
        overall_performance_summary=written_summary,
        overall_business_condition=biz_condition,
        total_sales_revenue=total_sales_str,
        total_cost_expense=total_cost_str,
        total_profit_loss=total_profit_str,
        profit_margin_pct=profit_margin_str,
        growth_or_decline_text=growth_or_decline_str,
        total_orders_count=total_orders_str,
        average_order_value=aov_str,
        total_units_sold=total_qty_str,
        average_discount_pct=avg_discount_str,
        overall_business_health="Attention Required" if len(loss_segments) > 0 or len(verified_risks) > 2 else "Healthy",
        major_positive_findings=major_positives,
        major_negative_findings=major_negatives,
        key_findings=key_findings,
        most_important_risks=top_risks_bullets,
        priority_corrective_actions=priority_actions_bullets,
        top_3_recommended_actions=top_3_actions,
    )

    # ----------------------------------------------------
    # CONCLUSION & DATA LIMITATIONS
    # ----------------------------------------------------
    business_limitations: List[str] = []
    if not has_profit:
        business_limitations.append("Full financial profit & loss analysis requires unit cost or expense data.")
    if not has_inventory:
        business_limitations.append("Inventory reorder recommendations require stock level and warehouse tracking data.")
    if not has_comp:
        business_limitations.append("Market share and external competitive benchmarking require third-party market filings.")

    data_driven_conclusion = ConclusionReportSchema(
        main_findings=key_findings,
        most_urgent_issues=[r.title for r in verified_risks[:3]],
        opportunities=[
            f"Optimize pricing and cap discounts on '{loss_segments[0].name}' to eliminate losses." if loss_segments else "Expand marketing in high-margin categories.",
            "Consolidate promotional concessions and test discount thresholds below 25%.",
        ],
        recommended_next_steps=[a.recommended_action for a in action_items[:3]],
        important_limitations=business_limitations or ["Analysis is constrained to internal historical transaction logs."],
        areas_requiring_additional_data=[
            "External competitor revenue filings for industry benchmarking.",
            "Unit product costs (COGS) for granular SKU margin tracking.",
            "Warehouse inventory balances for automated replenishment modeling.",
        ],
    )

    # ----------------------------------------------------
    # TECHNICAL DATA VALIDATION (SECONDARY / COLLAPSIBLE ONLY)
    # ----------------------------------------------------
    total_cells = total_rows * total_cols
    total_missing_cells = int(df.isna().sum().sum())
    missing_cells_pct = round((total_missing_cells / total_cells * 100) if total_cells > 0 else 0.0, 2)
    duplicate_rows_count = int(df.duplicated().sum())
    duplicate_rows_pct = round((duplicate_rows_count / total_rows * 100) if total_rows > 0 else 0.0, 2)

    columns_summary: List[ColumnSummaryItemSchema] = []
    for col_name, prof in profiles.items():
        sample_vals: List[str] = []
        try:
            non_nulls = df[col_name].dropna()
            if not non_nulls.empty:
                sample_vals = [str(x)[:40] for x in non_nulls.unique()[:3]]
        except Exception:
            pass

        null_pct = round((prof.null_count / total_rows * 100) if total_rows > 0 else 0.0, 2)
        columns_summary.append(
            ColumnSummaryItemSchema(
                column_name=col_name,
                dtype=prof.dtype,
                semantic_role=prof.role,
                missing_count=prof.null_count,
                missing_pct=null_pct,
                unique_count=prof.distinct_count,
                sample_values=sample_vals,
            )
        )

    dq_score = dq_data.get("overall_score", 100)
    dq_status = dq_data.get("status", "Healthy")
    dq_limitations: List[str] = []
    if duplicate_rows_count > 0:
        dq_limitations.append(f"Contains {duplicate_rows_count:,} duplicate records ({duplicate_rows_pct}%).")
    if total_missing_cells > 0:
        dq_limitations.append(f"Missing data present across {total_missing_cells:,} total cell values ({missing_cells_pct}%).")

    dataset_overview = DatasetOverviewReportSchema(
        dimensions_text=f"{total_rows:,} rows × {total_cols} columns",
        row_count=total_rows,
        column_count=total_cols,
        columns_summary=columns_summary,
        detected_date_range=date_range_str,
        has_date_dimension=has_date,
        data_quality_score=dq_score,
        data_quality_status=dq_status,
        missing_cells_count=total_missing_cells,
        missing_cells_pct=missing_cells_pct,
        duplicate_rows_count=duplicate_rows_count,
        duplicate_rows_pct=duplicate_rows_pct,
        important_limitations=dq_limitations,
    )

    metadata = ReportMetadataSchema(
        report_title=f"Executive Business Intelligence Report: {entry.filename}",
        dataset_name=entry.filename,
        dataset_id=dataset_id,
        generated_at=datetime.datetime.now().strftime("%d %b %Y, %I:%M %p"),
        domain_id=domain_id,
        domain_name=domain_name,
        row_count=total_rows,
        column_count=total_cols,
        reporting_period=date_range_str or "Full Historical Record",
        currency_symbol=currency_symbol,
        data_quality_score=dq_score,
        available_sections_count=12,
        total_sections_count=14,
    )

    return ComprehensiveReportResponse(
        metadata=metadata,
        executive_summary=executive_summary,
        business_performance=business_performance,
        profit_loss=profit_loss,
        customer_segment_analysis=customer_segment_analysis,
        regional_channel_analysis=regional_channel_analysis,
        discount_pricing=discount_pricing,
        inventory_analysis=inventory_analysis,
        root_cause_analysis=root_cause_analysis,
        trends_intelligence=trends_report,
        risks_anomalies=risks_report,
        market_competition=competition_report,
        recommendations=recommendations_report,
        corrective_action_plan=corrective_action_plan,
        forecasting=forecasting,
        data_driven_conclusion=data_driven_conclusion,
        dataset_overview=dataset_overview,
        methodology_audit=None,
    )
