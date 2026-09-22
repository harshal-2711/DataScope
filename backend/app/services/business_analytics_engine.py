"""Business Analytics & Decision Intelligence Engine.

Builds real-world, decision-oriented analytics tailored to the uploaded dataset's
domain with 14 specialized domain playbooks:
1. Sales & E-commerce
2. Finance & Accounting
3. IPL & Sports (Match-level + Ball-by-ball)
4. Education & Academic Performance
5. Healthcare & Clinical Operations
6. Movies & Box Office
7. Music & Streaming
8. Marketing & Advertising
9. HR & Workforce
10. Manufacturing & Industrial Operations
11. Logistics & Supply Chain
12. Real Estate & Property
13. Agriculture & Crop Yield
14. Social Media & Audience Engagement
15. Universal Generic Fallback

Every metric has an explicit status:
- 'Available'
- 'Calculated'
- 'Estimated'
- 'Unavailable'
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

import numpy as np
import pandas as pd

from app.schemas.domain_blueprint import (
    DashboardSectionSchema,
    DecisionDashboardResponse,
    DomainIdentitySchema,
    MetricStatusSchema,
    SectionChartSchema,
)
from app.services.column_formatter import detect_column_unit, format_metric_display
from app.services.column_profiler import ColumnProfile, profile_dataset
from app.services.semantic_rules import prettify
from app.services.type_inference import detect_dataset_currency


def _clean_num(val: Any, decimals: int = 2) -> Optional[float]:
    if val is None:
        return None
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return round(f, decimals)
    except (ValueError, TypeError):
        return None


def _format_currency(val: Optional[float], sym: str = "₹") -> str:
    if val is None:
        return "N/A"
    s = sym or "₹"
    if abs(val) >= 1_000_000_000:
        return f"{s}{val / 1_000_000_000:.2f}B"
    if abs(val) >= 1_000_000:
        return f"{s}{val / 1_000_000:.2f}M"
    if abs(val) >= 1_000:
        return f"{s}{val:,.2f}"
    return f"{s}{val:.2f}"


def _format_number(val: Optional[float]) -> str:
    if val is None:
        return "N/A"
    if abs(val) >= 1_000_000:
        return f"{val / 1_000_000:.2f}M"
    if abs(val) >= 1_000:
        return f"{val:,.0f}"
    return f"{val:,.1f}".rstrip("0").rstrip(".")


def _find_col(
    df: pd.DataFrame,
    profiles: List[ColumnProfile],
    keywords: Tuple[str, ...],
    role: Optional[Union[str, Tuple[str, ...]]] = None,
) -> Optional[str]:
    """Find the best column matching specified keywords and role."""
    best_col: Optional[str] = None
    best_score = 0.0

    allowed_roles = (role,) if isinstance(role, str) else role

    for prof in profiles:
        if allowed_roles:
            if "numeric" in allowed_roles and prof.role in ("numeric", "boolean"):
                pass
            elif prof.role not in allowed_roles:
                continue
        col_lower = prof.name.lower().replace("_", " ").replace("-", " ")
        words = set(col_lower.split())

        score = 0.0
        for kw in keywords:
            kw_clean = kw.lower()
            if kw_clean == prof.name.lower():
                score += 10.0
            elif kw_clean in words:
                score += 5.0
            elif kw_clean in col_lower:
                score += 2.5

        if score > best_score:
            best_score = score
            best_col = prof.name

    return best_col


def generate_decision_dashboard(
    df: pd.DataFrame,
    domain: DomainIdentitySchema,
    profiles: Optional[List[ColumnProfile]] = None,
) -> DecisionDashboardResponse:
    """Generate a structured, decision-oriented executive dashboard."""
    if profiles is None:
        profiles = profile_dataset(df)

    domain_id = domain.domain_id.lower()
    cols_lower = [str(c).lower() for c in df.columns]

    # 0. Procurement & Government Tenders
    has_procurement_cols = any(
        c in cols_lower
        for c in (
            "tender",
            "tender_id",
            "tender_value",
            "procurement",
            "contract_value",
            "bidder",
            "tenderer",
            "procurement_method",
            "contracting_authority",
            "award_date",
            "tender_duration",
        )
    )
    if "procurement" in domain_id or "tender" in domain_id or has_procurement_cols:
        return _build_procurement_dashboard(df, domain, profiles)

    # 1. Social Media
    has_social_cols = any(c in cols_lower for c in ("likes", "retweets", "shares", "followers", "post_type", "reactions", "reposts"))
    if "social" in domain_id or has_social_cols:
        return _build_social_media_dashboard(df, domain, profiles)

    # 2. Marketing & Advertising
    has_mkt_cols = any(c in cols_lower for c in ("campaign", "clicks", "ctr", "cpc", "roas", "ad_spend", "conversion_rate", "ad_name"))
    if any(k in domain_id for k in ("marketing", "ads", "advertising")) or has_mkt_cols:
        return _build_marketing_dashboard(df, domain, profiles)

    # 3. HR & Workforce
    if any(k in domain_id for k in ("hr", "workforce", "recruitment", "employee")) or any(
        c in cols_lower for c in ("employee_id", "salary", "attrition", "tenure", "job_title")
    ):
        return _build_hr_dashboard(df, domain, profiles)

    # 4. Manufacturing & Operations
    if any(k in domain_id for k in ("manufactur", "production", "assembly")) or any(
        c in cols_lower for c in ("oee", "downtime", "defect_rate", "work_order", "scrap")
    ):
        return _build_manufacturing_dashboard(df, domain, profiles)

    # 5. Logistics & Supply Chain
    if any(k in domain_id for k in ("logistic", "supply_chain", "freight", "shipping")) or any(
        c in cols_lower for c in ("freight_cost", "transit_days", "shipment_id", "carrier", "otif")
    ):
        return _build_logistics_dashboard(df, domain, profiles)

    # 6. Real Estate
    if "real_estate" in domain_id or "property" in domain_id or any(
        c in cols_lower for c in ("sqft", "square_feet", "bedroom", "property_price", "listing_price")
    ):
        return _build_real_estate_dashboard(df, domain, profiles)

    # 7. Agriculture
    if "agri" in domain_id or "crop" in domain_id or any(
        c in cols_lower for c in ("crop", "yield", "rainfall", "harvest", "hectare")
    ):
        return _build_agriculture_dashboard(df, domain, profiles)

    # 8. Music & Streaming
    if "music" in domain_id or any(c in cols_lower for c in ("track_name", "artist", "streams", "duration_ms")):
        return _build_music_dashboard(df, domain, profiles)

    # 9. Education & Academic
    has_edu_cols = any(c in cols_lower for c in ("student_id", "student", "attendance", "grade", "gpa", "marks"))
    if has_edu_cols or "edu" in domain_id or "academic" in domain_id or "school" in domain_id:
        return _build_education_dashboard(df, domain, profiles)

    # 10. Sports & Cricket / IPL
    has_sports_cols = any(c in cols_lower for c in ("batsman", "bowler", "over", "ball", "winner", "team1", "team2", "team", "match_id", "player"))
    if ("sport" in domain_id or "cricket" in domain_id or "ipl" in domain_id) and has_sports_cols:
        return _build_sports_dashboard(df, domain, profiles)

    # 11. Finance & Banking
    if "finance" in domain_id or "bank" in domain_id or "invest" in domain_id or any(c in cols_lower for c in ("debit_amount", "credit_amount", "balance")):
        return _build_finance_dashboard(df, domain, profiles)

    # 12. Healthcare & Clinical
    if "health" in domain_id or "medic" in domain_id or "hosp" in domain_id or any(c in cols_lower for c in ("diagnosis", "patient_id", "length_of_stay")):
        return _build_healthcare_dashboard(df, domain, profiles)

    # 13. Movies & Entertainment
    if any(k in domain_id for k in ("movie", "film", "entertain")) or any(c in cols_lower for c in ("box_office", "imdb_rating", "director")):
        return _build_movies_dashboard(df, domain, profiles)

    # 14. Sales & Commerce
    if any(k in domain_id for k in ("sales", "commerce", "retail", "fmcg", "grocery", "market")) or any(c in cols_lower for c in ("order_id", "sales", "revenue", "product_name")):
        return _build_sales_dashboard(df, domain, profiles)

    # 15. Generic Fallback
    return _build_generic_dashboard(df, domain, profiles)


# ==============================================================================
# 0. GOVERNMENT PROCUREMENT DECISION DASHBOARD
# ==============================================================================
def _build_procurement_dashboard(
    df: pd.DataFrame,
    domain: DomainIdentitySchema,
    profiles: List[ColumnProfile],
) -> DecisionDashboardResponse:
    row_count = len(df)

    tender_id_col = _find_col(df, profiles, ("tender_id", "tender_no", "contract_id", "id", "tender"), ("identifier", "categorical", "numeric"))
    val_col = _find_col(df, profiles, ("tender_value", "contract_value", "award_value", "amount", "budget", "value", "price"), "numeric")
    dur_col = _find_col(df, profiles, ("tender_duration", "duration_days", "procurement_days", "lead_time_days", "duration"), "numeric")
    bid_col = _find_col(df, profiles, ("bids_received", "tenderer_count", "bidders_count", "bids", "bidders", "suppliers"), "numeric")
    buyer_col = _find_col(df, profiles, ("buyer", "contracting_authority", "procuring_entity", "agency", "department", "ministry"), "categorical")
    method_col = _find_col(df, profiles, ("procurement_method", "method", "tender_type", "procedure", "type"), "categorical")
    cat_col = _find_col(df, profiles, ("category", "procurement_category", "sector", "goods_services"), "categorical")

    total_spend = _clean_num(df[val_col].sum()) if val_col else None
    total_tenders = int(df[tender_id_col].nunique()) if tender_id_col else row_count
    avg_tender_val = _clean_num(total_spend / total_tenders) if total_spend and total_tenders > 0 else None
    avg_duration = _clean_num(df[dur_col].mean()) if dur_col else None
    avg_bidders = _clean_num(df[bid_col].mean()) if bid_col else None

    exec_metrics = [
        MetricStatusSchema(
            id="total_procurement_spend",
            name="Total Procurement Value",
            value=total_spend,
            formatted_value=_format_currency(total_spend),
            status="Calculated" if val_col else "Unavailable",
            explanation=f"Sum of '{val_col}' across all awarded contracts." if val_col else "No contract value column detected.",
            category="executive",
            business_meaning="Aggregate public spending commitment across all recorded tenders.",
            formula=f"SUM({val_col})" if val_col else None,
        ),
        MetricStatusSchema(
            id="total_tenders",
            name="Total Tenders Processed",
            value=total_tenders,
            formatted_value=str(total_tenders),
            status="Calculated" if tender_id_col else "Estimated",
            explanation=f"Distinct count of '{tender_id_col}'." if tender_id_col else "Estimated from row count.",
            category="executive",
            business_meaning="Volume of public procurement solicitations.",
        ),
        MetricStatusSchema(
            id="avg_tender_value",
            name="Average Tender Value",
            value=avg_tender_val,
            formatted_value=_format_currency(avg_tender_val),
            status="Calculated" if avg_tender_val is not None else "Unavailable",
            explanation="Mean monetary size per tender contract.",
            category="executive",
            business_meaning="Benchmark size for public contract awards.",
        ),
        MetricStatusSchema(
            id="avg_tender_duration",
            name="Average Tender Duration",
            value=avg_duration,
            formatted_value=f"{avg_duration:.1f} days" if avg_duration else "N/A",
            status="Calculated" if dur_col else "Unavailable",
            explanation=f"Arithmetic mean of '{dur_col}' in days." if dur_col else "No duration column detected.",
            category="executive",
            business_meaning="Average administrative cycle time from notice to contract award.",
        ),
        MetricStatusSchema(
            id="avg_bidders",
            name="Average Bidders per Tender",
            value=avg_bidders,
            formatted_value=f"{avg_bidders:.1f}" if avg_bidders else "N/A",
            status="Calculated" if bid_col else "Unavailable",
            explanation=f"Average number of bids received ('{bid_col}')." if bid_col else "No bidder count column found.",
            category="executive",
            business_meaning="Market competition indicator for public tenders.",
        ),
    ]

    spend_charts: List[SectionChartSchema] = []
    if buyer_col and val_col:
        buyer_grp = df.groupby(buyer_col)[val_col].sum().sort_values(ascending=False).head(8)
        spend_charts.append(
            SectionChartSchema(
                id="spend_by_buyer",
                title="Procurement Spend by Buyer Agency",
                business_question="Which public agencies/departments account for the largest procurement spend?",
                chart_type="bar",
                metric="Procurement Spend",
                grouping="Buyer Agency",
                explanation="Ranks procuring authorities by total committed contract spend.",
                data=[{"x": str(idx), "y": _clean_num(val)} for idx, val in buyer_grp.items()],
                x_label="Buyer Agency",
                y_label="Total Spend ($)",
            )
        )

    if method_col:
        method_grp = df[method_col].value_counts().head(8)
        spend_charts.append(
            SectionChartSchema(
                id="tenders_by_method",
                title="Tenders by Procurement Method",
                business_question="What is the distribution of tenders across procurement methods?",
                chart_type="bar",
                metric="Tender Count",
                grouping="Procurement Method",
                explanation="Compares the frequency of open vs direct/restricted procurement procedures.",
                data=[{"x": str(idx), "y": _clean_num(val)} for idx, val in method_grp.items()],
                x_label="Procurement Method",
                y_label="Tender Count",
            )
        )

    cat_charts: List[SectionChartSchema] = []
    if cat_col and dur_col:
        dur_grp = df.groupby(cat_col)[dur_col].mean().sort_values(ascending=False).head(8)
        cat_charts.append(
            SectionChartSchema(
                id="avg_duration_by_category",
                title="Average Tender Duration by Category (Days)",
                business_question="Which procurement categories experience the longest administrative lead times?",
                chart_type="bar",
                metric="Average Duration (Days)",
                grouping="Category",
                explanation="Compares average turnaround days by category. Plotted as a bar chart because durations represent continuous averages, not part-to-whole shares.",
                data=[{"x": str(idx), "y": _clean_num(val)} for idx, val in dur_grp.items()],
                x_label="Procurement Category",
                y_label="Average Duration (Days)",
            )
        )

    if cat_col and val_col:
        cat_val_grp = df.groupby(cat_col)[val_col].sum().sort_values(ascending=False).head(8)
        cat_charts.append(
            SectionChartSchema(
                id="spend_by_category",
                title="Procurement Spend by Category",
                business_question="Which procurement categories absorb the highest public expenditure?",
                chart_type="bar",
                metric="Total Spend",
                grouping="Category",
                explanation="Ranks categories by total contract value committed.",
                data=[{"x": str(idx), "y": _clean_num(val)} for idx, val in cat_val_grp.items()],
                x_label="Category",
                y_label="Total Spend ($)",
            )
        )

    return DecisionDashboardResponse(
        dataset_id="",
        domain_name="Government Procurement",
        executive_summary=DashboardSectionSchema(
            section_id="executive_summary",
            title="Public Procurement Executive Summary",
            description="Overview of total public procurement spend, solicitation volumes, administrative turnaround, and bidder competition.",
            is_available=True,
            metrics=exec_metrics,
            highlights=[
                f"Audited {total_tenders:,} public tenders across {len(df):,} contract records.",
                f"Total procurement commitment: {_format_currency(total_spend)}." if total_spend else "Tender volumes captured.",
                f"Average turnaround duration: {avg_duration:.1f} days." if avg_duration else "Turnaround tracking unavailable.",
            ],
        ),
        sales_performance=DashboardSectionSchema(
            section_id="sales_performance",
            title="Procurement Spend & Agency Allocation",
            description="Agency-level procurement spending and procedural distribution.",
            is_available=len(spend_charts) > 0,
            charts=spend_charts,
        ),
        profitability=DashboardSectionSchema(
            section_id="profitability",
            title="Bidding Competition & Pricing Analysis",
            description="Market competition intensity, tenderer participation, and price efficiency.",
            is_available=bid_col is not None,
            unavailable_reason="No bidder count or competition column found." if not bid_col else None,
            metrics=[exec_metrics[4]],
        ),
        product_analysis=DashboardSectionSchema(
            section_id="product_analysis",
            title="Category Procurement & Lead Times",
            description="Category-level spend distribution and administrative duration benchmarks.",
            is_available=len(cat_charts) > 0,
            charts=cat_charts,
        ),
        operations_inventory=DashboardSectionSchema(
            section_id="operations_inventory",
            title="Procurement Operational Efficiency",
            description="Cycle time efficiency and procedural compliance.",
            is_available=dur_col is not None,
            unavailable_reason="No duration columns found." if not dur_col else None,
            metrics=[exec_metrics[3]],
        ),
        insights_recommendations=DashboardSectionSchema(
            section_id="insights_recommendations",
            title="Procurement Intelligence & Policy Recommendations",
            description="Actionable guidance to enhance procurement competition and accelerate cycle times.",
            is_available=True,
            insights=[
                {
                    "what_happened": f"Processed {total_tenders:,} public procurement solicitations with {_format_currency(total_spend)} in total commitments." if total_spend else f"Processed {total_tenders:,} tenders.",
                    "why_it_happened": "Spend concentration typically aligns with major infrastructure and healthcare categories.",
                    "what_to_investigate": "Investigate categories where average tender duration exceeds 90 days or where average bidders fall below 2.0.",
                    "limitations": "Does not reflect cancelled tenders, post-award contract amendments, or supplier delivery disputes.",
                }
            ],
        ),
    )


# ==============================================================================
# 1. SALES & E-COMMERCE DECISION DASHBOARD
# ==============================================================================
def _build_sales_dashboard(
    df: pd.DataFrame,
    domain: DomainIdentitySchema,
    profiles: List[ColumnProfile],
) -> DecisionDashboardResponse:
    row_count = len(df)

    rev_col = _find_col(df, profiles, ("revenue", "sales", "total_amount", "amount", "total", "price"), "numeric")
    qty_col = _find_col(df, profiles, ("quantity", "qty", "units", "items_sold", "volume"), "numeric")
    cost_col = _find_col(df, profiles, ("cost", "cogs", "expense", "purchase_price", "unit_cost"), "numeric")
    profit_col = _find_col(df, profiles, ("profit", "net_profit", "earnings", "margin_amount"), "numeric")
    discount_col = _find_col(df, profiles, ("discount", "discount_amount", "discount_pct", "rebate"), "numeric")
    order_col = _find_col(df, profiles, ("order_id", "order_number", "transaction_id", "invoice_id", "id"))
    product_col = _find_col(df, profiles, ("product_name", "product", "item_name", "item", "sku", "title"), "categorical")
    category_col = _find_col(df, profiles, ("category", "product_category", "department", "sub_category", "segment"), "categorical")
    region_col = _find_col(df, profiles, ("region", "country", "state", "city", "store", "territory", "location"), "categorical")
    stock_col = _find_col(df, profiles, ("stock", "inventory", "stock_level", "units_in_stock", "available_quantity"), "numeric")
    date_col = _find_col(df, profiles, ("order_date", "date", "created_at", "transaction_date", "time"), "temporal")

    total_rev = _clean_num(df[rev_col].sum()) if rev_col else None
    total_qty = _clean_num(df[qty_col].sum()) if qty_col else None
    total_orders = int(df[order_col].nunique()) if order_col else row_count
    aov = _clean_num(total_rev / total_orders) if total_rev and total_orders > 0 else None

    has_profit = False
    total_profit: Optional[float] = None
    profit_margin: Optional[float] = None
    profit_explanation = ""

    if profit_col:
        total_profit = _clean_num(df[profit_col].sum())
        has_profit = True
        profit_margin = _clean_num((total_profit / total_rev) * 100.0) if total_rev and total_rev > 0 else None
        profit_explanation = f"Calculated from '{profit_col}' column."
    elif cost_col and rev_col:
        total_cost = _clean_num(df[cost_col].sum())
        if total_cost is not None and total_rev is not None:
            total_profit = _clean_num(total_rev - total_cost)
            has_profit = True
            profit_margin = _clean_num((total_profit / total_rev) * 100.0) if total_rev > 0 else None
            profit_explanation = f"Calculated as Revenue ('{rev_col}') minus Cost ('{cost_col}')."
    else:
        profit_explanation = "Profit and profit margin cannot be calculated because the dataset lacks reliable cost (COGS) or net profit columns. Displaying top-line revenue metrics only."

    exec_metrics = [
        MetricStatusSchema(
            id="total_revenue",
            name="Total Revenue",
            value=total_rev,
            formatted_value=_format_currency(total_rev),
            status="Calculated" if rev_col else "Unavailable",
            explanation=f"Summed from '{rev_col}' across {row_count:,} records." if rev_col else "No revenue column found.",
            category="executive",
            business_meaning="Gross top-line sales generated across all orders.",
            formula=f"SUM({rev_col})" if rev_col else None,
        ),
        MetricStatusSchema(
            id="total_orders",
            name="Total Orders",
            value=total_orders,
            formatted_value=_format_number(total_orders),
            status="Calculated" if order_col else "Estimated",
            explanation=f"Distinct count of '{order_col}'." if order_col else "Estimated as total transaction rows.",
            category="executive",
            business_meaning="Total commercial transaction count.",
            formula=f"COUNT(DISTINCT {order_col})" if order_col else "COUNT(*)",
        ),
        MetricStatusSchema(
            id="units_sold",
            name="Units Sold",
            value=total_qty,
            formatted_value=_format_number(total_qty),
            status="Calculated" if qty_col else "Unavailable",
            explanation=f"Sum of quantity column '{qty_col}'." if qty_col else "No quantity/units column found.",
            category="executive",
            business_meaning="Total physical volume of items moved.",
            formula=f"SUM({qty_col})" if qty_col else None,
        ),
        MetricStatusSchema(
            id="aov",
            name="Average Order Value (AOV)",
            value=aov,
            formatted_value=_format_currency(aov),
            status="Calculated" if aov is not None else "Unavailable",
            explanation="Total revenue divided by total orders." if aov is not None else "Requires revenue and order counts.",
            category="executive",
            business_meaning="Average monetary expenditure per customer checkout.",
            formula="Total Revenue / Total Orders",
        ),
        MetricStatusSchema(
            id="net_profit",
            name="Net Profit",
            value=total_profit,
            formatted_value=_format_currency(total_profit) if has_profit else "N/A",
            status="Calculated" if has_profit else "Unavailable",
            explanation=profit_explanation,
            category="profitability",
            business_meaning="Net bottom-line financial earnings.",
            formula="Revenue - Cost" if has_profit else None,
        ),
        MetricStatusSchema(
            id="profit_margin",
            name="Profit Margin",
            value=profit_margin,
            formatted_value=f"{profit_margin:.1f}%" if profit_margin is not None else "N/A",
            status="Calculated" if profit_margin is not None else "Unavailable",
            explanation=profit_explanation,
            category="profitability",
            business_meaning="Percentage of revenue retained as profit.",
            formula="(Net Profit / Total Revenue) * 100",
        ),
    ]

    sales_charts: List[SectionChartSchema] = []
    if rev_col and date_col:
        try:
            ts_df = df[[date_col, rev_col]].copy()
            ts_df[date_col] = pd.to_datetime(ts_df[date_col], errors="coerce")
            ts_df = ts_df.dropna().sort_values(date_col)
            if len(ts_df) > 1:
                resampled = ts_df.set_index(date_col).resample("ME")[rev_col].sum()
                if len(resampled) < 2:
                    resampled = ts_df.set_index(date_col).resample("W")[rev_col].sum()
                if len(resampled) < 2:
                    resampled = ts_df.set_index(date_col).resample("D")[rev_col].sum()
                chart_data = [{"x": idx.strftime("%Y-%m-%d"), "y": _clean_num(val)} for idx, val in resampled.items()]
                if len(chart_data) >= 2:
                    sales_charts.append(
                        SectionChartSchema(
                            id="revenue_trend",
                            title="Revenue Trend Over Time",
                            business_question="How is sales revenue trending across operating periods?",
                            chart_type="line",
                            metric="Revenue",
                            grouping="Date",
                            explanation="Tracks historical revenue trajectory to detect growth periods, seasonality, and sudden sales drops.",
                            data=chart_data,
                            x_label="Date",
                            y_label="Revenue ($)",
                        )
                    )
        except Exception:
            pass

    if rev_col and category_col:
        cat_grouped = df.groupby(category_col)[rev_col].sum().sort_values(ascending=False).head(10)
        sales_charts.append(
            SectionChartSchema(
                id="sales_by_category",
                title="Revenue by Product Category",
                business_question="Which product categories generate the highest share of sales?",
                chart_type="bar",
                metric="Revenue",
                grouping="Category",
                explanation="Ranks product categories by gross revenue to guide inventory allocation and commercial focus.",
                data=[{"x": str(idx), "y": _clean_num(val)} for idx, val in cat_grouped.items()],
                x_label="Category",
                y_label="Total Revenue ($)",
            )
        )

    prod_charts: List[SectionChartSchema] = []
    prod_metrics: List[MetricStatusSchema] = []
    prod_insights: List[Dict[str, Any]] = []

    if product_col and rev_col:
        prod_rev = df.groupby(product_col)[rev_col].sum().sort_values(ascending=False)
        total_p_rev = prod_rev.sum()

        top_5 = prod_rev.head(5)
        prod_charts.append(
            SectionChartSchema(
                id="top_products",
                title="Top 5 Best-Selling Products",
                business_question="Which specific products generate the most revenue?",
                chart_type="bar",
                metric="Revenue",
                grouping="Product",
                explanation="Ranks top-performing SKUs to prioritize marketing and ensure stock continuity.",
                data=[{"x": str(idx), "y": _clean_num(val)} for idx, val in top_5.items()],
                x_label="Product",
                y_label="Revenue ($)",
            )
        )

        bottom_5 = prod_rev[prod_rev > 0].tail(5)
        prod_charts.append(
            SectionChartSchema(
                id="underperforming_products",
                title="Underperforming Products (Bottom 5)",
                business_question="Which active catalog products have the lowest revenue contribution?",
                chart_type="bar",
                metric="Revenue",
                grouping="Product",
                explanation="Surfaces bottom-revenue products that may require repricing or catalog rationalization.",
                data=[{"x": str(idx), "y": _clean_num(val)} for idx, val in bottom_5.items()],
                x_label="Product",
                y_label="Revenue ($)",
            )
        )

        cum_pct = (prod_rev.cumsum() / total_p_rev) * 100.0
        n_products = len(prod_rev)
        top_20_count = max(1, int(n_products * 0.2))
        top_20_rev_share = _clean_num(cum_pct.iloc[top_20_count - 1]) if n_products > 0 else 0.0

        prod_metrics.append(
            MetricStatusSchema(
                id="pareto_share",
                name="Top 20% Product Revenue Share",
                value=top_20_rev_share,
                formatted_value=f"{top_20_rev_share:.1f}%" if top_20_rev_share else "N/A",
                status="Calculated",
                explanation=f"The top {top_20_count} products ({top_20_rev_share:.1f}%) drive the majority of sales.",
                category="product",
                business_meaning="Measures revenue concentration risk across product catalog.",
            )
        )

    has_inventory = stock_col is not None
    inv_unavailable_reason = None if has_inventory else (
        "Inventory and stock analysis is unavailable because no inventory level, reorder point, "
        "or warehouse stock columns were detected in this dataset."
    )

    return DecisionDashboardResponse(
        dataset_id="",
        domain_name="Sales & E-Commerce",
        executive_summary=DashboardSectionSchema(
            section_id="executive_summary",
            title="Executive Summary",
            description="Commercial performance indicators, revenue health, and order volume.",
            is_available=True,
            metrics=exec_metrics,
            highlights=[
                f"Generated {_format_currency(total_rev)} in revenue across {total_orders:,} orders."
                if total_rev else "Sales activity analyzed."
            ],
        ),
        sales_performance=DashboardSectionSchema(
            section_id="sales_performance",
            title="Sales Performance",
            description="Revenue trends, category breakdowns, and order volume.",
            is_available=len(sales_charts) > 0,
            charts=sales_charts,
        ),
        profitability=DashboardSectionSchema(
            section_id="profitability",
            title="Profitability & Margins",
            description="Net profit, profit margin, and cost vs revenue relationship.",
            is_available=has_profit,
            unavailable_reason=profit_explanation if not has_profit else None,
            metrics=[m for m in exec_metrics if m.category == "profitability"],
        ),
        product_analysis=DashboardSectionSchema(
            section_id="product_analysis",
            title="Product & Catalog Analysis",
            description="Top-selling products, underperforming SKUs, and Pareto revenue contribution.",
            is_available=len(prod_charts) > 0,
            metrics=prod_metrics,
            charts=prod_charts,
        ),
        operations_inventory=DashboardSectionSchema(
            section_id="operations_inventory",
            title="Operations & Inventory",
            description="Stock availability, reorder thresholds, and warehouse inventory turnover.",
            is_available=has_inventory,
            unavailable_reason=inv_unavailable_reason,
        ),
        insights_recommendations=DashboardSectionSchema(
            section_id="insights_recommendations",
            title="Insights & Management Actions",
            description="Factual findings, root causes, and recommended executive investigations.",
            is_available=True,
            insights=[
                {
                    "what_happened": f"Gross sales volume reached {_format_currency(total_rev)}." if total_rev else "Sales data analyzed.",
                    "why_it_happened": "Commercial returns driven by product catalog demand.",
                    "what_to_investigate": "Assess marketing alignment with top-grossing products and evaluate supplier reliability.",
                    "limitations": "Does not reflect external promotional calendars or competitor pricing.",
                }
            ],
        ),
    )


# ==============================================================================
# 2. MARKETING & ADVERTISING DECISION DASHBOARD
# ==============================================================================
def _build_marketing_dashboard(
    df: pd.DataFrame,
    domain: DomainIdentitySchema,
    profiles: List[ColumnProfile],
) -> DecisionDashboardResponse:
    row_count = len(df)
    camp_col = _find_col(df, profiles, ("campaign", "campaign_name", "ad_name", "creative"))
    imp_col = _find_col(df, profiles, ("impressions", "views", "reach"), "numeric")
    click_col = _find_col(df, profiles, ("clicks", "click_count"), "numeric")
    conv_col = _find_col(df, profiles, ("conversions", "leads", "purchases", "orders"), "numeric")
    spend_col = _find_col(df, profiles, ("spend", "cost", "ad_spend", "budget"), "numeric")
    rev_col = _find_col(df, profiles, ("revenue", "conversion_value", "sales"), "numeric")
    channel_col = _find_col(df, profiles, ("channel", "platform", "medium", "network"), "categorical")

    total_imp = int(df[imp_col].sum()) if imp_col else None
    total_clicks = int(df[click_col].sum()) if click_col else None
    total_conv = int(df[conv_col].sum()) if conv_col else None
    total_spend = _clean_num(df[spend_col].sum()) if spend_col else None
    total_rev = _clean_num(df[rev_col].sum()) if rev_col else None

    ctr = _clean_num((total_clicks / total_imp) * 100.0) if total_clicks and total_imp and total_imp > 0 else None
    conv_rate = _clean_num((total_conv / total_clicks) * 100.0) if total_conv and total_clicks and total_clicks > 0 else None
    cac = _clean_num(total_spend / total_conv) if total_spend and total_conv and total_conv > 0 else None
    roas = _clean_num(total_rev / total_spend) if total_rev and total_spend and total_spend > 0 else None

    exec_metrics = [
        MetricStatusSchema(
            id="total_impressions",
            name="Total Ad Impressions",
            value=total_imp,
            formatted_value=_format_number(total_imp),
            status="Calculated" if imp_col else "Unavailable",
            explanation=f"Sum of impressions across {row_count:,} campaign records.",
            category="executive",
            business_meaning="Total audience advertising exposures.",
        ),
        MetricStatusSchema(
            id="total_clicks",
            name="Total Clicks",
            value=total_clicks,
            formatted_value=_format_number(total_clicks),
            status="Calculated" if click_col else "Unavailable",
            explanation="Sum of all ad clicks recorded.",
            category="executive",
            business_meaning="Direct user engagement with ad creatives.",
        ),
        MetricStatusSchema(
            id="ctr",
            name="Click-Through Rate (CTR)",
            value=ctr,
            formatted_value=f"{ctr:.2f}%" if ctr is not None else "N/A",
            status="Calculated" if ctr is not None else "Unavailable",
            explanation="Clicks divided by Impressions * 100.",
            category="executive",
            business_meaning="Ad creative resonance and relevancy benchmark.",
        ),
        MetricStatusSchema(
            id="conversions",
            name="Total Conversions",
            value=total_conv,
            formatted_value=_format_number(total_conv),
            status="Calculated" if conv_col else "Unavailable",
            explanation="Sum of successful customer conversions/leads.",
            category="executive",
            business_meaning="Gross downstream campaign goal completions.",
        ),
        MetricStatusSchema(
            id="ad_spend",
            name="Total Ad Spend",
            value=total_spend,
            formatted_value=_format_currency(total_spend),
            status="Calculated" if spend_col else "Unavailable",
            explanation="Sum of all campaign advertising costs.",
            category="profitability",
            business_meaning="Total media investment.",
        ),
        MetricStatusSchema(
            id="roas",
            name="Return on Ad Spend (ROAS)",
            value=roas,
            formatted_value=f"{roas:.2f}x" if roas is not None else "N/A",
            status="Calculated" if roas is not None else "Unavailable",
            explanation="Revenue divided by Ad Spend." if roas is not None else "Requires both revenue and ad spend data.",
            category="profitability",
            business_meaning="Revenue return generated per dollar of ad spend.",
        ),
    ]

    charts: List[SectionChartSchema] = []
    if camp_col and click_col:
        camp_clicks = df.groupby(camp_col)[click_col].sum().sort_values(ascending=False).head(8)
        charts.append(
            SectionChartSchema(
                id="clicks_by_campaign",
                title="Clicks by Campaign",
                business_question="Which marketing campaigns drive the highest user traffic?",
                chart_type="bar",
                metric="Clicks",
                grouping="Campaign",
                explanation="Ranks top-traffic campaigns to identify winning ad hooks.",
                data=[{"x": str(idx), "y": int(val)} for idx, val in camp_clicks.items()],
                x_label="Campaign",
                y_label="Clicks",
            )
        )

    if channel_col and click_col and imp_col:
        chan_data = df.groupby(channel_col)[[click_col, imp_col]].sum()
        chan_ctr = ((chan_data[click_col] / chan_data[imp_col].replace(0, np.nan)) * 100.0).dropna().sort_values(ascending=False)
        charts.append(
            SectionChartSchema(
                id="ctr_by_channel",
                title="CTR by Marketing Channel",
                business_question="Which distribution channels yield the highest click-through rate?",
                chart_type="bar",
                metric="CTR (%)",
                grouping="Channel",
                explanation="Compares channel efficiency to optimize budget allocation.",
                data=[{"x": str(idx), "y": _clean_num(val)} for idx, val in chan_ctr.items()],
                x_label="Channel",
                y_label="CTR (%)",
            )
        )

    return DecisionDashboardResponse(
        dataset_id="",
        domain_name="Marketing & Advertising",
        executive_summary=DashboardSectionSchema(
            section_id="executive_summary",
            title="Campaign Executive Summary",
            description="Overall reach, CTR benchmarks, and conversion acquisition volume.",
            is_available=True,
            metrics=exec_metrics,
            highlights=[
                f"Generated {total_clicks:,} clicks from {total_imp:,} impressions (CTR: {ctr:.2f}%)."
                if total_clicks and total_imp and ctr else "Audited marketing campaign performance."
            ],
        ),
        sales_performance=DashboardSectionSchema(
            section_id="sales_performance",
            title="Campaign & Channel Performance",
            description="Click volumes and conversion efficiency by channel.",
            is_available=len(charts) > 0,
            charts=charts,
        ),
        profitability=DashboardSectionSchema(
            section_id="profitability",
            title="Marketing ROI & Acquisition Cost",
            description="ROAS, CAC, and ad spend efficiency.",
            is_available=total_spend is not None,
            unavailable_reason="Ad spend column missing; cannot calculate CAC or ROAS." if total_spend is None else None,
            metrics=[m for m in exec_metrics if m.category == "profitability"],
        ),
        product_analysis=DashboardSectionSchema(
            section_id="product_analysis",
            title="Ad Creative & Message Analysis",
            description="Creative performance and copy engagement.",
            is_available=len(charts) > 0,
            charts=charts,
        ),
        operations_inventory=DashboardSectionSchema(
            section_id="operations_inventory",
            title="Operations & Media Delivery",
            description="Ad serving and impression fulfillment.",
            is_available=False,
            unavailable_reason="Physical inventory does not apply to digital marketing campaigns.",
        ),
        insights_recommendations=DashboardSectionSchema(
            section_id="insights_recommendations",
            title="Growth Insights & Optimizations",
            description="Actionable recommendations to lower CAC and scale winning channels.",
            is_available=True,
            insights=[
                {
                    "what_happened": f"Campaign generated {total_clicks:,} clicks." if total_clicks else "Marketing data processed.",
                    "why_it_happened": "Performance driven by creative relevance and channel targeting.",
                    "what_to_investigate": "Reallocate media spend from bottom-quartile CTR channels into top performers.",
                    "limitations": "Does not account for multi-touch attribution or post-view conversions.",
                }
            ],
        ),
    )


# ==============================================================================
# 3. HR & WORKFORCE DECISION DASHBOARD
# ==============================================================================
def _build_hr_dashboard(
    df: pd.DataFrame,
    domain: DomainIdentitySchema,
    profiles: List[ColumnProfile],
) -> DecisionDashboardResponse:
    row_count = len(df)
    emp_col = _find_col(df, profiles, ("employee_id", "emp_id", "staff_id", "worker_id", "id"))
    dept_col = _find_col(df, profiles, ("department", "dept", "division", "team"), "categorical")
    salary_col = _find_col(df, profiles, ("salary", "compensation", "base_pay", "wage"), "numeric")
    attr_col = _find_col(df, profiles, ("attrition", "is_terminated", "left_company", "status"), "numeric")
    tenure_col = _find_col(df, profiles, ("tenure", "years_at_company", "service_years"), "numeric")

    headcount = int(df[emp_col].nunique()) if emp_col else row_count
    avg_sal = _clean_num(df[salary_col].mean()) if salary_col else None
    avg_tenure = _clean_num(df[tenure_col].mean()) if tenure_col else None

    attr_rate: Optional[float] = None
    if attr_col:
        attr_rate = _clean_num((df[attr_col].mean()) * 100.0)
    elif "status" in df.columns:
        left_count = (df["status"].astype(str).str.lower().isin(["left", "terminated", "resigned"])).sum()
        attr_rate = _clean_num((left_count / row_count) * 100.0) if row_count > 0 else None

    exec_metrics = [
        MetricStatusSchema(
            id="headcount",
            name="Active Headcount",
            value=headcount,
            formatted_value=_format_number(headcount),
            status="Available",
            explanation=f"Total recorded employees across {headcount:,} records.",
            category="executive",
            business_meaning="Total organization workforce size.",
        ),
        MetricStatusSchema(
            id="avg_salary",
            name="Average Base Salary",
            value=avg_sal,
            formatted_value=_format_currency(avg_sal) if avg_sal else "N/A",
            status="Calculated" if salary_col else "Unavailable",
            explanation=f"Mean compensation from '{salary_col}'." if salary_col else "No salary column found.",
            category="executive",
            business_meaning="Average employee payroll expense.",
        ),
        MetricStatusSchema(
            id="turnover_rate",
            name="Turnover / Attrition Rate",
            value=attr_rate,
            formatted_value=f"{attr_rate:.1f}%" if attr_rate is not None else "N/A",
            status="Calculated" if attr_rate is not None else "Unavailable",
            explanation="Proportion of separated workforce members.",
            category="executive",
            business_meaning="Annualized staff departure rate.",
        ),
        MetricStatusSchema(
            id="avg_tenure",
            name="Average Employee Tenure",
            value=avg_tenure,
            formatted_value=f"{avg_tenure:.1f} yrs" if avg_tenure else "N/A",
            status="Calculated" if tenure_col else "Unavailable",
            explanation="Mean years of employee service.",
            category="executive",
            business_meaning="Institutional retention benchmark.",
        ),
    ]

    charts: List[SectionChartSchema] = []
    if dept_col:
        dept_counts = df[dept_col].value_counts().head(8)
        charts.append(
            SectionChartSchema(
                id="headcount_by_dept",
                title="Headcount by Department",
                business_question="How is organizational staffing distributed across departments?",
                chart_type="bar",
                metric="Employee Count",
                grouping="Department",
                explanation="Shows departmental staffing levels to inform organizational design.",
                data=[{"x": str(idx), "y": int(val)} for idx, val in dept_counts.items()],
                x_label="Department",
                y_label="Headcount",
            )
        )

    if dept_col and salary_col:
        dept_sal = df.groupby(dept_col)[salary_col].mean().sort_values(ascending=False).head(8)
        charts.append(
            SectionChartSchema(
                id="salary_by_dept",
                title="Average Salary by Department",
                business_question="Which departments command the highest average compensation?",
                chart_type="bar",
                metric="Average Salary",
                grouping="Department",
                explanation="Evaluates compensation fairness and departmental payroll budgets.",
                data=[{"x": str(idx), "y": _clean_num(val)} for idx, val in dept_sal.items()],
                x_label="Department",
                y_label="Average Salary ($)",
            )
        )

    return DecisionDashboardResponse(
        dataset_id="",
        domain_name="HR & Workforce Analytics",
        executive_summary=DashboardSectionSchema(
            section_id="executive_summary",
            title="Workforce Executive Summary",
            description="Organizational headcount, compensation levels, and retention benchmarks.",
            is_available=True,
            metrics=exec_metrics,
            highlights=[
                f"Workforce of {headcount:,} employees with average salary of {_format_currency(avg_sal)}."
                if avg_sal else f"Headcount of {headcount:,} employees analyzed."
            ],
        ),
        sales_performance=DashboardSectionSchema(
            section_id="sales_performance",
            title="Departmental Staffing & Compensation",
            description="Departmental headcount distribution and compensation bands.",
            is_available=len(charts) > 0,
            charts=charts,
        ),
        profitability=DashboardSectionSchema(
            section_id="profitability",
            title="Payroll & Compensation Cost",
            description="Total payroll expenditure and benefits burden.",
            is_available=salary_col is not None,
            unavailable_reason="Salary column not available." if not salary_col else None,
            metrics=[exec_metrics[1]],
        ),
        product_analysis=DashboardSectionSchema(
            section_id="product_analysis",
            title="Role & Job Title Breakdown",
            description="Staffing across seniority and job designations.",
            is_available=len(charts) > 0,
            charts=charts,
        ),
        operations_inventory=DashboardSectionSchema(
            section_id="operations_inventory",
            title="Workforce Attendance & Operations",
            description="Daily shift attendance and scheduling.",
            is_available=False,
            unavailable_reason="Physical inventory does not apply to human resources datasets.",
        ),
        insights_recommendations=DashboardSectionSchema(
            section_id="insights_recommendations",
            title="People Strategy & Retention Actions",
            description="Data-supported recommendations for talent retention and compensation.",
            is_available=True,
            insights=[
                {
                    "what_happened": f"Recorded workforce of {headcount:,} staff members.",
                    "why_it_happened": "Reflects departmental talent requirements and hiring cohorts.",
                    "what_to_investigate": "Review compensation parity in departments showing above-average attrition.",
                    "limitations": "Individual performance ratings and subjective manager reviews are excluded.",
                }
            ],
        ),
    )


# ==============================================================================
# 4. MANUFACTURING & OPERATIONS DECISION DASHBOARD
# ==============================================================================
def _build_manufacturing_dashboard(
    df: pd.DataFrame,
    domain: DomainIdentitySchema,
    profiles: List[ColumnProfile],
) -> DecisionDashboardResponse:
    row_count = len(df)
    machine_col = _find_col(df, profiles, ("machine_id", "equipment_id", "line_id", "asset_id"))
    output_col = _find_col(df, profiles, ("units_produced", "output_quantity", "good_units", "production_volume"), "numeric")
    downtime_col = _find_col(df, profiles, ("downtime_hours", "downtime", "stoppage_time"), "numeric")
    defect_col = _find_col(df, profiles, ("defect_rate", "defects", "scrap_rate", "rejection_rate"), "numeric")
    oee_col = _find_col(df, profiles, ("oee", "equipment_effectiveness"), "numeric")

    total_units = int(df[output_col].sum()) if output_col else None
    total_dt = _clean_num(df[downtime_col].sum()) if downtime_col else None
    avg_oee = _clean_num(df[oee_col].mean()) if oee_col else None
    avg_defects = _clean_num(df[defect_col].mean()) if defect_col else None

    exec_metrics = [
        MetricStatusSchema(
            id="total_production",
            name="Total Units Manufactured",
            value=total_units,
            formatted_value=_format_number(total_units),
            status="Calculated" if output_col else "Unavailable",
            explanation=f"Sum of output column '{output_col}'." if output_col else "No production volume column found.",
            category="executive",
            business_meaning="Gross manufacturing production volume.",
        ),
        MetricStatusSchema(
            id="total_downtime",
            name="Total Equipment Downtime (Hrs)",
            value=total_dt,
            formatted_value=f"{total_dt:,.1f} hrs" if total_dt else "N/A",
            status="Calculated" if downtime_col else "Unavailable",
            explanation=f"Sum of downtime hours from '{downtime_col}'." if downtime_col else "No downtime column found.",
            category="executive",
            business_meaning="Total lost manufacturing capacity due to stoppage.",
        ),
        MetricStatusSchema(
            id="oee",
            name="Overall Equipment Effectiveness (OEE)",
            value=avg_oee,
            formatted_value=f"{avg_oee:.1f}%" if avg_oee else "N/A",
            status="Calculated" if oee_col else "Unavailable",
            explanation="Mean OEE score across machines.",
            category="executive",
            business_meaning="Standard composite measure of plant productivity.",
        ),
        MetricStatusSchema(
            id="defect_rate",
            name="Average Defect / Scrap Rate",
            value=avg_defects,
            formatted_value=f"{avg_defects:.2f}%" if avg_defects else "N/A",
            status="Calculated" if defect_col else "Unavailable",
            explanation="Mean non-conformance rate across lots.",
            category="executive",
            business_meaning="Quality control yield efficiency benchmark.",
        ),
    ]

    charts: List[SectionChartSchema] = []
    if machine_col and downtime_col:
        dt_by_m = df.groupby(machine_col)[downtime_col].sum().sort_values(ascending=False).head(8)
        charts.append(
            SectionChartSchema(
                id="downtime_by_machine",
                title="Downtime Hours by Machine",
                business_question="Which machines account for the most production downtime?",
                chart_type="bar",
                metric="Downtime (Hrs)",
                grouping="Machine",
                explanation="Pinpoints top stoppage bottlenecks to prioritize preventive maintenance.",
                data=[{"x": str(idx), "y": _clean_num(val)} for idx, val in dt_by_m.items()],
                x_label="Machine",
                y_label="Downtime (Hours)",
            )
        )

    return DecisionDashboardResponse(
        dataset_id="",
        domain_name="Manufacturing & Operations",
        executive_summary=DashboardSectionSchema(
            section_id="executive_summary",
            title="Plant Executive Summary",
            description="Manufacturing throughput, machine downtime, and quality yield benchmarks.",
            is_available=True,
            metrics=exec_metrics,
            highlights=[
                f"Manufactured {total_units:,} units with {total_dt:.1f} hours of downtime."
                if total_units and total_dt else f"Analyzed {row_count:,} manufacturing operational records."
            ],
        ),
        sales_performance=DashboardSectionSchema(
            section_id="sales_performance",
            title="Production Throughput & Line Performance",
            description="Output volumes and machine utilization.",
            is_available=len(charts) > 0,
            charts=charts,
        ),
        profitability=DashboardSectionSchema(
            section_id="profitability",
            title="Manufacturing Cost & Scrap Loss",
            description="Scrap losses and unit manufacturing cost.",
            is_available=False,
            unavailable_reason="Per-unit cost data is not recorded to calculate financial scrap losses.",
        ),
        product_analysis=DashboardSectionSchema(
            section_id="product_analysis",
            title="Equipment & Line Reliability",
            description="Machine-level downtime and reliability metrics.",
            is_available=len(charts) > 0,
            charts=charts,
        ),
        operations_inventory=DashboardSectionSchema(
            section_id="operations_inventory",
            title="Shop Floor Operations",
            description="Shift scheduling and machine status.",
            is_available=True,
            metrics=[exec_metrics[1]],
        ),
        insights_recommendations=DashboardSectionSchema(
            section_id="insights_recommendations",
            title="Maintenance & Quality Actions",
            description="Operational interventions to minimize downtime and improve first-pass yield.",
            is_available=True,
            insights=[
                {
                    "what_happened": f"Produced {total_units:,} units across {row_count:,} production batches." if total_units else "Production monitored.",
                    "why_it_happened": "Throughput variance is heavily correlated with equipment downtime stoppage.",
                    "what_to_investigate": "Deploy preventive maintenance checks on the top 2 machines driving downtime.",
                    "limitations": "Does not account for micro-stoppages under 5 minutes.",
                }
            ],
        ),
    )


# ==============================================================================
# 5. LOGISTICS & SUPPLY CHAIN DECISION DASHBOARD
# ==============================================================================
def _build_logistics_dashboard(
    df: pd.DataFrame,
    domain: DomainIdentitySchema,
    profiles: List[ColumnProfile],
) -> DecisionDashboardResponse:
    row_count = len(df)
    ship_col = _find_col(df, profiles, ("shipment_id", "consignment_id", "tracking_no", "order_id", "id"))
    carrier_col = _find_col(df, profiles, ("carrier", "carrier_name", "freight_company"), "categorical")
    cost_col = _find_col(df, profiles, ("freight_cost", "shipping_cost", "cost", "spend"), "numeric")
    days_col = _find_col(df, profiles, ("transit_days", "transit_time", "delivery_days", "days"), "numeric")
    otif_col = _find_col(df, profiles, ("is_on_time", "otif", "on_time", "delivered_on_time"), "numeric")

    total_shipments = int(df[ship_col].nunique()) if ship_col else row_count
    total_freight = _clean_num(df[cost_col].sum()) if cost_col else None
    avg_transit = _clean_num(df[days_col].mean()) if days_col else None
    otif_rate: Optional[float] = None
    if otif_col:
        otif_rate = _clean_num((df[otif_col].mean()) * 100.0)

    exec_metrics = [
        MetricStatusSchema(
            id="total_shipments",
            name="Total Shipments",
            value=total_shipments,
            formatted_value=_format_number(total_shipments),
            status="Available",
            explanation=f"Total freight movements across {row_count:,} records.",
            category="executive",
            business_meaning="Gross freight logistics volume.",
        ),
        MetricStatusSchema(
            id="total_freight_cost",
            name="Total Freight Spend",
            value=total_freight,
            formatted_value=_format_currency(total_freight),
            status="Calculated" if cost_col else "Unavailable",
            explanation=f"Sum of '{cost_col}' across all shipments.",
            category="executive",
            business_meaning="Gross transportation logistics expenditure.",
        ),
        MetricStatusSchema(
            id="avg_transit_days",
            name="Average Transit Time (Days)",
            value=avg_transit,
            formatted_value=f"{avg_transit:.1f} days" if avg_transit else "N/A",
            status="Calculated" if days_col else "Unavailable",
            explanation="Mean transit days between dispatch and delivery.",
            category="executive",
            business_meaning="Supply chain cycle velocity.",
        ),
        MetricStatusSchema(
            id="otif_rate",
            name="On-Time Delivery (OTIF) Rate",
            value=otif_rate,
            formatted_value=f"{otif_rate:.1f}%" if otif_rate is not None else "N/A",
            status="Calculated" if otif_rate is not None else "Unavailable",
            explanation="Proportion of shipments arriving on schedule.",
            category="executive",
            business_meaning="Carrier fulfillment reliability benchmark.",
        ),
    ]

    charts: List[SectionChartSchema] = []
    if carrier_col and cost_col:
        carrier_spend = df.groupby(carrier_col)[cost_col].sum().sort_values(ascending=False).head(8)
        charts.append(
            SectionChartSchema(
                id="spend_by_carrier",
                title="Freight Spend by Carrier",
                business_question="Which freight carriers manage the largest share of shipping spend?",
                chart_type="bar",
                metric="Freight Cost ($)",
                grouping="Carrier",
                explanation="Evaluates freight spend concentration to support rate renegotiations.",
                data=[{"x": str(idx), "y": _clean_num(val)} for idx, val in carrier_spend.items()],
                x_label="Carrier",
                y_label="Spend ($)",
            )
        )

    return DecisionDashboardResponse(
        dataset_id="",
        domain_name="Logistics & Supply Chain",
        executive_summary=DashboardSectionSchema(
            section_id="executive_summary",
            title="Logistics Executive Summary",
            description="Freight spend, shipment volume, transit velocity, and OTIF fulfillment rates.",
            is_available=True,
            metrics=exec_metrics,
            highlights=[
                f"Dispatched {total_shipments:,} shipments with {_format_currency(total_freight)} freight spend."
                if total_freight else f"Dispatched {total_shipments:,} freight shipments."
            ],
        ),
        sales_performance=DashboardSectionSchema(
            section_id="sales_performance",
            title="Carrier & Lane Performance",
            description="Carrier freight spend and transit velocity.",
            is_available=len(charts) > 0,
            charts=charts,
        ),
        profitability=DashboardSectionSchema(
            section_id="profitability",
            title="Transportation Cost Efficiency",
            description="Freight cost per shipment and demurrage penalties.",
            is_available=cost_col is not None,
            unavailable_reason="Cost column not recorded." if not cost_col else None,
            metrics=[exec_metrics[1]],
        ),
        product_analysis=DashboardSectionSchema(
            section_id="product_analysis",
            title="Lane & Origin/Destination Analysis",
            description="Freight lane volume and carrier allocation.",
            is_available=len(charts) > 0,
            charts=charts,
        ),
        operations_inventory=DashboardSectionSchema(
            section_id="operations_inventory",
            title="Fulfillment & Warehouse Operations",
            description="On-time delivery performance and transit delays.",
            is_available=True,
            metrics=[exec_metrics[2]],
        ),
        insights_recommendations=DashboardSectionSchema(
            section_id="insights_recommendations",
            title="Supply Chain Optimization Actions",
            description="Strategic opportunities to lower logistics costs and shorten transit days.",
            is_available=True,
            insights=[
                {
                    "what_happened": f"Processed {total_shipments:,} freight movements." if total_shipments else "Logistics data audited.",
                    "why_it_happened": "Freight expenditure concentrated among primary contract carriers.",
                    "what_to_investigate": "Renegotiate tiered volume rates on primary lanes showing above-average transit days.",
                    "limitations": "Customs clearance delays and port demurrage details are not captured.",
                }
            ],
        ),
    )


# ==============================================================================
# 6. REAL ESTATE DECISION DASHBOARD
# ==============================================================================
def _build_real_estate_dashboard(
    df: pd.DataFrame,
    domain: DomainIdentitySchema,
    profiles: List[ColumnProfile],
) -> DecisionDashboardResponse:
    row_count = len(df)
    price_col = _find_col(df, profiles, ("property_price", "sale_price", "price", "listing_price"), "numeric")
    sqft_col = _find_col(df, profiles, ("sqft", "square_feet", "area", "size_sqft"), "numeric")
    neigh_col = _find_col(df, profiles, ("neighborhood", "location", "city", "zip_code", "suburb"), "categorical")
    type_col = _find_col(df, profiles, ("property_type", "type", "category", "building_type"), "categorical")

    median_price = _clean_num(df[price_col].median()) if price_col else None
    avg_price = _clean_num(df[price_col].mean()) if price_col else None
    avg_sqft = _clean_num(df[sqft_col].mean()) if sqft_col else None

    price_sqft: Optional[float] = None
    if price_col and sqft_col:
        valid = df[[price_col, sqft_col]].dropna()
        valid = valid[valid[sqft_col] > 0]
        if not valid.empty:
            price_sqft = _clean_num((valid[price_col] / valid[sqft_col]).median())

    exec_metrics = [
        MetricStatusSchema(
            id="total_listings",
            name="Total Property Listings",
            value=row_count,
            formatted_value=str(row_count),
            status="Available",
            explanation=f"Total property records in portfolio ({row_count:,}).",
            category="executive",
            business_meaning="Total real estate market sample size.",
        ),
        MetricStatusSchema(
            id="median_price",
            name="Median Property Price",
            value=median_price,
            formatted_value=_format_currency(median_price) if median_price else "N/A",
            status="Calculated" if price_col else "Unavailable",
            explanation=f"Median of '{price_col}' across all listings.",
            category="executive",
            business_meaning="Representative real estate valuation benchmark.",
        ),
        MetricStatusSchema(
            id="price_per_sqft",
            name="Median Price / Sq Ft",
            value=price_sqft,
            formatted_value=f"${price_sqft:,.0f}/sqft" if price_sqft else "N/A",
            status="Calculated" if price_sqft else "Unavailable",
            explanation="Property price divided by square footage.",
            category="executive",
            business_meaning="Normalized unit valuation across property sizes.",
        ),
        MetricStatusSchema(
            id="avg_sqft",
            name="Average Area (Sq Ft)",
            value=avg_sqft,
            formatted_value=f"{avg_sqft:,.0f} sqft" if avg_sqft else "N/A",
            status="Calculated" if sqft_col else "Unavailable",
            explanation="Mean square footage across properties.",
            category="executive",
            business_meaning="Average physical dwelling size.",
        ),
    ]

    charts: List[SectionChartSchema] = []
    if neigh_col and price_col:
        neigh_price = df.groupby(neigh_col)[price_col].median().sort_values(ascending=False).head(8)
        charts.append(
            SectionChartSchema(
                id="price_by_neighborhood",
                title="Median Price by Neighborhood",
                business_question="Which neighborhoods command the highest property valuations?",
                chart_type="bar",
                metric="Median Price ($)",
                grouping="Neighborhood",
                explanation="Identifies premium vs value real estate sub-markets.",
                data=[{"x": str(idx), "y": _clean_num(val)} for idx, val in neigh_price.items()],
                x_label="Neighborhood",
                y_label="Median Price ($)",
            )
        )

    if sqft_col and price_col:
        sample = df[[sqft_col, price_col]].dropna().head(100)
        charts.append(
            SectionChartSchema(
                id="sqft_vs_price",
                title="Square Footage vs Valuation Impact",
                business_question="How strongly does living area scale with property sale price?",
                chart_type="scatter",
                metric="Price",
                grouping="Sq Ft",
                explanation="Illustrates the valuation premium per additional square foot.",
                data=[{"x": _clean_num(r[sqft_col]), "y": _clean_num(r[price_col])} for _, r in sample.iterrows()],
                x_label="Square Footage (Sq Ft)",
                y_label="Price ($)",
            )
        )

    return DecisionDashboardResponse(
        dataset_id="",
        domain_name="Real Estate Analytics",
        executive_summary=DashboardSectionSchema(
            section_id="executive_summary",
            title="Real Estate Market Summary",
            description="Portfolio listings, median property valuations, and price-per-square-foot benchmarks.",
            is_available=True,
            metrics=exec_metrics,
            highlights=[
                f"Median property price is {_format_currency(median_price)} with ${price_sqft:,.0f}/sqft median valuation."
                if median_price and price_sqft else f"Analyzed {row_count:,} real estate property listings."
            ],
        ),
        sales_performance=DashboardSectionSchema(
            section_id="sales_performance",
            title="Neighborhood & Regional Valuations",
            description="Valuations and sales activity across neighborhoods.",
            is_available=len(charts) > 0,
            charts=charts,
        ),
        profitability=DashboardSectionSchema(
            section_id="profitability",
            title="Rental Yield & Investment Return",
            description="Capital appreciation and cap rates.",
            is_available=False,
            unavailable_reason="Rental income and maintenance cost data are not recorded to calculate cap rates or yield.",
        ),
        product_analysis=DashboardSectionSchema(
            section_id="product_analysis",
            title="Property Type & Square Footage Analysis",
            description="Size and architectural type breakdowns.",
            is_available=len(charts) > 0,
            charts=charts,
        ),
        operations_inventory=DashboardSectionSchema(
            section_id="operations_inventory",
            title="Market Listing Inventory",
            description="Active listing inventory and days on market.",
            is_available=False,
            unavailable_reason="Days on market data not recorded in this dataset.",
        ),
        insights_recommendations=DashboardSectionSchema(
            section_id="insights_recommendations",
            title="Real Estate Market Strategy",
            description="Valuation insights for acquisitions and property investments.",
            is_available=True,
            insights=[
                {
                    "what_happened": f"Portfolio contains {row_count:,} property listings." if row_count else "Properties evaluated.",
                    "why_it_happened": "Valuations reflect location desirability and square footage.",
                    "what_to_investigate": "Identify properties trading below the median neighborhood price-per-square-foot for value-add acquisitions.",
                    "limitations": "Does not account for structural condition, renovation status, or school district ratings.",
                }
            ],
        ),
    )


# ==============================================================================
# 7. AGRICULTURE DECISION DASHBOARD
# ==============================================================================
def _build_agriculture_dashboard(
    df: pd.DataFrame,
    domain: DomainIdentitySchema,
    profiles: List[ColumnProfile],
) -> DecisionDashboardResponse:
    row_count = len(df)
    crop_col = _find_col(df, profiles, ("crop", "crop_name", "commodity", "produce"), "categorical")
    yield_col = _find_col(df, profiles, ("yield", "crop_yield", "production_yield"), "numeric")
    prod_col = _find_col(df, profiles, ("production", "production_tons", "harvest_quantity", "output"), "numeric")
    area_col = _find_col(df, profiles, ("area", "area_hectares", "acreage", "cultivated_area"), "numeric")
    rain_col = _find_col(df, profiles, ("rainfall", "annual_rainfall", "precipitation"), "numeric")

    total_prod = _clean_num(df[prod_col].sum()) if prod_col else None
    avg_yield = _clean_num(df[yield_col].mean()) if yield_col else None
    total_area = _clean_num(df[area_col].sum()) if area_col else None

    exec_metrics = [
        MetricStatusSchema(
            id="total_production",
            name="Total Agricultural Production (Tons)",
            value=total_prod,
            formatted_value=_format_number(total_prod),
            status="Calculated" if prod_col else "Unavailable",
            explanation=f"Sum of production from '{prod_col}'." if prod_col else "No production column found.",
            category="executive",
            business_meaning="Gross agricultural commodity harvest volume.",
        ),
        MetricStatusSchema(
            id="avg_yield",
            name="Average Crop Yield (Tons/Ha)",
            value=avg_yield,
            formatted_value=f"{avg_yield:.2f} tons/ha" if avg_yield else "N/A",
            status="Calculated" if yield_col else "Unavailable",
            explanation=f"Mean crop yield from '{yield_col}'." if yield_col else "No yield column found.",
            category="executive",
            business_meaning="Agricultural land productivity benchmark.",
        ),
        MetricStatusSchema(
            id="total_area",
            name="Total Cultivated Area (Hectares)",
            value=total_area,
            formatted_value=_format_number(total_area),
            status="Calculated" if area_col else "Unavailable",
            explanation="Sum of acreage across farm plots.",
            category="executive",
            business_meaning="Total land resource deployed in farming.",
        ),
    ]

    charts: List[SectionChartSchema] = []
    if crop_col and prod_col:
        crop_prod = df.groupby(crop_col)[prod_col].sum().sort_values(ascending=False).head(8)
        charts.append(
            SectionChartSchema(
                id="prod_by_crop",
                title="Production Output by Crop",
                business_question="Which crops generate the highest harvest volume?",
                chart_type="bar",
                metric="Production (Tons)",
                grouping="Crop",
                explanation="Compares commodity output to guide planting and supply chain logistics.",
                data=[{"x": str(idx), "y": _clean_num(val)} for idx, val in crop_prod.items()],
                x_label="Crop",
                y_label="Harvest Output (Tons)",
            )
        )

    return DecisionDashboardResponse(
        dataset_id="",
        domain_name="Agriculture & Crop Yield",
        executive_summary=DashboardSectionSchema(
            section_id="executive_summary",
            title="Agricultural Harvest Summary",
            description="Total crop production, average yield efficiency, and cultivated acreage.",
            is_available=True,
            metrics=exec_metrics,
            highlights=[
                f"Total harvest of {total_prod:,.0f} tons across {total_area:,.0f} cultivated hectares."
                if total_prod and total_area else f"Analyzed {row_count:,} agricultural harvest records."
            ],
        ),
        sales_performance=DashboardSectionSchema(
            section_id="sales_performance",
            title="Crop & Regional Output",
            description="Commodity output and yield comparisons.",
            is_available=len(charts) > 0,
            charts=charts,
        ),
        profitability=DashboardSectionSchema(
            section_id="profitability",
            title="Farming Costs & Crop Margins",
            description="Fertilizer, seed, and labor expenditures.",
            is_available=False,
            unavailable_reason="Input costs (fertilizer, seeds, labor) are not recorded to calculate agricultural net margins.",
        ),
        product_analysis=DashboardSectionSchema(
            section_id="product_analysis",
            title="Crop Diversity & Yield Efficiency",
            description="Productivity benchmarks by commodity.",
            is_available=len(charts) > 0,
            charts=charts,
        ),
        operations_inventory=DashboardSectionSchema(
            section_id="operations_inventory",
            title="Grain Silo & Storage Operations",
            description="Post-harvest storage and spoilage rates.",
            is_available=False,
            unavailable_reason="Post-harvest grain storage data not recorded in this dataset.",
        ),
        insights_recommendations=DashboardSectionSchema(
            section_id="insights_recommendations",
            title="Agronomy Insights & Planting Strategy",
            description="Data-supported recommendations for crop selection and irrigation management.",
            is_available=True,
            insights=[
                {
                    "what_happened": f"Produced {total_prod:,.0f} tons across recorded agricultural plots." if total_prod else "Harvest records audited.",
                    "why_it_happened": "Yield variations reflect crop biology and climatic factors.",
                    "what_to_investigate": "Benchmark low-yield plots against top-performing regional averages to address soil fertility.",
                    "limitations": "Does not account for pest infestations, fertilizer application rates, or soil pH levels.",
                }
            ],
        ),
    )


# ==============================================================================
# 8. SOCIAL MEDIA DECISION DASHBOARD
# ==============================================================================
def _build_social_media_dashboard(
    df: pd.DataFrame,
    domain: DomainIdentitySchema,
    profiles: List[ColumnProfile],
) -> DecisionDashboardResponse:
    row_count = len(df)
    imp_col = _find_col(df, profiles, ("impressions", "views"), "numeric")
    reach_col = _find_col(df, profiles, ("reach", "audience"), "numeric")
    likes_col = _find_col(df, profiles, ("likes", "reactions"), "numeric")
    shares_col = _find_col(df, profiles, ("shares", "retweets", "reposts"), "numeric")
    type_col = _find_col(df, profiles, ("content_type", "post_type", "format", "media_type"), "categorical")

    total_imp = int(df[imp_col].sum()) if imp_col else None
    total_likes = int(df[likes_col].sum()) if likes_col else None
    total_shares = int(df[shares_col].sum()) if shares_col else None
    total_eng = (total_likes or 0) + (total_shares or 0)

    eng_rate: Optional[float] = None
    if total_imp and total_imp > 0 and total_eng > 0:
        eng_rate = _clean_num((total_eng / total_imp) * 100.0)

    exec_metrics = [
        MetricStatusSchema(
            id="total_posts",
            name="Total Posts Analyzed",
            value=row_count,
            formatted_value=str(row_count),
            status="Available",
            explanation=f"Total published social media posts ({row_count:,}).",
            category="executive",
            business_meaning="Social media publishing frequency.",
        ),
        MetricStatusSchema(
            id="total_impressions",
            name="Total Social Impressions",
            value=total_imp,
            formatted_value=_format_number(total_imp),
            status="Calculated" if imp_col else "Unavailable",
            explanation="Cumulative post impressions across feeds.",
            category="executive",
            business_meaning="Total brand exposure volume.",
        ),
        MetricStatusSchema(
            id="total_engagement",
            name="Total Engagements (Likes + Shares)",
            value=total_eng,
            formatted_value=_format_number(total_eng),
            status="Calculated" if (likes_col or shares_col) else "Unavailable",
            explanation="Sum of active user interactions.",
            category="executive",
            business_meaning="Active audience interest and interaction.",
        ),
        MetricStatusSchema(
            id="engagement_rate",
            name="Engagement Rate",
            value=eng_rate,
            formatted_value=f"{eng_rate:.2f}%" if eng_rate is not None else "N/A",
            status="Calculated" if eng_rate is not None else "Unavailable",
            explanation="Total interactions divided by impressions.",
            category="executive",
            business_meaning="Audience interaction propensity benchmark.",
        ),
    ]

    charts: List[SectionChartSchema] = []
    if type_col and (likes_col or imp_col):
        metric = likes_col or imp_col
        type_eng = df.groupby(type_col)[metric].sum().sort_values(ascending=False).head(8)
        charts.append(
            SectionChartSchema(
                id="eng_by_type",
                title=f"Engagement by {prettify(type_col)}",
                business_question=f"Which {prettify(type_col)} generates the highest audience interaction?",
                chart_type="bar",
                metric=prettify(metric or "Engagement"),
                grouping=prettify(type_col),
                explanation="Informs content strategy by highlighting highest-performing media formats.",
                data=[{"x": str(idx), "y": int(val)} for idx, val in type_eng.items()],
                x_label=prettify(type_col),
                y_label="Interactions",
            )
        )

    return DecisionDashboardResponse(
        dataset_id="",
        domain_name="Social Media & Audience Engagement",
        executive_summary=DashboardSectionSchema(
            section_id="executive_summary",
            title="Social Channel Summary",
            description="Audience exposure, interaction rates, and content publishing cadence.",
            is_available=True,
            metrics=exec_metrics,
            highlights=[
                f"Generated {total_eng:,} interactions across {total_imp:,} impressions (Rate: {eng_rate:.2f}%)."
                if total_eng and total_imp and eng_rate else f"Audited {row_count:,} social media posts."
            ],
        ),
        sales_performance=DashboardSectionSchema(
            section_id="sales_performance",
            title="Content Format & Audience Engagement",
            description="Interaction velocity across formats.",
            is_available=len(charts) > 0,
            charts=charts,
        ),
        profitability=DashboardSectionSchema(
            section_id="profitability",
            title="Social Commerce & Revenue",
            description="Direct revenue attribution from social links.",
            is_available=False,
            unavailable_reason="E-commerce conversion and checkout revenue are not captured in social engagement metrics.",
        ),
        product_analysis=DashboardSectionSchema(
            section_id="product_analysis",
            title="Post & Content Breakdown",
            description="Top-performing individual posts and media types.",
            is_available=len(charts) > 0,
            charts=charts,
        ),
        operations_inventory=DashboardSectionSchema(
            section_id="operations_inventory",
            title="Publishing Operations",
            description="Posting schedule and editorial calendar.",
            is_available=False,
            unavailable_reason="Physical inventory does not apply to social media posts.",
        ),
        insights_recommendations=DashboardSectionSchema(
            section_id="insights_recommendations",
            title="Content Strategy & Viral Hooks",
            description="Data-supported recommendations for editorial calendar optimization.",
            is_available=True,
            insights=[
                {
                    "what_happened": f"Published {row_count:,} social media posts." if row_count else "Social data analyzed.",
                    "why_it_happened": "Engagement correlates strongly with visual media formats.",
                    "what_to_investigate": "Double publishing frequency for content formats generating above-median engagement rates.",
                    "limitations": "Does not account for paid dark posts or algorithmic distribution shifts.",
                }
            ],
        ),
    )


# ==============================================================================
# 9. MUSIC & STREAMING DECISION DASHBOARD
# ==============================================================================
def _build_music_dashboard(
    df: pd.DataFrame,
    domain: DomainIdentitySchema,
    profiles: List[ColumnProfile],
) -> DecisionDashboardResponse:
    row_count = len(df)
    track_col = _find_col(df, profiles, ("track_name", "title", "song", "track"))
    artist_col = _find_col(df, profiles, ("artist", "artist_name", "performer"), "categorical")
    stream_col = _find_col(df, profiles, ("streams", "plays", "listen_count", "stream_count"), "numeric")
    pop_col = _find_col(df, profiles, ("popularity", "track_popularity", "score"), "numeric")
    dur_col = _find_col(df, profiles, ("duration_ms", "duration", "length_seconds"), "numeric")
    genre_col = _find_col(df, profiles, ("genre", "genre_name", "category"), "categorical")

    total_streams = int(df[stream_col].sum()) if stream_col else None
    avg_pop = _clean_num(df[pop_col].mean()) if pop_col else None
    avg_dur = _clean_num(df[dur_col].mean() / 60000.0) if dur_col and "ms" in dur_col.lower() else _clean_num(df[dur_col].mean() / 60.0) if dur_col else None

    exec_metrics = [
        MetricStatusSchema(
            id="total_tracks",
            name="Catalog Track Count",
            value=row_count,
            formatted_value=str(row_count),
            status="Available",
            explanation=f"Total songs/tracks in catalog ({row_count:,}).",
            category="executive",
            business_meaning="Music catalog breadth.",
        ),
        MetricStatusSchema(
            id="total_streams",
            name="Total Catalog Streams",
            value=total_streams,
            formatted_value=_format_number(total_streams),
            status="Calculated" if stream_col else "Unavailable",
            explanation="Sum of all streaming plays.",
            category="executive",
            business_meaning="Gross audience consumption volume.",
        ),
        MetricStatusSchema(
            id="avg_popularity",
            name="Average Popularity Score",
            value=avg_pop,
            formatted_value=f"{avg_pop:.1f}/100" if avg_pop else "N/A",
            status="Calculated" if pop_col else "Unavailable",
            explanation="Platform algorithmic popularity benchmark.",
            category="executive",
            business_meaning="Overall catalog commercial appeal.",
        ),
    ]

    charts: List[SectionChartSchema] = []
    if track_col and stream_col:
        top_tracks = df.groupby(track_col)[stream_col].sum().sort_values(ascending=False).head(8)
        charts.append(
            SectionChartSchema(
                id="top_tracks",
                title="Top 8 Streamed Tracks",
                business_question="Which songs drive the highest stream counts?",
                chart_type="bar",
                metric="Streams",
                grouping="Track",
                explanation="Identifies hit songs driving the bulk of audience engagement.",
                data=[{"x": str(idx), "y": int(val)} for idx, val in top_tracks.items()],
                x_label="Track Name",
                y_label="Streams",
            )
        )

    return DecisionDashboardResponse(
        dataset_id="",
        domain_name="Music & Streaming Analytics",
        executive_summary=DashboardSectionSchema(
            section_id="executive_summary",
            title="Catalog Streaming Summary",
            description="Streaming counts, popularity benchmarks, and track durations.",
            is_available=True,
            metrics=exec_metrics,
            highlights=[
                f"Catalog of {row_count:,} tracks with {total_streams:,} total streams."
                if total_streams else f"Catalog of {row_count:,} music tracks analyzed."
            ],
        ),
        sales_performance=DashboardSectionSchema(
            section_id="sales_performance",
            title="Streaming Consumption & Popularity",
            description="Play counts and artist streaming performance.",
            is_available=len(charts) > 0,
            charts=charts,
        ),
        profitability=DashboardSectionSchema(
            section_id="profitability",
            title="Royalties & Publishing Revenue",
            description="Per-stream mechanical and master royalties.",
            is_available=False,
            unavailable_reason="Royalty payout rates per stream are not recorded in this dataset.",
        ),
        product_analysis=DashboardSectionSchema(
            section_id="product_analysis",
            title="Track & Artist Performance",
            description="Hit songs and artist catalog rankings.",
            is_available=len(charts) > 0,
            charts=charts,
        ),
        operations_inventory=DashboardSectionSchema(
            section_id="operations_inventory",
            title="Digital Catalog Distribution",
            description="DSP playlist inclusion and licensing.",
            is_available=False,
            unavailable_reason="Physical inventory does not apply to digital music streams.",
        ),
        insights_recommendations=DashboardSectionSchema(
            section_id="insights_recommendations",
            title="A&R Strategy & Release Windows",
            description="Data-supported recommendations for artist promotion and playlist pitching.",
            is_available=True,
            insights=[
                {
                    "what_happened": f"Catalog spans {row_count:,} recorded tracks." if row_count else "Music catalog audited.",
                    "why_it_happened": "Streaming volume exhibits extreme Pareto concentration in top singles.",
                    "what_to_investigate": "Pitch top-quartile popularity tracks into curated editorial playlists.",
                    "limitations": "Does not capture physical vinyl/CD sales or sync licensing fees.",
                }
            ],
        ),
    )


# ==============================================================================
# 10. MOVIES & ENTERTAINMENT DECISION DASHBOARD
# ==============================================================================
def _build_movies_dashboard(
    df: pd.DataFrame,
    domain: DomainIdentitySchema,
    profiles: List[ColumnProfile],
) -> DecisionDashboardResponse:
    row_count = len(df)
    rev_col = _find_col(df, profiles, ("box_office", "revenue", "gross", "worldwide_gross"), "numeric")
    rating_col = _find_col(df, profiles, ("rating", "score", "imdb_rating", "critic_score", "popularity"), "numeric")
    genre_col = _find_col(df, profiles, ("genre", "category", "type"), "categorical")
    title_col = _find_col(df, profiles, ("title", "movie_title", "name"), "categorical")

    total_rev = _clean_num(df[rev_col].sum()) if rev_col else None
    avg_rating = _clean_num(df[rating_col].mean()) if rating_col else None

    exec_metrics = [
        MetricStatusSchema(
            id="total_titles",
            name="Total Movie Titles",
            value=row_count,
            formatted_value=str(row_count),
            status="Available",
            explanation=f"Catalog size of {row_count:,} film releases.",
            category="executive",
            business_meaning="Total portfolio titles analyzed.",
        ),
        MetricStatusSchema(
            id="total_gross",
            name="Total Box Office Gross",
            value=total_rev,
            formatted_value=_format_currency(total_rev) if total_rev else "N/A",
            status="Calculated" if rev_col else "Unavailable",
            explanation=f"Sum of '{rev_col}' column." if rev_col else "No box office column found.",
            category="executive",
            business_meaning="Gross box office revenue.",
        ),
        MetricStatusSchema(
            id="avg_rating",
            name="Average Audience Rating",
            value=avg_rating,
            formatted_value=f"{avg_rating:.1f}/10" if avg_rating is not None else "N/A",
            status="Calculated" if rating_col else "Unavailable",
            explanation=f"Mean rating from '{rating_col}'.",
            category="executive",
            business_meaning="Audience and critical reception benchmark.",
        ),
    ]

    charts: List[SectionChartSchema] = []
    if genre_col and rev_col:
        genre_agg = df.groupby(genre_col)[rev_col].sum().sort_values(ascending=False).head(8)
        charts.append(
            SectionChartSchema(
                id="genre_revenue",
                title="Box Office Gross by Genre",
                business_question="Which movie genres generate the highest box office revenue?",
                chart_type="bar",
                metric=prettify(rev_col),
                grouping="Genre",
                explanation="Ranks genres by commercial returns to guide film greenlighting.",
                data=[{"x": str(idx), "y": _clean_num(val)} for idx, val in genre_agg.items()],
                x_label="Genre",
                y_label="Gross ($)",
            )
        )

    return DecisionDashboardResponse(
        dataset_id="",
        domain_name="Movies & Entertainment",
        executive_summary=DashboardSectionSchema(
            section_id="executive_summary",
            title="Film Portfolio Summary",
            description="Box office gross, critical reception, and genre popularity.",
            is_available=True,
            metrics=exec_metrics,
            highlights=[
                f"Generated {_format_currency(total_rev)} in box office across {row_count:,} titles."
                if total_rev else f"Analyzed {row_count:,} movie releases."
            ],
        ),
        sales_performance=DashboardSectionSchema(
            section_id="sales_performance",
            title="Theatrical Box Office & Genre Trends",
            description="Genre commercial returns and release patterns.",
            is_available=len(charts) > 0,
            charts=charts,
        ),
        profitability=DashboardSectionSchema(
            section_id="profitability",
            title="Production Budget & ROI",
            description="Production budget vs worldwide box office.",
            is_available=False,
            unavailable_reason="Production budget column not recorded to calculate theatrical ROI.",
        ),
        product_analysis=DashboardSectionSchema(
            section_id="product_analysis",
            title="Top Title Rankings",
            description="Highest grossing and highest rated films.",
            is_available=len(charts) > 0,
            charts=charts,
        ),
        operations_inventory=DashboardSectionSchema(
            section_id="operations_inventory",
            title="Theatrical Screen Operations",
            description="Theater screen counts and distribution windows.",
            is_available=False,
            unavailable_reason="Physical inventory does not apply to digital entertainment assets.",
        ),
        insights_recommendations=DashboardSectionSchema(
            section_id="insights_recommendations",
            title="Greenlighting & Content Strategy",
            description="Actionable recommendations for theatrical release planning.",
            is_available=True,
            insights=[
                {
                    "what_happened": f"Catalog spans {row_count:,} movie titles." if row_count else "Films analyzed.",
                    "why_it_happened": "Commercial returns concentrated in top genre categories.",
                    "what_to_investigate": "Analyze release month performance to optimize theatrical release dates.",
                    "limitations": "Does not account for streaming video on demand (SVOD) licensing deals.",
                }
            ],
        ),
    )


# ==============================================================================
# 11. SPORTS & CRICKET / IPL DECISION DASHBOARD
# ==============================================================================
def _build_sports_dashboard(
    df: pd.DataFrame,
    domain: DomainIdentitySchema,
    profiles: List[ColumnProfile],
) -> DecisionDashboardResponse:
    row_count = len(df)
    is_ball_by_ball = any(c in df.columns for c in ("batsman", "bowler", "over", "ball", "batter"))

    if is_ball_by_ball:
        batsman_col = _find_col(df, profiles, ("batsman", "batter", "player")) or "batsman"
        bowler_col = _find_col(df, profiles, ("bowler",)) or "bowler"
        runs_col = _find_col(df, profiles, ("batsman_runs", "runs", "total_runs")) or "batsman_runs"
        wicket_col = _find_col(df, profiles, ("is_wicket", "wicket")) or "is_wicket"
        over_col = _find_col(df, profiles, ("over",)) or "over"

        total_runs = int(df[runs_col].sum()) if runs_col in df.columns else 0
        total_wickets = int(df[wicket_col].sum()) if wicket_col in df.columns else 0
        total_balls = len(df)
        run_rate = _clean_num((total_runs / (total_balls / 6.0))) if total_balls > 0 else 0.0

        exec_metrics = [
            MetricStatusSchema(
                id="total_runs",
                name="Total Runs Scored",
                value=total_runs,
                formatted_value=_format_number(total_runs),
                status="Calculated",
                explanation=f"Sum of '{runs_col}' across all legal deliveries.",
                category="executive",
                business_meaning="Total aggregate match scoring volume.",
            ),
            MetricStatusSchema(
                id="total_wickets",
                name="Total Wickets Taken",
                value=total_wickets,
                formatted_value=str(total_wickets),
                status="Calculated",
                explanation=f"Sum of '{wicket_col}' across deliveries.",
                category="executive",
                business_meaning="Total dismissals recorded in dataset.",
            ),
            MetricStatusSchema(
                id="run_rate",
                name="Overall Run Rate (RPO)",
                value=run_rate,
                formatted_value=f"{run_rate:.2f}" if run_rate else "N/A",
                status="Calculated",
                explanation="Total runs scored divided by total overs completed.",
                category="executive",
                business_meaning="Scoring velocity per 6 legal deliveries.",
            ),
        ]

        perf_charts: List[SectionChartSchema] = []
        if batsman_col in df.columns and runs_col in df.columns:
            top_batsmen = df.groupby(batsman_col)[runs_col].sum().sort_values(ascending=False).head(5)
            perf_charts.append(
                SectionChartSchema(
                    id="top_run_scorers",
                    title="Top 5 Batsmen by Total Runs",
                    business_question="Which batsmen have scored the highest cumulative runs?",
                    chart_type="bar",
                    metric="Runs",
                    grouping="Batsman",
                    explanation="Ranks top individual run-scorers to evaluate batting consistency.",
                    data=[{"x": str(idx), "y": _clean_num(val)} for idx, val in top_batsmen.items()],
                    x_label="Batsman",
                    y_label="Total Runs",
                )
            )

        if bowler_col in df.columns and wicket_col in df.columns:
            top_bowlers = df.groupby(bowler_col)[wicket_col].sum().sort_values(ascending=False).head(5)
            perf_charts.append(
                SectionChartSchema(
                    id="top_wicket_takers",
                    title="Top 5 Wicket Takers",
                    business_question="Which bowlers have taken the most dismissals?",
                    chart_type="bar",
                    metric="Wickets",
                    grouping="Bowler",
                    explanation="Identifies top strike bowlers by total wickets taken.",
                    data=[{"x": str(idx), "y": _clean_num(val)} for idx, val in top_bowlers.items()],
                    x_label="Bowler",
                    y_label="Wickets Taken",
                )
            )

        if over_col in df.columns and runs_col in df.columns:
            over_prog = df.groupby(over_col)[runs_col].mean().sort_index().head(20)
            perf_charts.append(
                SectionChartSchema(
                    id="over_progression",
                    title="Average Runs per Over (1 to 20)",
                    business_question="How does run rate accelerate from Powerplay to Death Overs?",
                    chart_type="line",
                    metric="Average Runs",
                    grouping="Over",
                    explanation="Illustrates innings progression: Powerplay (1-6), Middle (7-15), Death (16-20).",
                    data=[{"x": f"Over {idx}", "y": _clean_num(val)} for idx, val in over_prog.items()],
                    x_label="Over Number",
                    y_label="Average Runs / Over",
                )
            )

    else:
        winner_col = _find_col(df, profiles, ("winner", "winning_team", "match_winner")) or "winner"
        toss_col = _find_col(df, profiles, ("toss_winner",))
        toss_dec_col = _find_col(df, profiles, ("toss_decision",))

        total_matches = row_count
        toss_advantage: Optional[float] = None
        if toss_col and winner_col and toss_col in df.columns and winner_col in df.columns:
            toss_wins = (df[toss_col] == df[winner_col]).sum()
            toss_advantage = _clean_num((toss_wins / total_matches) * 100.0) if total_matches > 0 else None

        exec_metrics = [
            MetricStatusSchema(
                id="total_matches",
                name="Total Matches",
                value=total_matches,
                formatted_value=str(total_matches),
                status="Calculated",
                explanation=f"Total match fixtures analyzed across {row_count:,} records.",
                category="executive",
                business_meaning="Total tournament match count.",
            ),
            MetricStatusSchema(
                id="toss_win_pct",
                name="Toss Advantage Win Rate",
                value=toss_advantage,
                formatted_value=f"{toss_advantage:.1f}%" if toss_advantage is not None else "N/A",
                status="Calculated" if toss_advantage is not None else "Unavailable",
                explanation="Percentage of matches won by the team that won the coin toss.",
                category="executive",
                business_meaning="Measures statistical significance of winning the toss.",
            ),
        ]

        perf_charts = []
        if winner_col in df.columns:
            team_wins = df[winner_col].value_counts().head(8)
            perf_charts.append(
                SectionChartSchema(
                    id="team_wins",
                    title="Match Wins by Franchise",
                    business_question="Which teams have won the most matches across seasons?",
                    chart_type="bar",
                    metric="Wins",
                    grouping="Team",
                    explanation="Compares historical match victories across franchises.",
                    data=[{"x": str(idx), "y": int(val)} for idx, val in team_wins.items()],
                    x_label="Franchise",
                    y_label="Match Wins",
                )
            )

        if toss_dec_col in df.columns:
            toss_dec = df[toss_dec_col].value_counts()
            perf_charts.append(
                SectionChartSchema(
                    id="toss_decision",
                    title="Toss Decision Preference (Bat vs Field)",
                    business_question="Do captains prefer batting first or chasing?",
                    chart_type="bar",
                    metric="Selections",
                    grouping="Decision",
                    explanation="Displays tactical toss decisions made by captains.",
                    data=[{"x": str(idx).capitalize(), "y": int(val)} for idx, val in toss_dec.items()],
                    x_label="Toss Decision",
                    y_label="Frequency",
                )
            )

    return DecisionDashboardResponse(
        dataset_id="",
        domain_name="Cricket / IPL Analytics",
        executive_summary=DashboardSectionSchema(
            section_id="executive_summary",
            title="Tournament Executive Summary",
            description="Tournament match outcomes, scoring aggregates, and primary performance indicators.",
            is_available=True,
            metrics=exec_metrics,
            highlights=[
                f"Analyzed {row_count:,} records with specialized cricket match modeling."
            ],
        ),
        sales_performance=DashboardSectionSchema(
            section_id="sales_performance",
            title="Match & Team Performance",
            description="Team victories, toss impact, and over-by-over scoring dynamics.",
            is_available=len(perf_charts) > 0,
            charts=perf_charts,
        ),
        profitability=DashboardSectionSchema(
            section_id="profitability",
            title="Profitability & Commercial Financials",
            description="Commercial financial metrics.",
            is_available=False,
            unavailable_reason="Profitability and commercial cost metrics do not apply to cricket match and player performance datasets.",
        ),
        product_analysis=DashboardSectionSchema(
            section_id="product_analysis",
            title="Player Performance & Impact",
            description="Individual batting, bowling, and player of the match achievements.",
            is_available=True,
            charts=perf_charts[:2] if len(perf_charts) >= 2 else perf_charts,
        ),
        operations_inventory=DashboardSectionSchema(
            section_id="operations_inventory",
            title="Operations & Match Logistics",
            description="Venue logistics and match scheduling.",
            is_available=False,
            unavailable_reason="Warehouse inventory does not apply to sports performance data.",
        ),
        insights_recommendations=DashboardSectionSchema(
            section_id="insights_recommendations",
            title="Tactical Insights & Strategy",
            description="Data-supported tactical considerations for team management.",
            is_available=True,
            insights=[
                {
                    "what_happened": f"Dataset covers {row_count:,} cricket performance records.",
                    "why_it_happened": "Performance distributions reflect tournament conditions and player matchups.",
                    "what_to_investigate": "Analyze venue-specific chasing win rates to inform toss decisions.",
                    "limitations": "Does not account for pitch deterioration, dew factor, or weather interruptions.",
                }
            ],
        ),
    )


# ==============================================================================
# 12. FINANCE & BANKING DECISION DASHBOARD
# ==============================================================================
def _build_finance_dashboard(
    df: pd.DataFrame,
    domain: DomainIdentitySchema,
    profiles: List[ColumnProfile],
) -> DecisionDashboardResponse:
    row_count = len(df)
    debit_col = _find_col(df, profiles, ("debit_amount", "debit", "expense", "withdrawal", "spent"), "numeric")
    credit_col = _find_col(df, profiles, ("credit_amount", "credit", "income", "deposit", "received"), "numeric")
    balance_col = _find_col(df, profiles, ("balance", "current_balance", "net_balance", "account_balance"), "numeric")
    branch_col = _find_col(df, profiles, ("branch", "division", "region", "account_type", "category"), "categorical")

    total_debit = _clean_num(df[debit_col].sum()) if debit_col else None
    total_credit = _clean_num(df[credit_col].sum()) if credit_col else None
    net_flow = _clean_num(total_credit - total_debit) if total_credit is not None and total_debit is not None else None

    exec_metrics = [
        MetricStatusSchema(
            id="total_income",
            name="Total Credits / Inflow",
            value=total_credit,
            formatted_value=_format_currency(total_credit),
            status="Calculated" if credit_col else "Unavailable",
            explanation=f"Sum of credit column '{credit_col}'." if credit_col else "No credit/income column found.",
            category="executive",
            business_meaning="Gross cash inflow into accounts.",
        ),
        MetricStatusSchema(
            id="total_expenses",
            name="Total Debits / Outflow",
            value=total_debit,
            formatted_value=_format_currency(total_debit),
            status="Calculated" if debit_col else "Unavailable",
            explanation=f"Sum of debit column '{debit_col}'." if debit_col else "No debit/expense column found.",
            category="executive",
            business_meaning="Gross cash outflow and disbursements.",
        ),
        MetricStatusSchema(
            id="net_cash_flow",
            name="Net Cash Flow",
            value=net_flow,
            formatted_value=_format_currency(net_flow) if net_flow is not None else "N/A",
            status="Calculated" if net_flow is not None else "Unavailable",
            explanation="Credits minus debits across all transactions.",
            category="executive",
            business_meaning="Net liquidity position change.",
        ),
    ]

    charts: List[SectionChartSchema] = []
    if branch_col and (credit_col or debit_col):
        metric_col = credit_col or debit_col
        branch_agg = df.groupby(branch_col)[metric_col].sum().sort_values(ascending=False).head(8)
        charts.append(
            SectionChartSchema(
                id="branch_volume",
                title=f"Transaction Volume by {prettify(branch_col)}",
                business_question=f"Which {prettify(branch_col)} accounts for the highest transaction flow?",
                chart_type="bar",
                metric=prettify(metric_col or "Amount"),
                grouping=prettify(branch_col),
                explanation="Compares financial activity across branches/divisions.",
                data=[{"x": str(idx), "y": _clean_num(val)} for idx, val in branch_agg.items()],
                x_label=prettify(branch_col),
                y_label="Amount ($)",
            )
        )

    return DecisionDashboardResponse(
        dataset_id="",
        domain_name="Finance & Banking",
        executive_summary=DashboardSectionSchema(
            section_id="executive_summary",
            title="Financial Executive Summary",
            description="Net cash flow, aggregate debits, credits, and liquidity metrics.",
            is_available=True,
            metrics=exec_metrics,
            highlights=[
                f"Net cash flow is {_format_currency(net_flow)} across {row_count:,} financial records."
                if net_flow is not None else f"Analyzed {row_count:,} financial transaction records."
            ],
        ),
        sales_performance=DashboardSectionSchema(
            section_id="sales_performance",
            title="Transaction Activity",
            description="Branch and divisional transaction volumes.",
            is_available=len(charts) > 0,
            charts=charts,
        ),
        profitability=DashboardSectionSchema(
            section_id="profitability",
            title="Net Cash Position",
            description="Net balance and liquidity.",
            is_available=net_flow is not None,
            unavailable_reason="Net cash flow requires both credit and debit transaction amounts." if net_flow is None else None,
            metrics=[exec_metrics[2]],
        ),
        product_analysis=DashboardSectionSchema(
            section_id="product_analysis",
            title="Account & Instrument Breakdown",
            description="Performance across account categories.",
            is_available=len(charts) > 0,
            charts=charts,
        ),
        operations_inventory=DashboardSectionSchema(
            section_id="operations_inventory",
            title="Operations & Clearing",
            description="Settlement operations.",
            is_available=False,
            unavailable_reason="Physical inventory does not apply to banking ledger datasets.",
        ),
        insights_recommendations=DashboardSectionSchema(
            section_id="insights_recommendations",
            title="Financial Insights & Actions",
            description="Audit findings and cash management recommendations.",
            is_available=True,
            insights=[
                {
                    "what_happened": f"Recorded {_format_currency(total_credit)} in credits and {_format_currency(total_debit)} in debits." if total_credit and total_debit else "Ledger entries processed.",
                    "why_it_happened": "Reflects ongoing transaction activity across accounts.",
                    "what_to_investigate": "Audit top expense disbursements and investigate high-value single transactions.",
                    "limitations": "Ledger data reflects recorded settlements; pending authorizations are not captured.",
                }
            ],
        ),
    )


# ==============================================================================
# 13. EDUCATION DECISION DASHBOARD
# ==============================================================================
def _build_education_dashboard(
    df: pd.DataFrame,
    domain: DomainIdentitySchema,
    profiles: List[ColumnProfile],
) -> DecisionDashboardResponse:
    row_count = len(df)
    score_col = _find_col(df, profiles, ("score", "marks", "grade", "percentage", "gpa"), "numeric")
    attendance_col = _find_col(df, profiles, ("attendance", "attendance_rate", "present_days"), "numeric")
    subject_col = _find_col(df, profiles, ("subject", "course", "class", "department", "grade_level"), "categorical")

    avg_score = _clean_num(df[score_col].mean()) if score_col else None
    pass_pct: Optional[float] = None
    if score_col:
        pass_count = (df[score_col] >= 40.0).sum()
        pass_pct = _clean_num((pass_count / row_count) * 100.0) if row_count > 0 else None

    exec_metrics = [
        MetricStatusSchema(
            id="total_students",
            name="Total Student Records",
            value=row_count,
            formatted_value=str(row_count),
            status="Available",
            explanation=f"Total enrolled student records in dataset ({row_count:,}).",
            category="executive",
            business_meaning="Total student cohort size.",
        ),
        MetricStatusSchema(
            id="avg_score",
            name="Average Academic Score",
            value=avg_score,
            formatted_value=f"{avg_score:.1f}" if avg_score is not None else "N/A",
            status="Calculated" if score_col else "Unavailable",
            explanation=f"Mean of score column '{score_col}'." if score_col else "No score column found.",
            category="executive",
            business_meaning="Overall cohort academic performance level.",
        ),
        MetricStatusSchema(
            id="pass_rate",
            name="Pass Percentage (>= 40%)",
            value=pass_pct,
            formatted_value=f"{pass_pct:.1f}%" if pass_pct is not None else "N/A",
            status="Calculated" if pass_pct is not None else "Unavailable",
            explanation="Proportion of students scoring 40 or higher.",
            category="executive",
            business_meaning="Benchmark academic qualification success.",
        ),
    ]

    charts = []
    if subject_col and score_col:
        sub_scores = df.groupby(subject_col)[score_col].mean().sort_values(ascending=False).head(8)
        charts.append(
            SectionChartSchema(
                id="subject_performance",
                title="Average Score by Subject / Course",
                business_question="Which subjects have the highest and lowest student performance?",
                chart_type="bar",
                metric="Average Score",
                grouping="Subject",
                explanation="Highlights subject areas requiring academic support or curriculum review.",
                data=[{"x": str(idx), "y": _clean_num(val)} for idx, val in sub_scores.items()],
                x_label="Subject",
                y_label="Average Score",
            )
        )

    return DecisionDashboardResponse(
        dataset_id="",
        domain_name="Education & Academic Performance",
        executive_summary=DashboardSectionSchema(
            section_id="executive_summary",
            title="Academic Cohort Summary",
            description="Overall student enrollment, academic scoring benchmarks, and pass rates.",
            is_available=True,
            metrics=exec_metrics,
            highlights=[
                f"Cohort average score is {avg_score:.1f} with a {pass_pct:.1f}% pass rate."
                if avg_score is not None and pass_pct is not None else f"Analyzed {row_count:,} student academic records."
            ],
        ),
        sales_performance=DashboardSectionSchema(
            section_id="sales_performance",
            title="Curriculum & Subject Performance",
            description="Subject score distributions.",
            is_available=len(charts) > 0,
            charts=charts,
        ),
        profitability=DashboardSectionSchema(
            section_id="profitability",
            title="Commercial Profitability",
            description="Commercial margins.",
            is_available=False,
            unavailable_reason="Commercial profitability metrics are not applicable to academic datasets.",
        ),
        product_analysis=DashboardSectionSchema(
            section_id="product_analysis",
            title="Course & Subject Evaluation",
            description="Evaluation of academic subjects and curriculum outcomes.",
            is_available=len(charts) > 0,
            charts=charts,
        ),
        operations_inventory=DashboardSectionSchema(
            section_id="operations_inventory",
            title="Campus & Attendance Operations",
            description="Student attendance rates.",
            is_available=attendance_col is not None,
            unavailable_reason="No attendance data recorded." if not attendance_col else None,
        ),
        insights_recommendations=DashboardSectionSchema(
            section_id="insights_recommendations",
            title="Academic Guidance & Interventions",
            description="Pedagogical insights and recommended academic interventions.",
            is_available=True,
            insights=[
                {
                    "what_happened": f"Cohort achieved an average score of {avg_score:.1f}." if avg_score else "Academic records evaluated.",
                    "why_it_happened": "Subject scores demonstrate variance between quantitative and qualitative courses.",
                    "what_to_investigate": "Introduce remedial workshops for subjects in the lowest performance quartile.",
                    "limitations": "Does not reflect student socioeconomic background or extracurricular factors.",
                }
            ],
        ),
    )


# ==============================================================================
# 14. HEALTHCARE DECISION DASHBOARD
# ==============================================================================
def _build_healthcare_dashboard(
    df: pd.DataFrame,
    domain: DomainIdentitySchema,
    profiles: List[ColumnProfile],
) -> DecisionDashboardResponse:
    row_count = len(df)
    los_col = _find_col(df, profiles, ("length_of_stay", "stay_duration", "los", "days"), "numeric")
    bill_col = _find_col(df, profiles, ("billing_amount", "charges", "cost", "total_billed"), "numeric")
    diag_col = _find_col(df, profiles, ("diagnosis", "condition", "disease", "department", "admission_type"), "categorical")

    avg_los = _clean_num(df[los_col].mean()) if los_col else None
    total_bill = _clean_num(df[bill_col].sum()) if bill_col else None

    exec_metrics = [
        MetricStatusSchema(
            id="total_patients",
            name="Total Patient Encounters",
            value=row_count,
            formatted_value=str(row_count),
            status="Available",
            explanation=f"Total clinical admission/encounter records in dataset ({row_count:,}).",
            category="executive",
            business_meaning="Clinical patient volume.",
        ),
        MetricStatusSchema(
            id="avg_los",
            name="Average Length of Stay (Days)",
            value=avg_los,
            formatted_value=f"{avg_los:.1f} days" if avg_los is not None else "N/A",
            status="Calculated" if los_col else "Unavailable",
            explanation=f"Mean of '{los_col}' column." if los_col else "No length of stay column found.",
            category="executive",
            business_meaning="Bed utilization and clinical stay efficiency.",
        ),
        MetricStatusSchema(
            id="total_billing",
            name="Total Billed Charges",
            value=total_bill,
            formatted_value=_format_currency(total_bill) if total_bill is not None else "N/A",
            status="Calculated" if bill_col else "Unavailable",
            explanation=f"Sum of '{bill_col}' column." if bill_col else "No billing column found.",
            category="executive",
            business_meaning="Gross clinical revenue billed.",
        ),
    ]

    charts = []
    if diag_col:
        diag_counts = df[diag_col].value_counts().head(8)
        charts.append(
            SectionChartSchema(
                id="top_diagnoses",
                title=f"Patient Encounters by {prettify(diag_col)}",
                business_question=f"Which {prettify(diag_col)} categories represent the highest patient volume?",
                chart_type="bar",
                metric="Patient Count",
                grouping=prettify(diag_col),
                explanation="Shows patient distribution across clinical specialties.",
                data=[{"x": str(idx), "y": int(val)} for idx, val in diag_counts.items()],
                x_label=prettify(diag_col),
                y_label="Patient Count",
            )
        )

    return DecisionDashboardResponse(
        dataset_id="",
        domain_name="Healthcare & Clinical Operations",
        executive_summary=DashboardSectionSchema(
            section_id="executive_summary",
            title="Clinical Executive Summary",
            description="Patient census, length of stay efficiency, and clinical encounter volume.",
            is_available=True,
            metrics=exec_metrics,
            highlights=[
                f"Analyzed {row_count:,} patient encounters with average stay of {avg_los:.1f} days."
                if avg_los is not None else f"Analyzed {row_count:,} clinical encounter records."
            ],
        ),
        sales_performance=DashboardSectionSchema(
            section_id="sales_performance",
            title="Clinical Volumes & Encounters",
            description="Encounters by diagnosis and department.",
            is_available=len(charts) > 0,
            charts=charts,
        ),
        profitability=DashboardSectionSchema(
            section_id="profitability",
            title="Clinical Billing & Charges",
            description="Billed charges and reimbursement rates.",
            is_available=bill_col is not None,
            unavailable_reason="No financial billing columns detected." if not bill_col else None,
            metrics=[exec_metrics[2]],
        ),
        product_analysis=DashboardSectionSchema(
            section_id="product_analysis",
            title="Diagnosis & Treatment Breakdown",
            description="Clinical specialty performance.",
            is_available=len(charts) > 0,
            charts=charts,
        ),
        operations_inventory=DashboardSectionSchema(
            section_id="operations_inventory",
            title="Hospital Bed Operations",
            description="Bed occupancy and stay duration.",
            is_available=los_col is not None,
            unavailable_reason="No length of stay data found." if not los_col else None,
            metrics=[exec_metrics[1]],
        ),
        insights_recommendations=DashboardSectionSchema(
            section_id="insights_recommendations",
            title="Clinical Insights & Operational Actions",
            description="Operational guidance for hospital administration.",
            is_available=True,
            insights=[
                {
                    "what_happened": f"Processed {row_count:,} clinical encounters." if row_count else "Encounters audited.",
                    "why_it_happened": "Volume concentration aligns with top primary diagnosis categories.",
                    "what_to_investigate": "Review discharge protocols for patient cohorts exceeding the 75th percentile of stay length.",
                    "limitations": "Does not account for patient comorbidities or readmission status.",
                }
            ],
        ),
    )


# ==============================================================================
# 15. UNKNOWN / GENERIC DATASET DECISION DASHBOARD
# ==============================================================================
def _build_generic_dashboard(
    df: pd.DataFrame,
    domain: DomainIdentitySchema,
    profiles: List[ColumnProfile],
) -> DecisionDashboardResponse:
    row_count = len(df)
    col_count = len(df.columns)

    num_cols = [p.name for p in profiles if p.role == "numeric"]
    cat_cols = [p.name for p in profiles if p.role == "categorical"]

    primary_num = num_cols[0] if num_cols else None
    primary_cat = cat_cols[0] if cat_cols else None

    primary_sum = _clean_num(df[primary_num].sum()) if primary_num else None
    primary_avg = _clean_num(df[primary_num].mean()) if primary_num else None

    exec_metrics = [
        MetricStatusSchema(
            id="row_count",
            name="Total Records",
            value=row_count,
            formatted_value=str(row_count),
            status="Available",
            explanation=f"Dataset contains {row_count:,} observation rows.",
            category="executive",
            business_meaning="Overall dataset scale.",
        ),
        MetricStatusSchema(
            id="col_count",
            name="Total Features / Attributes",
            value=col_count,
            formatted_value=str(col_count),
            status="Available",
            explanation=f"Dataset contains {col_count} columns ({len(num_cols)} numeric, {len(cat_cols)} categorical).",
            category="executive",
            business_meaning="Dimensionality of dataset.",
        ),
    ]

    if primary_num:
        exec_metrics.append(
            MetricStatusSchema(
                id="primary_measure_total",
                name=f"Total {prettify(primary_num)}",
                value=primary_sum,
                formatted_value=_format_number(primary_sum),
                status="Calculated",
                explanation=f"Sum of primary numeric measure '{primary_num}'.",
                category="executive",
                business_meaning="Aggregate volume of main numeric measure.",
            )
        )
        exec_metrics.append(
            MetricStatusSchema(
                id="primary_measure_mean",
                name=f"Average {prettify(primary_num)}",
                value=primary_avg,
                formatted_value=_format_number(primary_avg),
                status="Calculated",
                explanation=f"Arithmetic mean of '{primary_num}'.",
                category="executive",
                business_meaning="Central tendency of main numeric measure.",
            )
        )

    charts = []
    if primary_num and primary_cat:
        grouped = df.groupby(primary_cat)[primary_num].sum().sort_values(ascending=False).head(8)
        charts.append(
            SectionChartSchema(
                id="primary_breakdown",
                title=f"{prettify(primary_num)} by {prettify(primary_cat)}",
                business_question=f"How does {prettify(primary_num)} distribute across top {prettify(primary_cat)} groups?",
                chart_type="bar",
                metric=prettify(primary_num),
                grouping=prettify(primary_cat),
                explanation=f"Shows distribution of '{primary_num}' across distinct '{primary_cat}' categories.",
                data=[{"x": str(idx), "y": _clean_num(val)} for idx, val in grouped.items()],
                x_label=prettify(primary_cat),
                y_label=prettify(primary_num),
            )
        )

    return DecisionDashboardResponse(
        dataset_id="",
        domain_name="General Tabular Analysis",
        executive_summary=DashboardSectionSchema(
            section_id="executive_summary",
            title="General Dataset Summary",
            description="Overview of dataset scale, primary numeric measures, and data hygiene.",
            is_available=True,
            metrics=exec_metrics,
            highlights=[
                f"Profiled {row_count:,} records across {col_count} columns."
            ],
        ),
        sales_performance=DashboardSectionSchema(
            section_id="sales_performance",
            title="Primary Feature Breakdown",
            description="Distribution of primary measures across dominant categorical attributes.",
            is_available=len(charts) > 0,
            charts=charts,
        ),
        profitability=DashboardSectionSchema(
            section_id="profitability",
            title="Profitability & Commercial Margins",
            description="Financial profit and cost analysis.",
            is_available=False,
            unavailable_reason="Profitability and margin analysis is unavailable because no commercial cost, revenue, or profit columns were detected.",
        ),
        product_analysis=DashboardSectionSchema(
            section_id="product_analysis",
            title="Category & Entity Breakdown",
            description="Top entities and categorical distributions.",
            is_available=len(charts) > 0,
            charts=charts,
        ),
        operations_inventory=DashboardSectionSchema(
            section_id="operations_inventory",
            title="Operations & Logistics",
            description="Operational turnover and inventory tracking.",
            is_available=False,
            unavailable_reason="No supply chain, inventory, or operational columns detected in this dataset.",
        ),
        insights_recommendations=DashboardSectionSchema(
            section_id="insights_recommendations",
            title="Data Observations & Guidance",
            description="Statistical findings and data quality recommendations.",
            is_available=True,
            insights=[
                {
                    "what_happened": f"Dataset contains {row_count:,} rows and {col_count} columns.",
                    "why_it_happened": "Unsupervised profiling applied without specialized domain column assumptions.",
                    "what_to_investigate": "Inspect universal statistics for outlier values or missing cell concentrations.",
                    "limitations": "Generic analysis does not assume industry-specific business rules without verified column mappings.",
                }
            ],
        ),
    )
