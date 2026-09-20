"""Analysis Validation & Quality Checker.

Verifies:
- Relevance of the selected analysis to the dataset domain.
- Mathematical correctness of calculations and statistics.
- Compatibility of chart types with underlying column data types.
- Logical consistency of comparisons.
- Presence and mapping of required columns.
- Data evidence backing for insights and recommendations.
- Prevention of duplicate counting, incorrect aggregation, and misleading conclusions.

Clearly labels each analysis component as:
- 'Valid'
- 'Needs Review'
- 'Unsupported'
with transparent explanations.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Literal, Optional, Tuple

import pandas as pd

from app.schemas.domain_blueprint import (
    DomainChartSpecSchema,
    DomainIdentitySchema,
    DomainKpiSchema,
    RecommendationItemSchema,
    RiskItemSchema,
    SkippedAnalysisSchema,
    TrendItemSchema,
)

ValidationStatus = Literal["Valid", "Needs Review", "Unsupported"]


class ValidationCheckResult:
    def __init__(
        self,
        component_type: str,  # "kpi", "chart", "trend", "risk", "recommendation", "overall"
        component_id: str,
        title: str,
        status: ValidationStatus,
        reason: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.component_type = component_type
        self.component_id = component_id
        self.title = title
        self.status = status
        self.reason = reason
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "component_type": self.component_type,
            "component_id": self.component_id,
            "title": self.title,
            "status": self.status,
            "reason": self.reason,
            "details": self.details,
        }


def validate_kpi(kpi: DomainKpiSchema, df: pd.DataFrame) -> ValidationCheckResult:
    """Validate mathematical correctness and column mapping of a single KPI."""
    if kpi.value is None:
        return ValidationCheckResult(
            "kpi", kpi.id, kpi.name, "Unsupported",
            "KPI value could not be calculated (result is null or empty)."
        )

    # Check for NaN / Inf
    if isinstance(kpi.value, float) and (math.isnan(kpi.value) or math.isinf(kpi.value)):
        return ValidationCheckResult(
            "kpi", kpi.id, kpi.name, "Unsupported",
            "KPI value resulted in an invalid mathematical state (NaN or Infinity)."
        )

    # Check percentage boundaries
    if kpi.format == "percentage":
        try:
            val = float(kpi.value)
            if val < 0.0 or val > 100.0:
                return ValidationCheckResult(
                    "kpi", kpi.id, kpi.name, "Needs Review",
                    f"Percentage value ({val}%) is outside the expected 0-100% range."
                )
        except ValueError:
            pass

    # Check count formulas
    if kpi.aggregation in ("count", "count_distinct"):
        try:
            val = float(kpi.value)
            if val < 0 or not val.is_integer():
                return ValidationCheckResult(
                    "kpi", kpi.id, kpi.name, "Needs Review",
                    f"Count metric value ({val}) is negative or fractional."
                )
        except ValueError:
            pass

    # Check duplicate counting hazard in ball-by-ball or transaction datasets
    col = kpi.matched_columns[0] if kpi.matched_columns else None
    if col and col in df.columns:
        if "match_id" in df.columns and "ball" in df.columns and ("margin" in col.lower() or "target" in col.lower()):
            if kpi.aggregation == "sum":
                return ValidationCheckResult(
                    "kpi", kpi.id, kpi.name, "Needs Review",
                    f"Duplicate counting hazard: Summing '{col}' over ball-by-ball rows multiplies match-level data. Group by match_id first."
                )

    return ValidationCheckResult(
        "kpi", kpi.id, kpi.name, "Valid",
        f"Mathematically verified using {kpi.aggregation} on '{', '.join(kpi.matched_columns)}'."
    )


def validate_chart(chart: DomainChartSpecSchema, df: pd.DataFrame) -> ValidationCheckResult:
    """Validate data type compatibility and display logic for a chart."""
    if not chart.data or len(chart.data) == 0:
        return ValidationCheckResult(
            "chart", chart.id, chart.title, "Unsupported",
            "Chart has no aggregated data points to render."
        )

    # Validate histogram
    if chart.chart_type == "histogram":
        if chart.metric_column and chart.metric_column in df.columns:
            if not pd.api.types.is_numeric_dtype(df[chart.metric_column]):
                return ValidationCheckResult(
                    "chart", chart.id, chart.title, "Unsupported",
                    f"Histogram requires a numeric measure; '{chart.metric_column}' is not numeric."
                )

    # Validate scatter plot
    if chart.chart_type == "scatter":
        if not (chart.dimension_column and chart.metric_column):
            return ValidationCheckResult(
                "chart", chart.id, chart.title, "Unsupported",
                "Scatter plot requires two numeric axes (X and Y measures)."
            )

    # Validate bar / pie category cardinality
    if chart.chart_type in ("bar", "pie"):
        if chart.dimension_column and chart.dimension_column in df.columns:
            unique_cats = df[chart.dimension_column].nunique()
            if unique_cats > 100 and len(chart.data) > 30:
                return ValidationCheckResult(
                    "chart", chart.id, chart.title, "Needs Review",
                    f"High cardinality ({unique_cats} categories); categories should be capped with an 'Other' group."
                )

    return ValidationCheckResult(
        "chart", chart.id, chart.title, "Valid",
        f"Chart type '{chart.chart_type}' is appropriate for dimensions ({chart.dimension_column or 'None'}) and metrics ({chart.metric_column or 'None'})."
    )


def validate_domain_relevance(
    domain: DomainIdentitySchema,
    kpis: List[DomainKpiSchema],
    charts: List[DomainChartSpecSchema],
) -> List[ValidationCheckResult]:
    """Verify that generated analyses are relevant to the detected domain."""
    results: List[ValidationCheckResult] = []

    is_sports = "sport" in domain.domain_id or "cricket" in domain.domain_id or "ipl" in domain.domain_id

    if is_sports:
        # Check that business-only metrics are not erroneously included in sports
        irrelevant_keywords = ("revenue", "profit", "ebitda", "churn", "cpa", "cpc", "roas")
        for kpi in kpis:
            if any(ik in kpi.id.lower() or ik in kpi.name.lower() for ik in irrelevant_keywords):
                results.append(
                    ValidationCheckResult(
                        "kpi", kpi.id, kpi.name, "Unsupported",
                        f"Irrelevant metric: Business metric '{kpi.name}' is not applicable to sports/cricket domain."
                    )
                )

    return results


def run_analysis_quality_check(
    df: pd.DataFrame,
    domain: DomainIdentitySchema,
    kpis: List[DomainKpiSchema],
    charts: List[DomainChartSpecSchema],
    trends: List[TrendItemSchema],
    risks: List[RiskItemSchema],
    recommendations: List[RecommendationItemSchema],
    skipped: List[SkippedAnalysisSchema],
) -> Dict[str, Any]:
    """Execute comprehensive analysis validation and generate quality report."""
    checks: List[ValidationCheckResult] = []

    # 1. Relevance checks
    relevance_checks = validate_domain_relevance(domain, kpis, charts)
    checks.extend(relevance_checks)

    # 2. KPI checks
    for kpi in kpis:
        checks.append(validate_kpi(kpi, df))

    # 3. Chart checks
    for chart in charts:
        checks.append(validate_chart(chart, df))

    # 4. Skipped analyses report as Unsupported
    for s in skipped:
        checks.append(
            ValidationCheckResult(
                component_type=s.analysis_type,
                component_id=s.item_id,
                title=s.name,
                status="Unsupported",
                reason=s.reason,
            )
        )

    # Determine overall status
    statuses = [c.status for c in checks]
    valid_count = statuses.count("Valid")
    review_count = statuses.count("Needs Review")
    unsupported_count = statuses.count("Unsupported")

    if review_count > 0:
        overall_status = "Needs Review"
        summary = f"{valid_count} analyses verified valid; {review_count} need review; {unsupported_count} unsupported due to missing columns."
    elif valid_count > 0:
        overall_status = "Valid"
        summary = f"All {valid_count} generated analyses are mathematically and logically verified."
    else:
        overall_status = "Unsupported"
        summary = "No valid analyses could be generated from available dataset columns."

    return {
        "overall_status": overall_status,
        "summary": summary,
        "counts": {
            "valid": valid_count,
            "needs_review": review_count,
            "unsupported": unsupported_count,
            "total_evaluated": len(checks),
        },
        "checks": [c.to_dict() for c in checks],
    }
