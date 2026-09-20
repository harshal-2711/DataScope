"""Entity detection engine.

Dynamically detects business, operational, and domain entities from dataset
columns, data types, sample values, and cardinality:
- Customer, Product, Order, Transaction, Employee, Student, Patient, Doctor,
  Vehicle, Route, Location, Supplier, Campaign, Property, Account, Subscription,
  Match, Player, Sensor, Device, Ticket, Incident, etc.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Set, Tuple

import pandas as pd

from app.domains.base import DomainBlueprint, EntityRule
from app.schemas.domain_blueprint import DetectedEntitySchema
from app.services.column_profiler import ColumnProfile

# Common entity catalog
_COMMON_ENTITIES: List[EntityRule] = [
    EntityRule("customer", "Customer / Client", ("customer", "cust", "client", "buyer", "shopper", "consumer")),
    EntityRule("product", "Product / Item", ("product", "item", "sku", "merchandise", "good", "part")),
    EntityRule("order", "Order / Purchase", ("order", "invoice", "receipt", "purchase")),
    EntityRule("transaction", "Financial Transaction", ("transaction", "trans", "payment", "tx")),
    EntityRule("employee", "Employee / Staff", ("employee", "emp", "staff", "worker", "associate")),
    EntityRule("student", "Student / Learner", ("student", "pupil", "learner", "enrollee")),
    EntityRule("patient", "Patient", ("patient", "mrn", "subject")),
    EntityRule("doctor", "Doctor / Physician", ("doctor", "physician", "clinician", "provider")),
    EntityRule("vehicle", "Vehicle / Fleet", ("vehicle", "car", "truck", "vin", "fleet")),
    EntityRule("location", "Location / Region", ("location", "city", "state", "region", "country", "store_location")),
    EntityRule("supplier", "Supplier / Vendor", ("supplier", "vendor", "manufacturer")),
    EntityRule("campaign", "Campaign", ("campaign", "promotion", "ad_group")),
    EntityRule("property", "Property / Real Estate", ("property", "listing", "building", "unit")),
    EntityRule("account", "Account / Organization", ("account", "org", "company", "tenant")),
    EntityRule("subscription", "Subscription", ("subscription", "plan", "membership")),
    EntityRule("sensor", "Sensor / Telemetry", ("sensor", "telemetry", "probe", "meter")),
    EntityRule("device", "Device / Host", ("device", "host", "node", "machine", "terminal")),
    EntityRule("ticket", "Ticket / Issue", ("ticket", "issue", "case", "bug")),
    EntityRule("incident", "Incident / Alert", ("incident", "alert", "event", "alarm")),
]

_WORD_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> Set[str]:
    spaced = re.sub(r"(?<!^)(?=[A-Z])", " ", str(text))
    spaced = spaced.replace("_", " ").replace("-", " ")
    return set(_WORD_RE.findall(spaced.lower()))


def detect_entities(
    df: pd.DataFrame,
    profiles: List[ColumnProfile],
    blueprint: Optional[DomainBlueprint] = None,
) -> List[DetectedEntitySchema]:
    """Identify candidate entities present in the dataset."""
    profile_map: Dict[str, ColumnProfile] = {p.name: p for p in profiles}

    # Combine common entities with blueprint-specific entities
    candidate_rules: List[EntityRule] = list(_COMMON_ENTITIES)
    if blueprint:
        existing_types = {e.entity_type for e in candidate_rules}
        for be in blueprint.entities:
            if be.entity_type not in existing_types:
                candidate_rules.append(be)

    detected: List[DetectedEntitySchema] = []
    used_columns: Set[str] = set()

    for rule in candidate_rules:
        best_col: Optional[str] = None
        best_score = 0.0
        best_evidence = ""

        for col in df.columns:
            col_name = str(col)
            if col_name in used_columns:
                continue

            prof = profile_map.get(col_name)
            if not prof or prof.role == "ignore":
                continue

            col_tokens = _tokenize(col_name)
            full_lower = col_name.strip().lower()

            for pat in rule.name_patterns:
                pat_tokens = set(pat.split("_"))
                matches_token = pat_tokens <= col_tokens
                matches_substring = (len(pat) >= 4 and pat in full_lower) or (f"_{pat}" in full_lower or f"{pat}_" in full_lower)

                if matches_token or matches_substring:
                    score = 2.0
                    # Check role preference
                    if prof.role in rule.role_preference:
                        score += 1.5

                    # Check identifier-like or categorical
                    if prof.role == "identifier":
                        score += 1.0

                    if score > best_score:
                        best_score = score
                        best_col = col_name
                        best_evidence = (
                            f"Column '{col_name}' matches '{pat}' pattern "
                            f"({prof.distinct_count} distinct values, role: {prof.role})"
                        )

        if best_col and best_score >= 2.0:
            used_columns.add(best_col)
            confidence = min(0.98, max(0.4, best_score / 4.5))
            detected.append(
                DetectedEntitySchema(
                    entity_type=rule.entity_type,
                    label=rule.label,
                    matched_column=best_col,
                    confidence=round(confidence, 2),
                    evidence=best_evidence,
                )
            )

    return detected
