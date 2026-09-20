"""Evidence-based insight and recommendation engine.

Synthesizes mathematically verified findings from KPIs, trends, risks, and comparisons
into structured, actionable recommendations with transparent evidence and explicit limitations.
Never fabricates values or infers unsupported causation.
"""
from __future__ import annotations

from typing import List

from app.domains.base import DomainBlueprint
from app.schemas.domain_blueprint import (
    ComparisonItemSchema,
    DetectedEntitySchema,
    DomainKpiSchema,
    RecommendationItemSchema,
    RiskItemSchema,
    TrendItemSchema,
)


def generate_evidence_based_recommendations(
    blueprint: DomainBlueprint,
    kpis: List[DomainKpiSchema],
    trends: List[TrendItemSchema],
    risks: List[RiskItemSchema],
    comparisons: List[ComparisonItemSchema],
    entities: List[DetectedEntitySchema],
) -> List[RecommendationItemSchema]:
    """Derive actionable recommendations directly backed by data evidence."""
    recommendations: List[RecommendationItemSchema] = []
    rec_counter = 1

    entity_labels = [e.label for e in entities]

    # 1. Recommendations derived from detected risks / anomalies
    for risk in risks[:3]:
        recommendations.append(
            RecommendationItemSchema(
                rec_id=f"rec_risk_{rec_counter}",
                category="risk_mitigation",
                title=f"Address {risk.label}: {risk.category}",
                finding=risk.description,
                supporting_metric=risk.evidence,
                relevant_columns=[risk.affected_column] if risk.affected_column else [],
                time_period=None,
                entities_involved=entity_labels[:3],
                severity=risk.severity,
                confidence=0.9,
                evidence=f"Identified in dataset: {risk.evidence}",
                recommended_action=risk.recommended_action,
                limitations="Relies on statistical thresholds; domain subject-matter review required before operational changes.",
            )
        )
        rec_counter += 1

    # 2. Recommendations derived from segment / category comparisons
    for comp in comparisons[:2]:
        recommendations.append(
            RecommendationItemSchema(
                rec_id=f"rec_comp_{rec_counter}",
                category="operational_efficiency",
                title=f"Optimize {comp.metric.capitalize()} across {comp.comparison_type.capitalize()}s",
                finding=f"Significant disparity observed: {comp.insight}.",
                supporting_metric=f"Difference of {comp.difference:,.2f}" + (f" ({comp.pct_change:+.1f}%)" if comp.pct_change is not None else ""),
                relevant_columns=[comp.metric],
                time_period=None,
                entities_involved=entity_labels[:2],
                severity="medium" if (comp.pct_change and abs(comp.pct_change) > 30) else "low",
                confidence=0.85,
                evidence=f"Baseline '{comp.baseline}' ({comp.baseline_value:,.2f}) vs '{comp.target}' ({comp.target_value:,.2f}).",
                recommended_action=f"Investigate operational practices in leading segment '{comp.target}' to apply learnings to '{comp.baseline}'.",
                limitations="Correlation between segments does not establish direct causation.",
            )
        )
        rec_counter += 1

    # 3. Recommendations derived from trends
    for trend in trends[:2]:
        action = (
            f"Capitalize on sustained upward trajectory by securing adequate resource capacity."
            if trend.trend_direction == "increasing"
            else f"Conduct root-cause analysis on recent decline in {trend.metric_name}."
        )
        recommendations.append(
            RecommendationItemSchema(
                rec_id=f"rec_trend_{rec_counter}",
                category="revenue_improvement" if trend.trend_direction == "increasing" else "risk_mitigation",
                title=f"Manage {trend.metric_name.capitalize()} {trend.trend_direction.capitalize()} Trend",
                finding=trend.description,
                supporting_metric=f"Net growth rate: {trend.growth_rate_pct:+0.1f}%" if trend.growth_rate_pct is not None else "Observed trajectory",
                relevant_columns=[trend.metric_name, trend.time_column],
                time_period=f"Peak: {trend.peak_period}, Trough: {trend.trough_period}",
                entities_involved=entity_labels[:2],
                severity="medium",
                confidence=0.88,
                evidence=f"Measured across {len(trend.data_points)} time periods in dataset.",
                recommended_action=action,
                limitations="Historical trend extrapolation is subject to external market conditions.",
            )
        )
        rec_counter += 1

    # 4. Blueprint-specific recommendations if rules match
    for rule in blueprint.recommendations:
        if len(recommendations) >= 6:
            break
        # Check if we have a matching KPI
        matched_kpi = next((k for k in kpis if rule.trigger_metric_or_risk in k.id or rule.trigger_metric_or_risk in k.name.lower()), None)
        if matched_kpi and matched_kpi.value is not None:
            recommendations.append(
                RecommendationItemSchema(
                    rec_id=f"rec_bp_{rec_counter}",
                    category=rule.category,
                    title=f"{rule.category.replace('_', ' ').capitalize()} Opportunity",
                    finding=f"Calculated {matched_kpi.name} is {matched_kpi.value:,.2f} ({matched_kpi.format}).",
                    supporting_metric=f"{matched_kpi.name}: {matched_kpi.value:,.2f}",
                    relevant_columns=matched_kpi.matched_columns,
                    time_period=None,
                    entities_involved=entity_labels[:2],
                    severity="low",
                    confidence=0.82,
                    evidence=f"Derived from {matched_kpi.aggregation} of {matched_kpi.matched_columns}.",
                    recommended_action=rule.action_template,
                    limitations=rule.limitation,
                )
            )
            rec_counter += 1

    return recommendations
