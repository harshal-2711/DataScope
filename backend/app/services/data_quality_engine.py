"""Comprehensive Data Quality & Hygiene Validation Engine.

Performs robust verification of:
- Missing values and completeness percentages (isolated from empty columns)
- Duplicate rows and candidate primary ID / entity identifier evaluation
- Semantic date formats vs fiscal year/period preservation
- Suspicious negative values in non-negative domains
- Zero denominators / division-by-zero hazards
- Extreme statistical outliers (3x IQR and Z > 3)
- Inconsistent categories (casing differences, trailing whitespace)
- Empty columns vs constant metadata columns
- Sample size adequacy
- Overall Data Quality Score (0-100) and actionable recommendations
"""
from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Literal, Optional, Tuple

import numpy as np
import pandas as pd

from app.domains.base import DomainBlueprint
from app.domains.registry import get_blueprint_by_id
from app.schemas.domain_blueprint import (
    ColumnQualityDiagnosticSchema,
    DataQualityCheckSchema,
    DataQualityReportResponse,
    DomainIdentitySchema,
)

_FISCAL_YEAR_PATTERNS = re.compile(
    r"^\s*(FY\s*\d{2,4}([-/]\d{2,4})?|\d{4}[-/]\d{2,4}|Q[1-4][-_/\s]\d{2,4}|\d{4}\s*[-/]\s*Q[1-4]|FY\d{2,4}|[12]\d{3}\s*-\s*[12]\d{3})\s*$",
    re.IGNORECASE,
)

_FISCAL_NAME_PATTERNS = re.compile(
    r"(^|[_.\-\s/])(fiscal|fiscal_year|financial_year|fy|academic_year|tax_year|fiscal_period|season|period)($|[_.\-\s/])",
    re.IGNORECASE,
)

_METADATA_CONST_HINTS = (
    "fiscal", "year", "currency", "country", "state", "tag", "type", "initiation",
    "season", "version", "source", "unit", "format", "mode", "allow", "flag",
)


