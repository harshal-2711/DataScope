"""Universal, Domain-Aware Risk and Anomaly Detection Engine.

Surfaces only meaningful, evidence-based risks using simple human-readable explanations,
transparent severity classifications, and cautious, qualified recommendations.

Eliminates misleading concentration signals and non-summable metric summations.
"""
from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np
import pandas as pd

from app.domains.base import RiskRule
from app.schemas.domain_blueprint import (
    DistributionInsightSchema,
    DomainIdentitySchema,
    RiskItemSchema,
    RiskOverviewSchema,
    RiskIntelligenceResponse,
)
from app.services.column_formatter import detect_column_unit, format_metric_display, humanize_column_name
from app.services.column_profiler import ColumnProfile


# Polarity mappings
_NEGATIVE_POLARITY_TERMS = {
    "cost", "expense", "spend", "loss", "losses", "defect", "defects", "defect_rate",
    "error", "errors", "error_rate", "delay", "delays", "delivery_time", "lead_time",
    "lead_time_days", "cancellation", "cancellations", "churn", "churn_rate",
    "attrition", "attrition_rate", "turnover", "turnover_rate", "latency", "ping",
    "failure", "failures", "return_rate", "refund", "refunds", "refund_rate",
    "incident", "incidents", "waiting_time", "wait_time", "downtime", "unscheduled_downtime",
    "bad_debts", "complaint", "complaints", "bounce_rate",
}

_POSITIVE_POLARITY_TERMS = {
    "revenue", "sales", "gross_sales", "net_sales", "profit", "net_profit", "gross_profit",
    "margin", "operating_margin", "income", "volume", "order_volume", "orders",
    "units_sold", "quantity", "win_rate", "wins", "score", "points", "attendance",
    "headcount", "conversion", "conversion_rate", "retention", "retention_rate",
    "yield", "output", "traffic", "subscribers", "active_users", "pass_rate", "satisfaction",
}

# Non-summable metric keywords: metrics that make NO mathematical sense to sum across categories
_NON_SUMMABLE_METRIC_TERMS = {
    "aging", "age", "days", "tenure", "tenure_days", "rating", "score", "temperature",
    "rank", "ranking", "year", "month", "id", "code", "postal", "zip", "pct",
    "percent", "percentage", "rate", "ratio", "margin", "discount", "discount_rate",
    "lat", "latitude", "lon", "longitude", "phone", "duration", "avg", "average",
}

# Meaningful volume/financial metrics for concentration evaluation
_VALID_CONCENTRATION_METRICS = {
    "sales", "revenue", "gross_sales", "net_sales", "spend", "total_spend", "cost",
    "orders", "order_volume", "volume", "units_sold", "contract_value", "tender_value",
    "amount", "freight_value", "gmv",
}

# Meaningful dependency grouping dimensions
_VALID_DEPENDENCY_DIMENSIONS = {
    "customer", "customer_name", "customer_id", "client", "buyer", "buyer_agency",
    "supplier", "vendor", "supplier_name", "vendor_name", "partner", "account",
    "borrower", "doctor", "provider", "hospital", "facility",
}

# Non-dependency / client-side UI dimensions
_NON_DEPENDENCY_DIMENSIONS = {
    "login", "customer_login_type", "login_type", "device", "device_type", "browser",
    "os", "platform", "channel", "payment", "payment_method", "gender", "status",
    "stage", "city", "state", "region", "country", "type", "method", "category", "tag",
}


def _is_negative_polarity(column_name: str) -> bool:
    """Return True if an increase in this metric represents an adverse/risky condition."""
    name_clean = str(column_name).lower().strip().replace("-", "_").replace(" ", "_")
    tokens = set(re.findall(r"[a-z0-9]+", name_clean))
    if tokens & _NEGATIVE_POLARITY_TERMS:
        return True
    padded = f"_{name_clean}_"
    return any(f"_{term}_" in padded for term in _NEGATIVE_POLARITY_TERMS)


def _is_positive_polarity(column_name: str) -> bool:
    """Return True if a decrease in this metric represents an adverse/risky condition."""
    name_clean = str(column_name).lower().strip().replace("-", "_").replace(" ", "_")
    tokens = set(re.findall(r"[a-z0-9]+", name_clean))
    if tokens & _POSITIVE_POLARITY_TERMS:
        return True
    padded = f"_{name_clean}_"
    return any(f"_{term}_" in padded for term in _POSITIVE_POLARITY_TERMS)


def _is_non_summable_metric(column_name: str) -> bool:
    """Return True if summing this metric across categories is mathematically misleading."""
    name_clean = str(column_name).lower().strip().replace("-", "_").replace(" ", "_")
    tokens = set(re.findall(r"[a-z0-9]+", name_clean))
    if tokens & _NON_SUMMABLE_METRIC_TERMS:
        return True
    padded = f"_{name_clean}_"
    return any(f"_{term}_" in padded for term in _NON_SUMMABLE_METRIC_TERMS)



def _find_date_column(df: pd.DataFrame, profiles: List[ColumnProfile]) -> Optional[str]:
    """Identify the most reliable datetime column in the dataset."""
    for p in profiles:
        if p.role in ("datetime", "time", "date") and p.name in df.columns:
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


