"""Domain detection engine.

Analyzes dataset column names, data types, and sample values against the
75 registered domain blueprints to identify:
- Primary domain identity
- Confidence score (0.0 to 1.0)
- Supporting evidence (specific matched tokens, columns, sample values)
- Alternative candidate domains
"""
from __future__ import annotations

import re
from typing import Dict, List, Set, Tuple

import pandas as pd

from app.domains.base import DomainBlueprint
from app.domains.registry import get_all_blueprints, get_fallback_blueprint
from app.schemas.domain_blueprint import DomainIdentitySchema
from app.services.column_profiler import ColumnProfile

_WORD_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> Set[str]:
    """Tokenize a column name or string into clean lowercase words."""
    spaced = re.sub(r"(?<!^)(?=[A-Z])", " ", str(text))
    spaced = spaced.replace("_", " ").replace("-", " ").replace(".", " ").replace("/", " ")
    return set(_WORD_RE.findall(spaced.lower()))


def _match_keyword(kw: str, tokens: Set[str], full_name: str) -> bool:
    """Check if a keyword matches the extracted tokens or column full name."""
    kw_tokens = set(kw.split("_"))
    if kw_tokens <= tokens:
        return True
    if "_" in kw and kw in full_name:
        return True
    if len(kw) >= 4 and kw in full_name:
        return True
    return False


def detect_domain(
    df: pd.DataFrame,
    profiles: List[ColumnProfile],
) -> DomainIdentitySchema:
    """Detect the most applicable domain for a dataset with evidence and confidence."""
    all_blueprints = get_all_blueprints()
    if not all_blueprints:
        fallback = get_fallback_blueprint()
        return DomainIdentitySchema(
            domain_id=fallback.id,
            name=fallback.name,
            description=fallback.description,
            confidence=0.1,
            evidence=["Default fallback"],
        )

    # Pre-extract column tokens and full lowercase names
    col_data: List[Tuple[str, Set[str], str]] = []
    for col in df.columns:
        col_str = str(col)
        tokens = _tokenize(col_str)
        full_lower = col_str.strip().lower()
        col_data.append((col_str, tokens, full_lower))

    # Also inspect a small sample of text values from categorical columns
    sample_tokens: Set[str] = set()
    for col in df.columns[:10]:
        if df[col].dtype == "object":
            sample_vals = df[col].dropna().head(10).astype(str)
            for v in sample_vals:
                if len(v) < 50:
                    sample_tokens.update(_tokenize(v))

    scored_domains: List[Tuple[float, DomainBlueprint, List[str]]] = []

    for bp in all_blueprints:
        if bp.id == "general_unknown":
            continue

        score = 0.0
        evidence: List[str] = []
        matched_keywords: Set[str] = set()

        # 1. Match blueprint keywords against column names
        for kw in bp.keywords:
            for col_name, tokens, full_lower in col_data:
                if _match_keyword(kw, tokens, full_lower):
                    if kw not in matched_keywords:
                        matched_keywords.add(kw)
                        score += 2.0
                        evidence.append(f"Column '{col_name}' matches keyword '{kw}'")

        # 2. Match blueprint entity name patterns
        for entity in bp.entities:
            for pat in entity.name_patterns:
                for col_name, tokens, full_lower in col_data:
                    if _match_keyword(pat, tokens, full_lower):
                        score += 1.5
                        evidence.append(f"Column '{col_name}' indicates entity '{entity.label}'")

        # 3. Match against sample text values
        for kw in bp.keywords:
            if kw in sample_tokens and kw not in matched_keywords:
                matched_keywords.add(kw)
                score += 0.5
                evidence.append(f"Sample data values match keyword '{kw}'")

        if score > 0:
            # Normalize score against number of keywords
            kw_coverage = len(matched_keywords) / max(1, min(len(bp.keywords), 8))
            composite_score = score + (kw_coverage * 3.0)
            scored_domains.append((composite_score, bp, evidence))

    # Sort domains by composite score descending
    scored_domains.sort(key=lambda x: x[0], reverse=True)

    if not scored_domains or scored_domains[0][0] < 2.0:
        # Check if dataset has general business metrics (revenue, sales, cost)
        for _, bp, _ in scored_domains:
            if bp.id == "general_business":
                return DomainIdentitySchema(
                    domain_id=bp.id,
                    name=bp.name,
                    description=bp.description,
                    confidence=0.4,
                    evidence=["Matched general business terminology"],
                    alternative_domains=["General / Unknown"],
                )

        fallback = get_fallback_blueprint()
        return DomainIdentitySchema(
            domain_id=fallback.id,
            name=fallback.name,
            description=fallback.description,
            confidence=0.2,
            evidence=["No specialized domain vocabulary strongly detected; using generic baseline"],
            alternative_domains=["General Business Analytics"],
        )

    best_score, best_bp, best_evidence = scored_domains[0]

    # Calculate confidence score between 0.35 and 0.98
    confidence = min(0.98, max(0.35, 0.35 + (best_score / 15.0)))

    # Alternative domains (next top candidates with score >= 2.0)
    alternatives = [
        bp.name
        for score, bp, _ in scored_domains[1:4]
        if score >= 2.0 and bp.id != best_bp.id
    ]

    return DomainIdentitySchema(
        domain_id=best_bp.id,
        name=best_bp.name,
        description=best_bp.description,
        confidence=round(confidence, 2),
        evidence=best_evidence[:8],  # Keep top 8 concise evidence items
        alternative_domains=alternatives,
    )
