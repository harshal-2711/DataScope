"""Central registry and indexing for all 75 DataScope domain blueprints."""
from __future__ import annotations

from typing import Dict, List, Optional

from app.domains.base import DomainBlueprint
from app.domains.commerce import DOMAINS as COMMERCE_DOMAINS
from app.domains.education import DOMAINS as EDUCATION_DOMAINS
from app.domains.finance import DOMAINS as FINANCE_DOMAINS
from app.domains.healthcare_life import DOMAINS as HEALTHCARE_DOMAINS
from app.domains.logistics_travel import DOMAINS as LOGISTICS_DOMAINS
from app.domains.manufacturing_energy import DOMAINS as MANUFACTURING_DOMAINS
from app.domains.media_entertainment import DOMAINS as MEDIA_DOMAINS
from app.domains.people_hr import DOMAINS as PEOPLE_DOMAINS
from app.domains.public_environment import DOMAINS as PUBLIC_DOMAINS
from app.domains.sales_marketing import DOMAINS as SALES_DOMAINS
from app.domains.technology import DOMAINS as TECHNOLOGY_DOMAINS

# Combine all domain definitions
_ALL_BLUEPRINTS: List[DomainBlueprint] = (
    COMMERCE_DOMAINS
    + FINANCE_DOMAINS
    + TECHNOLOGY_DOMAINS
    + SALES_DOMAINS
    + PEOPLE_DOMAINS
    + HEALTHCARE_DOMAINS
    + EDUCATION_DOMAINS
    + LOGISTICS_DOMAINS
    + MANUFACTURING_DOMAINS
    + MEDIA_DOMAINS
    + PUBLIC_DOMAINS
)

_BLUEPRINT_BY_ID: Dict[str, DomainBlueprint] = {bp.id: bp for bp in _ALL_BLUEPRINTS}
_BLUEPRINT_BY_NAME: Dict[str, DomainBlueprint] = {bp.name.lower(): bp for bp in _ALL_BLUEPRINTS}


def get_all_blueprints() -> List[DomainBlueprint]:
    """Return all 75 registered domain blueprints."""
    return list(_ALL_BLUEPRINTS)


def get_blueprint_by_id(domain_id: str) -> Optional[DomainBlueprint]:
    """Look up a domain blueprint by its unique identifier."""
    return _BLUEPRINT_BY_ID.get(domain_id)


def get_blueprint_by_name(name: str) -> Optional[DomainBlueprint]:
    """Look up a domain blueprint by its display name (case-insensitive)."""
    return _BLUEPRINT_BY_NAME.get(name.strip().lower())


def get_fallback_blueprint() -> DomainBlueprint:
    """Return the General / Unknown fallback blueprint."""
    fallback = _BLUEPRINT_BY_ID.get("general_unknown")
    if fallback is None:
        raise RuntimeError("Fallback blueprint 'general_unknown' is not registered.")
    return fallback
