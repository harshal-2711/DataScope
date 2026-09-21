"""Universal Dataset Grain and Entity Engine.

Determines the analytical grain of a dataset (what 1 row represents):
- One row per tender
- One row per transaction
- One row per customer
- One row per match
- One row per ball/delivery
- One row per student
- One row per employee
- One row per event
- One row per measurement
- One row per record

Prevents invalid assumptions that row count equals entity count.
Provides aggregation guardrails against duplicate counting.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

import pandas as pd
from pandas.api import types as pdt

# Grain detection rules based on column signatures and domain hints
_GRAIN_SIGNATURES = [
    {
        "grain_type": "one_row_per_ball",
        "grain_label": "One row per ball / delivery",
        "description": "Each row captures an individual ball/delivery in a cricket match.",
        "keywords": ["ball", "over", "delivery", "batsman", "bowler", "non_striker", "runs_off_bat", "extra_runs"],
        "min_matches": 2,
    },
    {
        "grain_type": "one_row_per_match",
        "grain_label": "One row per match",
        "description": "Each row captures a completed match or fixture between two teams/competitors.",
        "keywords": ["match_id", "team1", "team2", "toss_winner", "winner", "venue", "player_of_match"],
        "min_matches": 2,
    },
    {
        "grain_type": "one_row_per_tender",
        "grain_label": "One row per tender / contract",
        "description": "Each row represents a public procurement tender, bid solicitation, or contract award.",
        "keywords": ["tender", "tender_id", "tender_no", "bid_id", "contract_id", "procurement_method", "buyer", "tender_value", "tenderer"],
        "min_matches": 2,
    },
    {
        "grain_type": "one_row_per_student",
        "grain_label": "One row per student / exam record",
        "description": "Each row records a student, enrollment, course grade, or exam score.",
        "keywords": ["student_id", "roll_no", "student_name", "gpa", "marks", "exam_score", "attendance_rate", "course_id"],
        "min_matches": 2,
    },
    {
        "grain_type": "one_row_per_employee",
        "grain_label": "One row per employee / staff member",
        "description": "Each row represents an employee profile, payroll record, or HR event.",
        "keywords": ["emp_id", "employee_id", "staff_id", "hire_date", "department", "salary", "job_title", "tenure"],
        "min_matches": 2,
    },
    {
        "grain_type": "one_row_per_transaction",
        "grain_label": "One row per transaction / order",
        "description": "Each row represents a customer order, purchase transaction, or invoice line.",
        "keywords": ["order_id", "transaction_id", "invoice_id", "customer_id", "sales", "unit_price", "quantity", "discount"],
        "min_matches": 2,
    },
    {
        "grain_type": "one_row_per_customer",
        "grain_label": "One row per customer / account",
        "description": "Each row records an individual customer, client profile, or user account.",
        "keywords": ["customer_id", "account_id", "client_id", "signup_date", "churn", "lifetime_value", "clv"],
        "min_matches": 2,
    },
    {
        "grain_type": "one_row_per_event",
        "grain_label": "One row per event / interaction",
        "description": "Each row captures a discrete system log, user interaction, or timestamped event.",
        "keywords": ["event_id", "session_id", "event_type", "action", "timestamp", "log_id", "user_action"],
        "min_matches": 2,
    },
    {
        "grain_type": "one_row_per_measurement",
        "grain_label": "One row per sensor measurement",
        "description": "Each row represents an environmental, scientific, or telemetry measurement.",
        "keywords": ["sensor_id", "reading", "measurement", "metric_value", "temperature", "humidity", "pressure"],
        "min_matches": 2,
    },
]


@dataclass
class DatasetGrain:
    grain_type: str
    grain_label: str
    description: str
    primary_entity_column: Optional[str]
    row_count: int
    unique_entity_count: int
    repeated_observations_count: int
    repetition_ratio: float
    is_one_to_one: bool
    candidate_entities: List[Dict[str, Any]]
    measures: List[str]
    dimensions: List[str]
    aggregation_guardrails: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def detect_dataset_grain(df: pd.DataFrame) -> DatasetGrain:
    row_count = int(len(df))
    columns = [str(c) for c in df.columns]
    lower_cols = [c.lower() for c in columns]
    col_map = {c.lower(): c for c in columns}

    # 1. Identify candidate entity identifier columns
    candidate_entities: List[Dict[str, Any]] = []
    id_regex = re.compile(r"(id|uuid|guid|key|code|pk|ref|no|number|name)$", re.IGNORECASE)
    measure_regex = re.compile(
        r"(amount|value|price|cost|spend|revenue|profit|discount|duration|days|score|rate|pct|percent|total|reading|temp|bids)",
        re.IGNORECASE,
    )

    for col in columns:
        s = df[col]
        non_null = int(s.notna().sum())
        if non_null == 0:
            continue
        nunique = int(s.nunique(dropna=True))
        is_id_name = bool(id_regex.search(col))
        is_measure_name = bool(measure_regex.search(col))
        is_num = pdt.is_numeric_dtype(s)
        uniqueness_ratio = nunique / non_null if non_null > 0 else 0.0

        # Skip continuous floats, boolean flags, or obvious numeric measures
        if pdt.is_float_dtype(s) or pdt.is_bool_dtype(s) or is_measure_name:
            continue

        if is_id_name or (uniqueness_ratio >= 0.5 and not is_num):
            candidate_entities.append({
                "column": col,
                "unique_count": nunique,
                "uniqueness_ratio": round(uniqueness_ratio, 4),
                "is_unique_per_row": nunique == row_count,
            })

    # Sort candidate entities by uniqueness ratio descending
    candidate_entities.sort(key=lambda x: x["uniqueness_ratio"], reverse=True)

    # 2. Match grain signature
    selected_grain = None
    for sig in _GRAIN_SIGNATURES:
        matches = 0
        for kw in sig["keywords"]:
            if any(kw in c for c in lower_cols):
                matches += 1
        if matches >= sig["min_matches"]:
            selected_grain = sig
            break

    if not selected_grain:
        # Fallback heuristic
        selected_grain = {
            "grain_type": "one_row_per_record",
            "grain_label": "One row per observation / record",
            "description": "Each row represents a distinct observation or record in the dataset.",
            "keywords": [],
            "min_matches": 0,
        }

    # 3. Determine primary entity column
    primary_entity_col: Optional[str] = None
    if candidate_entities:
        grain_kw = selected_grain.get("keywords", [])
        # Prioritize explicit ID columns matching grain keywords
        for cand in candidate_entities:
            c_name = cand["column"]
            c_lower = c_name.lower()
            if any(kw in c_lower for kw in grain_kw) and bool(id_regex.search(c_name)):
                primary_entity_col = c_name
                break
        if not primary_entity_col:
            for cand in candidate_entities:
                c_lower = cand["column"].lower()
                if any(kw in c_lower for kw in grain_kw):
                    primary_entity_col = cand["column"]
                    break
        if not primary_entity_col:
            primary_entity_col = candidate_entities[0]["column"]

    # 4. Compute entity counts vs row counts
    if primary_entity_col and primary_entity_col in df.columns:
        unique_entity_count = int(df[primary_entity_col].nunique(dropna=True))
    else:
        unique_entity_count = row_count

    repeated_observations = max(0, row_count - unique_entity_count)
    repetition_ratio = round(repeated_observations / row_count, 4) if row_count > 0 else 0.0
    is_one_to_one = (unique_entity_count == row_count)

    # 5. Classify measures and dimensions
    measures: List[str] = []
    dimensions: List[str] = []

    for col in columns:
        s = df[col]
        is_num = pdt.is_numeric_dtype(s)
        nunique = int(s.nunique(dropna=True))
        is_id = any(c["column"] == col for c in candidate_entities if c["uniqueness_ratio"] > 0.9)

        if is_num and not is_id:
            # Check if discrete code or continuous
            if nunique > 5 or not pdt.is_integer_dtype(s):
                measures.append(col)
            else:
                dimensions.append(col)
        elif not is_num:
            if nunique <= 60:
                dimensions.append(col)

    # 6. Build aggregation guardrails
    guardrails: List[str] = []
    if not is_one_to_one and primary_entity_col:
        guardrails.append(
            f"Dataset contains repeated observations for '{primary_entity_col}' "
            f"({row_count:,} rows across {unique_entity_count:,} unique entities). "
            f"Directly summing entity-level attributes without grouping may cause double-counting."
        )
    if "one_row_per_ball" in selected_grain["grain_type"]:
        guardrails.append(
            "Ball-by-ball grain detected. Match-level statistics (such as match winner, toss result) "
            "must be aggregated at match level, not summed per ball."
        )
    if "one_row_per_tender" in selected_grain["grain_type"]:
        guardrails.append(
            "Tender grain detected. Tender duration must be analyzed using average or median, "
            "never as a sum or part-to-whole share."
        )

    return DatasetGrain(
        grain_type=selected_grain["grain_type"],
        grain_label=selected_grain["grain_label"],
        description=selected_grain["description"],
        primary_entity_column=primary_entity_col,
        row_count=row_count,
        unique_entity_count=unique_entity_count,
        repeated_observations_count=repeated_observations,
        repetition_ratio=repetition_ratio,
        is_one_to_one=is_one_to_one,
        candidate_entities=candidate_entities[:5],
        measures=measures,
        dimensions=dimensions,
        aggregation_guardrails=guardrails,
    )
