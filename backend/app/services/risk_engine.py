"""Universal, Domain-Aware Risk and Anomaly Detection Engine.

Automatically detects, classifies, prioritizes, and explains potential risks
across diverse industry domains (E-Commerce, Finance, Healthcare, HR, Operations,
Procurement, Sports, and General Tabular Datasets).

All conclusions are evidence-based, mathematically grounded, and neutrally framed.
"""
from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np
import pandas as pd

from app.domains.base import RiskRule
from app.schemas.domain_blueprint import (
    DomainIdentitySchema,
    RiskItemSchema,
    RiskOverviewSchema,
    RiskIntelligenceResponse,
)
from app.services.column_formatter import detect_column_unit, format_metric_display
from app.services.column_profiler import ColumnProfile


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


def _is_negative_polarity(column_name: str) -> bool:
    """Return True if an increase in this metric represents an adverse/risky condition."""
    name_clean = str(column_name).lower().strip().replace("-", "_").replace(" ", "_")
    tokens = set(re.findall(r"[a-z0-9]+", name_clean))
    return bool(tokens & _NEGATIVE_POLARITY_TERMS) or any(term in name_clean for term in _NEGATIVE_POLARITY_TERMS)


def _is_positive_polarity(column_name: str) -> bool:
    """Return True if a decrease in this metric represents an adverse/risky condition."""
    name_clean = str(column_name).lower().strip().replace("-", "_").replace(" ", "_")
    tokens = set(re.findall(r"[a-z0-9]+", name_clean))
    return bool(tokens & _POSITIVE_POLARITY_TERMS) or any(term in name_clean for term in _POSITIVE_POLARITY_TERMS)


