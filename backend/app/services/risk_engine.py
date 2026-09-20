"""Statistical risk and anomaly detection engine.

Surfaces factual data quality issues, statistical outliers, concentration imbalances,
and sudden spikes/drops using neutral, evidence-based labels:
- "Potential anomaly"
- "Requires investigation"
- "Unusual pattern detected"
"""
from __future__ import annotations

import math
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

from app.domains.base import RiskRule
from app.schemas.domain_blueprint import RiskItemSchema
from app.services.column_profiler import ColumnProfile


def detect_risks_and_anomalies(
    df: pd.DataFrame,
    profiles: List[ColumnProfile],
    validated_risks: List[Tuple[RiskRule, Optional[str], Optional[str]]],
) -> List[RiskItemSchema]:
    """Identify statistical anomalies, outliers, and data quality patterns."""
    results: List[RiskItemSchema] = []
    seen_risk_ids = set()

    # 1. Dataset-level Data Quality Checks
    row_count = len(df)
    if row_count > 0:
        # Check duplicate rows
        dup_count = int(df.duplicated().sum())
        if dup_count > 0 and (dup_count / row_count) >= 0.02:
            results.append(
                RiskItemSchema(
                    risk_id="duplicate_records",
                    category="Data Quality",
                    label="Potential anomaly",
                    description=f"Detected {dup_count:,} duplicate rows ({round((dup_count/row_count)*100, 1)}% of dataset).",
                    severity="medium",
                    affected_column=None,
                    evidence=f"{dup_count} identical row entries found across columns.",
                    recommended_action="Verify data ingestion deduplication pipeline.",
                )
            )
            seen_risk_ids.add("duplicate_records")

        # Check high missingness columns
        for prof in profiles:
            if prof.null_count > 0 and (prof.null_count / row_count) >= 0.20:
                results.append(
                    RiskItemSchema(
                        risk_id=f"missing_{prof.name}",
                        category="Data Quality",
                        label="Requires investigation",
                        description=f"Column '{prof.name}' has {round((prof.null_count/row_count)*100, 1)}% missing values ({prof.null_count:,} rows).",
                        severity="low" if (prof.null_count / row_count) < 0.4 else "medium",
                        affected_column=prof.name,
                        evidence=f"{prof.null_count} null entries out of {row_count} total records.",
                        recommended_action="Audit upstream data capture to prevent unrecorded entries.",
                    )
                )

    # 2. Domain-Specific Risk Rules
    for rule, met_col, dim_col in validated_risks:
        if rule.risk_id in seen_risk_ids:
            continue

        try:
            if rule.risk_type == "outlier" and met_col and met_col in df.columns:
                s = pd.to_numeric(df[met_col], errors="coerce").dropna()
                if len(s) >= 20:
                    q25 = s.quantile(0.25)
                    q75 = s.quantile(0.75)
                    iqr = q75 - q25
                    upper_bound = q75 + (3.0 * iqr)
                    outliers = s[s > upper_bound]

                    if len(outliers) > 0:
                        outlier_pct = round((len(outliers) / len(s)) * 100.0, 1)
                        results.append(
                            RiskItemSchema(
                                risk_id=rule.risk_id,
                                category=rule.category,
                                label=rule.label or "Potential anomaly",
                                description=f"Found {len(outliers)} high-magnitude outlier values in '{met_col}' exceeding 3x IQR ({upper_bound:,.2f}).",
                                severity="medium",
                                affected_column=met_col,
                                evidence=f"Max outlier value is {s.max():,.2f} vs upper IQR threshold {upper_bound:,.2f} ({outlier_pct}% of records).",
                                recommended_action=rule.recommended_action or "Audit outlier records for entry error or exceptional activity.",
                            )
                        )
                        seen_risk_ids.add(rule.risk_id)

            elif rule.risk_type == "concentration" and met_col and dim_col:
                if met_col in df.columns and dim_col in df.columns:
                    clean = df[[dim_col, met_col]].dropna()
                    if len(clean) >= 10:
                        grouped = clean.groupby(dim_col)[met_col].sum()
                        total_met = grouped.sum()
                        if total_met > 0:
                            top_share = float(grouped.max() / total_met)
                            top_name = str(grouped.idxmax())
                            if top_share >= 0.50:
                                results.append(
                                    RiskItemSchema(
                                        risk_id=rule.risk_id,
                                        category=rule.category,
                                        label="Unusual pattern detected",
                                        description=f"High concentration in '{dim_col}': '{top_name}' represents {round(top_share*100, 1)}% of total {met_col}.",
                                        severity="medium",
                                        affected_column=dim_col,
                                        evidence=f"Top contributor '{top_name}' volume is {grouped.max():,.2f} of {total_met:,.2f} total.",
                                        recommended_action=rule.recommended_action or "Assess operational dependency on top contributing entity.",
                                    )
                                )
                                seen_risk_ids.add(rule.risk_id)

        except Exception:
            continue

    return results