def _format_val(
    val: Optional[float],
    column_name: Optional[str],
    domain_id: Optional[str] = None,
    dataset_currency: Optional[str] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """Return (formatted_str, unit_label) for a numeric value."""
    if val is None or math.isnan(val):
        return None, None
    unit_label, semantic_type, currency_sym = detect_column_unit(
        column_name=column_name or "",
        domain_id=domain_id,
        dataset_currency=dataset_currency,
    )
    formatted = format_metric_display(
        val,
        unit=unit_label,
        semantic_type=semantic_type,
        currency_symbol=currency_sym,
        compact=False,
        precision=2,
    )
    return formatted, unit_label


def compute_full_risk_intelligence(
    df: pd.DataFrame,
    dataset_id: str,
    profiles: List[ColumnProfile],
    domain: DomainIdentitySchema,
    dataset_currency: Optional[str] = None,
) -> RiskIntelligenceResponse:
    """Execute deep universal and domain-aware risk detection across all dimensions."""
    risks: List[RiskItemSchema] = []
    distribution_insights: List[DistributionInsightSchema] = []
    seen_risk_keys: Set[str] = set()
    data_safety_notes: List[str] = []
    data_quality_count = 0

    row_count = len(df)
    if row_count == 0:
        return RiskIntelligenceResponse(
            dataset_id=dataset_id,
            domain_id=domain.domain_id if domain else "general",
            domain_name=domain.name if domain else "General Dataset",
            overview=RiskOverviewSchema(
                total_risks=0,
                high_count=0,
                medium_count=0,
                low_count=0,
                most_significant_risk=None,
                data_quality_warnings_count=0,
                health_status="Healthy",
                summary_statement="The dataset is empty. No risk signals could be evaluated.",
            ),
            risks=[],
            categories=[],
            affected_metrics=[],
            has_time_dimension=False,
            data_safety_notes=["The uploaded dataset contains zero rows."],
        )

    # -------------------------------------------------------------------------
    # 1. DATA QUALITY & INTEGRITY ISSUES
    # -------------------------------------------------------------------------
    # 1a. Duplicate Records
    dup_count = int(df.duplicated().sum())
    dup_pct = (dup_count / row_count) * 100.0 if row_count > 0 else 0.0
    if dup_count > 0 and dup_pct >= 2.0:
        data_quality_count += 1
        is_high = dup_pct >= 10.0
        severity = "high" if is_high else "medium"
        risks.append(
            RiskItemSchema(
                risk_id="dq_duplicate_records",
                title="Duplicate data records detected",
                category="Data Quality Issue",
                label="Data hygiene issue",
                description=f"Found {dup_count:,} duplicate rows ({dup_pct:.1f}% of the dataset).",
                severity=severity,
                severity_reason=(
                    f"Duplicate rows exceed {'10%' if is_high else '2%'} of total records, "
                    "which may skew aggregate totals and statistics."
                ),
                affected_metric=None,
                affected_column=None,
                current_value=float(dup_count),
                current_value_formatted=f"{dup_count:,} duplicates",
                previous_value=0.0,
                previous_value_formatted="0 duplicates",
                absolute_change=float(dup_count),
                absolute_change_formatted=f"+{dup_count:,}",
                pct_change=round(dup_pct, 1),
                unit="records",
                time_period="Full Dataset",
                evidence=f"{dup_count:,} identical row entries out of {row_count:,} total records.",
                why_it_matters="Redundant entries can lead to double-counting in KPI sums and skewed category counts.",
                confidence=0.98,
                qualification="Identified through exact row-level matching across all columns.",
                recommended_action="Review data ingestion or deduplicate rows before final analysis.",
                risk_type="data_quality",
            )
        )
        seen_risk_keys.add("dq_duplicate_records")

    # 1b. Missing Data in Key Columns
    for prof in profiles:
        if prof.null_count > 0 and row_count > 0:
            null_pct = (prof.null_count / row_count) * 100.0
            if null_pct >= 20.0:
                data_quality_count += 1
                is_high = null_pct >= 50.0
                severity = "high" if is_high else ("medium" if null_pct >= 30.0 else "low")
                human_col = humanize_column_name(prof.name)

                risks.append(
                    RiskItemSchema(
                        risk_id=f"dq_missing_{prof.name}",
                        title=f"High proportion of missing values in '{human_col}'",
                        category="Data Quality Issue",
                        label="Missing data",
                        description=f"'{human_col}' is missing {null_pct:.1f}% of its values ({prof.null_count:,} unrecorded rows).",
                        severity=severity,
                        severity_reason=f"Over {null_pct:.1f}% of records lack data in this field.",
                        affected_metric=prof.name,
                        affected_column=prof.name,
                        current_value=float(prof.null_count),
                        current_value_formatted=f"{prof.null_count:,} missing",
                        previous_value=0.0,
                        previous_value_formatted="0 missing",
                        absolute_change=float(prof.null_count),
                        absolute_change_formatted=f"{prof.null_count:,} nulls",
                        pct_change=round(null_pct, 1),
                        unit="records",
                        time_period="Full Dataset",
                        evidence=f"{prof.null_count:,} null values out of {row_count:,} rows ({null_pct:.1f}%).",
                        why_it_matters="High missingness limits the statistical reliability of metrics derived from this column.",
                        confidence=0.99,
                        qualification="Counted directly from unpopulated data cells.",
                        recommended_action=f"Check upstream data collection for '{human_col}' or apply appropriate imputation if necessary.",
                        risk_type="data_quality",
                    )
                )
                seen_risk_keys.add(f"dq_missing_{prof.name}")

    # 1c. Statistical Outliers
    for prof in profiles:
        if prof.role == "numeric" and prof.name in df.columns:
            s = pd.to_numeric(df[prof.name], errors="coerce").dropna()
            if len(s) >= 20 and not _is_non_summable_metric(prof.name):
                q25 = float(s.quantile(0.25))
                q75 = float(s.quantile(0.75))
                iqr = q75 - q25
                if iqr > 1e-6:
                    upper_bound = q75 + (3.0 * iqr)
                    high_outliers = s[s > upper_bound]
                    total_outliers = len(high_outliers)
                    outlier_pct = (total_outliers / len(s)) * 100.0

                    if total_outliers > 0 and outlier_pct >= 1.5:
                        severity = "medium" if outlier_pct >= 5.0 else "low"
                        max_val = float(s.max())
                        human_col = humanize_column_name(prof.name)
                        formatted_max, unit_lbl = _format_val(max_val, prof.name, domain.domain_id, dataset_currency)
                        formatted_thresh, _ = _format_val(upper_bound, prof.name, domain.domain_id, dataset_currency)

                        risks.append(
                            RiskItemSchema(
                                risk_id=f"stat_outlier_{prof.name}",
                                title=f"Unusual high values detected in '{human_col}'",
                                category="Unusual Outlier",
                                label="Outlier observation",
                                description=(
                                    f"Found {total_outliers} unusually high values in '{human_col}' exceeding "
                                    f"the upper threshold of {formatted_thresh}."
                                ),
                                severity=severity,
                                severity_reason=f"{outlier_pct:.1f}% of records exceed the standard 3.0× IQR fence.",
                                affected_metric=prof.name,
                                affected_column=prof.name,
                                current_value=max_val,
                                current_value_formatted=formatted_max,
                                previous_value=upper_bound,
                                previous_value_formatted=formatted_thresh,
                                absolute_change=round(max_val - upper_bound, 2),
                                absolute_change_formatted=f"+{round(max_val - upper_bound, 2):,}",
                                pct_change=round(outlier_pct, 1),
                                unit=unit_lbl or "units",
                                time_period="Full Distribution",
                                evidence=f"Highest value is {formatted_max} vs expected threshold {formatted_thresh}.",
                                why_it_matters="Extreme values can skew averages and may indicate data entry errors or exceptional transactions.",
                                confidence=0.92,
                                qualification="Calculated using Tukey's statistical dispersion fence (Q3 + 3.0 * IQR).",
                                recommended_action=f"Review the highest records in '{human_col}' to confirm whether they represent valid activity.",
                                risk_type="outlier",
                            )
                        )
                        seen_risk_keys.add(f"stat_outlier_{prof.name}")

    # -------------------------------------------------------------------------
    # 2. TIME-SERIES PERFORMANCE & COST RISKS
    # -------------------------------------------------------------------------
    date_col = _find_date_column(df, profiles)
    has_time_dimension = date_col is not None

    if has_time_dimension and date_col:
        try:
            df_time = df.copy()
            df_time["_dt_parsed"] = pd.to_datetime(df_time[date_col], errors="coerce")
            df_time = df_time.dropna(subset=["_dt_parsed"]).sort_values("_dt_parsed")

            if len(df_time) >= 6:
                span_days = (df_time["_dt_parsed"].max() - df_time["_dt_parsed"].min()).days
                freq_code = "ME" if span_days > 60 else "D"
                freq_label = "Monthly" if freq_code == "ME" else "Daily"
                numeric_cols = [
                    p.name for p in profiles
                    if p.role == "numeric" and p.name in df_time.columns and p.name != date_col and not _is_non_summable_metric(p.name)
                ]

                # Pre-compute metric series across numeric columns for cross-metric correlation
                metric_series_map: Dict[str, pd.Series] = {}
                for met in numeric_cols[:8]:
                    s_clean = pd.to_numeric(df_time[met], errors="coerce")
                    if s_clean.notna().sum() < 6:
                        continue
                    try:
                        grp = df_time.set_index("_dt_parsed").resample(freq_code)[met].sum().dropna()
                    except Exception:
                        try:
                            grp = df_time.groupby(df_time["_dt_parsed"].dt.to_period("M" if span_days > 60 else "D"))[met].sum()
                            grp.index = grp.index.astype(str)
                        except Exception:
                            continue
                    if len(grp) >= 3:
                        metric_series_map[met] = grp

                # Check if both Revenue and Profit decline concurrently
                rev_col = next((m for m in metric_series_map if any(k in m.lower() for k in ("sales", "revenue", "gross_sales", "income"))), None)
                prof_col = next((m for m in metric_series_map if "profit" in m.lower() and m != rev_col), None)
                both_financial_declining = False
                margin_contracting = False

                if rev_col and prof_col:
                    r_vals = metric_series_map[rev_col].values.astype(float)
                    p_vals = metric_series_map[prof_col].values.astype(float)
                    if len(r_vals) >= 2 and len(p_vals) >= 2 and abs(r_vals[-2]) > 1e-6 and abs(p_vals[-2]) > 1e-6:
                        r_pct = ((r_vals[-1] - r_vals[-2]) / abs(r_vals[-2])) * 100.0
                        p_pct = ((p_vals[-1] - p_vals[-2]) / abs(p_vals[-2])) * 100.0
                        if r_pct <= -5.0 and p_pct <= -5.0:
                            both_financial_declining = True
                            if p_pct < r_pct:
                                margin_contracting = True

                for met, grouped in metric_series_map.items():
                    vals = grouped.values.astype(float)
                    periods = [str(idx)[:10] for idx in grouped.index]
                    n_periods = len(vals)

                    curr_val = float(vals[-1])
                    prev_val = float(vals[-2])
                    abs_change = curr_val - prev_val
                    pct_change = ((abs_change / abs(prev_val)) * 100.0) if abs(prev_val) > 1e-6 else 0.0
                    abs_pct = abs(pct_change)

                    # Statistical baseline over prior periods
                    hist_vals = vals[:-1] if n_periods >= 4 else vals
                    mean_hist = float(np.mean(hist_vals))
                    std_hist = float(np.std(hist_vals)) if len(hist_vals) >= 3 else 0.0
                    is_below_2sigma = bool(std_hist > 1e-6 and curr_val < (mean_hist - 2.0 * std_hist))
                    is_below_1sigma = bool(std_hist > 1e-6 and curr_val < (mean_hist - 1.0 * std_hist))
                    is_sustained = (n_periods >= 3 and vals[-1] < vals[-2] < vals[-3])

                    preview_points = [
                        {"period": periods[i], "value": round(float(vals[i]), 2)}
                        for i in range(max(0, n_periods - 12), n_periods)
                    ]

                    human_met = humanize_column_name(met)
                    curr_fmt, unit_lbl = _format_val(curr_val, met, domain.domain_id, dataset_currency)
                    prev_fmt, _ = _format_val(prev_val, met, domain.domain_id, dataset_currency)
                    abs_fmt, _ = _format_val(abs_change, met, domain.domain_id, dataset_currency)

                    is_neg_metric = _is_negative_polarity(met)
                    is_pos_metric = _is_positive_polarity(met)
                    is_financial = any(k in met.lower() for k in ("sales", "revenue", "profit", "income", "margin", "gmv"))

                    # 2a. Performance / Revenue / Profit Decline
                    if (is_pos_metric or not is_neg_metric) and pct_change <= -5.0:
                        # Evidence-based severity calibration:
                        # High: Severe drop (>=25%), or >=15% with sustained trend / below 2-sigma baseline
                        # Medium: Meaningful drop (>=10%), or >=7.5% sustained / below 1-sigma baseline
                        # Low: Minor isolated drop (5% - 10%)
                        is_high = (
                            abs_pct >= 25.0
                            or (abs_pct >= 15.0 and is_sustained)
                            or (abs_pct >= 18.0 and is_below_2sigma)
                            or (is_financial and abs_pct >= 20.0 and (is_sustained or is_below_1sigma))
                        )
                        is_med = (
                            abs_pct >= 10.0
                            or (abs_pct >= 7.5 and is_sustained)
                            or (abs_pct >= 8.0 and is_below_1sigma)
                            or (is_financial and abs_pct >= 10.0)
                        )
                        severity = "high" if is_high else ("medium" if is_med else "low")

                        # Meaningful labels and categories
                        if "profit" in met.lower():
                            category = "Revenue/Profit Risk"
                            label = "Profit decline" if severity in ("high", "medium") else "Minor profit drop"
                        elif any(k in met.lower() for k in ("sales", "revenue", "gmv", "income")):
                            category = "Revenue/Profit Risk"
                            label = "Revenue decline" if severity in ("high", "medium") else "Minor revenue drop"
                        else:
                            category = "Performance Decline"
                            label = "Performance decline" if severity in ("high", "medium") else "Minor variation"

                        title = f"{human_met} decreased compared with the previous period"
                        sustained_note = " with a sustained downward trend across consecutive periods" if is_sustained else ""

                        # Contextual why_it_matters explanation
                        if both_financial_declining and is_financial:
                            if margin_contracting and "profit" in met.lower():
                                why_note = (
                                    f"Both revenue and profit contracted simultaneously in this period, with profit declining at a steeper rate ({pct_change:+.1f}%), "
                                    f"reflecting compressed operational margins."
                                )
                            else:
                                why_note = (
                                    f"Both revenue and profit experienced concurrent decreases in this period, signaling combined top-line contraction. "
                                    f"Continued declines in '{human_met}' directly reduce available operating funds."
                                )
                        elif "profit" in met.lower():
                            why_note = (
                                f"A {abs_pct:.1f}% decline in '{human_met}' directly compresses net operating margins. "
                                "Persistent profit erosion may require structural cost adjustments."
                            )
                        elif any(k in met.lower() for k in ("sales", "revenue")):
                            why_note = (
                                f"Top-line reduction in '{human_met}' reduces gross volume and cash flow. "
                                "Investigating sales channels and client segments is recommended to stabilize performance."
                            )
                        else:
                            why_note = f"Continued declines in '{human_met}' may impact overall operational throughput and performance goals."

                        severity_justification = (
                            f"Period-over-period decline of {abs_pct:.1f}% ({prev_fmt} -> {curr_fmt})"
                            f"{' persisting across multiple consecutive periods' if is_sustained else ''}"
                            f"{' dropping significantly below historical baseline' if is_below_1sigma else ''}."
                        )

                        risks.append(
                            RiskItemSchema(
                                risk_id=f"trend_decline_{met}",
                                title=title,
                                category=category,
                                label=label,
                                description=(
                                    f"'{human_met}' decreased by {abs(pct_change):.1f}% from {prev_fmt} ({periods[-2]}) "
                                    f"to {curr_fmt} ({periods[-1]}){sustained_note}."
                                ),
                                severity=severity,
                                severity_reason=severity_justification,
                                affected_metric=met,
                                affected_column=met,
                                current_value=curr_val,
                                current_value_formatted=curr_fmt,
                                previous_value=prev_val,
                                previous_value_formatted=prev_fmt,
                                absolute_change=abs_change,
                                absolute_change_formatted=abs_fmt,
                                pct_change=round(pct_change, 1),
                                unit=unit_lbl or "units",
                                time_period=f"{periods[-2]} to {periods[-1]} ({freq_label})",
                                evidence=f"Previous period: {prev_fmt} -> Current period: {curr_fmt} ({pct_change:+.1f}%).",
                                why_it_matters=why_note,
                                confidence=0.94,
                                qualification="Calculated directly from chronological period aggregation.",
                                recommended_action=f"Investigate the underlying product categories, client segments, or regions contributing to the decline in '{human_met}'.",
                                risk_type="performance_decline",
                                time_series_preview=preview_points,
                            )
                        )
                        seen_risk_keys.add(f"trend_decline_{met}")

                    # 2b. Cost / Delay / Expense Increase
                    elif is_neg_metric and pct_change >= 5.0:
                        is_high = pct_change >= 25.0 or (pct_change >= 15.0 and is_sustained)
                        is_med = pct_change >= 10.0 or (pct_change >= 7.5 and is_sustained)
                        severity = "high" if is_high else ("medium" if is_med else "low")

                        category = "Cost Increase" if any(k in met.lower() for k in ("cost", "expense", "spend")) else "Operational Risk"
                        title = f"{human_met} increased compared with the previous period"

                        risks.append(
                            RiskItemSchema(
                                risk_id=f"trend_escalation_{met}",
                                title=title,
                                category=category,
                                label="Cost surge" if severity in ("high", "medium") else "Minor cost rise",
                                description=(
                                    f"'{human_met}' rose by {pct_change:.1f}% from {prev_fmt} ({periods[-2]}) "
                                    f"to {curr_fmt} ({periods[-1]})."
                                ),
                                severity=severity,
                                severity_reason=f"Period-over-period adverse rise of {pct_change:.1f}%.",
                                affected_metric=met,
                                affected_column=met,
                                current_value=curr_val,
                                current_value_formatted=curr_fmt,
                                previous_value=prev_val,
                                previous_value_formatted=prev_fmt,
                                absolute_change=abs_change,
                                absolute_change_formatted=abs_fmt,
                                pct_change=round(pct_change, 1),
                                unit=unit_lbl or "units",
                                time_period=f"{periods[-2]} to {periods[-1]} ({freq_label})",
                                evidence=f"Previous period: {prev_fmt} -> Current period: {curr_fmt} ({pct_change:+.1f}%).",
                                why_it_matters=f"Unchecked growth in '{human_met}' can compress operating margins and reduce operational efficiency.",
                                confidence=0.93,
                                qualification="Calculated from chronological period aggregation.",
                                recommended_action=f"Audit recent drivers or expenditure categories causing elevated '{human_met}'.",
                                risk_type="cost_escalation",
                                time_series_preview=preview_points,
                            )
                        )
                        seen_risk_keys.add(f"trend_escalation_{met}")

                    # 2c. Time-Series Volatility
                    if n_periods >= 4:
                        mean_val = float(np.mean(vals))
                        std_val = float(np.std(vals))
                        if abs(mean_val) > 1e-6:
                            cv = std_val / abs(mean_val)
                            if cv >= 0.50:
                                severity = "medium" if cv < 0.85 else "high"
                                risks.append(
                                    RiskItemSchema(
                                        risk_id=f"trend_volatility_{met}",
                                        title=f"High variation observed in '{human_met}'",
                                        category="High Volatility",
                                        label="Volatility observation",
                                        description=(
                                            f"'{human_met}' shows notable fluctuations over time with a coefficient "
                                            f"of variation of {cv * 100.0:.1f}% (standard deviation: {std_val:,.2f} vs average: {mean_val:,.2f})."
                                        ),
                                        severity=severity,
                                        severity_reason=f"Dispersion ratio (CV = {cv * 100.0:.1f}%) indicates significant period swings.",
                                        affected_metric=met,
                                        affected_column=met,
                                        current_value=std_val,
                                        current_value_formatted=f"±{std_val:,.2f}",
                                        previous_value=mean_val,
                                        previous_value_formatted=f"Average {mean_val:,.2f}",
                                        absolute_change=std_val,
                                        absolute_change_formatted=f"σ = {std_val:,.2f}",
                                        pct_change=round(cv * 100.0, 1),
                                        unit=unit_lbl or "units",
                                        time_period=f"{periods[0]} to {periods[-1]} ({len(periods)} periods)",
                                        evidence=f"Average = {mean_val:,.2f}, Standard Deviation = {std_val:,.2f} across {len(periods)} periods.",
                                        why_it_matters="High unpredictability makes forecasting, budgeting, and capacity planning more challenging.",
                                        confidence=0.88,
                                        qualification="Derived from historical empirical coefficient of variation (CV = σ / μ).",
                                        recommended_action=f"Analyze drivers of volatility in '{human_met}' to determine if fluctuations are seasonal or sporadic.",
                                        risk_type="volatility",
                                        time_series_preview=preview_points,
                                    )
                                )
                                seen_risk_keys.add(f"trend_volatility_{met}")
        except Exception:
            data_safety_notes.append("Time-series risk evaluation encountered unparseable dates; defaulted to cross-sectional checks.")

    # -------------------------------------------------------------------------
    # 3. CROSS-SECTIONAL & OPERATIONAL SIGNALS (CLEAN & NON-MISLEADING)
    # -------------------------------------------------------------------------
    categorical_cols = [
        p.name for p in profiles
        if p.role in ("categorical", "identifier") and p.name in df.columns and p.distinct_count and 2 <= p.distinct_count <= 200
    ]
    numeric_cols_all = [
        p.name for p in profiles
        if p.role == "numeric" and p.name in df.columns and not _is_non_summable_metric(p.name)
    ]

    # 3a. Descriptive Population & Distribution Insights (Descriptive Observations Only)
    for dim_col in categorical_cols:
        dim_lower = str(dim_col).lower().replace("-", "_").replace(" ", "_")
        human_dim = humanize_column_name(dim_col)
        try:
            s_cat = df[dim_col].dropna().astype(str)
            if len(s_cat) >= 15:
                counts = s_cat.value_counts()
                if len(counts) >= 2:
                    top_cat = str(counts.index[0])
                    top_cnt = int(counts.iloc[0])
                    tot_cnt = int(len(s_cat))
                    pct = (top_cnt / tot_cnt) * 100.0
                    if pct >= 70.0:
                        distribution_insights.append(
                            DistributionInsightSchema(
                                insight_id=f"dist_{dim_col}",
                                dimension=dim_col,
                                dimension_label=human_dim,
                                dominant_category=top_cat,
                                category_count=top_cnt,
                                total_records=tot_cnt,
                                percentage=round(pct, 1),
                                description=f"'{top_cat}' represents {pct:.1f}% of recorded entries in {human_dim} ({top_cnt:,} of {tot_cnt:,} rows).",
                                observation_note=f"Descriptive population characteristic. High prevalence in {human_dim} does not indicate an operational vulnerability.",
                            )
                        )
        except Exception:
            pass

    # 3b. Genuine Operational Concentration Risks (Validated Dependencies ONLY)
    for dim_col in categorical_cols:
        dim_lower = str(dim_col).lower().replace("-", "_").replace(" ", "_")
        is_non_dep = any(term in dim_lower for term in _NON_DEPENDENCY_DIMENSIONS)
        is_valid_dep = any(term in dim_lower for term in _VALID_DEPENDENCY_DIMENSIONS)

        # Strictly skip non-dependency dimensions (e.g. login_type, device_type, payment_method, etc.)
        if is_non_dep or not is_valid_dep:
            continue

        for met_col in numeric_cols_all:
            met_lower = str(met_col).lower().replace("-", "_").replace(" ", "_")
            is_valid_met = any(term in met_lower for term in _VALID_CONCENTRATION_METRICS)
            if not is_valid_met:
                continue

            key = f"conc_{dim_col}_{met_col}"
            if key in seen_risk_keys:
                continue

            try:
                clean = df[[dim_col, met_col]].dropna()
                if len(clean) >= 20:
                    grouped = clean.groupby(dim_col)[met_col].sum()
                    if len(grouped) >= 3:
                        total_vol = float(grouped.sum())
                        if total_vol > 0:
                            top_val = float(grouped.max())
                            top_name = str(grouped.idxmax())
                            top_share = (top_val / total_vol) * 100.0

                            if top_share >= 50.0:
                                severity = "high" if top_share >= 80.0 else "medium"
                                human_dim = humanize_column_name(dim_col)
                                human_met = humanize_column_name(met_col)
                                top_val_fmt, unit_lbl = _format_val(top_val, met_col, domain.domain_id, dataset_currency)
                                tot_val_fmt, _ = _format_val(total_vol, met_col, domain.domain_id, dataset_currency)

                                risks.append(
                                    RiskItemSchema(
                                        risk_id=key,
                                        title=f"High concentration in {human_dim}: {top_name}",
                                        category="Operational Risk",
                                        label="Dependency risk",
                                        description=(
                                            f"Single entity '{top_name}' represents {top_share:.1f}% of total '{human_met}' "
                                            f"({top_val_fmt} out of {tot_val_fmt})."
                                        ),
                                        severity=severity,
                                        severity_reason=f"Top entity accounts for {top_share:.1f}% of total volume across {len(grouped)} entities.",
                                        affected_metric=met_col,
                                        affected_column=dim_col,
                                        current_value=top_val,
                                        current_value_formatted=top_val_fmt,
                                        previous_value=total_vol,
                                        previous_value_formatted=tot_val_fmt,
                                        absolute_change=top_val,
                                        absolute_change_formatted=f"{top_share:.1f}% share",
                                        pct_change=round(top_share, 1),
                                        unit=unit_lbl or "units",
                                        time_period="Full Dataset",
                                        evidence=f"'{top_name}' contributes {top_val_fmt} of total {tot_val_fmt} ({top_share:.1f}% share).",
                                        why_it_matters="High reliance on a single entity creates operational vulnerability if their activity changes.",
                                        confidence=0.95,
                                        qualification="Evaluated directly from entity summation over available records.",
                                        recommended_action=f"Assess diversification options to balance operational dependency on '{top_name}'.",
                                        risk_type="concentration",
                                    )
                                )
                                seen_risk_keys.add(key)
                                break
            except Exception:
                continue

    # 3b. Operating Losses / Negative Margins
    for prof in profiles:
        if prof.role == "numeric" and prof.name in df.columns:
            name_lower = prof.name.lower()
            if any(k in name_lower for k in ("profit", "net_margin", "operating_income")):
                s = pd.to_numeric(df[prof.name], errors="coerce").dropna()
                if len(s) > 0:
                    neg_count = int((s < 0).sum())
                    neg_pct = (neg_count / len(s)) * 100.0
                    total_sum = float(s.sum())

                    if total_sum < 0 or neg_pct >= 15.0:
                        severity = "high" if total_sum < 0 else "medium"
                        human_col = humanize_column_name(prof.name)
                        tot_fmt, unit_lbl = _format_val(total_sum, prof.name, domain.domain_id, dataset_currency)
                        risks.append(
                            RiskItemSchema(
                                risk_id=f"financial_loss_{prof.name}",
                                title=f"Operating losses observed in '{human_col}'",
                                category="Revenue/Profit Risk",
                                label="Loss observation",
                                description=(
                                    f"Dataset contains {neg_count:,} negative entries ({neg_pct:.1f}% of records) "
                                    f"with a net total of {tot_fmt}."
                                ),
                                severity=severity,
                                severity_reason="Net aggregate is negative" if total_sum < 0 else f"{neg_pct:.1f}% of records are unprofitable.",
                                affected_metric=prof.name,
                                affected_column=prof.name,
                                current_value=total_sum,
                                current_value_formatted=tot_fmt,
                                previous_value=0.0,
                                previous_value_formatted="0",
                                absolute_change=total_sum,
                                absolute_change_formatted=tot_fmt,
                                pct_change=round(neg_pct, 1),
                                unit=unit_lbl or "₹",
                                time_period="Full Dataset",
                                evidence=f"{neg_count:,} loss records out of {len(s):,} total transactions (net sum: {tot_fmt}).",
                                why_it_matters="Negative margins erode profitability and may indicate underpriced products or excessive discounts.",
                                confidence=0.96,
                                qualification="Calculated by identifying records where value < 0.",
                                recommended_action=f"Review unprofitable transactions in '{human_col}' to pinpoint margin leaks.",
                                risk_type="financial_loss",
                            )
                        )
                        seen_risk_keys.add(f"financial_loss_{prof.name}")

    # 3c. Inventory Stockout
    for prof in profiles:
        if prof.role == "numeric" and prof.name in df.columns:
            name_lower = prof.name.lower()
            if any(k in name_lower for k in ("stock", "inventory", "stock_level", "units_in_stock", "available_quantity")):
                s = pd.to_numeric(df[prof.name], errors="coerce").dropna()
                if len(s) >= 10:
                    zero_stock_count = int((s <= 0).sum())
                    zero_stock_pct = (zero_stock_count / len(s)) * 100.0
                    if zero_stock_count > 0 and zero_stock_pct >= 5.0:
                        severity = "medium" if zero_stock_pct < 25.0 else "high"
                        human_col = humanize_column_name(prof.name)
                        risks.append(
                            RiskItemSchema(
                                risk_id=f"inventory_stockout_{prof.name}",
                                title="Depleted inventory items detected",
                                category="Operational Risk",
                                label="Inventory notice",
                                description=f"Found {zero_stock_count:,} items ({zero_stock_pct:.1f}%) with zero or negative recorded stock.",
                                severity=severity,
                                severity_reason=f"{zero_stock_pct:.1f}% of inventory records have zero available units.",
                                affected_metric=prof.name,
                                affected_column=prof.name,
                                current_value=float(zero_stock_count),
                                current_value_formatted=f"{zero_stock_count:,} items",
                                previous_value=0.0,
                                previous_value_formatted="0 items",
                                absolute_change=float(zero_stock_count),
                                absolute_change_formatted=f"+{zero_stock_count:,}",
                                pct_change=round(zero_stock_pct, 1),
                                unit="units",
                                time_period="Full Dataset",
                                evidence=f"{zero_stock_count:,} SKUs with stock <= 0 out of {len(s):,} total items.",
                                why_it_matters="Stockouts can lead to unfulfilled demand and lost revenue opportunities.",
                                confidence=0.95,
                                qualification="Evaluated from non-positive inventory records.",
                                recommended_action="Check replenishment schedules for depleted items to avoid availability bottlenecks.",
                                risk_type="inventory_risk",
                            )
                        )
                        seen_risk_keys.add(f"inventory_stockout_{prof.name}")

    # 3d. HR Attrition
    if domain.domain_id in ("people_hr", "hr"):
        for prof in profiles:
            name_lower = prof.name.lower()
            if any(k in name_lower for k in ("attrition", "left", "exit", "turnover", "status")) and prof.name in df.columns:
                col_vals = df[prof.name].dropna().astype(str).str.lower()
                exit_count = int(col_vals.isin(["yes", "true", "1", "left", "terminated", "resigned", "exit"]).sum())
                if exit_count > 0 and len(col_vals) > 0:
                    attrition_rate = (exit_count / len(col_vals)) * 100.0
                    if attrition_rate >= 12.0:
                        severity = "high" if attrition_rate >= 25.0 else "medium"
                        risks.append(
                            RiskItemSchema(
                                risk_id="hr_attrition_risk",
                                title="Elevated workforce turnover rate",
                                category="Operational Risk",
                                label="Turnover observation",
                                description=f"Observed an employee turnover rate of {attrition_rate:.1f}% ({exit_count:,} exits out of {len(col_vals):,} total personnel).",
                                severity=severity,
                                severity_reason=f"Turnover rate of {attrition_rate:.1f}% exceeds typical reference thresholds.",
                                affected_metric=prof.name,
                                affected_column=prof.name,
                                current_value=round(attrition_rate, 1),
                                current_value_formatted=f"{attrition_rate:.1f}%",
                                previous_value=10.0,
                                previous_value_formatted="10.0% benchmark",
                                absolute_change=round(attrition_rate - 10.0, 1),
                                absolute_change_formatted=f"+{round(attrition_rate - 10.0, 1):.1f}%",
                                pct_change=round(attrition_rate, 1),
                                unit="%",
                                time_period="Full Dataset",
                                evidence=f"{exit_count:,} exits recorded out of {len(col_vals):,} total personnel.",
                                why_it_matters="High turnover increases hiring and onboarding costs and may affect team productivity.",
                                confidence=0.92,
                                qualification="Calculated directly from employee status records.",
                                recommended_action="Review exit patterns and retention feedback across departments.",
                                risk_type="workforce_attrition",
                            )
                        )
                        seen_risk_keys.add("hr_attrition_risk")

    # -------------------------------------------------------------------------
    # 4. OVERVIEW SYNTHESIS & REALISTIC HEALTH STATUS
    # -------------------------------------------------------------------------
    # Sort risks: high severity first, then medium, then low, then absolute pct change
    severity_order = {"high": 3, "medium": 2, "low": 1}
    risks.sort(
        key=lambda r: (
            severity_order.get(r.severity, 0),
            abs(r.pct_change or 0.0),
            abs(r.current_value or 0.0),
        ),
        reverse=True,
    )

    high_count = sum(1 for r in risks if r.severity == "high")
    medium_count = sum(1 for r in risks if r.severity == "medium")
    low_count = sum(1 for r in risks if r.severity == "low")
    total_risks = len(risks)

    # Realistic, non-alarmist health status
    if high_count >= 2:
        health_status = "Critical Risks Identified"
        summary_stmt = (
            f"Identified {total_risks} findings ({high_count} high priority, {medium_count} moderate, {low_count} informational). "
            f"Primary focus recommended for '{risks[0].title}'."
        )
    elif high_count == 1 or medium_count > 0:
        health_status = "Attention Required"
        summary_stmt = (
            f"Identified {total_risks} finding{'' if total_risks == 1 else 's'} ({high_count} high, {medium_count} moderate, {low_count} informational). "
            "Data demonstrates general operational consistency with isolated areas for review."
        )
    elif low_count > 0:
        health_status = "Healthy"
        summary_stmt = (
            f"Identified {low_count} informational distribution observation{'' if low_count == 1 else 's'}. "
            "No critical risks or severe performance drops were detected."
        )
    else:
        health_status = "Healthy"
        summary_stmt = "No significant risks detected in the available data."

    categories = sorted(list({r.category for r in risks if r.category}))
    affected_metrics = sorted(list({r.affected_metric for r in risks if r.affected_metric}))

    overview = RiskOverviewSchema(
        total_risks=total_risks,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,
        most_significant_risk=risks[0] if risks else None,
        data_quality_warnings_count=data_quality_count,
        health_status=health_status,
        summary_statement=summary_stmt,
    )

    return RiskIntelligenceResponse(
        dataset_id=dataset_id,
        domain_id=domain.domain_id if domain else "general",
        domain_name=domain.name if domain else "General Tabular Dataset",
        overview=overview,
        risks=risks,
        distribution_insights=distribution_insights,
        categories=categories,
        affected_metrics=affected_metrics,
        has_time_dimension=has_time_dimension,
        data_safety_notes=data_safety_notes,
    )


def detect_risks_and_anomalies(
    df: pd.DataFrame,
    profiles: List[ColumnProfile],
    validated_risks: List[Tuple[RiskRule, Optional[str], Optional[str]]],
) -> List[RiskItemSchema]:
    """Maintain backward compatibility for domain intelligence blueprint pipeline."""
    dummy_domain = DomainIdentitySchema(
        domain_id="general",
        name="Dataset",
        description="",
    )
    intel = compute_full_risk_intelligence(
        df=df,
        dataset_id="compat",
        profiles=profiles,
        domain=dummy_domain,
    )
    return intel.risks

