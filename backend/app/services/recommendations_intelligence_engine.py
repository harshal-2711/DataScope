"""Universal, Domain-Aware Evidence-Based Recommendations Intelligence Engine.

Synthesizes real, verified, actionable business recommendations in plain, understandable English.
Every recommendation clearly answers:
- What is the problem?
- Where is the problem?
- How big is the problem?
- What action should you take?
- How will you know if it worked?
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from app.schemas.domain_blueprint import (
    ActionPlanSchema,
    DomainIdentitySchema,
    EvidenceRecommendationSchema,
    RecommendationsIntelligenceResponse,
    RecommendationsOverviewSchema,
)
from app.services.column_formatter import format_metric_display, humanize_column_name
from app.services.column_profiler import ColumnProfile
from app.services.data_quality_engine import compute_data_quality_report
from app.services.risk_engine import compute_full_risk_intelligence
from app.services.trend_engine import compute_trends_intelligence
from app.services.competition_engine import compute_competition_intelligence
from app.services.type_inference import detect_dataset_currency

logger = logging.getLogger("datascope.services.recommendations_engine")

_CATEGORY_LABELS = {
    "cost_optimization": "Cost Saving",
    "revenue_opportunities": "Revenue Growth",
    "operational_efficiency": "Operations & Speed",
    "performance_improvement": "Performance Improvement",
    "risk_mitigation": "Risk Protection",
    "data_quality": "Data Quality",
    "market_competitive_actions": "Market Competition",
}


def _normalize_col(c: str) -> str:
    """Convert column name to normalized snake_case."""
    return re.sub(r"[^a-z0-9]", "_", str(c).strip().lower()).strip("_")


def _match_kw(name: str, includes: List[str], excludes: Optional[List[str]] = None) -> bool:
    """Check if normalized column name matches include keywords while avoiding excluded terms."""
    norm = _normalize_col(name)
    tokens = set(norm.split("_"))
    if excludes:
        for ex in excludes:
            if ex in tokens or f"_{ex}_" in f"_{norm}_" or norm == ex or norm.endswith(f"_{ex}") or norm.startswith(f"{ex}_"):
                return False
    for inc in includes:
        if inc in tokens or inc == norm or f"_{inc}_" in f"_{norm}_" or norm.endswith(f"_{inc}") or norm.startswith(f"{inc}_"):
            return True
        if len(inc) >= 5 and inc in norm:
            return True
    return False


def _classify_semantic_columns(df: pd.DataFrame) -> Dict[str, List[str]]:
    """Classify DataFrame columns into business semantic roles."""
    cols = df.columns.tolist()

    # 1. Dates
    date_cols: List[str] = []
    for c in cols:
        norm = _normalize_col(c)
        if any(k in norm for k in ["order_date", "transaction_date", "trans_date", "date", "timestamp", "datetime", "time_stamp", "period", "month", "year", "day"]):
            parsed = pd.to_datetime(df[c], errors="coerce")
            if parsed.notna().sum() > len(df) * 0.4:
                date_cols.append(c)
        elif pd.api.types.is_datetime64_any_dtype(df[c]):
            date_cols.append(c)

    # 2. Revenue / Sales
    rev_cols = [c for c in cols if _match_kw(c, ["sales", "revenue", "turnover", "total_sales", "gross_sales", "order_value", "net_sales"], ["tax", "discount", "margin", "pct"]) and pd.api.types.is_numeric_dtype(df[c])]
    if not rev_cols:
        rev_cols = [c for c in cols if _normalize_col(c) in ["amount", "value", "total", "price_total"] and pd.api.types.is_numeric_dtype(df[c])]

    # 3. Profit / Earnings
    profit_cols = [c for c in cols if _match_kw(c, ["profit", "net_profit", "operating_profit", "earnings", "net_income", "margin_amount"], ["margin_pct", "ratio", "rate"]) and pd.api.types.is_numeric_dtype(df[c])]

    # 4. Cost / Expenses / Shipping
    cost_cols = [c for c in cols if _match_kw(c, ["cost", "cogs", "expense", "expenses", "spend", "operational_cost", "unit_cost", "shipping_cost", "freight"], ["ratio", "pct"]) and pd.api.types.is_numeric_dtype(df[c])]

    # 5. Discount
    discount_cols = [c for c in cols if _match_kw(c, ["discount", "discount_pct", "markdown", "rebate", "discount_rate", "promo_pct"]) and pd.api.types.is_numeric_dtype(df[c])]

    # 6. Quantity / Volume
    qty_cols = [c for c in cols if _match_kw(c, ["quantity", "qty", "units", "volume", "order_quantity", "count", "headcount", "attendance"], ["discount", "amount", "price"]) and pd.api.types.is_numeric_dtype(df[c])]

    # 7. Categories vs Products (Disambiguated)
    cat_cols = [c for c in cols if _match_kw(c, ["category", "sub_category", "department", "item_group", "genre", "product_category", "division", "line_of_business", "sector"])]
    prod_cols = [c for c in cols if _match_kw(c, ["product", "item", "sku", "product_name", "item_name", "model", "article", "title"]) and c not in cat_cols]
    if not prod_cols:
        prod_cols = [c for c in cols if _normalize_col(c) in ["product", "item", "sku", "product_name", "item_name", "model"]]
        cat_cols = [c for c in cat_cols if c not in prod_cols]

    # 8. Geographic / Regions
    region_cols = [c for c in cols if _match_kw(c, ["region", "country", "state", "city", "zone", "territory", "market", "location", "branch", "store", "province"])]

    # 9. Customer / User / Segments
    cust_cols = [c for c in cols if _match_kw(c, ["customer", "client", "account", "customer_id", "buyer", "login_type", "user_type", "segment", "customer_segment", "gender", "device_type", "payment_method"])]

    # 10. Suppliers / Vendors
    supp_cols = [c for c in cols if _match_kw(c, ["supplier", "vendor", "provider", "distributor", "carrier"])]

    # 11. Turnaround / Delay / Aging
    aging_cols = [c for c in cols if _match_kw(c, ["aging", "delay", "delivery_delay", "lead_time", "turnaround", "processing_time", "days_to_ship", "wait_time"]) and pd.api.types.is_numeric_dtype(df[c])]

    # 12. Priority / Severity
    prio_cols = [c for c in cols if _match_kw(c, ["order_priority", "priority", "severity", "tier", "status", "urgency"])]

    # 13. HR / Workforce
    attrition_cols = [c for c in cols if _match_kw(c, ["attrition", "left", "turnover", "resigned", "terminated", "exit"])]
    dept_cols = [c for c in cols if _match_kw(c, ["department", "dept", "team", "business_unit", "function", "division"])]

    # 14. Sports Analytics
    player_cols = [c for c in cols if _match_kw(c, ["player", "batsman", "bowler", "athlete", "driver", "runner", "driver_name", "team_name"])]
    score_cols = [c for c in cols if _match_kw(c, ["runs", "points", "goals", "score", "strike_rate", "wickets", "assists", "yards"]) and pd.api.types.is_numeric_dtype(df[c])]

    # 15. Inventory
    inventory_cols = [c for c in cols if _match_kw(c, ["inventory", "stock", "stock_level", "units_in_stock", "quantity_on_hand", "reorder_level"]) and pd.api.types.is_numeric_dtype(df[c])]

    # 16. Unit Price / Rate
    price_cols = [c for c in cols if _match_kw(c, ["unit_price", "price", "rate", "purchase_price", "item_price", "unit_rate"]) and pd.api.types.is_numeric_dtype(df[c])]

    # Fallback categorical dimensions if none detected
    if not cat_cols and not prod_cols and not region_cols and not cust_cols:
        for c in cols:
            if not pd.api.types.is_numeric_dtype(df[c]) and not pd.api.types.is_datetime64_any_dtype(df[c]):
                n_uniq = df[c].nunique()
                if 1 < n_uniq <= max(len(df) * 0.5, 50):
                    cat_cols.append(c)

    return {
        "date": date_cols,
        "revenue": rev_cols,
        "profit": profit_cols,
        "cost": cost_cols,
        "discount": discount_cols,
        "quantity": qty_cols,
        "category": cat_cols,
        "product": prod_cols,
        "region": region_cols,
        "customer": cust_cols,
        "supplier": supp_cols,
        "aging": aging_cols,
        "priority": prio_cols,
        "attrition": attrition_cols,
        "dept": dept_cols,
        "player": player_cols,
        "score": score_cols,
        "inventory": inventory_cols,
        "price": price_cols,
    }


def compute_recommendations_intelligence(
    df: pd.DataFrame,
    dataset_id: str,
    profiles: List[ColumnProfile],
    domain: DomainIdentitySchema,
    dataset_currency: Optional[str] = None,
    benchmark_df: Optional[pd.DataFrame] = None,
    benchmark_filename: Optional[str] = None,
) -> RecommendationsIntelligenceResponse:
    """Generate up to 5 real, high-value, evidence-backed business recommendations."""
    domain_id = domain.domain_id if domain else "general"
    domain_name = domain.name if domain else "General Analytics"
    currency = dataset_currency or detect_dataset_currency(df)

    # Empty or tiny dataset handling
    if df is None or df.empty or len(df) < 3:
        return RecommendationsIntelligenceResponse(
            dataset_id=dataset_id,
            is_available=False,
            domain_id=domain_id,
            domain_name=domain_name,
            currency_symbol=currency,
            overview=RecommendationsOverviewSchema(
                total_recommendations=0,
                critical_count=0,
                high_count=0,
                medium_count=0,
                low_count=0,
                evidence_backed_count=0,
                data_limitations_summary=[
                    "Insufficient records: The dataset contains fewer than 3 valid rows.",
                    "At least 5–10 records are required to calculate reliable business patterns.",
                ],
                summary_statement="Insufficient data for reliable recommendations. Please upload a dataset with structured business records.",
            ),
            recommendations=[],
            categories_present=[],
            has_time_dimension=False,
            analyzed_at=datetime.now(timezone.utc).isoformat(),
        )

    candidates: List[EvidenceRecommendationSchema] = []
    rec_counter = 1
    total_rows = len(df)

    # Classify semantic columns
    classes = _classify_semantic_columns(df)
    date_cols = classes["date"]
    rev_cols = classes["revenue"]
    profit_cols = classes["profit"]
    cost_cols = classes["cost"]
    discount_cols = classes["discount"]
    qty_cols = classes["quantity"]
    category_cols = classes["category"]
    product_cols = classes["product"]
    region_cols = classes["region"]
    customer_cols = classes["customer"]
    supplier_cols = classes["supplier"]
    aging_cols = classes["aging"]
    prio_cols = classes["priority"]
    attrition_cols = classes["attrition"]
    dept_cols = classes["dept"]
    player_cols = classes["player"]
    score_cols = classes["score"]
    inventory_cols = classes["inventory"]
    price_cols = classes["price"]

    has_time_dim = len(date_cols) > 0
    date_col = date_cols[0] if date_cols else None

    # Track data limitations dynamically based on missing dimensions
    data_limitations: List[str] = []
    if not has_time_dim:
        data_limitations.append("No date column found: Time-based trend analysis and monthly comparisons are unavailable.")
    if not profit_cols and not cost_cols:
        data_limitations.append("No profit or cost column found: Profit margin analysis and cost savings recommendations are unavailable.")
    if not category_cols and not product_cols and not region_cols:
        data_limitations.append("No category or product column found: Segment-level breakdown recommendations are unavailable.")
    if not benchmark_df or benchmark_df.empty:
        data_limitations.append("No external market benchmark uploaded: Recommendations are based only on your uploaded dataset.")

    # =========================================================================
    # MODULE 1: E-COMMERCE / RETAIL / SALES DEEP-DIVE
    # =========================================================================

    # 1A. Product-Level Profit Margin Compression on High-Volume Leaders
    target_prod_col = product_cols[0] if product_cols else (category_cols[0] if category_cols else None)
    if rev_cols and profit_cols and target_prod_col:
        r_col = rev_cols[0]
        p_col = profit_cols[0]
        try:
            prod_summary = df.groupby(target_prod_col).agg(
                sales=(r_col, "sum"),
                profit=(p_col, "sum"),
                orders=(target_prod_col, "count"),
            ).reset_index()
            prod_summary = prod_summary.dropna()

            if len(prod_summary) >= 2:
                prod_summary["margin_pct"] = (prod_summary["profit"] / prod_summary["sales"].replace(0, np.nan)) * 100
                total_portfolio_sales = float(prod_summary["sales"].sum())
                total_portfolio_profit = float(prod_summary["profit"].sum())
                portfolio_avg_margin = (total_portfolio_profit / total_portfolio_sales * 100) if total_portfolio_sales > 0 else 0.0
                median_sales = float(prod_summary["sales"].median())

                # Find volume leaders where margin is compressed or negative
                low_margin_prods = prod_summary[
                    (prod_summary["sales"] >= median_sales * 0.7) &
                    ((prod_summary["margin_pct"] < portfolio_avg_margin - 12.0) | (prod_summary["profit"] < 0))
                ].sort_values("sales", ascending=False)

                if not low_margin_prods.empty:
                    worst_row = low_margin_prods.iloc[0]
                    p_name = str(worst_row[target_prod_col])
                    p_sales = float(worst_row["sales"])
                    p_profit = float(worst_row["profit"])
                    p_margin = float(worst_row["margin_pct"])
                    p_orders = int(worst_row["orders"])
                    p_sales_share = (p_sales / total_portfolio_sales * 100) if total_portfolio_sales > 0 else 0.0
                    margin_gap = p_margin - portfolio_avg_margin

                    p_sales_fmt = format_metric_display(p_sales, unit=currency, semantic_type="currency")
                    p_profit_fmt = format_metric_display(p_profit, unit=currency, semantic_type="currency")

                    is_negative = p_profit < 0
                    prio = "critical" if is_negative and p_sales_share > 5.0 else ("high" if abs(margin_gap) > 20.0 or p_sales_share > 5.0 else "medium")

                    candidates.append(
                        EvidenceRecommendationSchema(
                            rec_id=f"rec_ec_prod_margin_{rec_counter}",
                            title=f"Improve Profit on High-Volume Product: {p_name}",
                            category="cost_optimization",
                            category_label=_CATEGORY_LABELS["cost_optimization"],
                            priority=prio,
                            priority_reason=f"'{p_name}' generates {p_sales_fmt} in sales ({p_sales_share:.1f}% of total) but earns only {p_margin:.1f}% margin compared to the {portfolio_avg_margin:.1f}% store average.",
                            short_summary=f"'{p_name}' is selling in large volume but earns a {p_margin:.1f}% profit margin, which is below the store average of {portfolio_avg_margin:.1f}%.",
                            key_metrics=[
                                {"label": "Product Margin", "value": f"{p_margin:.1f}%"},
                                {"label": "Store Average", "value": f"{portfolio_avg_margin:.1f}%"},
                                {"label": "Sales Affected", "value": p_sales_fmt},
                                {"label": "Orders Affected", "value": f"{p_orders:,}"},
                            ],
                            what_we_found=[
                                f"'{p_name}' generated {p_sales_fmt} in sales across {p_orders:,} orders ({p_sales_share:.1f}% of total revenue).",
                                f"Total profit earned was {p_profit_fmt}, giving a {p_margin:.1f}% realized profit margin.",
                                f"This profit margin is {abs(margin_gap):.1f} percentage points below the store average of {portfolio_avg_margin:.1f}%.",
                            ],
                            why_it_matters="Selling large quantities of low-margin products uses warehouse space, handling time, and shipping capacity without producing healthy business profit.",
                            action_steps=[
                                f"Review the supplier purchase cost for '{p_name}'.",
                                f"Reduce promotional discounts on '{p_name}' by 3–5% to test price sensitivity.",
                                f"Bundle '{p_name}' with higher-margin accessories to lift overall order profitability.",
                                "Renegotiate wholesale rates with suppliers if order volume remains strong.",
                            ],
                            expected_result=f"Increase profit margin on '{p_name}' closer to the store average of {portfolio_avg_margin:.1f}%.",
                            business_problem=f"Significant sales volume generated by '{p_name}' yields compressed profit margins ({p_margin:.1f}% vs {portfolio_avg_margin:.1f}% store average).",
                            evidence=f"Revenue: {p_sales_fmt} ({p_sales_share:.1f}% share) | Profit: {p_profit_fmt} | Margin: {p_margin:.1f}% | Store Baseline: {portfolio_avg_margin:.1f}% | Orders: {p_orders:,}.",
                            metric_name="Profit Margin %",
                            entity_name=p_name,
                            current_value=f"{p_margin:.1f}%",
                            baseline_value=f"{portfolio_avg_margin:.1f}% Store Avg",
                            pct_change=f"{margin_gap:.1f}% pts vs benchmark",
                            root_cause_signal=f"High sales volume in '{p_name}' is paired with high supplier costs or frequent discounts.",
                            recommended_action=f"Review supplier purchase costs and reduce discount depth on '{p_name}' by 3–5% to restore healthy margins.",
                            expected_objective="Increase Profit Margin on Key Products",
                            data_required="Product cost breakdown, shipping cost per unit, and price elasticity test results.",
                            limitations="The dataset reflects past transactions. Check whether this product was discounted intentionally as a promotional lead-in.",
                            action_plan=ActionPlanSchema(
                                immediate_action=f"Check supplier invoice costs and active discount rules for '{p_name}'.",
                                follow_up_investigation=f"Compare pricing with competitors and test a 3–5% price adjustment on '{p_name}'.",
                                metric_to_monitor=f"Profit Margin % ({p_name})",
                                suggested_review_period="Monthly business review",
                                data_required="Supplier contract pricing and unit shipping costs.",
                            ),
                            suggested_investigation_route="/explore",
                            suggested_investigation_label=f"Inspect '{p_name}' in Explore",
                            relevant_metric="Profit Margin %",
                            source_columns=[target_prod_col, r_col, p_col],
                            time_period=None,
                            evidence_strength="verified_statistical_finding",
                        )
                    )
                    rec_counter += 1
        except Exception as e:
            logger.debug("Product margin recommendation error: %s", e)

    # 1B. Promotional Discount Depth Margin Erosion
    if discount_cols and rev_cols and profit_cols:
        d_col = discount_cols[0]
        r_col = rev_cols[0]
        p_col = profit_cols[0]
        try:
            temp_disc = df.dropna(subset=[d_col, r_col, p_col]).copy()
            if temp_disc[d_col].max() > 1.0:
                temp_disc["_disc_dec"] = temp_disc[d_col] / 100.0
            else:
                temp_disc["_disc_dec"] = temp_disc[d_col]

            temp_disc["_tier"] = pd.cut(
                temp_disc["_disc_dec"],
                bins=[-0.01, 0.15, 0.30, 1.0],
                labels=["Standard (<15%)", "Moderate (15-30%)", "Deep (30%+)"],
            )

            disc_tiers = temp_disc.groupby("_tier", observed=False).agg(
                sales=(r_col, "sum"),
                profit=(p_col, "sum"),
                orders=(r_col, "count"),
            ).reset_index()

            if len(disc_tiers) >= 2:
                disc_tiers["margin_pct"] = (disc_tiers["profit"] / disc_tiers["sales"].replace(0, np.nan)) * 100
                deep_row = disc_tiers[disc_tiers["_tier"] == "Deep (30%+)"]
                std_row = disc_tiers[disc_tiers["_tier"] == "Standard (<15%)"]

                if not deep_row.empty and not std_row.empty:
                    deep_sales = float(deep_row["sales"].iloc[0])
                    deep_profit = float(deep_row["profit"].iloc[0])
                    deep_margin = float(deep_row["margin_pct"].iloc[0])
                    deep_orders = int(deep_row["orders"].iloc[0])

                    std_margin = float(std_row["margin_pct"].iloc[0])
                    total_sales = float(disc_tiers["sales"].sum())
                    deep_share = (deep_sales / total_sales * 100) if total_sales > 0 else 0.0
                    margin_erosion_pct = std_margin - deep_margin

                    if margin_erosion_pct > 2.0 and deep_sales > 0:
                        deep_sales_fmt = format_metric_display(deep_sales, unit=currency, semantic_type="currency")

                        candidates.append(
                            EvidenceRecommendationSchema(
                                rec_id=f"rec_ec_discount_erosion_{rec_counter}",
                                title="High Discounts Are Reducing Profit",
                                category="cost_optimization",
                                category_label=_CATEGORY_LABELS["cost_optimization"],
                                priority="high" if deep_sales > 500000 or margin_erosion_pct > 4.0 else "medium",
                                priority_reason=f"Orders with discounts above 30% account for {deep_sales_fmt} ({deep_share:.1f}% of sales) but yield a {deep_margin:.1f}% margin vs {std_margin:.1f}% on standard discounts.",
                                short_summary="Orders with discounts above 30% generate lower profit margins than orders with standard discounts.",
                                key_metrics=[
                                    {"label": "High-Discount Margin", "value": f"{deep_margin:.1f}%"},
                                    {"label": "Standard Margin", "value": f"{std_margin:.1f}%"},
                                    {"label": "Difference", "value": f"-{margin_erosion_pct:.1f} pts"},
                                    {"label": "Sales Affected", "value": deep_sales_fmt},
                                ],
                                what_we_found=[
                                    f"High-discount orders (30%+): {deep_margin:.1f}% profit margin.",
                                    f"Standard-discount orders (<15%): {std_margin:.1f}% profit margin.",
                                    f"Margin difference: {margin_erosion_pct:.1f} percentage points.",
                                    f"Sales affected: {deep_sales_fmt} across {deep_orders:,} orders ({deep_share:.1f}% of total sales).",
                                ],
                                why_it_matters="Higher discounts may reduce the profit earned from each order without significantly growing total customer demand.",
                                action_steps=[
                                    "Review products currently receiving discounts above 30%.",
                                    "Identify products with low profit margins.",
                                    "Test lower discounts, such as 20–25%, where appropriate.",
                                    "Keep higher discounts for clearance inventory only.",
                                ],
                                expected_result="Improve profit from discounted orders while maintaining sales volume.",
                                business_problem=f"Orders with discounts above 30% yield {deep_margin:.1f}% margin compared to {std_margin:.1f}% on standard orders.",
                                evidence=f"High-Discount (30%+) Sales: {deep_sales_fmt} | Margin: {deep_margin:.1f}% vs Standard (<15%) Margin: {std_margin:.1f}% | Difference: -{margin_erosion_pct:.1f} percentage points | Orders: {deep_orders:,}.",
                                metric_name="Profit Margin by Discount Tier",
                                entity_name="Discounts Above 30%",
                                current_value=f"{deep_margin:.1f}%",
                                baseline_value=f"{std_margin:.1f}% Standard Margin",
                                pct_change=f"-{margin_erosion_pct:.1f}% pts",
                                root_cause_signal="Large discounts are linked to lower profit margins. The dataset does not prove whether discounts caused the decline.",
                                recommended_action="Cap standard discounts at 20–25% for high-velocity items and reserve 30%+ discounts for clearance items.",
                                expected_objective="Improve Profit from Discounted Orders",
                                data_required="Promotional campaign codes, coupon redemption history, and marketing ad spend.",
                                limitations=f"The margin difference is observed across {deep_orders:,} transactions. Actual profit recovery will depend on customer price sensitivity.",
                                action_plan=ActionPlanSchema(
                                    immediate_action="Review all active discount rules and coupons over 25%.",
                                    follow_up_investigation="Compare customer re-order rates between full-price and discounted buyers.",
                                    metric_to_monitor="Average Discount Rate % vs Profit Margin %",
                                    suggested_review_period="Bi-weekly sales review",
                                    data_required="Detailed coupon redemption and promo campaign logs.",
                                ),
                                suggested_investigation_route="/trends",
                                suggested_investigation_label="View Discount vs Margin Trends",
                                relevant_metric="Discount Rate %",
                                source_columns=[d_col, r_col, p_col],
                                time_period=None,
                                evidence_strength="verified_statistical_finding",
                            )
                        )
                        rec_counter += 1
        except Exception as e:
            logger.debug("Discount erosion recommendation error: %s", e)

    # 1C. Periodic / Month-over-Month Sales Contractions with Root-Cause Category Attribution
    if date_col and rev_cols:
        r_col = rev_cols[0]
        try:
            temp_trend = df.dropna(subset=[date_col, r_col]).copy()
            temp_trend["_dt"] = pd.to_datetime(temp_trend[date_col], errors="coerce")
            temp_trend = temp_trend.dropna(subset=["_dt"]).sort_values("_dt")

            if len(temp_trend) >= 20:
                temp_trend["_period"] = temp_trend["_dt"].dt.to_period("M")
                monthly = temp_trend.groupby("_period")[r_col].sum().reset_index()

                if len(monthly) >= 2:
                    monthly["sales_diff"] = monthly[r_col].diff()
                    monthly["sales_pct"] = (monthly["sales_diff"] / monthly[r_col].shift(1)) * 100
                    drops = monthly[monthly["sales_pct"] < -8.0].sort_values("sales_pct")

                    if not drops.empty:
                        worst_drop = drops.iloc[0]
                        period_idx = int(worst_drop.name)
                        prev_period = monthly.iloc[period_idx - 1]

                        p1_name = str(prev_period["_period"])
                        p2_name = str(worst_drop["_period"])
                        p1_val = float(prev_period[r_col])
                        p2_val = float(worst_drop[r_col])
                        drop_amt = abs(float(worst_drop["sales_diff"]))
                        drop_pct = abs(float(worst_drop["sales_pct"]))

                        cat_attr_str = ""
                        worst_cat_name = "Primary Products"
                        cat_share_pct = 0.0
                        cat_loss_fmt = ""
                        if category_cols:
                            c_col = category_cols[0]
                            t1_cat = temp_trend[temp_trend["_period"] == prev_period["_period"]].groupby(c_col)[r_col].sum()
                            t2_cat = temp_trend[temp_trend["_period"] == worst_drop["_period"]].groupby(c_col)[r_col].sum()
                            cat_diffs = (t2_cat - t1_cat).dropna().sort_values()
                            if not cat_diffs.empty and cat_diffs.iloc[0] < 0:
                                worst_cat_name = str(cat_diffs.index[0])
                                cat_loss = abs(float(cat_diffs.iloc[0]))
                                cat_loss_fmt = format_metric_display(cat_loss, unit=currency, semantic_type="currency")
                                cat_share_pct = min(round((cat_loss / drop_amt) * 100, 1), 100.0)
                                cat_attr_str = f" Category '{worst_cat_name}' accounted for {cat_loss_fmt} ({cat_share_pct}%) of the decline."

                        drop_amt_fmt = format_metric_display(drop_amt, unit=currency, semantic_type="currency")
                        p1_fmt = format_metric_display(p1_val, unit=currency, semantic_type="currency")
                        p2_fmt = format_metric_display(p2_val, unit=currency, semantic_type="currency")

                        prio = "high" if drop_pct > 15.0 or drop_amt > 100000 else "medium"

                        what_found_list = [
                            f"Sales decreased from {p1_fmt} ({p1_name}) to {p2_fmt} ({p2_name}).",
                            f"Total sales drop: {drop_amt_fmt} (-{drop_pct:.1f}%).",
                        ]
                        if cat_attr_str:
                            what_found_list.append(f"Category '{worst_cat_name}' drove {cat_share_pct:.1f}% of the decrease ({cat_loss_fmt}).")

                        candidates.append(
                            EvidenceRecommendationSchema(
                                rec_id=f"rec_ec_trend_drop_{rec_counter}",
                                title=f"Sales Decreased in Recent Period ({p2_name})",
                                category="revenue_opportunities",
                                category_label=_CATEGORY_LABELS["revenue_opportunities"],
                                priority=prio,
                                priority_reason=f"Monthly sales declined by {drop_pct:.1f}% from {p1_fmt} to {p2_fmt} (drop of {drop_amt_fmt}).",
                                short_summary=f"Sales dropped by {drop_pct:.1f}% from {p1_name} to {p2_name}, led by a pullback in {worst_cat_name}.",
                                key_metrics=[
                                    {"label": "Sales Decline", "value": f"-{drop_pct:.1f}%"},
                                    {"label": "Revenue Drop", "value": f"-{drop_amt_fmt}"},
                                    {"label": f"{p2_name} Sales", "value": p2_fmt},
                                    {"label": f"{p1_name} Sales", "value": p1_fmt},
                                ],
                                what_we_found=what_found_list,
                                why_it_matters="A sharp sequential sales decline can lead to unsold inventory and lower operating cash flow.",
                                action_steps=[
                                    f"Check if top-selling items in '{worst_cat_name}' had stockouts during {p2_name}.",
                                    f"Compare promotional campaign pacing between {p1_name} and {p2_name}.",
                                    f"Reach out to key retail or wholesale customers in '{worst_cat_name}' to confirm upcoming demand.",
                                ],
                                expected_result=f"Stabilize monthly sales and return category '{worst_cat_name}' to steady growth.",
                                business_problem=f"Sequential sales drop of {drop_pct:.1f}% occurred in {p2_name}.{cat_attr_str}",
                                evidence=f"Sales fell from {p1_fmt} to {p2_fmt} (-{drop_pct:.1f}%). Decrease: -{drop_amt_fmt}.{cat_attr_str}",
                                metric_name="Monthly Sales Revenue",
                                entity_name=worst_cat_name,
                                current_value=p2_fmt,
                                baseline_value=p1_fmt,
                                pct_change=f"-{drop_pct:.1f}%",
                                root_cause_signal=f"Customer order volume or average basket size decreased following the {p1_name} peak.{cat_attr_str}",
                                recommended_action=f"Check inventory availability and marketing campaign pacing for '{worst_cat_name}' to prevent post-peak sales slowdowns.",
                                expected_objective="Stabilize Monthly Sales",
                                data_required="Daily out-of-stock logs and promotional spend schedules.",
                                limitations="The dataset does not record external competitor campaigns, weather events, or broader economic shifts.",
                                action_plan=ActionPlanSchema(
                                    immediate_action=f"Check warehouse stock levels and out-of-stock frequency during {p2_name}.",
                                    follow_up_investigation=f"Review marketing and email campaign schedules for '{worst_cat_name}'.",
                                    metric_to_monitor=f"Monthly Sales ({worst_cat_name})",
                                    suggested_review_period="Monthly commercial review",
                                    data_required="Daily inventory logs and marketing spend schedules.",
                                ),
                                suggested_investigation_route="/trends",
                                suggested_investigation_label="View Monthly Sales Trend",
                                relevant_metric="Sales Revenue",
                                source_columns=[date_col, r_col] + ([category_cols[0]] if category_cols else []),
                                time_period=f"{p1_name} vs {p2_name}",
                                evidence_strength="verified_statistical_finding",
                            )
                        )
                        rec_counter += 1
        except Exception as e:
            logger.debug("Periodic sales contraction recommendation error: %s", e)

    # 1D. Operational SLA Turnaround Bottlenecks (Aging by Order Priority)
    if aging_cols and prio_cols:
        ag_col = aging_cols[0]
        pr_col = prio_cols[0]
        try:
            prio_summary = df.groupby(pr_col).agg(
                avg_aging=(ag_col, "mean"),
                max_aging=(ag_col, "max"),
                orders=(ag_col, "count"),
            ).reset_index()

            crit_row = prio_summary[prio_summary[pr_col].astype(str).str.strip().str.lower().isin(["critical", "high", "urgent", "express"])]
            if not crit_row.empty:
                crit_data = crit_row.sort_values("avg_aging", ascending=False).iloc[0]
                tier_name = str(crit_data[pr_col])
                avg_age = float(crit_data["avg_aging"])
                max_age = float(crit_data["max_aging"])
                tier_orders = int(crit_data["orders"])
                overall_avg_age = float(df[ag_col].mean())

                if avg_age > 3.0 and tier_orders >= 50:
                    candidates.append(
                        EvidenceRecommendationSchema(
                            rec_id=f"rec_ec_aging_bottleneck_{rec_counter}",
                            title=f"High-Priority Orders Have Slow Turnaround Times ({avg_age:.1f} Days Avg)",
                            category="operational_efficiency",
                            category_label=_CATEGORY_LABELS["operational_efficiency"],
                            priority="high" if avg_age > 5.0 else "medium",
                            priority_reason=f"{tier_orders:,} '{tier_name}' priority orders average {avg_age:.1f} days turnaround (longest: {max_age:.1f} days) compared to the 2.0-day target.",
                            short_summary=f"'{tier_name}' priority orders average {avg_age:.1f} days to fulfill, which is slower than standard express delivery expectations.",
                            key_metrics=[
                                {"label": "Average Time", "value": f"{avg_age:.1f} days"},
                                {"label": "Target Time", "value": "2.0 days"},
                                {"label": "Longest Delay", "value": f"{max_age:.1f} days"},
                                {"label": "Orders Affected", "value": f"{tier_orders:,}"},
                            ],
                            what_we_found=[
                                f"{tier_orders:,} orders marked as '{tier_name}' took an average of {avg_age:.1f} days to process.",
                                f"Some orders experienced fulfillment times as long as {max_age:.1f} days.",
                                f"Overall store fulfillment average is {overall_avg_age:.1f} days.",
                            ],
                            why_it_matters="Customers who place high-priority orders expect fast delivery. Delays can lead to order cancellations and negative reviews.",
                            action_steps=[
                                f"Set up a dedicated priority queue in the warehouse for '{tier_name}' orders.",
                                "Ensure high-priority orders are picked and packed within 24 hours of placement.",
                                "Partner with courier services to provide guaranteed same-day or next-day pickup.",
                            ],
                            expected_result=f"Reduce average fulfillment time for '{tier_name}' orders to under 2.0 days.",
                            business_problem=f"Elevated fulfillment aging on high-priority orders ({tier_name} orders average {avg_age:.1f} days).",
                            evidence=f"Tier: '{tier_name}' | Average Time: {avg_age:.1f} days | Longest: {max_age:.1f} days | Orders: {tier_orders:,} | Store Avg: {overall_avg_age:.1f} days.",
                            metric_name="Order Turnaround (Days)",
                            entity_name=f"{tier_name} Priority",
                            current_value=f"{avg_age:.1f} days",
                            baseline_value="2.0 days Target",
                            pct_change=f"+{avg_age - 2.0:.1f} days above target",
                            root_cause_signal=f"Orders marked '{tier_name}' are processed through standard warehouse lines without fast-track sorting.",
                            recommended_action=f"Create a dedicated pick-and-pack workflow for '{tier_name}' orders to achieve delivery under 2.0 days.",
                            expected_objective="Faster Order Delivery for High-Priority Customers",
                            data_required="Warehouse station timestamps and courier scan logs.",
                            limitations="The recorded turnaround includes internal handling and may also include courier transit days.",
                            action_plan=ActionPlanSchema(
                                immediate_action=f"Inspect warehouse packing queues for pending '{tier_name}' orders.",
                                follow_up_investigation="Set up dedicated express packing stations during peak hours.",
                                metric_to_monitor=f"Fulfillment Time ({tier_name})",
                                suggested_review_period="Weekly operations check",
                                data_required="Warehouse station timestamps and carrier scan logs.",
                            ),
                            suggested_investigation_route="/explore",
                            suggested_investigation_label="Inspect Turnaround in Explore",
                            relevant_metric="Fulfillment Time (Days)",
                            source_columns=[pr_col, ag_col],
                            time_period=None,
                            evidence_strength="verified_statistical_finding",
                        )
                    )
                    rec_counter += 1
        except Exception as e:
            logger.debug("Aging recommendation error: %s", e)

    # 1E. Guest Checkout Conversion & Retention Opportunity
    if customer_cols and rev_cols:
        login_col = next((c for c in customer_cols if any(k in _normalize_col(c) for k in ["login", "member", "account", "user_type", "customer_type", "segment"])), None) or next((c for c in customer_cols if "type" in _normalize_col(c)), None)
        if login_col:
            r_col = rev_cols[0]
            try:
                cust_summary = df.groupby(login_col).agg(
                    sales=(r_col, "sum"),
                    orders=(login_col, "count"),
                ).reset_index()

                guest_row = cust_summary[cust_summary[login_col].astype(str).str.strip().str.lower().isin(["guest", "non_member", "anonymous", "new", "first_signup"])]
                if not guest_row.empty:
                    g_data = guest_row.iloc[0]
                    g_name = str(g_data[login_col])
                    g_sales = float(g_data["sales"])
                    g_orders = int(g_data["orders"])
                    total_sales = float(cust_summary["sales"].sum())
                    g_share = (g_sales / total_sales * 100) if total_sales > 0 else 0.0

                    if g_orders >= 50 and g_sales > 0:
                        g_sales_fmt = format_metric_display(g_sales, unit=currency, semantic_type="currency")
                        candidates.append(
                            EvidenceRecommendationSchema(
                                rec_id=f"rec_ec_guest_conversion_{rec_counter}",
                                title=f"Turn '{g_name}' Shoppers into Registered Members",
                                category="revenue_opportunities",
                                category_label=_CATEGORY_LABELS["revenue_opportunities"],
                                priority="medium",
                                priority_reason=f"{g_orders:,} orders totaling {g_sales_fmt} ({g_share:.1f}% of sales) were completed without creating customer accounts.",
                                short_summary=f"'{g_name}' checkouts represent {g_sales_fmt} in sales across {g_orders:,} orders without saving customer accounts.",
                                key_metrics=[
                                    {"label": "Guest Sales", "value": g_sales_fmt},
                                    {"label": "Guest Share", "value": f"{g_share:.1f}%"},
                                    {"label": "Guest Orders", "value": f"{g_orders:,}"},
                                    {"label": "Target", "value": "Member Sign-Up"},
                                ],
                                what_we_found=[
                                    f"{g_orders:,} orders were placed by '{g_name}' shoppers ({g_share:.1f}% of total sales).",
                                    f"These orders generated {g_sales_fmt} in revenue.",
                                    "These shoppers did not create accounts, making follow-up offers more difficult.",
                                ],
                                why_it_matters="When shoppers buy as guests, you cannot send them personalized offers, making repeat purchases less likely.",
                                action_steps=[
                                    "Add a simple 1-click account creation prompt on the order confirmation page.",
                                    "Offer a 5% discount on the next order when guest buyers create an account.",
                                    "Highlight member benefits such as easier order tracking and hassle-free returns.",
                                ],
                                expected_result="Convert at least 25% of guest buyers into registered members to increase repeat purchases.",
                                business_problem=f"High checkout volume ({g_orders:,} orders) occurs without customer account creation.",
                                evidence=f"Checkout Type: '{g_name}' | Total Sales: {g_sales_fmt} ({g_share:.1f}% of revenue) | Total Orders: {g_orders:,}.",
                                metric_name="Guest Checkout Sales",
                                entity_name=g_name,
                                current_value=g_sales_fmt,
                                baseline_value="Registered Account Target",
                                pct_change=f"{g_share:.1f}% of total sales",
                                root_cause_signal="Shoppers choose guest checkout to avoid filling out long account forms during payment.",
                                recommended_action="Add a 1-click account creation prompt on the thank-you page with a discount on the next purchase.",
                                expected_objective="Turn One-Time Guest Buyers into Repeat Customers",
                                data_required="Checkout funnel analytics and customer account signup conversion rates.",
                                limitations="Customer signup rates will depend on the simplicity of the checkout flow.",
                                action_plan=ActionPlanSchema(
                                    immediate_action="Add a simple account creation prompt on the order confirmation page.",
                                    follow_up_investigation="Compare repeat purchase rates between registered members and guest buyers.",
                                    metric_to_monitor="Guest Checkout Share %",
                                    suggested_review_period="Monthly marketing review",
                                    data_required="E-commerce conversion funnel and repeat order history.",
                                ),
                                suggested_investigation_route="/explore",
                                suggested_investigation_label="Inspect Customer Segments in Explore",
                                relevant_metric="Guest Checkout Share %",
                                source_columns=[login_col, r_col],
                                time_period=None,
                                evidence_strength="verified_statistical_finding",
                            )
                        )
                        rec_counter += 1
            except Exception as e:
                logger.debug("Guest conversion recommendation error: %s", e)

    # 1F. Inventory Overstock & Low Turnover
    if inventory_cols and (rev_cols or product_cols):
        inv_col = inventory_cols[0]
        try:
            inv_series = pd.to_numeric(df[inv_col], errors="coerce").dropna()
            if not inv_series.empty and inv_series.max() > 0:
                p_col = product_cols[0] if product_cols else None
                if p_col:
                    grouped_inv = df.groupby(p_col)[inv_col].sum().sort_values(ascending=False)
                    top_stocked_item = str(grouped_inv.index[0])
                    stock_qty = float(grouped_inv.iloc[0])
                    
                    if rev_cols:
                        sales_qty = float(df[df[p_col] == top_stocked_item][rev_cols[0]].sum())
                        if stock_qty > sales_qty * 3 and stock_qty > 50:
                            candidates.append(
                                EvidenceRecommendationSchema(
                                    rec_id=f"rec_inv_overstock_{rec_counter}",
                                    title=f"Reduce Excess Stock for '{top_stocked_item}' ({stock_qty:,.0f} Units)",
                                    category="cost_optimization",
                                    category_label=_CATEGORY_LABELS["cost_optimization"],
                                    priority="medium",
                                    priority_reason=f"Current inventory of {stock_qty:,.0f} units is more than 3 times higher than observed sales demand.",
                                    short_summary=f"Warehouse has {stock_qty:,.0f} units of '{top_stocked_item}' in stock, which is significantly higher than recent demand.",
                                    key_metrics=[
                                        {"label": "Stock on Hand", "value": f"{stock_qty:,.0f} units"},
                                        {"label": "Units Demanded", "value": f"{sales_qty:,.0f} units"},
                                        {"label": "Stock Coverage", "value": f"{(stock_qty / max(sales_qty, 1)):.1f}x"},
                                    ],
                                    what_we_found=[
                                        f"Inventory on hand: {stock_qty:,.0f} units for '{top_stocked_item}'.",
                                        f"Observed customer sales: {sales_qty:,.0f} units.",
                                        f"Current stock covers {(stock_qty / max(sales_qty, 1)):.1f} times recent demand.",
                                    ],
                                    why_it_matters="Excess inventory ties up cash, takes up warehouse space, and risks product aging.",
                                    action_steps=[
                                        f"Pause automated purchase orders for '{top_stocked_item}'.",
                                        f"Bundle '{top_stocked_item}' with high-selling products to clear stock faster.",
                                        "Review re-order quantities with the purchasing team.",
                                    ],
                                    expected_result="Reduce excess stock and free up warehouse working capital.",
                                    business_problem=f"Excess inventory tied up in slow-moving stock for '{top_stocked_item}'.",
                                    evidence=f"Stock on hand: {stock_qty:,.0f} units vs sales demand of {sales_qty:,.0f} units ({(stock_qty / max(sales_qty, 1)):.1f}x coverage).",
                                    metric_name="Inventory on Hand",
                                    entity_name=top_stocked_item,
                                    current_value=f"{stock_qty:,.0f} units",
                                    baseline_value=f"{sales_qty:,.0f} units demanded",
                                    pct_change=f"+{(stock_qty / max(sales_qty, 1)):.1f}x coverage",
                                    root_cause_signal="Purchasing quantities exceeded historical customer demand.",
                                    recommended_action=f"Pause reorders for '{top_stocked_item}' and bundle with popular items to clear stock.",
                                    expected_objective="Clear Slow-Moving Stock",
                                    data_required="Supplier lead times and warehouse holding fees.",
                                    limitations="Upcoming promotional marketing campaigns or seasonal demand spikes may justify buffer inventory.",
                                    action_plan=ActionPlanSchema(
                                        immediate_action=f"Pause open purchase orders for '{top_stocked_item}'.",
                                        follow_up_investigation="Review bundle discount options to accelerate sales.",
                                        metric_to_monitor=f"Inventory Turnover ({top_stocked_item})",
                                        suggested_review_period="Next inventory cycle",
                                        data_required="Detailed warehouse storage fees and stock aging logs.",
                                    ),
                                    suggested_investigation_route="/explore",
                                    suggested_investigation_label="Inspect Inventory in Explore",
                                    relevant_metric="Inventory on Hand",
                                    source_columns=[p_col, inv_col],
                                    time_period=None,
                                    evidence_strength="verified_statistical_finding",
                                )
                            )
                            rec_counter += 1
        except Exception as e:
            logger.debug("Inventory overstock rule error: %s", e)

    # =========================================================================
    # MODULE 2: FINANCE / BANKING / EXPENSE DEEP-DIVE
    # =========================================================================

    if cost_cols and rev_cols:
        c_col = cost_cols[0]
        r_col = rev_cols[0]
        try:
            total_rev = float(pd.to_numeric(df[r_col], errors="coerce").sum())
            total_cost = float(pd.to_numeric(df[c_col], errors="coerce").sum())

            if total_rev > 0 and total_cost > 0:
                cost_ratio = (total_cost / total_rev) * 100
                if cost_ratio > 70.0:
                    r_fmt = format_metric_display(total_rev, unit=currency, semantic_type="currency")
                    c_fmt = format_metric_display(total_cost, unit=currency, semantic_type="currency")
                    net_margin = ((total_rev - total_cost) / total_rev) * 100

                    top_cost_cat_str = ""
                    cat_field = category_cols[0] if category_cols else (dept_cols[0] if dept_cols else None)
                    top_cat_name = "Primary Operations"
                    top_cat_val = 0.0
                    top_cat_pct = 0.0
                    if cat_field:
                        cat_costs = df.groupby(cat_field)[c_col].sum().sort_values(ascending=False)
                        if not cat_costs.empty:
                            top_cat_name = str(cat_costs.index[0])
                            top_cat_val = float(cat_costs.iloc[0])
                            top_cat_pct = (top_cat_val / total_cost) * 100
                            top_cost_cat_str = f" The largest cost driver is '{top_cat_name}' at {format_metric_display(top_cat_val, unit=currency, semantic_type='currency')} ({top_cat_pct:.1f}% of total costs)."

                    candidates.append(
                        EvidenceRecommendationSchema(
                            rec_id=f"rec_fin_cost_burden_{rec_counter}",
                            title=f"Operating Expenses Are Consuming {cost_ratio:.1f}% of Revenue",
                            category="cost_optimization",
                            category_label=_CATEGORY_LABELS["cost_optimization"],
                            priority="high" if cost_ratio > 85.0 else "medium",
                            priority_reason=f"Operating expenses ({c_fmt}) represent {cost_ratio:.1f}% of total revenue ({r_fmt}), leaving an operating margin of only {net_margin:.1f}%.",
                            short_summary=f"Costs are high relative to sales ({cost_ratio:.1f}% of revenue), leaving an operating margin of {net_margin:.1f}%.",
                            key_metrics=[
                                {"label": "Cost Ratio", "value": f"{cost_ratio:.1f}%"},
                                {"label": "Total Costs", "value": c_fmt},
                                {"label": "Total Revenue", "value": r_fmt},
                                {"label": "Net Margin", "value": f"{net_margin:.1f}%"},
                            ],
                            what_we_found=[
                                f"Total operating expenses: {c_fmt} vs total revenue of {r_fmt}.",
                                f"Operating costs represent {cost_ratio:.1f}% of top-line revenue.",
                                f"Current operating profit margin is {net_margin:.1f}%.",
                            ] + ([f"Top cost area: '{top_cat_name}' ({format_metric_display(top_cat_val, unit=currency, semantic_type='currency')}, {top_cat_pct:.1f}% of spend)."] if top_cat_val > 0 else []),
                            why_it_matters="When expenses consume most of your revenue, even a small dip in sales can push the business into a net loss.",
                            action_steps=[
                                "Review expenses in the largest cost categories.",
                                "Audit recurring vendor contracts coming up for renewal.",
                                "Set a target to reduce non-essential operating expenses by 5–10%.",
                            ],
                            expected_result="Lower the cost-to-revenue ratio and improve operating profit buffer.",
                            business_problem=f"High expense ratio ({cost_ratio:.1f}%) leaves narrow operating profit margin.",
                            evidence=f"Revenue: {r_fmt} | Costs: {c_fmt} | Expense Ratio: {cost_ratio:.1f}% | Net Margin: {net_margin:.1f}%.{top_cost_cat_str}",
                            metric_name="Cost-to-Revenue Ratio",
                            entity_name="Operating Expenses",
                            current_value=f"{cost_ratio:.1f}%",
                            baseline_value="65.0% Benchmark",
                            pct_change=f"+{cost_ratio - 65.0:.1f}% pts above target",
                            root_cause_signal="Expenses have grown faster than sales revenue across recent periods.",
                            recommended_action="Conduct a line-item expense review to identify opportunities for supplier renegotiation or operational efficiency.",
                            expected_objective="Reduce Operating Expenses",
                            data_required="Detailed expense breakdown by ledger account.",
                            limitations="The dataset does not distinguish between fixed overhead costs and variable per-order costs.",
                            action_plan=ActionPlanSchema(
                                immediate_action="Categorize operating costs by department or supplier.",
                                follow_up_investigation="Review upcoming vendor contracts and software subscriptions.",
                                metric_to_monitor="Cost-to-Revenue %",
                                suggested_review_period="Monthly financial review",
                                data_required="Detailed general ledger expense breakdown.",
                            ),
                            suggested_investigation_route="/trends",
                            suggested_investigation_label="View Revenue vs Cost Trends",
                            relevant_metric="Cost-to-Revenue Ratio",
                            source_columns=[r_col, c_col] + ([cat_field] if cat_field else []),
                            time_period=None,
                            evidence_strength="verified_statistical_finding",
                        )
                    )
                    rec_counter += 1
        except Exception as e:
            logger.debug("Finance cost burden rule error: %s", e)

    # =========================================================================
    # MODULE 3: PROCUREMENT & OPERATIONS DEEP-DIVE
    # =========================================================================

    if supplier_cols:
        s_col = supplier_cols[0]

        # 3A. Supplier Unit Price Disparity
        if price_cols:
            pr_col = price_cols[0]
            try:
                supp_prices = df.groupby(s_col)[pr_col].mean().dropna()
                if len(supp_prices) >= 2:
                    min_p = float(supp_prices.min())
                    max_p = float(supp_prices.max())
                    spread_pct = ((max_p - min_p) / min_p) * 100 if min_p > 0 else 0.0

                    if spread_pct > 20.0:
                        min_s = str(supp_prices.idxmin())
                        max_s = str(supp_prices.idxmax())
                        min_p_fmt = format_metric_display(min_p, unit=currency, semantic_type="currency")
                        max_p_fmt = format_metric_display(max_p, unit=currency, semantic_type="currency")

                        candidates.append(
                            EvidenceRecommendationSchema(
                                rec_id=f"rec_proc_price_spread_{rec_counter}",
                                title=f"Supplier Prices Vary by {spread_pct:.1f}% for Similar Items",
                                category="cost_optimization",
                                category_label=_CATEGORY_LABELS["cost_optimization"],
                                priority="high" if spread_pct > 40.0 else "medium",
                                priority_reason=f"Average unit purchase price ranges from {min_p_fmt} ('{min_s}') to {max_p_fmt} ('{max_s}'), a {spread_pct:.1f}% price difference.",
                                short_summary=f"Different suppliers are charging noticeably different prices for comparable purchases (up to a {spread_pct:.1f}% difference).",
                                key_metrics=[
                                    {"label": "Highest Price", "value": max_p_fmt},
                                    {"label": "Lowest Price", "value": min_p_fmt},
                                    {"label": "Price Difference", "value": f"+{spread_pct:.1f}%"},
                                    {"label": "Highest Supplier", "value": max_s},
                                ],
                                what_we_found=[
                                    f"Lowest average supplier rate: {min_p_fmt} ('{min_s}').",
                                    f"Highest average supplier rate: {max_p_fmt} ('{max_s}').",
                                    f"Price spread: {spread_pct:.1f}% difference between vendors.",
                                ],
                                why_it_matters="Purchasing identical or similar items at higher rates increases overall procurement costs.",
                                action_steps=[
                                    f"Review pricing contracts with '{max_s}'.",
                                    f"Ask '{max_s}' to match rates offered by '{min_s}'.",
                                    "Consolidate orders with lower-cost suppliers where quality is comparable.",
                                ],
                                expected_result="Standardize supplier rates and reduce purchase costs.",
                                business_problem=f"Wide price difference ({spread_pct:.1f}%) across suppliers for comparable items.",
                                evidence=f"Lowest avg price: {min_p_fmt} ('{min_s}') | Highest avg price: {max_p_fmt} ('{max_s}') | Price Spread: {spread_pct:.1f}%.",
                                metric_name="Average Unit Purchase Price",
                                entity_name=max_s,
                                current_value=max_p_fmt,
                                baseline_value=min_p_fmt,
                                pct_change=f"+{spread_pct:.1f}% difference",
                                root_cause_signal="Purchasing occurs across different suppliers without standardized volume price agreements.",
                                recommended_action=f"Negotiate standardized pricing with '{max_s}' or shift order volume to lower-cost vendors.",
                                expected_objective="Reduce Supplier Purchase Costs",
                                data_required="Supplier contract terms, volume discount tiers, and delivery terms.",
                                limitations="Differences in delivery speed, order minimums, or warranty terms may justify part of the price difference.",
                                action_plan=ActionPlanSchema(
                                    immediate_action=f"Compare contract terms between '{min_s}' and '{max_s}'.",
                                    follow_up_investigation="Review volume discount tiers across suppliers.",
                                    metric_to_monitor="Average Unit Purchase Price",
                                    suggested_review_period="Next contract renewal",
                                    data_required="Supplier contracts and volume discount tiers.",
                                ),
                                suggested_investigation_route="/explore",
                                suggested_investigation_label="Inspect Suppliers in Explore",
                                relevant_metric="Unit Purchase Price",
                                source_columns=[s_col, pr_col],
                                time_period=None,
                                evidence_strength="verified_statistical_finding",
                            )
                        )
                        rec_counter += 1
            except Exception as e:
                logger.debug("Procurement price spread rule error: %s", e)

        # 3B. Supplier Delivery Delays
        delay_cols = classes["aging"]
        if delay_cols:
            del_col = delay_cols[0]
            try:
                supp_delays = df.groupby(s_col)[del_col].mean().dropna()
                if len(supp_delays) >= 2 and float(supp_delays.max()) > 3.0:
                    worst_s = str(supp_delays.idxmax())
                    worst_del = float(supp_delays.max())
                    avg_del = float(supp_delays.mean())

                    candidates.append(
                        EvidenceRecommendationSchema(
                            rec_id=f"rec_proc_delay_{rec_counter}",
                            title=f"Address Delivery Delays with Supplier '{worst_s}' (Avg {worst_del:.1f} Days)",
                            category="operational_efficiency",
                            category_label=_CATEGORY_LABELS["operational_efficiency"],
                            priority="high" if worst_del > 8.0 else "medium",
                            priority_reason=f"Supplier '{worst_s}' averages {worst_del:.1f} days delivery time compared to the supplier fleet average of {avg_del:.1f} days.",
                            short_summary=f"Orders from '{worst_s}' take an average of {worst_del:.1f} days to arrive, which is noticeably slower than other suppliers ({avg_del:.1f} days).",
                            key_metrics=[
                                {"label": "Supplier Average", "value": f"{worst_del:.1f} days"},
                                {"label": "Fleet Average", "value": f"{avg_del:.1f} days"},
                                {"label": "Delay Difference", "value": f"+{worst_del - avg_del:.1f} days"},
                                {"label": "Supplier Name", "value": worst_s},
                            ],
                            what_we_found=[
                                f"Supplier '{worst_s}' delivery time averages {worst_del:.1f} days.",
                                f"Other suppliers average {avg_del:.1f} days.",
                                f"Orders from '{worst_s}' take {worst_del - avg_del:.1f} extra days on average.",
                            ],
                            why_it_matters="Slow supplier deliveries can lead to out-of-stock situations and delayed fulfillment to customers.",
                            action_steps=[
                                f"Review recent delayed purchase orders with '{worst_s}'.",
                                "Set clear delivery time expectations in future purchase orders.",
                                "Identify backup suppliers for critical items.",
                            ],
                            expected_result=f"Reduce delivery time from '{worst_s}' to under {avg_del:.1f} days.",
                            business_problem=f"Delivery delays concentrated with supplier '{worst_s}'.",
                            evidence=f"Supplier '{worst_s}' avg delay: {worst_del:.1f} days | Peer fleet avg: {avg_del:.1f} days | Difference: +{worst_del - avg_del:.1f} days.",
                            metric_name="Delivery Time (Days)",
                            entity_name=worst_s,
                            current_value=f"{worst_del:.1f} days",
                            baseline_value=f"{avg_del:.1f} days Fleet Avg",
                            pct_change=f"+{worst_del - avg_del:.1f} days",
                            root_cause_signal=f"Orders from '{worst_s}' consistently experience slower processing or transit times.",
                            recommended_action=f"Meet with '{worst_s}' to set delivery time benchmarks and prepare backup suppliers for key items.",
                            expected_objective="Faster Supplier Deliveries",
                            data_required="Detailed shipment tracking logs and carrier timestamps.",
                            limitations="External transport disruptions or customs delays may explain part of the transit time.",
                            action_plan=ActionPlanSchema(
                                immediate_action=f"Review recent delayed purchase orders for '{worst_s}'.",
                                follow_up_investigation="Check inventory buffer levels for items sourced from this supplier.",
                                metric_to_monitor=f"Delivery Days ({worst_s})",
                                suggested_review_period="Monthly supplier review",
                                data_required="Detailed PO tracking and shipment logs.",
                            ),
                            suggested_investigation_route="/explore",
                            suggested_investigation_label="Inspect Supplier Delays in Explore",
                            relevant_metric="Delivery Time (Days)",
                            source_columns=[s_col, del_col],
                            time_period=None,
                            evidence_strength="verified_statistical_finding",
                        )
                    )
                    rec_counter += 1
            except Exception as e:
                logger.debug("Procurement delay rule error: %s", e)

    # =========================================================================
    # MODULE 4: HR / WORKFORCE ANALYTICS DEEP-DIVE
    # =========================================================================

    if attrition_cols and dept_cols:
        att_col = attrition_cols[0]
        d_col = dept_cols[0]
        try:
            numeric_mask = pd.to_numeric(df[att_col], errors="coerce") == 1
            text_mask = df[att_col].astype(str).str.strip().str.lower().isin(["yes", "true", "left", "resigned", "terminated", "voluntary", "1", "1.0"])
            positive_mask = numeric_mask | text_mask
            if positive_mask.sum() > 0:
                dept_counts = df.groupby(d_col).size()
                dept_leaves = df[positive_mask].groupby(d_col).size().reindex(dept_counts.index, fill_value=0)
                dept_rates = ((dept_leaves / dept_counts) * 100).dropna()

                if not dept_rates.empty:
                    worst_dept = str(dept_rates.idxmax())
                    worst_rate = float(dept_rates.max())
                    overall_rate = float(positive_mask.sum() / len(df)) * 100
                    departures = int(dept_leaves[worst_dept])
                    total_dept_headcount = int(dept_counts[worst_dept])

                    if worst_rate > 15.0:
                        candidates.append(
                            EvidenceRecommendationSchema(
                                rec_id=f"rec_hr_turnover_{rec_counter}",
                                title=f"Department '{worst_dept}' Has Higher Turnover ({worst_rate:.1f}%)",
                                category="operational_efficiency",
                                category_label=_CATEGORY_LABELS["operational_efficiency"],
                                priority="high" if worst_rate > 35.0 else "medium",
                                priority_reason=f"Department '{worst_dept}' recorded {departures} departures out of {total_dept_headcount} employees ({worst_rate:.1f}% turnover vs {overall_rate:.1f}% company average).",
                                short_summary=f"Employee departures are concentrated in '{worst_dept}' ({worst_rate:.1f}% turnover compared with the company average of {overall_rate:.1f}%).",
                                key_metrics=[
                                    {"label": "Department Turnover", "value": f"{worst_rate:.1f}%"},
                                    {"label": "Company Average", "value": f"{overall_rate:.1f}%"},
                                    {"label": "Departures", "value": f"{departures}"},
                                    {"label": "Team Size", "value": f"{total_dept_headcount}"},
                                ],
                                what_we_found=[
                                    f"Department '{worst_dept}': {departures} departures out of {total_dept_headcount} staff ({worst_rate:.1f}% turnover).",
                                    f"Company-wide average turnover: {overall_rate:.1f}%.",
                                    f"Turnover in '{worst_dept}' is {worst_rate - overall_rate:.1f} percentage points above the company average.",
                                ],
                                why_it_matters="High team turnover increases replacement recruiting costs and causes delays in team deliverables.",
                                action_steps=[
                                    f"Conduct 1-on-1 check-ins with current team members in '{worst_dept}'.",
                                    "Review workload distribution and team feedback.",
                                    "Benchmark compensation with industry standards for these roles.",
                                ],
                                expected_result=f"Improve retention in '{worst_dept}' and lower turnover toward {overall_rate:.1f}%.",
                                business_problem=f"Turnover concentration in department '{worst_dept}'.",
                                evidence=f"Department '{worst_dept}': {worst_rate:.1f}% turnover ({departures}/{total_dept_headcount} staff) vs company average of {overall_rate:.1f}%.",
                                metric_name="Department Turnover Rate %",
                                entity_name=worst_dept,
                                current_value=f"{worst_rate:.1f}%",
                                baseline_value=f"{overall_rate:.1f}% Company Avg",
                                pct_change=f"+{worst_rate - overall_rate:.1f}% pts above baseline",
                                root_cause_signal=f"Departures are higher in '{worst_dept}' relative to other departments.",
                                recommended_action=f"Conduct stay interviews and review workload and compensation for '{worst_dept}'.",
                                expected_objective="Improve Employee Retention",
                                data_required="Exit interview feedback and salary benchmarking data.",
                                limitations="The dataset does not record personal reasons for departure or external job market factors.",
                                action_plan=ActionPlanSchema(
                                    immediate_action=f"Review recent exit feedback for '{worst_dept}'.",
                                    follow_up_investigation="Compare compensation and promotion timelines across teams.",
                                    metric_to_monitor="Department Turnover Rate %",
                                    suggested_review_period="Quarterly HR review",
                                    data_required="Exit interview feedback and compensation benchmarks.",
                                ),
                                suggested_investigation_route="/explore",
                                suggested_investigation_label="Inspect Departments in Explore",
                                relevant_metric="Department Turnover Rate %",
                                source_columns=[att_col, d_col],
                                time_period=None,
                                evidence_strength="verified_statistical_finding",
                            )
                        )
                        rec_counter += 1
        except Exception as e:
            logger.debug("HR attrition rule error: %s", e)

    # =========================================================================
    # MODULE 5: SPORTS ANALYTICS DEEP-DIVE
    # =========================================================================

    if player_cols and score_cols:
        pl_col = player_cols[0]
        sc_col = score_cols[0]
        try:
            player_stats = df.groupby(pl_col)[sc_col].agg(["mean", "std", "count"]).dropna()
            valid_players = player_stats[player_stats["count"] >= 5]
            if not valid_players.empty:
                valid_players["cv"] = valid_players["std"] / valid_players["mean"].replace(0, np.nan)
                valid_players = valid_players.sort_values("cv", ascending=False)
                
                if not valid_players.empty:
                    most_volatile = str(valid_players.index[0])
                    vol_val = float(valid_players.loc[most_volatile, "cv"])
                    avg_val = float(valid_players.loc[most_volatile, "mean"])
                    match_count = int(valid_players.loc[most_volatile, "count"])

                    if vol_val > 0.8:
                        candidates.append(
                            EvidenceRecommendationSchema(
                                rec_id=f"rec_sports_volatility_{rec_counter}",
                                title=f"Player '{most_volatile}' Has Inconsistent Match Performance",
                                category="performance_improvement",
                                category_label=_CATEGORY_LABELS["performance_improvement"],
                                priority="medium",
                                priority_reason=f"'{most_volatile}' exhibits wide match-to-match performance fluctuation (variability score: {vol_val:.2f}) across {match_count} matches.",
                                short_summary=f"Performance numbers for '{most_volatile}' vary significantly from match to match (variability score: {vol_val:.2f}).",
                                key_metrics=[
                                    {"label": "Variability Score", "value": f"{vol_val:.2f}"},
                                    {"label": "Average Score", "value": f"{avg_val:.1f}"},
                                    {"label": "Matches Played", "value": f"{match_count}"},
                                ],
                                what_we_found=[
                                    f"'{most_volatile}' played in {match_count} matches with an average score of {avg_val:.1f}.",
                                    f"Performance standard deviation is {float(valid_players.loc[most_volatile, 'std']):.1f}, indicating high volatility.",
                                ],
                                why_it_matters="High inconsistency makes tactical match planning harder and leads to unpredictable results.",
                                action_steps=[
                                    f"Review match conditions where '{most_volatile}' had below-average performances.",
                                    "Clarify tactical role and match strategy.",
                                ],
                                expected_result="Improve match-to-match consistency.",
                                business_problem=f"Performance volatility in '{most_volatile}'.",
                                evidence=f"Average: {avg_val:.1f} | Standard Deviation: {float(valid_players.loc[most_volatile, 'std']):.1f} | Variability Score: {vol_val:.2f} across {match_count} matches.",
                                metric_name="Performance Consistency",
                                entity_name=most_volatile,
                                current_value=f"{vol_val:.2f}",
                                baseline_value="0.50 Target Score",
                                pct_change=f"+{vol_val - 0.50:.2f} variance",
                                root_cause_signal="Performance alternates between high and low match outputs.",
                                recommended_action=f"Review role clarity and situational match execution for '{most_volatile}'.",
                                expected_objective="Improve Performance Consistency",
                                data_required="Opponent rankings and match conditions.",
                                limitations="Raw statistics do not capture situational match context (e.g. chasing high targets vs defensive play).",
                                action_plan=ActionPlanSchema(
                                    immediate_action=f"Review match conditions where '{most_volatile}' underperformed.",
                                    follow_up_investigation="Analyze role clarity and match tactics.",
                                    metric_to_monitor=f"Performance Consistency ({most_volatile})",
                                    suggested_review_period="Next tournament series",
                                    data_required="Opponent data and match telemetry.",
                                ),
                                suggested_investigation_route="/explore",
                                suggested_investigation_label="Inspect Player in Explore",
                                relevant_metric="Performance Consistency",
                                source_columns=[pl_col, sc_col],
                                time_period=None,
                                evidence_strength="verified_statistical_finding",
                            )
                        )
                        rec_counter += 1
        except Exception as e:
            logger.debug("Sports volatility rule error: %s", e)

    # =========================================================================
    # MODULE 6: DATA QUALITY HYGIENE FINDINGS
    # =========================================================================

    try:
        dq_report = compute_data_quality_report(df, dataset_id, domain)
        dup_rows = int(df.duplicated().sum())
        dup_pct = round((dup_rows / total_rows) * 100.0, 2) if total_rows > 0 else 0.0

        if dup_rows > 0 and dup_pct > 1.0:
            candidates.append(
                EvidenceRecommendationSchema(
                    rec_id=f"rec_dq_dup_{rec_counter}",
                    title=f"Remove {dup_rows:,} Duplicate Rows in Dataset",
                    category="data_quality",
                    category_label=_CATEGORY_LABELS["data_quality"],
                    priority="high" if dup_pct > 10.0 else "medium",
                    priority_reason=f"Found {dup_rows:,} duplicate records ({dup_pct:.1f}% of the file) which can artificially inflate sales and count totals.",
                    short_summary=f"{dup_pct:.1f}% of rows in the dataset are exact duplicates ({dup_rows:,} rows), which can distort business totals.",
                    key_metrics=[
                        {"label": "Duplicate Rows", "value": f"{dup_rows:,}"},
                        {"label": "Duplicate Share", "value": f"{dup_pct:.1f}%"},
                        {"label": "Total Records", "value": f"{total_rows:,}"},
                    ],
                    what_we_found=[
                        f"{dup_rows:,} duplicate rows were identified out of {total_rows:,} total records.",
                        f"Duplicates represent {dup_pct:.1f}% of the entire dataset.",
                    ],
                    why_it_matters="Duplicate rows cause double-counting in financial sums, sales volume, and customer reporting.",
                    action_steps=[
                        "Apply deduplication in your data export query before uploading.",
                        "Verify unique ID constraints in your source database.",
                    ],
                    expected_result="Ensure clean, accurate metric totals across all analytics reports.",
                    business_problem=f"Dataset contains {dup_rows:,} duplicate rows.",
                    evidence=f"{dup_rows:,} duplicate rows identified out of {total_rows:,} total records ({dup_pct:.1f}%).",
                    metric_name="Duplicate Rows",
                    entity_name="Dataset Records",
                    current_value=f"{dup_rows:,} ({dup_pct:.1f}%)",
                    baseline_value="0 Duplicates",
                    pct_change=f"{dup_pct:.1f}%",
                    root_cause_signal="Data export generated repeated rows without unique key filtering.",
                    recommended_action="Apply deduplication in your data export query before running business reports.",
                    expected_objective="Clean Accurate Data",
                    data_required="Source database schema with primary key definitions.",
                    limitations="Identifies exact row matches across all columns.",
                    action_plan=ActionPlanSchema(
                        immediate_action="Check database export script for cartesian table joins.",
                        follow_up_investigation="Validate primary key constraints across ingestion pipelines.",
                        metric_to_monitor="Duplicate Row Count",
                        suggested_review_period="Next data export",
                        data_required="Primary key column definitions.",
                    ),
                    suggested_investigation_route="/explore",
                    suggested_investigation_label="Inspect Dataset in Explore",
                    relevant_metric="Duplicate Rows",
                    source_columns=list(df.columns[:3]),
                    time_period=None,
                    evidence_strength="data_hygiene_warning",
                )
            )
            rec_counter += 1

        # Missing values in critical column
        for col_name, col_diag in dq_report.column_diagnostics.items():
            if col_diag.null_pct > 25.0 and col_diag.null_count > 0:
                candidates.append(
                    EvidenceRecommendationSchema(
                        rec_id=f"rec_dq_null_{rec_counter}",
                        title=f"Fix Missing Data in Column '{col_name}' ({col_diag.null_pct:.1f}% Missing)",
                        category="data_quality",
                        category_label=_CATEGORY_LABELS["data_quality"],
                        priority="medium",
                        priority_reason=f"Column '{col_name}' has {col_diag.null_pct:.1f}% empty values ({col_diag.null_count:,} rows), which limits reporting accuracy.",
                        short_summary=f"Column '{col_name}' is missing values in {col_diag.null_pct:.1f}% of records ({col_diag.null_count:,} rows).",
                        key_metrics=[
                            {"label": "Missing Values", "value": f"{col_diag.null_count:,}"},
                            {"label": "Missing %", "value": f"{col_diag.null_pct:.1f}%"},
                            {"label": "Total Records", "value": f"{total_rows:,}"},
                        ],
                        what_we_found=[
                            f"Column '{col_name}' is empty in {col_diag.null_count:,} out of {total_rows:,} rows.",
                            f"Missing data represents {col_diag.null_pct:.1f}% of all rows.",
                        ],
                        why_it_matters="Missing values reduce the reliability of segment filters and category summaries.",
                        action_steps=[
                            f"Make '{col_name}' a required field in your data collection forms.",
                            "Check if older records can be backfilled from transaction archives.",
                        ],
                        expected_result=f"Improve data completeness for '{col_name}' above 95%.",
                        business_problem=f"Missing data in column '{col_name}'.",
                        evidence=f"Empty count: {col_diag.null_count:,} / {total_rows:,} rows ({col_diag.null_pct:.1f}% missing).",
                        metric_name=col_name,
                        entity_name=col_name,
                        current_value=f"{col_diag.null_pct:.1f}% missing",
                        baseline_value="< 5.0% Target",
                        pct_change=f"+{col_diag.null_pct - 5.0:.1f}% pts above target",
                        root_cause_signal="Data entry forms permitted null values for this field.",
                        recommended_action=f"Enforce mandatory input validation for '{col_name}' in data collection forms.",
                        expected_objective="Complete Business Records",
                        data_required="Upstream data collection form logs.",
                        limitations="Cannot determine whether missing values were optional or unrecorded.",
                        action_plan=ActionPlanSchema(
                            immediate_action=f"Audit forms and systems recording '{col_name}'.",
                            follow_up_investigation="Evaluate appropriate default values or backfill rules.",
                            metric_to_monitor=f"Missing % in {col_name}",
                            suggested_review_period="Next data pipeline update",
                            data_required="Source schema definitions.",
                        ),
                        suggested_investigation_route="/explore",
                        suggested_investigation_label="Inspect Columns in Explore",
                        relevant_metric=col_name,
                        source_columns=[col_name],
                        time_period=None,
                        evidence_strength="data_hygiene_warning",
                    )
                )
                rec_counter += 1
                break
    except Exception as e:
        logger.debug("Data quality recommendation error: %s", e)

    # =========================================================================
    # MODULE 7: GENERAL CROSS-SECTIONAL / NUMERICAL FALLBACK
    # =========================================================================

    if len(candidates) < 3:
        num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        all_cat_cols = category_cols or product_cols or region_cols or customer_cols
        if num_cols and all_cat_cols:
            n_col = num_cols[0]
            dim_col = all_cat_cols[0]
            try:
                grouped_dim = df.groupby(dim_col)[n_col].agg(["mean", "sum", "count"]).dropna()
                valid_dims = grouped_dim[grouped_dim["count"] >= 3]
                if len(valid_dims) >= 2:
                    min_val = float(valid_dims["mean"].min())
                    max_val = float(valid_dims["mean"].max())
                    if min_val > 0:
                        dispersion_pct = ((max_val - min_val) / min_val) * 100
                        if dispersion_pct > 30.0:
                            worst_dim = str(valid_dims["mean"].idxmin())
                            best_dim = str(valid_dims["mean"].idxmax())
                            candidates.append(
                                EvidenceRecommendationSchema(
                                    rec_id=f"rec_gen_dispersion_{rec_counter}",
                                    title=f"Performance Difference Across '{worst_dim}' and '{best_dim}'",
                                    category="performance_improvement",
                                    category_label=_CATEGORY_LABELS["performance_improvement"],
                                    priority="medium",
                                    priority_reason=f"Average '{humanize_column_name(n_col)}' in '{worst_dim}' ({min_val:,.1f}) lags behind '{best_dim}' ({max_val:,.1f}) by {dispersion_pct:.1f}%.",
                                    short_summary=f"Average results in '{worst_dim}' lag behind the top-performing segment ('{best_dim}') by {dispersion_pct:.1f}%.",
                                    key_metrics=[
                                        {"label": "Top Segment", "value": f"{max_val:,.1f} ('{best_dim}')"},
                                        {"label": "Lower Segment", "value": f"{min_val:,.1f} ('{worst_dim}')"},
                                        {"label": "Difference", "value": f"-{dispersion_pct:.1f}%"},
                                    ],
                                    what_we_found=[
                                        f"Top segment ('{best_dim}') average: {max_val:,.1f}.",
                                        f"Lower segment ('{worst_dim}') average: {min_val:,.1f}.",
                                        f"Performance gap: {dispersion_pct:.1f}% difference.",
                                    ],
                                    why_it_matters="Lower performance in specific segments pulls down overall business averages.",
                                    action_steps=[
                                        f"Review operations and practices in '{worst_dim}'.",
                                        f"Share best practices from '{best_dim}' with the '{worst_dim}' team.",
                                    ],
                                    expected_result=f"Improve performance in '{worst_dim}' toward top-tier levels.",
                                    business_problem=f"Performance difference across '{humanize_column_name(dim_col)}' segments.",
                                    evidence=f"Lowest Segment: '{worst_dim}' (Avg: {min_val:,.1f}) | Highest Segment: '{best_dim}' (Avg: {max_val:,.1f}) | Difference: {dispersion_pct:.1f}%.",
                                    metric_name=humanize_column_name(n_col),
                                    entity_name=worst_dim,
                                    current_value=f"{min_val:,.1f}",
                                    baseline_value=f"{max_val:,.1f} ('{best_dim}')",
                                    pct_change=f"-{dispersion_pct:.1f}% vs top segment",
                                    root_cause_signal="Operational or process differences between segments.",
                                    recommended_action=f"Apply effective methods from '{best_dim}' to operations in '{worst_dim}'.",
                                    expected_objective="Improve Segment Performance",
                                    data_required="Segment-level operational notes and staffing details.",
                                    limitations="Territory differences or product mix variations may explain baseline variations.",
                                    action_plan=ActionPlanSchema(
                                        immediate_action=f"Conduct a review of operations in '{worst_dim}'.",
                                        follow_up_investigation=f"Identify key success drivers in '{best_dim}'.",
                                        metric_to_monitor=f"Average {humanize_column_name(n_col)} ({worst_dim})",
                                        suggested_review_period="Monthly review",
                                        data_required="Activity logs across segments.",
                                    ),
                                    suggested_investigation_route="/explore",
                                    suggested_investigation_label="Inspect Segments in Explore",
                                    relevant_metric=humanize_column_name(n_col),
                                    source_columns=[dim_col, n_col],
                                    time_period=None,
                                    evidence_strength="verified_statistical_finding",
                                )
                            )
                            rec_counter += 1
            except Exception as e:
                logger.debug("General dispersion recommendation error: %s", e)
        elif num_cols and len(num_cols) >= 1:
            for n_col in num_cols:
                series = pd.to_numeric(df[n_col], errors="coerce").dropna()
                if len(series) >= 10:
                    mean_val = float(series.mean())
                    std_val = float(series.std())
                    if mean_val > 0:
                        cv = std_val / mean_val
                        if cv > 0.6:
                            q75, q25 = float(series.quantile(0.75)), float(series.quantile(0.25))
                            iqr = q75 - q25
                            outliers_cnt = int(((series < (q25 - 1.5 * iqr)) | (series > (q75 + 1.5 * iqr))).sum())
                            outlier_pct = round((outliers_cnt / len(series)) * 100.0, 1)

                            candidates.append(
                                EvidenceRecommendationSchema(
                                    rec_id=f"rec_num_volatility_{rec_counter}",
                                    title=f"High Variability in '{humanize_column_name(n_col)}' Values",
                                    category="performance_improvement",
                                    category_label=_CATEGORY_LABELS["performance_improvement"],
                                    priority="medium",
                                    priority_reason=f"Column '{humanize_column_name(n_col)}' exhibits high fluctuation around its average across {len(series):,} records.",
                                    short_summary=f"Values in '{humanize_column_name(n_col)}' show wide fluctuation around the average ({outliers_cnt:,} outlier records).",
                                    key_metrics=[
                                        {"label": "Average Value", "value": f"{mean_val:,.1f}"},
                                        {"label": "Standard Deviation", "value": f"{std_val:,.1f}"},
                                        {"label": "Outlier Records", "value": f"{outliers_cnt:,} ({outlier_pct}%)"},
                                    ],
                                    what_we_found=[
                                        f"Average '{humanize_column_name(n_col)}': {mean_val:,.1f}.",
                                        f"Standard deviation: {std_val:,.1f}.",
                                        f"{outliers_cnt:,} records ({outlier_pct}%) fall well outside standard ranges.",
                                    ],
                                    why_it_matters="Wide variability makes future planning and forecasting less predictable.",
                                    action_steps=[
                                        f"Inspect top and bottom outlier rows in '{humanize_column_name(n_col)}'.",
                                        "Check if records can be grouped into more uniform customer or product segments.",
                                    ],
                                    expected_result="Improve predictability and reduce extreme swings.",
                                    business_problem=f"High statistical variability in '{humanize_column_name(n_col)}'.",
                                    evidence=f"Mean: {mean_val:,.1f} | Standard Deviation: {std_val:,.1f} | Outliers: {outliers_cnt:,} ({outlier_pct}%).",
                                    metric_name=humanize_column_name(n_col),
                                    entity_name=humanize_column_name(n_col),
                                    current_value=f"{cv:.2f} CV",
                                    baseline_value="Standard Distribution",
                                    pct_change=f"+{cv - 0.40:.2f} variance",
                                    root_cause_signal="Data contains wide swings with distinct outlier clusters.",
                                    recommended_action=f"Group '{humanize_column_name(n_col)}' by customer or operational tier to understand what drives extreme values.",
                                    expected_objective="Improve Consistency",
                                    data_required="Segment or cohort attributes.",
                                    limitations="Reflects past data distribution without external explanatory factors.",
                                    action_plan=ActionPlanSchema(
                                        immediate_action=f"Inspect highest and lowest records in '{humanize_column_name(n_col)}'.",
                                        follow_up_investigation="Segment data into distinct tiers.",
                                        metric_to_monitor=f"Variability in {humanize_column_name(n_col)}",
                                        suggested_review_period="Monthly review",
                                        data_required="Granular customer and transaction notes.",
                                    ),
                                    suggested_investigation_route="/explore",
                                    suggested_investigation_label="Inspect Distribution in Explore",
                                    relevant_metric=humanize_column_name(n_col),
                                    source_columns=[n_col],
                                    time_period=None,
                                    evidence_strength="verified_statistical_finding",
                                )
                            )
                            rec_counter += 1
                            break

    # =========================================================================
    # DEDUPLICATION, RANKING & TOP-5 SELECTION
    # =========================================================================

    if not candidates:
        return RecommendationsIntelligenceResponse(
            dataset_id=dataset_id,
            is_available=False,
            domain_id=domain_id,
            domain_name=domain_name,
            currency_symbol=currency,
            overview=RecommendationsOverviewSchema(
                total_recommendations=0,
                critical_count=0,
                high_count=0,
                medium_count=0,
                low_count=0,
                evidence_backed_count=0,
                data_limitations_summary=data_limitations or [
                    "Insufficient variance: The uploaded dataset does not exhibit sufficient variance or volume to generate reliable recommendations.",
                ],
                summary_statement="No statistically actionable patterns were identified in the current dataset slice.",
            ),
            recommendations=[],
            categories_present=[],
            has_time_dimension=has_time_dim,
            analyzed_at=datetime.now(timezone.utc).isoformat(),
        )

    # Deduplicate candidates by (title, entity_name, metric_name)
    unique_candidates: List[EvidenceRecommendationSchema] = []
    seen_keys: set = set()
    for cand in candidates:
        key = (cand.title.strip().lower(), str(cand.entity_name).strip().lower(), str(cand.metric_name).strip().lower())
        if key not in seen_keys:
            seen_keys.add(key)
            unique_candidates.append(cand)

    _PRIO_SCORES = {"critical": 400, "high": 300, "medium": 200, "low": 100}

    def _rank_key(c: EvidenceRecommendationSchema) -> Tuple[int, int]:
        prio_score = _PRIO_SCORES.get(c.priority, 100)
        strength_score = 3 if c.evidence_strength == "verified_statistical_finding" else (2 if c.evidence_strength == "strong_trend_correlation" else 1)
        return (prio_score, strength_score)

    unique_candidates.sort(key=_rank_key, reverse=True)

    # Slice to top 5 recommendations
    final_recommendations = unique_candidates[:5]

    for idx, rec in enumerate(final_recommendations, 1):
        rec.rec_id = f"rec_{idx}"

    crit_cnt = sum(1 for r in final_recommendations if r.priority == "critical")
    high_cnt = sum(1 for r in final_recommendations if r.priority == "high")
    med_cnt = sum(1 for r in final_recommendations if r.priority == "medium")
    low_cnt = sum(1 for r in final_recommendations if r.priority == "low")
    ev_cnt = sum(1 for r in final_recommendations if r.evidence_strength == "verified_statistical_finding")

    categories_present = list(dict.fromkeys(r.category for r in final_recommendations))

    top_prio = final_recommendations[0].priority.capitalize()
    summary_text = f"Identified {len(final_recommendations)} prioritized, data-backed recommendations for {domain_name}. Top priority: {final_recommendations[0].title}."

    return RecommendationsIntelligenceResponse(
        dataset_id=dataset_id,
        is_available=True,
        domain_id=domain_id,
        domain_name=domain_name,
        currency_symbol=currency,
        overview=RecommendationsOverviewSchema(
            total_recommendations=len(final_recommendations),
            critical_count=crit_cnt,
            high_count=high_cnt,
            medium_count=med_cnt,
            low_count=low_cnt,
            evidence_backed_count=ev_cnt,
            data_limitations_summary=data_limitations,
            summary_statement=summary_text,
        ),
        recommendations=final_recommendations,
        categories_present=categories_present,
        has_time_dimension=has_time_dim,
        analyzed_at=datetime.now(timezone.utc).isoformat(),
    )
