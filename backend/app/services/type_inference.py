"""Universal Semantic Type Inference Engine.

Infers semantic data types for tabular columns beyond raw pandas dtypes:
1. Integer
2. Float
3. Boolean
4. Text
5. Category
6. Identifier
7. Date
8. Datetime
9. Duration
10. Percentage
11. Currency
12. Timestamp

Guards against misclassifications (e.g. phone numbers or numeric IDs as dates).
Computes confidence, completeness, unique counts, sample values, and warnings.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd
from pandas.api import types as pdt

SEMANTIC_TYPES = {
    "Integer",
    "Float",
    "Boolean",
    "Text",
    "Category",
    "Identifier",
    "Date",
    "Datetime",
    "Duration",
    "Percentage",
    "Currency",
    "Timestamp",
}

_IDENTIFIER_NAME_PATTERNS = re.compile(
    r"(^|[_.\-\s])(id|uuid|guid|key|code|pk|ref|number|no|sku|index|idx|hash|token)($|[_.\-\s])",
    re.IGNORECASE,
)

_DATE_NAME_PATTERNS = re.compile(
    r"(^|[_.\-\s])(date|dt|day|dob|created_at|updated_at|published|deadline|submission|expiry|timestamp)($|[_.\-\s])",
    re.IGNORECASE,
)

_CURRENCY_SYMBOLS = {"$", "€", "£", "¥", "₹", "rs", "inr", "usd", "eur", "gbp", "aud", "cad"}

_CURRENCY_NAME_PATTERNS = re.compile(
    r"(^|[_.\-\s])(price|cost|revenue|amount|budget|salary|wage|fee|charge|tender_value|contract_value|bid|total_spend|spend|income|expense|profit|tax)($|[_.\-\s])",
    re.IGNORECASE,
)

_PERCENT_NAME_PATTERNS = re.compile(
    r"(^|[_.\-\s])(pct|percent|percentage|rate|share|ratio|margin|discount)($|[_.\-\s])",
    re.IGNORECASE,
)

_DURATION_NAME_PATTERNS = re.compile(
    r"(^|[_.\-\s])(duration|elapsed|tenure|lead_time|turnaround|days_to|time_spent|hours_spent|period_days)($|[_.\-\s])",
    re.IGNORECASE,
)

_DURATION_VALUE_PATTERNS = re.compile(
    r"^\s*(\d+(\.\d+)?)\s*(days?|d|hours?|hrs?|h|mins?|minutes?|m|secs?|seconds?|s|weeks?|w|months?)\s*$",
    re.IGNORECASE,
)

_FISCAL_YEAR_PATTERNS = re.compile(
    r"^\s*(FY\s*\d{2,4}([-/]\d{2,4})?|\d{4}[-/]\d{2,4}|Q[1-4][-_/\s]\d{2,4}|\d{4}\s*[-/]\s*Q[1-4]|FY\d{2,4}|[12]\d{3}\s*-\s*[12]\d{3})\s*$",
    re.IGNORECASE,
)

_FISCAL_NAME_PATTERNS = re.compile(
    r"(^|[_.\-\s/])(fiscal|fiscal_year|financial_year|fy|academic_year|tax_year|fiscal_period|period)($|[_.\-\s/])",
    re.IGNORECASE,
)


@dataclass
class ColumnInference:
    name: str
    original_type: str
    inferred_type: str
    confidence: float
    missing_count: int
    missing_percentage: float
    unique_count: int
    sample_values: List[Any]
    warnings: List[str]
    unit: Optional[str] = None
    currency_symbol: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


_INDIAN_CONTEXT_KEYWORDS = {
    "ipl", "cricket", "runs", "wickets", "lakh", "lakhs", "crore", "crores",
    "gst", "pan", "aadhaar", "inr", "rs", "rupee", "rupees", "pwd", "nhm",
    "mumbai", "delhi", "bengaluru", "chennai", "kolkata", "hyderabad", "ahmedabad",
    "pune", "jaipur", "bihar", "maharashtra", "karnataka", "tamil", "gujarat"
}


def detect_dataset_currency(df: pd.DataFrame) -> Optional[str]:
    """Detect dataset-wide currency symbol from columns, metadata, sample values, or domain signals."""
    col_names = [str(c).lower() for c in df.columns]
    
    # 1. Dedicated currency column
    for c in df.columns:
        clow = str(c).lower()
        if "currency" in clow or clow == "curr":
            vals = df[c].dropna().astype(str).str.upper().str.strip()
            if not vals.empty:
                val_counts = vals.value_counts()
                top_val = val_counts.index[0]
                if top_val in ("INR", "₹", "RS", "RUPEES", "RUPEE"):
                    return "₹"
                if top_val in ("USD", "$"):
                    return "$"
                if top_val in ("EUR", "€"):
                    return "€"
                if top_val in ("GBP", "£"):
                    return "£"
                if top_val in ("JPY", "¥", "CNY"):
                    return "¥"
                if top_val in ("AUD", "CAD", "NZD", "SGD"):
                    return "$"

    # 2. Column name hints
    for name in col_names:
        if any(kw in name for kw in ("inr", "rupee", "rupees", "_rs", "rs_")):
            return "₹"
        if any(kw in name for kw in ("_usd", "usd_", "in_usd", "(usd)")):
            return "$"
        if any(kw in name for kw in ("_eur", "eur_", "in_eur", "(eur)")):
            return "€"
        if any(kw in name for kw in ("_gbp", "gbp_", "in_gbp", "(gbp)")):
            return "£"

    # 3. Check sample values across string columns for currency symbols
    for col in df.columns:
        s = df[col]
        if not pdt.is_numeric_dtype(s) and not pdt.is_bool_dtype(s):
            samples = s.dropna().head(50).astype(str).str.strip()
            if not samples.empty:
                if (samples.str.startswith("₹") | samples.str.endswith("₹") | samples.str.contains("INR", case=False) | samples.str.contains("Rs.", case=False)).mean() > 0.3:
                    return "₹"
                if (samples.str.startswith("€") | samples.str.endswith("€")).mean() > 0.3:
                    return "€"
                if (samples.str.startswith("£") | samples.str.endswith("£")).mean() > 0.3:
                    return "£"
                if (samples.str.startswith("¥") | samples.str.endswith("¥")).mean() > 0.3:
                    return "¥"
                if (samples.str.startswith("$") | samples.str.endswith("$")).mean() > 0.3:
                    return "$"

    # 4. Check Indian domain keywords
    combined_text = " ".join(col_names).lower()
    if any(k in combined_text for k in _INDIAN_CONTEXT_KEYWORDS):
        return "₹"

    return None


def _looks_like_identifier_name(name: str) -> bool:
    return bool(_IDENTIFIER_NAME_PATTERNS.search(name))


def _looks_like_date_name(name: str) -> bool:
    return bool(_DATE_NAME_PATTERNS.search(name))


def _looks_like_currency_name(name: str) -> bool:
    return bool(_CURRENCY_NAME_PATTERNS.search(name))


def _looks_like_percent_name(name: str) -> bool:
    return bool(_PERCENT_NAME_PATTERNS.search(name))


def _looks_like_duration_name(name: str) -> bool:
    return bool(_DURATION_NAME_PATTERNS.search(name))


def _is_phone_or_postal(series: pd.Series) -> bool:
    """Detect phone numbers or zip/postal codes that shouldn't be parsed as dates."""
    non_null = series.dropna().astype(str).str.strip()
    if non_null.empty:
        return False
    # Phone number patterns: e.g. +1-555-..., 10 digits starting with 6-9, etc.
    phone_matches = non_null.str.match(r"^(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$")
    if phone_matches.mean() > 0.7:
        return True
    # 5-digit zip or 6-digit postal
    postal_matches = non_null.str.match(r"^\d{5}(-\d{4})?$|^\d{6}$")
    if postal_matches.mean() > 0.8:
        return True
    return False


