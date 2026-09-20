"""Field validation engine for domain blueprints.

Matches dataset columns to blueprint analytical requirements using semantic matching,
aliases, role checking, and data profiling. If required columns are missing, skips
the analysis and provides a clear, traceable explanation.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Set, Tuple

import pandas as pd

from app.domains.base import (
    ChartRule,
    ComparisonRule,
    DomainBlueprint,
    KpiRule,
    RiskRule,
    TrendRule,
)
from app.schemas.domain_blueprint import DetectedEntitySchema, SkippedAnalysisSchema
from app.services.column_profiler import ColumnProfile

_WORD_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> Set[str]:
    spaced = re.sub(r"(?<!^)(?=[A-Z])", " ", str(text))
    spaced = spaced.replace("_", " ").replace("-", " ")
    return set(_WORD_RE.findall(spaced.lower()))


def find_matching_column(
    profiles: List[ColumnProfile],
    allowed_roles: Tuple[str, ...],
    patterns: Tuple[str, ...],
    fallback_to_any_role_match: bool = True,
    excluded_columns: Optional[Set[str]] = None,
) -> Optional[str]:
    """Find the best column matching specified roles and naming patterns."""
    if excluded_columns is None:
        excluded_columns = set()

    candidates: List[Tuple[float, str]] = []

    for prof in profiles:
        if prof.name in excluded_columns or prof.role == "ignore":
            continue

        if prof.role not in allowed_roles:
            continue

        col_tokens = _tokenize(prof.name)
        full_lower = prof.name.strip().lower()

        pattern_score = 0.0
        if patterns:
            for pat in patterns:
                pat_tokens = set(pat.split("_"))
                if pat_tokens <= col_tokens:
                    pattern_score += 3.0
                elif pat in full_lower or f"_{pat}" in full_lower or f"{pat}_" in full_lower:
                    pattern_score += 2.0
        elif fallback_to_any_role_match:
            # If no specific patterns required, any valid column of the role is a weak candidate
            pattern_score = 1.0

        if pattern_score > 0:
            candidates.append((pattern_score, prof.name))

    if not candidates:
        if fallback_to_any_role_match and not patterns:
            for prof in profiles:
                if prof.name not in excluded_columns and prof.role in allowed_roles:
                    return prof.name
        return None

    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


class ValidatedDomainCapabilities:
    def __init__(self) -> None:
        self.kpis: List[Tuple[KpiRule, List[str]]] = []
        self.charts: List[Tuple[ChartRule, Optional[str], Optional[str]]] = []
        self.comparisons: List[Tuple[ComparisonRule, str, str]] = []
        self.trends: List[Tuple[TrendRule, str, str]] = []
        self.risks: List[Tuple[RiskRule, Optional[str], Optional[str]]] = []
        self.skipped: List[SkippedAnalysisSchema] = []


def validate_blueprint_fields(
    df: pd.DataFrame,
    profiles: List[ColumnProfile],
    blueprint: DomainBlueprint,
    entities: List[DetectedEntitySchema],
) -> ValidatedDomainCapabilities:
    """Validate which blueprint rules can be computed from available dataset columns."""
    capabilities = ValidatedDomainCapabilities()

    # 1. Validate KPIs
    for kpi_rule in blueprint.kpis:
        matched_cols: List[str] = []
        is_valid = True

        if "numeric" in kpi_rule.required_roles:
            col = find_matching_column(
                profiles,
                allowed_roles=("numeric",),
                patterns=kpi_rule.metric_patterns,
                fallback_to_any_role_match=False,
            )
            if col:
                matched_cols.append(col)
            elif kpi_rule.formula in ("count", "count_distinct"):
                # Count formulas can fall back to categorical or identifier
                count_col = find_matching_column(
                    profiles,
                    allowed_roles=("identifier", "categorical", "numeric"),
                    patterns=kpi_rule.dimension_patterns or kpi_rule.metric_patterns,
                    fallback_to_any_role_match=True,
                )
                if count_col:
                    matched_cols.append(count_col)
                else:
                    is_valid = False
            else:
                is_valid = False
        else:
            # Handle categorical / identifier / count KPIs
            allowed = tuple(r for r in kpi_rule.required_roles if r in ("identifier", "categorical", "numeric", "text", "temporal"))
            if not allowed:
                allowed = ("identifier", "categorical", "numeric")
            col = find_matching_column(
                profiles,
                allowed_roles=allowed,
                patterns=kpi_rule.dimension_patterns or kpi_rule.metric_patterns,
                fallback_to_any_role_match=True,
            )
            if col:
                matched_cols.append(col)
            else:
                is_valid = False

        if is_valid and matched_cols:
            capabilities.kpis.append((kpi_rule, matched_cols))
        else:
            pat_str = ", ".join(kpi_rule.metric_patterns) or "numeric measure"
            capabilities.skipped.append(
                SkippedAnalysisSchema(
                    analysis_type="kpi",
                    item_id=kpi_rule.id,
                    name=kpi_rule.name,
                    reason=f"Required numeric metric matching '{pat_str}' was not found in dataset.",
                )
            )

    # 2. Validate Charts
    for chart_rule in blueprint.charts:
        dim_col: Optional[str] = None
        metric_col: Optional[str] = None

        if chart_rule.chart_type == "histogram":
            metric_col = find_matching_column(
                profiles,
                allowed_roles=("numeric",),
                patterns=chart_rule.metric_patterns,
                fallback_to_any_role_match=True,
            )
            if metric_col:
                capabilities.charts.append((chart_rule, None, metric_col))
            else:
                capabilities.skipped.append(
                    SkippedAnalysisSchema(
                        analysis_type="chart",
                        item_id=chart_rule.id,
                        name=chart_rule.title,
                        reason="Requires at least one numeric measure for histogram distribution.",
                    )
                )
        elif chart_rule.chart_type == "scatter":
            col1 = find_matching_column(
                profiles,
                allowed_roles=("numeric",),
                patterns=chart_rule.metric_patterns,
                fallback_to_any_role_match=True,
            )
            col2 = None
            if col1:
                col2 = find_matching_column(
                    profiles,
                    allowed_roles=("numeric",),
                    patterns=(),
                    fallback_to_any_role_match=True,
                    excluded_columns={col1},
                )
            if col1 and col2:
                capabilities.charts.append((chart_rule, col1, col2))
            else:
                capabilities.skipped.append(
                    SkippedAnalysisSchema(
                        analysis_type="chart",
                        item_id=chart_rule.id,
                        name=chart_rule.title,
                        reason="Requires at least two distinct numeric measures for scatter correlation.",
                    )
                )
        else:
            # bar, line, pie
            allowed_dim_roles = ("datetime", "categorical") if chart_rule.chart_type == "line" else ("categorical", "boolean")
            dim_col = find_matching_column(
                profiles,
                allowed_roles=allowed_dim_roles,
                patterns=chart_rule.dimension_patterns,
                fallback_to_any_role_match=True,
            )
            metric_col = find_matching_column(
                profiles,
                allowed_roles=("numeric",),
                patterns=chart_rule.metric_patterns,
                fallback_to_any_role_match=True,
            )

            if dim_col:
                capabilities.charts.append((chart_rule, dim_col, metric_col))
            else:
                pat_str = ", ".join(chart_rule.dimension_patterns) or "dimension column"
                capabilities.skipped.append(
                    SkippedAnalysisSchema(
                        analysis_type="chart",
                        item_id=chart_rule.id,
                        name=chart_rule.title,
                        reason=f"Missing suitable grouping dimension matching '{pat_str}'.",
                    )
                )

    # 3. Validate Comparisons
    for comp_rule in blueprint.comparisons:
        dim = find_matching_column(
            profiles,
            allowed_roles=("categorical", "datetime", "boolean"),
            patterns=comp_rule.dimension_patterns,
            fallback_to_any_role_match=True,
        )
        met = find_matching_column(
            profiles,
            allowed_roles=("numeric",),
            patterns=comp_rule.metric_patterns,
            fallback_to_any_role_match=True,
        )
        if dim and met:
            capabilities.comparisons.append((comp_rule, dim, met))
        else:
            capabilities.skipped.append(
                SkippedAnalysisSchema(
                    analysis_type="comparison",
                    item_id=comp_rule.title,
                    name=comp_rule.title,
                    reason="Required comparison dimension or metric was absent in dataset.",
                )
            )

    # 4. Validate Trends
    date_col = find_matching_column(
        profiles,
        allowed_roles=("datetime",),
        patterns=(),
        fallback_to_any_role_match=True,
    )
    for trend_rule in blueprint.trends:
        met = find_matching_column(
            profiles,
            allowed_roles=("numeric",),
            patterns=trend_rule.metric_patterns,
            fallback_to_any_role_match=True,
        )
        if date_col and met:
            capabilities.trends.append((trend_rule, met, date_col))
        else:
            capabilities.skipped.append(
                SkippedAnalysisSchema(
                    analysis_type="trend",
                    item_id="time_trend",
                    name="Time-Series Trend",
                    reason="Dataset does not contain both a parseable datetime column and a numeric measure.",
                )
            )

    # 5. Validate Risks
    for risk_rule in blueprint.risks:
        met = find_matching_column(
            profiles,
            allowed_roles=("numeric",),
            patterns=risk_rule.metric_patterns,
            fallback_to_any_role_match=False,
        )
        dim = find_matching_column(
            profiles,
            allowed_roles=("categorical", "identifier"),
            patterns=risk_rule.dimension_patterns,
            fallback_to_any_role_match=False,
        )
        if met or dim or risk_rule.risk_type in ("missing", "outlier"):
            capabilities.risks.append((risk_rule, met, dim))
        else:
            capabilities.skipped.append(
                SkippedAnalysisSchema(
                    analysis_type="risk",
                    item_id=risk_rule.risk_id,
                    name=risk_rule.category,
                    reason=f"Required metric or dimension for risk rule '{risk_rule.risk_id}' was absent.",
                )
            )

    return capabilities