def compute_data_quality_report(
    df: pd.DataFrame,
    dataset_id: str,
    domain: Optional[DomainIdentitySchema] = None,
) -> DataQualityReportResponse:
    """Run full data quality and hygiene inspection on a DataFrame."""
    checks: List[DataQualityCheckSchema] = []
    column_diagnostics: Dict[str, ColumnQualityDiagnosticSchema] = {}
    recommendations: List[str] = []

    total_rows = len(df)
    total_cols = len(df.columns)
    score = 100

    # 1. Sample Size Check
    if total_rows < 5:
        checks.append(
            DataQualityCheckSchema(
                id="sample_size_critical",
                name="Insufficient Records",
                category="sample_size",
                status="Critical",
                severity="critical",
                affected_columns=[],
                message=f"Dataset contains only {total_rows} rows. Statistical aggregations require at least 5-10 rows.",
                recommendation="Upload a dataset with at least 10-20 records for statistically meaningful analysis.",
            )
        )
        score -= 35
    elif total_rows < 20:
        checks.append(
            DataQualityCheckSchema(
                id="sample_size_small",
                name="Small Sample Size",
                category="sample_size",
                status="Warning",
                severity="warning",
                affected_columns=[],
                message=f"Dataset contains {total_rows} rows. Statistical confidence intervals may be wide.",
                recommendation="Interpret percentages and averages with caution due to limited sample size.",
            )
        )
        score -= 10
    else:
        checks.append(
            DataQualityCheckSchema(
                id="sample_size_pass",
                name="Sufficient Records",
                category="sample_size",
                status="Pass",
                severity="info",
                affected_columns=[],
                message=f"Dataset contains {total_rows:,} rows, sufficient for robust exploratory analytics.",
                recommendation="Sample size is adequate for standard descriptive and trend analysis.",
            )
        )

    # 2. Duplicate Rows Check
    dup_rows = int(df.duplicated().sum())
    dup_pct = round((dup_rows / total_rows) * 100.0, 2) if total_rows > 0 else 0.0
    if dup_rows > 0:
        sev: Literal["warning", "critical"] = "critical" if dup_pct > 10.0 else "warning"
        checks.append(
            DataQualityCheckSchema(
                id="duplicate_rows",
                name="Duplicate Rows Detected",
                category="duplicates",
                status="Critical" if sev == "critical" else "Warning",
                severity=sev,
                affected_columns=[],
                message=f"Found {dup_rows:,} duplicate rows ({dup_pct}% of total records).",
                recommendation="Deduplicate records prior to performing sum or count aggregations to avoid double-counting.",
            )
        )
        score -= 20 if sev == "critical" else 10
        recommendations.append("Apply row deduplication to ensure metrics are not artificially inflated.")
    else:
        checks.append(
            DataQualityCheckSchema(
                id="duplicate_rows_pass",
                name="No Duplicate Rows",
                category="duplicates",
                status="Pass",
                severity="info",
                affected_columns=[],
                message="All dataset rows are unique.",
                recommendation="No action needed.",
            )
        )

    # 3. Candidate Identifier Duplicates
    id_terms = ("order_id", "transaction_id", "invoice_id", "customer_id", "patient_id", "student_id", "employee_id", "id", "pk", "uuid")
    for col in df.columns:
        col_str = str(col)
        col_lower = col_str.lower().strip()
        is_id_name = any(col_lower == term or col_lower.endswith(f"_{term}") or col_lower.endswith(f"/{term}") for term in id_terms)
        
        if is_id_name:
            s = df[col].dropna()
            if not s.empty:
                unique_c = int(s.nunique())
                total_c = len(s)
                uniqueness_ratio = unique_c / total_c if total_c > 0 else 0.0

                # Distinguish constant or low-cardinality package indices from true entity identifiers
                if unique_c <= 1 or (unique_c <= 5 and total_c > 20 and uniqueness_ratio < 0.05):
                    # Constant attribute / version flag (e.g. id=1 repeated for all rows in OCDS release package)
                    # NOT a primary key; do not penalize or falsely flag as duplicate primary ID.
                    continue

                col_dups = int(s.duplicated().sum())
                dup_rate = round((col_dups / total_c) * 100.0, 1)

                if col_dups > 0:
                    if uniqueness_ratio >= 0.90:
                        # Near-unique column -> true Candidate Primary Key duplicate risk
                        checks.append(
                            DataQualityCheckSchema(
                                id=f"dup_id_{col_str}",
                                name=f"Duplicate Primary IDs in '{col_str}'",
                                category="duplicates",
                                status="Warning",
                                severity="warning",
                                affected_columns=[col_str],
                                message=f"Column '{col_str}' has {col_dups:,} duplicate values ({dup_rate}% duplicate rate). Risk of accidental duplicate records.",
                                recommendation="Verify whether duplicate IDs represent accidental duplicate submissions.",
                            )
                        )
                        score -= 5
                        recommendations.append(f"Inspect '{col_str}' to confirm whether duplicate IDs are accidental re-submissions.")
                    elif uniqueness_ratio >= 0.30:
                        # Repeated entity observation (e.g. order_id in line-item dataset, match_id in ball-by-ball)
                        checks.append(
                            DataQualityCheckSchema(
                                id=f"repeated_id_{col_str}",
                                name=f"Repeated Entity Observations in '{col_str}'",
                                category="duplicates",
                                status="Pass",
                                severity="info",
                                affected_columns=[col_str],
                                message=f"Column '{col_str}' contains {unique_c:,} distinct entities across {total_c:,} records ({dup_rate}% repeated rows), indicating multi-line grain.",
                                recommendation="Grain represents multi-line entity observations; aggregate by entity before calculating entity counts.",
                            )
                        )

    # 4. Column-by-column diagnostic analysis
    non_negative_keywords = (
        "price", "sales", "revenue", "cost", "amount", "quantity", "units",
        "age", "duration", "attendance", "score", "runs", "wickets", "views", "clicks", "spend"
    )
    denominator_keywords = ("impressions", "clicks", "balls_faced", "overs", "population", "total", "budget")

    for col in df.columns:
        col_str = str(col)
        col_lower = col_str.lower().strip()
        series = df[col]
        total_c = len(series)
        missing_c = int(series.isna().sum())
        missing_p = round((missing_c / total_c) * 100.0, 2) if total_c > 0 else 0.0
        unique_c = int(series.nunique())
        col_issues: List[str] = []

        is_numeric = pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series)
        is_string = series.dtype == "object" or pd.api.types.is_string_dtype(series)

        neg_count = 0
        zero_count = 0
        outlier_count = 0
        dup_count = int(series.dropna().duplicated().sum())

        if unique_c == 0:
            col_issues.append("Completely empty column (100% missing)")
        elif missing_p > 40.0:
            col_issues.append(f"High missing rate ({missing_p}% nulls)")
        elif missing_p > 0.0:
            col_issues.append(f"{missing_c} missing values ({missing_p}%)")

        if unique_c == 1 and total_c > 1:
            col_issues.append("Constant value column (zero variance)")

        if is_numeric:
            num_s = pd.to_numeric(series, errors="coerce").dropna()
            if not num_s.empty:
                neg_count = int((num_s < 0).sum())
                zero_count = int((num_s == 0).sum())

                # Check suspicious negatives
                if neg_count > 0 and any(kw in col_lower for kw in non_negative_keywords):
                    col_issues.append(f"Contains {neg_count} suspicious negative values")

                # Check zero denominators
                if zero_count > 0 and any(kw in col_lower for kw in denominator_keywords):
                    col_issues.append(f"Contains {zero_count} zeros (potential division-by-zero in ratios)")

                # Outlier check (3x IQR)
                p25 = float(num_s.quantile(0.25))
                p75 = float(num_s.quantile(0.75))
                iqr = p75 - p25
                if iqr > 0:
                    lb = p25 - (3.0 * iqr)
                    ub = p75 + (3.0 * iqr)
                    outlier_count = int(((num_s < lb) | (num_s > ub)).sum())
                    if outlier_count > 0:
                        col_issues.append(f"{outlier_count} extreme statistical outliers (> 3x IQR)")

        if is_string:
            str_s = series.dropna().astype(str)
            if not str_s.empty:
                # Check for inconsistent casing or trailing whitespace
                stripped = str_s.str.strip()
                has_whitespace = (str_s != stripped).any()
                if has_whitespace:
                    col_issues.append("Contains values with leading/trailing whitespace")

                lower_s = stripped.str.lower()
                if lower_s.nunique() < stripped.nunique():
                    col_issues.append("Inconsistent casing across identical category names")

        column_diagnostics[col_str] = ColumnQualityDiagnosticSchema(
            column_name=col_str,
            dtype=str(series.dtype),
            total_count=total_c,
            missing_count=missing_c,
            missing_pct=missing_p,
            unique_count=unique_c,
            duplicate_count=dup_count,
            negative_count=neg_count,
            zero_count=zero_count,
            outlier_count=outlier_count,
            issues=col_issues,
        )

    # 5. Aggregate missing values across entire dataset (separated from completely empty columns)
    empty_cols = [c for c, d in column_diagnostics.items() if d.unique_count == 0]
    populated_cols = [c for c, d in column_diagnostics.items() if d.unique_count > 0]
    
    total_cells = total_rows * total_cols
    total_nulls = int(df.isna().sum().sum())
    overall_null_pct_with_empty = round((total_nulls / total_cells) * 100.0, 2) if total_cells > 0 else 0.0

    populated_cells = total_rows * len(populated_cols)
    populated_nulls = sum(column_diagnostics[c].missing_count for c in populated_cols)
    populated_null_pct = round((populated_nulls / populated_cells) * 100.0, 2) if populated_cells > 0 else 0.0

    if populated_null_pct > 20.0:
        checks.append(
            DataQualityCheckSchema(
                id="high_missing_cells",
                name="Substantial Missing Data in Populated Fields",
                category="missing_data",
                status="Critical",
                severity="critical",
                affected_columns=[c for c in populated_cols if column_diagnostics[c].missing_pct > 20.0],
                message=(
                    f"Populated columns have {populated_null_pct}% missing values "
                    f"({overall_null_pct_with_empty}% across all columns including {len(empty_cols)} empty columns)."
                ),
                recommendation="Impute missing values or filter out sparse records before building statistical models.",
            )
        )
        score -= 20
        recommendations.append("Address high missingness in affected populated columns using domain-appropriate imputation or row filtering.")
    elif populated_null_pct > 5.0:
        checks.append(
            DataQualityCheckSchema(
                id="moderate_missing_cells",
                name="Moderate Missing Values in Populated Fields",
                category="missing_data",
                status="Warning",
                severity="warning",
                affected_columns=[c for c in populated_cols if column_diagnostics[c].missing_pct > 5.0],
                message=(
                    f"Populated columns have {populated_null_pct}% missing values "
                    f"({overall_null_pct_with_empty}% across all columns including {len(empty_cols)} empty columns)."
                ),
                recommendation="Verify whether missing values reflect optional business fields or data extraction gaps.",
            )
        )
        score -= 8
    else:
        checks.append(
            DataQualityCheckSchema(
                id="low_missing_cells_pass",
                name="High Populated Data Completeness",
                category="missing_data",
                status="Pass",
                severity="info",
                affected_columns=[],
                message=(
                    f"Populated columns are {100.0 - populated_null_pct:.1f}% complete "
                    f"({100.0 - overall_null_pct_with_empty:.1f}% total completeness across all {total_cols} columns)."
                ),
                recommendation="Data completeness across populated features is strong.",
            )
        )

    # 6. Check for completely empty columns (isolated check)
    if empty_cols:
        empty_pct = round((len(empty_cols) / total_cols) * 100.0, 1)
        sev_empty: Literal["warning", "critical"] = "critical" if empty_pct > 30.0 else "warning"
        checks.append(
            DataQualityCheckSchema(
                id="empty_columns",
                name="Completely Empty Columns",
                category="columns",
                status="Critical" if sev_empty == "critical" else "Warning",
                severity=sev_empty,
                affected_columns=empty_cols,
                message=f"{len(empty_cols)} of {total_cols} columns ({empty_pct}%) contain 100% null values: {', '.join(empty_cols[:6])}{'...' if len(empty_cols) > 6 else ''}.",
                recommendation="Drop unused empty columns from dataset to reduce noise and optimize storage.",
            )
        )
        score -= 15 if sev_empty == "critical" else 10
        recommendations.append(f"Exclude {len(empty_cols)} completely empty columns from downstream analysis pipelines.")

    # 7. Check for constant-value columns (isolated from empty columns and separated into metadata vs variance)
    constant_cols = [c for c, d in column_diagnostics.items() if d.unique_count == 1 and total_rows > 1]
    if constant_cols:
        meta_constants = [c for c in constant_cols if any(k in c.lower() for k in _METADATA_CONST_HINTS)]
        non_meta_constants = [c for c in constant_cols if c not in meta_constants]

        if non_meta_constants:
            checks.append(
                DataQualityCheckSchema(
                    id="constant_columns_variance",
                    name="Zero-Variance Feature Columns",
                    category="columns",
                    status="Warning",
                    severity="warning",
                    affected_columns=non_meta_constants,
                    message=f"{len(non_meta_constants)} feature columns have single static values (zero variance): {', '.join(non_meta_constants[:5])}.",
                    recommendation="Constant columns provide no explanatory power for comparisons or predictive models.",
                )
            )
            score -= 5

        if meta_constants:
            checks.append(
                DataQualityCheckSchema(
                    id="constant_columns_metadata",
                    name="Constant Scope & Metadata Attributes",
                    category="columns",
                    status="Pass",
                    severity="info",
                    affected_columns=meta_constants,
                    message=f"{len(meta_constants)} columns represent uniform dataset scope or context metadata (e.g. {', '.join(meta_constants[:4])}).",
                    recommendation="Valid metadata establishing the dataset scope and reporting parameters.",
                )
            )

    # 8. Check for suspicious negative values
    suspicious_neg_cols = [
        c for c, d in column_diagnostics.items()
        if d.negative_count > 0 and any(kw in c.lower() for kw in non_negative_keywords)
    ]
    if suspicious_neg_cols:
        checks.append(
            DataQualityCheckSchema(
                id="suspicious_negatives",
                name="Suspicious Negative Values",
                category="business_logic",
                status="Warning",
                severity="warning",
                affected_columns=suspicious_neg_cols,
                message=f"Negative values detected in naturally non-negative columns: {', '.join(suspicious_neg_cols)}.",
                recommendation="Audit negative values to ensure they reflect valid adjustments (e.g. refunds) rather than data entry errors.",
            )
        )
        score -= 10
        recommendations.append("Review negative values in financial or count measures to confirm they represent valid business transactions.")

    # 9. Date Parsing & Interval Checks (Guards against Fiscal Years / Periods / Season Numbers)
    date_cols = [
        c for c in df.columns
        if any(kw in str(c).lower() for kw in ("date", "time", "published", "deadline", "dob", "created_at", "timestamp", "due_date"))
        and not _FISCAL_NAME_PATTERNS.search(str(c))
    ]
    for dc in date_cols:
        raw_s = df[dc].dropna()
        if not raw_s.empty:
            # Check if values are fiscal year strings or plain integers
            sample_str = raw_s.head(20).astype(str).str.strip()
            if sample_str.str.match(_FISCAL_YEAR_PATTERNS).mean() >= 0.7:
                # Valid fiscal year string, skip calendar date coercion
                continue

            parsed = pd.to_datetime(raw_s, errors="coerce", format="mixed")
            inv_count = int(parsed.isna().sum())
            if inv_count > 0:
                checks.append(
                    DataQualityCheckSchema(
                        id=f"invalid_dates_{dc}",
                        name=f"Invalid Date Formats in '{dc}'",
                        category="dates",
                        status="Warning",
                        severity="warning",
                        affected_columns=[str(dc)],
                        message=f"{inv_count} values in date column '{dc}' could not be parsed.",
                        recommendation="Standardize date strings into ISO 8601 (YYYY-MM-DD) format.",
                    )
                )
                score -= 8

    # Ensure score stays in 0-100 range
    final_score = max(0, min(100, score))

    crit_count = sum(1 for c in checks if c.severity == "critical")
    warn_count = sum(1 for c in checks if c.severity == "warning")
    info_count = sum(1 for c in checks if c.severity == "info")

    if final_score >= 80 and crit_count == 0:
        overall_status = "Healthy"
        summary = f"Dataset is in healthy condition (Score: {final_score}/100) with {info_count} passed checks and {warn_count} minor warnings."
    elif final_score >= 50:
        overall_status = "Warning"
        summary = f"Dataset has quality warnings (Score: {final_score}/100). {warn_count} warnings and {crit_count} critical issues require attention."
    else:
        overall_status = "Critical"
        summary = f"Significant data quality concerns identified (Score: {final_score}/100). {crit_count} critical issues should be addressed before decision-making."

    if not recommendations:
        recommendations.append("Dataset passed core hygiene validation checks; proceed with domain exploration and trend intelligence.")

    return DataQualityReportResponse(
        dataset_id=dataset_id,
        overall_score=final_score,
        status=overall_status,
        summary=summary,
        issue_counts={
            "critical": crit_count,
            "warning": warn_count,
            "info": info_count,
        },
        checks=checks,
        column_diagnostics=column_diagnostics,
        recommendations=recommendations,
    )