def infer_column_type(series: pd.Series, row_count: int) -> ColumnInference:
    name = str(series.name)
    original_type = str(series.dtype)
    non_null_count = int(series.notna().sum())
    missing_count = int(row_count - non_null_count)
    missing_percentage = round((missing_count / row_count * 100.0), 2) if row_count > 0 else 0.0
    unique_count = int(series.nunique(dropna=True))

    # Sample values for preview
    sample_values = (
        series.dropna().head(5).tolist()
        if non_null_count > 0
        else []
    )
    # Ensure serializable sample values
    clean_samples = []
    for val in sample_values:
        if isinstance(val, (pd.Timestamp, np.datetime64)):
            clean_samples.append(str(val))
        elif isinstance(val, (np.integer, int)):
            clean_samples.append(int(val))
        elif isinstance(val, (np.floating, float)):
            clean_samples.append(round(float(val), 4))
        else:
            clean_samples.append(str(val))

    warnings: List[str] = []
    if missing_percentage > 40.0:
        warnings.append(f"High missing rate ({missing_percentage:.1f}%)")

    # Degenerate cases: all null or single constant
    if non_null_count == 0:
        return ColumnInference(
            name=name,
            original_type=original_type,
            inferred_type="Text",
            confidence=0.1,
            missing_count=missing_count,
            missing_percentage=missing_percentage,
            unique_count=0,
            sample_values=[],
            warnings=["Column contains entirely null values"],
        )

    if unique_count <= 1:
        warnings.append("Constant column (single unique value)")

    non_null_series = series.dropna()
    uniqueness_ratio = unique_count / non_null_count if non_null_count > 0 else 0.0

    # 1. Native Datetime
    if pdt.is_datetime64_any_dtype(series):
        # Distinguish Date vs Datetime
        has_time = False
        try:
            has_time = (non_null_series.dt.hour != 0).any() or (non_null_series.dt.minute != 0).any()
        except Exception:
            pass
        inferred = "Datetime" if has_time else "Date"
        return ColumnInference(
            name=name,
            original_type=original_type,
            inferred_type=inferred,
            confidence=0.98,
            missing_count=missing_count,
            missing_percentage=missing_percentage,
            unique_count=unique_count,
            sample_values=clean_samples,
            warnings=warnings,
        )

    # 2. Native Timedelta / Duration
    if pdt.is_timedelta64_dtype(series) or _looks_like_duration_name(name):
        if pdt.is_timedelta64_dtype(series):
            return ColumnInference(
                name=name,
                original_type=original_type,
                inferred_type="Duration",
                confidence=0.99,
                missing_count=missing_count,
                missing_percentage=missing_percentage,
                unique_count=unique_count,
                sample_values=clean_samples,
                warnings=warnings,
            )

    # 3. Native Boolean or Boolean-like
    if pdt.is_bool_dtype(series):
        return ColumnInference(
            name=name,
            original_type=original_type,
            inferred_type="Boolean",
            confidence=1.0,
            missing_count=missing_count,
            missing_percentage=missing_percentage,
            unique_count=unique_count,
            sample_values=clean_samples,
            warnings=warnings,
        )

    str_samples = non_null_series.astype(str).str.strip()
    lower_samples = str_samples.str.lower()
    distinct_lower = set(lower_samples.unique())

    bool_pairs = [
        {"true", "false"},
        {"yes", "no"},
        {"y", "n"},
        {"t", "f"},
        {"0", "1"},
        {"0.0", "1.0"},
        {"enabled", "disabled"},
        {"active", "inactive"},
    ]
    if any(distinct_lower == pair or distinct_lower.issubset(pair) and len(distinct_lower) == 2 for pair in bool_pairs):
        return ColumnInference(
            name=name,
            original_type=original_type,
            inferred_type="Boolean",
            confidence=0.95,
            missing_count=missing_count,
            missing_percentage=missing_percentage,
            unique_count=unique_count,
            sample_values=clean_samples,
            warnings=warnings,
        )

    # 4. Currency Detection (String with currency symbols or Numeric with currency name)
    # Check string currency symbols: e.g. "$1,200.00", "€ 45", "₹10,500"
    symbol_matches = lower_samples.apply(lambda s: any(s.startswith(sym) or s.endswith(sym) for sym in _CURRENCY_SYMBOLS))
    if symbol_matches.mean() >= 0.7:
        return ColumnInference(
            name=name,
            original_type=original_type,
            inferred_type="Currency",
            confidence=0.95,
            missing_count=missing_count,
            missing_percentage=missing_percentage,
            unique_count=unique_count,
            sample_values=clean_samples,
            warnings=warnings,
        )

    if pdt.is_numeric_dtype(series) and _looks_like_currency_name(name):
        return ColumnInference(
            name=name,
            original_type=original_type,
            inferred_type="Currency",
            confidence=0.90,
            missing_count=missing_count,
            missing_percentage=missing_percentage,
            unique_count=unique_count,
            sample_values=clean_samples,
            warnings=warnings,
        )

    # 5. Percentage Detection
    pct_matches = str_samples.str.endswith("%")
    if pct_matches.mean() >= 0.7:
        return ColumnInference(
            name=name,
            original_type=original_type,
            inferred_type="Percentage",
            confidence=0.95,
            missing_count=missing_count,
            missing_percentage=missing_percentage,
            unique_count=unique_count,
            sample_values=clean_samples,
            warnings=warnings,
        )
    if pdt.is_numeric_dtype(series) and _looks_like_percent_name(name):
        val_min = float(non_null_series.min())
        val_max = float(non_null_series.max())
        if (0 <= val_min and val_max <= 1.0) or (0 <= val_min and val_max <= 100.0):
            return ColumnInference(
                name=name,
                original_type=original_type,
                inferred_type="Percentage",
                confidence=0.90,
                missing_count=missing_count,
                missing_percentage=missing_percentage,
                unique_count=unique_count,
                sample_values=clean_samples,
                warnings=warnings,
            )

    # 6. Duration String Pattern (e.g. "15 days", "3 hours", "45 mins")
    duration_matches = str_samples.str.match(_DURATION_VALUE_PATTERNS)
    if duration_matches.mean() >= 0.7:
        return ColumnInference(
            name=name,
            original_type=original_type,
            inferred_type="Duration",
            confidence=0.92,
            missing_count=missing_count,
            missing_percentage=missing_percentage,
            unique_count=unique_count,
            sample_values=clean_samples,
            warnings=warnings,
        )
    if pdt.is_numeric_dtype(series) and _looks_like_duration_name(name):
        return ColumnInference(
            name=name,
            original_type=original_type,
            inferred_type="Duration",
            confidence=0.88,
            missing_count=missing_count,
            missing_percentage=missing_percentage,
            unique_count=unique_count,
            sample_values=clean_samples,
            warnings=warnings,
        )

    # 7. Numeric Timestamp Candidates (e.g. Unix seconds 1.6e9 or ms 1.6e12)
    if pdt.is_integer_dtype(series) or pdt.is_float_dtype(series):
        if not non_null_series.empty:
            med_val = float(non_null_series.median())
            # Unix seconds range: 1,000,000,000 (Sept 2001) to 2,500,000,000 (2049)
            if 1_000_000_000 <= med_val <= 2_500_000_000:
                return ColumnInference(
                    name=name,
                    original_type=original_type,
                    inferred_type="Timestamp",
                    confidence=0.92,
                    missing_count=missing_count,
                    missing_percentage=missing_percentage,
                    unique_count=unique_count,
                    sample_values=clean_samples,
                    warnings=warnings,
                )
            # Unix milliseconds range: 1e12 to 2.5e12
            if 1_000_000_000_000 <= med_val <= 2_500_000_000_000:
                return ColumnInference(
                    name=name,
                    original_type=original_type,
                    inferred_type="Timestamp",
                    confidence=0.92,
                    missing_count=missing_count,
                    missing_percentage=missing_percentage,
                    unique_count=unique_count,
                    sample_values=clean_samples,
                    warnings=warnings,
                )

    # 7.5 Fiscal Year / Fiscal Period Detection
    if _FISCAL_NAME_PATTERNS.search(name) or str_samples.str.match(_FISCAL_YEAR_PATTERNS).mean() >= 0.7:
        return ColumnInference(
            name=name,
            original_type=original_type,
            inferred_type="Category",
            confidence=0.95,
            missing_count=missing_count,
            missing_percentage=missing_percentage,
            unique_count=unique_count,
            sample_values=clean_samples,
            warnings=warnings,
        )

    # 8. Date / Datetime from Strings
    # Guard against phone numbers, postal codes, pure numeric IDs, and fiscal year strings
    if not pdt.is_numeric_dtype(series) and not _is_phone_or_postal(series):
        # Test datetime parseability
        try:
            sample_test = str_samples.head(50)
            parsed = pd.to_datetime(sample_test, errors="coerce", format="mixed")
            valid_ratio = parsed.notna().mean()
            if valid_ratio >= 0.8:
                # Check if it has time component
                has_time = (parsed.dt.hour != 0).any() or (parsed.dt.minute != 0).any()
                inferred = "Datetime" if has_time else "Date"
                confidence = 0.95 if _looks_like_date_name(name) else 0.88
                return ColumnInference(
                    name=name,
                    original_type=original_type,
                    inferred_type=inferred,
                    confidence=confidence,
                    missing_count=missing_count,
                    missing_percentage=missing_percentage,
                    unique_count=unique_count,
                    sample_values=clean_samples,
                    warnings=warnings,
                )
        except Exception:
            pass

    # 9. Identifier Detection
    # If explicitly named like an ID / key, or near-unique integer / string
    # Must have genuine variation (> 1 distinct value, not a constant like id=1 in multi-row datasets)
    if _looks_like_identifier_name(name) and unique_count > 1:
        if uniqueness_ratio >= 0.7 or (uniqueness_ratio >= 0.5 and non_null_count >= 10 and unique_count >= 5):
            return ColumnInference(
                name=name,
                original_type=original_type,
                inferred_type="Identifier",
                confidence=0.95,
                missing_count=missing_count,
                missing_percentage=missing_percentage,
                unique_count=unique_count,
                sample_values=clean_samples,
                warnings=warnings,
            )

    if uniqueness_ratio >= 0.95 and non_null_count >= 20 and unique_count > 10:
        return ColumnInference(
            name=name,
            original_type=original_type,
            inferred_type="Identifier",
            confidence=0.90,
            missing_count=missing_count,
            missing_percentage=missing_percentage,
            unique_count=unique_count,
            sample_values=clean_samples,
            warnings=warnings,
        )

    # 10. Integer vs Float
    if pdt.is_integer_dtype(series):
        return ColumnInference(
            name=name,
            original_type=original_type,
            inferred_type="Integer",
            confidence=0.95,
            missing_count=missing_count,
            missing_percentage=missing_percentage,
            unique_count=unique_count,
            sample_values=clean_samples,
            warnings=warnings,
        )

    if pdt.is_float_dtype(series):
        # Check if actually all integer values (e.g. floats with .0 due to NaNs)
        valid_floats = non_null_series.dropna()
        if (valid_floats % 1 == 0).all() and len(valid_floats) > 0:
            return ColumnInference(
                name=name,
                original_type=original_type,
                inferred_type="Integer",
                confidence=0.90,
                missing_count=missing_count,
                missing_percentage=missing_percentage,
                unique_count=unique_count,
                sample_values=clean_samples,
                warnings=warnings,
            )
        return ColumnInference(
            name=name,
            original_type=original_type,
            inferred_type="Float",
            confidence=0.95,
            missing_count=missing_count,
            missing_percentage=missing_percentage,
            unique_count=unique_count,
            sample_values=clean_samples,
            warnings=warnings,
        )

    # 11. Category vs Text
    is_cat_dtype = isinstance(series.dtype, pd.CategoricalDtype)
    avg_len = float(non_null_series.astype(str).str.len().mean()) if len(non_null_series) > 0 else 0.0
    has_spaces = float(non_null_series.astype(str).str.contains(r"\s+").mean()) if len(non_null_series) > 0 else 0.0

    # If values are largely unique and text is sentence-like or long, it's Text, not Category
    if not is_cat_dtype and (uniqueness_ratio >= 0.8 and (avg_len > 12 or has_spaces > 0.5)):
        return ColumnInference(
            name=name,
            original_type=original_type,
            inferred_type="Text",
            confidence=0.90,
            missing_count=missing_count,
            missing_percentage=missing_percentage,
            unique_count=unique_count,
            sample_values=clean_samples,
            warnings=warnings,
        )

    if is_cat_dtype or (unique_count <= 60 and (uniqueness_ratio <= 0.25 or (unique_count <= 15 and avg_len <= 25 and has_spaces <= 0.4))):
        return ColumnInference(
            name=name,
            original_type=original_type,
            inferred_type="Category",
            confidence=0.92,
            missing_count=missing_count,
            missing_percentage=missing_percentage,
            unique_count=unique_count,
            sample_values=clean_samples,
            warnings=warnings,
        )

    # Default fallback: Text
    return ColumnInference(
        name=name,
        original_type=original_type,
        inferred_type="Text",
        confidence=0.85,
        missing_count=missing_count,
        missing_percentage=missing_percentage,
        unique_count=unique_count,
        sample_values=clean_samples,
        warnings=warnings,
    )


def infer_dataset_types(df: pd.DataFrame) -> List[ColumnInference]:
    """Infers semantic types for all columns in a DataFrame."""
    row_count = len(df)
    return [infer_column_type(df[col], row_count) for col in df.columns]