def _find_date_column(df: pd.DataFrame, profiles: List[ColumnProfile]) -> Optional[str]:
    """Identify the most reliable datetime column in the dataset."""
    # 1. Check profile roles
    for p in profiles:
        if p.role in ("datetime", "time", "date") and p.name in df.columns:
            return p.name

    # 2. Check column dtypes
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            return col

    # 3. Check name heuristics with date conversion test
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
    # 1. DATA QUALITY & INTEGRITY SIGNALS
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
                title="Duplicate Data Records",
                category="Data Quality",
                label="Potential anomaly",
                description=f"Detected {dup_count:,} duplicate rows representing {dup_pct:.1f}% of all records.",
                severity=severity,
                severity_reason=(
                    f"Classified as {severity.upper()} severity because duplicate records exceed "
                    f"{'10%' if is_high else '2%'} of total volume, which may distort aggregate metrics."
                ),
                affected_metric=None,
                affected_column=None,
                current_value=float(dup_count),
                current_value_formatted=f"{dup_count:,} rows",
                previous_value=0.0,
                previous_value_formatted="0 rows",
                absolute_change=float(dup_count),
                absolute_change_formatted=f"+{dup_count:,} duplicates",
                pct_change=round(dup_pct, 1),
                unit="records",
                time_period="Full Dataset",
                evidence=f"{dup_count} duplicate row entries out of {row_count} total rows ({dup_pct:.1f}%).",
                confidence=0.98,
                qualification="Calculated by strict full-row exact matching across all columns.",
                recommended_action="Review upstream data ingestion and deduplicate redundant records before executive reporting.",
                risk_type="data_quality",
            )
        )
        seen_risk_keys.add("dq_duplicate_records")

    # 1b. Missing Data / Null Values
    for prof in profiles:
        if prof.null_count > 0 and row_count > 0:
            null_pct = (prof.null_count / row_count) * 100.0
            if null_pct >= 20.0:
                data_quality_count += 1
                is_high = null_pct >= 50.0
                severity = "high" if is_high else ("medium" if null_pct >= 30.0 else "low")
                col_formatted, unit_lbl = _format_val(float(prof.null_count), prof.name, domain.domain_id, dataset_currency)
                risks.append(
                    RiskItemSchema(
                        risk_id=f"dq_missing_{prof.name}",
                        title=f"High Missingness in '{prof.name}'",
                        category="Data Quality",
                        label="Requires investigation",
                        description=f"Column '{prof.name}' is missing {null_pct:.1f}% of its entries ({prof.null_count:,} unrecorded rows).",
                        severity=severity,
                        severity_reason=(
                            f"Classified as {severity.upper()} severity due to {null_pct:.1f}% unrecorded data in '{prof.name}', "
                            "limiting statistical reliability."
                        ),
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
                        evidence=f"{prof.null_count} null records out of {row_count} total records ({null_pct:.1f}% missing).",
                        confidence=0.99,
                        qualification="Evaluated directly from pandas null / NaN profiling.",
                        recommended_action=f"Audit upstream capture for '{prof.name}' or apply documented imputation if required.",
                        risk_type="data_quality",
                    )
                )
                seen_risk_keys.add(f"dq_missing_{prof.name}")

    # 1c. Extreme Statistical Outliers (3x IQR)
    for prof in profiles:
        if prof.role == "numeric" and prof.name in df.columns:
            s = pd.to_numeric(df[prof.name], errors="coerce").dropna()
            if len(s) >= 20:
                q25 = float(s.quantile(0.25))
                q75 = float(s.quantile(0.75))
                iqr = q75 - q25
                if iqr > 1e-6:
                    upper_bound = q75 + (3.0 * iqr)
                    lower_bound = q25 - (3.0 * iqr)
                    high_outliers = s[s > upper_bound]
                    low_outliers = s[s < lower_bound]
                    total_outliers = len(high_outliers) + len(low_outliers)
                    outlier_pct = (total_outliers / len(s)) * 100.0

                    if total_outliers > 0 and outlier_pct >= 1.5:
                        severity = "high" if outlier_pct >= 8.0 else ("medium" if outlier_pct >= 3.0 else "low")
                        max_val = float(s.max())
                        formatted_max, unit_lbl = _format_val(max_val, prof.name, domain.domain_id, dataset_currency)
                        formatted_thresh, _ = _format_val(upper_bound, prof.name, domain.domain_id, dataset_currency)

                        risks.append(
                            RiskItemSchema(
                                risk_id=f"stat_outlier_{prof.name}",
                                title=f"Extreme Statistical Outliers in '{prof.name}'",
                                category="Statistical Dispersion",
                                label="Unusual pattern detected",
                                description=(
                                    f"Found {total_outliers} extreme values in '{prof.name}' exceeding the 3.0× IQR threshold "
                                    f"({formatted_thresh or round(upper_bound, 2)})."
                                ),
                                severity=severity,
                                severity_reason=(
                                    f"Classified as {severity.upper()} severity because {outlier_pct:.1f}% of data points "
                                    "deviate substantially beyond standard interquartile spread."
                                ),
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
                                evidence=(
                                    f"Max observed value is {formatted_max} vs 3× IQR upper limit of {formatted_thresh} "
                                    f"({total_outliers} outlier records, {outlier_pct:.1f}% of series)."
                                ),
                                confidence=0.92,
                                qualification="Calculated using Tukey's extreme outlier fence (Q3 + 3.0 * IQR).",
                                recommended_action="Audit outlier transactions for entry errors, exceptional promotions, or anomalous spikes.",
                                risk_type="outlier",
                            )
                        )
                        seen_risk_keys.add(f"stat_outlier_{prof.name}")

    # -------------------------------------------------------------------------
    # 2. TIME-SERIES & TREND PERFORMANCE RISKS
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
                    if p.role == "numeric" and p.name in df_time.columns and p.name != date_col
                ]

                for met in numeric_cols[:6]:
                    s_clean = pd.to_numeric(df_time[met], errors="coerce")
                    if s_clean.notna().sum() < 6:
                        continue

                    try:
                        grouped = df_time.set_index("_dt_parsed").resample(freq_code)[met].sum().dropna()
                    except Exception:
                        try:
                            grouped = df_time.groupby(df_time["_dt_parsed"].dt.to_period("M" if span_days > 60 else "D"))[met].sum()
                            grouped.index = grouped.index.astype(str)
                        except Exception:
                            continue

                    if len(grouped) < 3:
                        continue

                    vals = grouped.values.astype(float)
                    periods = [str(idx)[:10] for idx in grouped.index]
                    n_periods = len(vals)

                    curr_val = float(vals[-1])
                    prev_val = float(vals[-2])
                    abs_change = curr_val - prev_val
                    pct_change = ((abs_change / abs(prev_val)) * 100.0) if abs(prev_val) > 1e-6 else 0.0

                    preview_points = [
                        {"period": periods[i], "value": round(float(vals[i]), 2)}
                        for i in range(max(0, n_periods - 12), n_periods)
                    ]

                    curr_fmt, unit_lbl = _format_val(curr_val, met, domain.domain_id, dataset_currency)
                    prev_fmt, _ = _format_val(prev_val, met, domain.domain_id, dataset_currency)
                    abs_fmt, _ = _format_val(abs_change, met, domain.domain_id, dataset_currency)

                    is_neg_metric = _is_negative_polarity(met)
                    is_pos_metric = _is_positive_polarity(met)

                    # 2a. Performance Decline
                    if (is_pos_metric or not is_neg_metric) and pct_change <= -5.0:
                        is_sustained = (
                            n_periods >= 3 and vals[-1] < vals[-2] < vals[-3]
                        )
                        is_high = pct_change <= -30.0 or (pct_change <= -20.0 and is_sustained)
                        is_med = pct_change <= -15.0 or is_sustained
                        severity = "high" if is_high else ("medium" if is_med else "low")

                        title = f"Decline in {met}"
                        if domain.domain_id in ("ecommerce", "sales_marketing", "retail") and any(k in met.lower() for k in ("sales", "revenue")):
                            title = "Revenue Contraction"
                        elif domain.domain_id in ("finance", "fintech") and any(k in met.lower() for k in ("profit", "margin", "income")):
                            title = "Profit Margin Compression"
                        elif domain.domain_id in ("people_hr", "hr") and any(k in met.lower() for k in ("attendance", "headcount")):
                            title = "Workforce Participation Decline"
                        elif domain.domain_id in ("sports", "sports_performance") and any(k in met.lower() for k in ("win", "score", "points")):
                            title = "Sports Performance Contraction"
                        elif domain.domain_id in ("healthcare", "healthcare_life") and any(k in met.lower() for k in ("patient", "volume", "admission")):
                            title = "Patient Volume Shift"
                        elif domain.domain_id in ("procurement", "logistics_travel") and any(k in met.lower() for k in ("order", "volume")):
                            title = "Order Volume Contraction"

                        sustained_text = " (exhibiting sustained consecutive-period decline)" if is_sustained else ""
                        risks.append(
                            RiskItemSchema(
                                risk_id=f"trend_decline_{met}",
                                title=title,
                                category="Performance Trend",
                                label="Requires investigation" if severity in ("high", "medium") else "Potential anomaly",
                                description=(
                                    f"'{met}' decreased by {abs(pct_change):.1f}% from {prev_fmt} ({periods[-2]}) "
                                    f"to {curr_fmt} ({periods[-1]}){sustained_text}."
                                ),
                                severity=severity,
                                severity_reason=(
                                    f"Classified as {severity.upper()} severity due to a {abs(pct_change):.1f}% period-over-period decline"
                                    f"{' with multi-period persistence' if is_sustained else ''}."
                                ),
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
                                evidence=(
                                    f"Period comparison: Previous={prev_fmt}, Latest={curr_fmt}, "
                                    f"Delta={abs_fmt} ({pct_change:+.1f}%)."
                                ),
                                confidence=0.94,
                                qualification="Calculated from period-aggregated time-series historical values without external assumptions.",
                                recommended_action=(
                                    f"Investigate recent drivers behind '{met}' contraction across underlying operational segments."
                                ),
                                risk_type="performance_decline",
                                time_series_preview=preview_points,
                            )
                        )
                        seen_risk_keys.add(f"trend_decline_{met}")

                    # 2b. Cost / Expense / Defect / Delay Escalation
                    elif is_neg_metric and pct_change >= 10.0:
                        is_sustained = (
                            n_periods >= 3 and vals[-1] > vals[-2] > vals[-3]
                        )
                        is_high = pct_change >= 30.0 or (pct_change >= 20.0 and is_sustained)
                        is_med = pct_change >= 15.0 or is_sustained
                        severity = "high" if is_high else ("medium" if is_med else "low")

                        title = f"Escalation in {met}"
                        if any(k in met.lower() for k in ("cost", "expense", "spend")):
                            title = "Cost & Expenditure Surge"
                        elif any(k in met.lower() for k in ("defect", "error", "failure")):
                            title = "Defect Rate Surge"
                        elif any(k in met.lower() for k in ("delay", "lead_time", "delivery_time")):
                            title = "Operational Lead Time Delay"
                        elif any(k in met.lower() for k in ("attrition", "turnover", "churn")):
                            title = "Turnover Rate Escalation"
                        elif any(k in met.lower() for k in ("refund", "return", "cancellation")):
                            title = "Cancellation / Refund Rate Spike"

                        risks.append(
                            RiskItemSchema(
                                risk_id=f"trend_escalation_{met}",
                                title=title,
                                category="Cost & Operational Risk",
                                label="Requires investigation" if severity in ("high", "medium") else "Potential anomaly",
                                description=(
                                    f"'{met}' surged by {pct_change:.1f}% from {prev_fmt} ({periods[-2]}) "
                                    f"to {curr_fmt} ({periods[-1]})."
                                ),
                                severity=severity,
                                severity_reason=(
                                    f"Classified as {severity.upper()} severity due to a {pct_change:.1f}% adverse increase in '{met}'."
                                ),
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
                                evidence=(
                                    f"Period comparison: Previous={prev_fmt}, Latest={curr_fmt}, "
                                    f"Delta={abs_fmt} ({pct_change:+.1f}%)."
                                ),
                                confidence=0.93,
                                qualification="Calculated from chronological period aggregation.",
                                recommended_action=(
                                    f"Audit cost allocation and workflow bottlenecks causing elevated '{met}' levels."
                                ),
                                risk_type="cost_escalation",
                                time_series_preview=preview_points,
                            )
                        )
                        seen_risk_keys.add(f"trend_escalation_{met}")

                    # 2c. Time-Series Volatility Risk
                    if n_periods >= 4:
                        mean_val = float(np.mean(vals))
                        std_val = float(np.std(vals))
                        if abs(mean_val) > 1e-6:
                            cv = std_val / abs(mean_val)
                            if cv >= 0.45:
                                severity = "high" if cv >= 0.80 else "medium"
                                risks.append(
                                    RiskItemSchema(
                                        risk_id=f"trend_volatility_{met}",
                                        title=f"High Volatility in '{met}'",
                                        category="Stability & Volatility",
                                        label="Unusual pattern detected",
                                        description=(
                                            f"'{met}' exhibits erratic swings over time with a coefficient of variation "
                                            f"of {cv * 100.0:.1f}% (standard deviation: {std_val:,.2f} vs mean: {mean_val:,.2f})."
                                        ),
                                        severity=severity,
                                        severity_reason=(
                                            f"Classified as {severity.upper()} severity due to a high dispersion ratio "
                                            f"(CV = {cv * 100.0:.1f}%), indicating low baseline predictability."
                                        ),
                                        affected_metric=met,
                                        affected_column=met,
                                        current_value=std_val,
                                        current_value_formatted=f"±{std_val:,.2f}",
                                        previous_value=mean_val,
                                        previous_value_formatted=f"Mean {mean_val:,.2f}",
                                        absolute_change=std_val,
                                        absolute_change_formatted=f"σ = {std_val:,.2f}",
                                        pct_change=round(cv * 100.0, 1),
                                        unit=unit_lbl or "units",
                                        time_period=f"{periods[0]} to {periods[-1]} ({len(periods)} periods)",
                                        evidence=(
                                            f"Mean={mean_val:,.2f}, StdDev={std_val:,.2f}, CV={cv * 100.0:.1f}% "
                                            f"across {len(periods)} observation periods."
                                        ),
                                        confidence=0.88,
                                        qualification="Derived from historical empirical coefficient of variation (CV = σ / μ).",
                                        recommended_action=f"Assess potential demand smoothing or operational buffers to mitigate volatility in '{met}'.",
                                        risk_type="volatility",
                                        time_series_preview=preview_points,
                                    )
                                )
                                seen_risk_keys.add(f"trend_volatility_{met}")
        except Exception:
            data_safety_notes.append("Time-series risk evaluation encountered unparseable date formats; defaulted to cross-sectional analysis.")

    # -------------------------------------------------------------------------
    # 3. CROSS-SECTIONAL & OPERATIONAL DOMAIN SIGNALS
    # -------------------------------------------------------------------------
    categorical_cols = [
        p.name for p in profiles
        if p.role in ("categorical", "identifier") and p.name in df.columns and p.distinct_count and 2 <= p.distinct_count <= 200
    ]
    numeric_cols_all = [
        p.name for p in profiles
        if p.role == "numeric" and p.name in df.columns
    ]

    # 3a. Concentration Risk (Single Entity Dominance)
    for dim_col in categorical_cols[:3]:
        for met_col in numeric_cols_all[:3]:
            key = f"conc_{dim_col}_{met_col}"
            if key in seen_risk_keys:
                continue
            try:
                clean = df[[dim_col, met_col]].dropna()
                if len(clean) >= 15:
                    grouped = clean.groupby(dim_col)[met_col].sum()
                    total_vol = float(grouped.sum())
                    if total_vol > 0:
                        top_val = float(grouped.max())
                        top_name = str(grouped.idxmax())
                        top_share = (top_val / total_vol) * 100.0

                        if top_share >= 50.0:
                            severity = "high" if top_share >= 70.0 else "medium"
                            top_val_fmt, unit_lbl = _format_val(top_val, met_col, domain.domain_id, dataset_currency)
                            tot_val_fmt, _ = _format_val(total_vol, met_col, domain.domain_id, dataset_currency)

                            risks.append(
                                RiskItemSchema(
                                    risk_id=key,
                                    title=f"Severe Concentration in '{dim_col}'",
                                    category="Concentration & Dependency",
                                    label="Unusual pattern detected",
                                    description=(
                                        f"Single entity '{top_name}' accounts for {top_share:.1f}% of total '{met_col}' "
                                        f"({top_val_fmt} out of {tot_val_fmt})."
                                    ),
                                    severity=severity,
                                    severity_reason=(
                                        f"Classified as {severity.upper()} severity because a single entity exceeds "
                                        f"{'70%' if severity == 'high' else '50%'} concentration, creating vulnerability."
                                    ),
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
                                    evidence=(
                                        f"Top entity '{top_name}' accounts for {top_val_fmt} of total {tot_val_fmt} "
                                        f"({top_share:.1f}% share among {len(grouped)} unique {dim_col} entities)."
                                    ),
                                    confidence=0.95,
                                    qualification="Evaluated directly from entity summation over available records.",
                                    recommended_action=(
                                        f"Develop diversification strategies to reduce operational dependency on top entity '{top_name}'."
                                    ),
                                    risk_type="concentration",
                                )
                            )
                            seen_risk_keys.add(key)
                            break
            except Exception:
                continue

    # 3b. Negative Profit / Operating Losses
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
                        severity = "high" if total_sum < 0 or neg_pct >= 35.0 else "medium"
                        tot_fmt, unit_lbl = _format_val(total_sum, prof.name, domain.domain_id, dataset_currency)
                        risks.append(
                            RiskItemSchema(
                                risk_id=f"financial_loss_{prof.name}",
                                title="Negative Profitability & Losses",
                                category="Financial Performance",
                                label="Requires investigation",
                                description=(
                                    f"Dataset contains {neg_count:,} unprofitable transactions ({neg_pct:.1f}% of total) "
                                    f"resulting in net aggregate '{prof.name}' of {tot_fmt}."
                                ),
                                severity=severity,
                                severity_reason=(
                                    f"Classified as {severity.upper()} severity because {'net total is negative' if total_sum < 0 else f'{neg_pct:.1f}% of transactions operate at a loss'}."
                                ),
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
                                evidence=f"{neg_count} negative records ({neg_pct:.1f}%), net sum is {tot_fmt}.",
                                confidence=0.96,
                                qualification="Calculated by identifying records where profit < 0.",
                                recommended_action="Audit negative-margin items, discounts, or cost structures generating losses.",
                                risk_type="financial_loss",
                            )
                        )
                        seen_risk_keys.add(f"financial_loss_{prof.name}")

    # 3c. Inventory Stockout / Low Stock Risk
    for prof in profiles:
        if prof.role == "numeric" and prof.name in df.columns:
            name_lower = prof.name.lower()
            if any(k in name_lower for k in ("stock", "inventory", "stock_level", "units_in_stock", "available_quantity")):
                s = pd.to_numeric(df[prof.name], errors="coerce").dropna()
                if len(s) >= 10:
                    zero_stock_count = int((s <= 0).sum())
                    zero_stock_pct = (zero_stock_count / len(s)) * 100.0
                    if zero_stock_count > 0 and zero_stock_pct >= 5.0:
                        severity = "high" if zero_stock_pct >= 20.0 else "medium"
                        risks.append(
                            RiskItemSchema(
                                risk_id=f"inventory_stockout_{prof.name}",
                                title="Inventory Stock-Out Risk",
                                category="Operations & Supply",
                                label="Requires investigation",
                                description=f"Detected {zero_stock_count:,} inventory items ({zero_stock_pct:.1f}%) with zero or depleted stock levels.",
                                severity=severity,
                                severity_reason=f"Classified as {severity.upper()} severity due to {zero_stock_pct:.1f}% stockout rate.",
                                affected_metric=prof.name,
                                affected_column=prof.name,
                                current_value=float(zero_stock_count),
                                current_value_formatted=f"{zero_stock_count:,} items",
                                previous_value=0.0,
                                previous_value_formatted="0 items",
                                absolute_change=float(zero_stock_count),
                                absolute_change_formatted=f"+{zero_stock_count:,} depleted",
                                pct_change=round(zero_stock_pct, 1),
                                unit="units",
                                time_period="Full Dataset",
                                evidence=f"{zero_stock_count} SKUs out of {len(s)} total items have stock <= 0 ({zero_stock_pct:.1f}%).",
                                confidence=0.95,
                                qualification="Evaluated from non-positive inventory records.",
                                recommended_action="Trigger replenishment protocols for depleted SKUs to avoid lost sales.",
                                risk_type="inventory_risk",
                            )
                        )
                        seen_risk_keys.add(f"inventory_stockout_{prof.name}")

    # 3d. Domain-Specific: HR Employee Attrition
    if domain.domain_id in ("people_hr", "hr"):
        for prof in profiles:
            name_lower = prof.name.lower()
            if any(k in name_lower for k in ("attrition", "left", "exit", "turnover", "status")):
                if prof.name in df.columns:
                    col_vals = df[prof.name].dropna().astype(str).str.lower()
                    exit_count = int(col_vals.isin(["yes", "true", "1", "left", "terminated", "resigned", "exit"]).sum())
                    if exit_count > 0 and len(col_vals) > 0:
                        attrition_rate = (exit_count / len(col_vals)) * 100.0
                        if attrition_rate >= 12.0:
                            severity = "high" if attrition_rate >= 25.0 else "medium"
                            risks.append(
                                RiskItemSchema(
                                    risk_id="hr_attrition_risk",
                                    title="Elevated Employee Attrition",
                                    category="Human Resources",
                                    label="Requires investigation",
                                    description=f"Observed employee attrition rate of {attrition_rate:.1f}% ({exit_count:,} exits out of {len(col_vals):,} total personnel).",
                                    severity=severity,
                                    severity_reason=f"Classified as {severity.upper()} severity because workforce turnover rate exceeds {'25%' if severity == 'high' else '12%'}.",
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
                                    evidence=f"{exit_count} exits out of {len(col_vals)} personnel records ({attrition_rate:.1f}%).",
                                    confidence=0.92,
                                    qualification="Calculated directly from employee status records.",
                                    recommended_action="Conduct departmental retention reviews and exit interviews to address turnover factors.",
                                    risk_type="workforce_attrition",
                                )
                            )
                            seen_risk_keys.add("hr_attrition_risk")

    # 3e. Domain-Specific: Sports Performance
    if domain.domain_id in ("sports", "sports_performance", "sports_cricket"):
        for prof in profiles:
            name_lower = prof.name.lower()
            if any(k in name_lower for k in ("win", "winner", "result", "outcome")) and prof.name in df.columns:
                try:
                    s = df[prof.name].dropna().astype(str)
                    if len(s) >= 10:
                        counts = s.value_counts()
                        if len(counts) >= 2:
                            lowest_rate = (counts.min() / len(s)) * 100.0
                            if lowest_rate < 25.0:
                                lowest_name = counts.idxmin()
                                risks.append(
                                    RiskItemSchema(
                                        risk_id="sports_win_rate_deficit",
                                        title=f"Performance Deficit for '{lowest_name}'",
                                        category="Sports Performance",
                                        label="Requires investigation",
                                        description=f"Entity '{lowest_name}' recorded a low success rate of {lowest_rate:.1f}% ({counts.min()} outcomes out of {len(s)} matches).",
                                        severity="medium",
                                        severity_reason="Classified as Medium severity due to significant outcome win-rate divergence.",
                                        affected_metric=prof.name,
                                        affected_column=prof.name,
                                        current_value=round(lowest_rate, 1),
                                        current_value_formatted=f"{lowest_rate:.1f}%",
                                        previous_value=50.0,
                                        previous_value_formatted="50.0% parity",
                                        absolute_change=round(lowest_rate - 50.0, 1),
                                        absolute_change_formatted=f"{round(lowest_rate - 50.0, 1):.1f}%",
                                        pct_change=round(lowest_rate, 1),
                                        unit="%",
                                        time_period="Full Match History",
                                        evidence=f"Win/outcome count is {counts.min()} out of {len(s)} entries ({lowest_rate:.1f}%).",
                                        confidence=0.90,
                                        qualification="Derived from historical match result outcomes.",
                                        recommended_action="Analyze tactical factors, opposition matchups, and venue conditions.",
                                        risk_type="sports_deficit",
                                    )
                                )
                                seen_risk_keys.add("sports_win_rate_deficit")
                except Exception:
                    pass

    # -------------------------------------------------------------------------
    # 4. OVERVIEW SYNTHESIS & PRIORITIZATION
    # -------------------------------------------------------------------------
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

    if high_count > 0:
        health_status = "Critical Risks Identified"
        summary_stmt = (
            f"Detected {total_risks} potential risk signals ({high_count} High, {medium_count} Medium, {low_count} Low). "
            f"Primary attention required for {risks[0].title}."
        )
    elif medium_count > 0:
        health_status = "Attention Required"
        summary_stmt = (
            f"Identified {total_risks} moderate risk signals ({medium_count} Medium, {low_count} Low). "
            "Data demonstrates reasonable stability with isolated variances."
        )
    elif low_count > 0:
        health_status = "Healthy"
        summary_stmt = (
            f"Identified {low_count} minor informational signals. No critical statistical anomalies detected."
        )
    else:
        health_status = "Healthy"
        summary_stmt = (
            "No significant statistical anomalies, severe concentrations, or critical performance drops "
            "were detected across the analyzed data distributions and time periods."
        )

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

