"""Business-relevance heuristics used by the recommendation engine.

The recommendation engine's job isn't just "these two columns are
type-compatible, chart them" -- a technically valid chart isn't
automatically a *useful* one. This module scores column names against
common analytics vocabulary (metrics like sales/revenue/profit, dimensions
like category/product/region, low-signal operational fields like
login_type/session_id) so the engine can prefer "Total Sales by Category"
over "Total Discount by Customer_Login_type" without ever hard-coding a
specific dataset's schema.

Everything here is a *heuristic bias*, not a hard requirement: unrecognized
column names still get a usable neutral score, so the engine stays generic
for datasets that don't use e-commerce vocabulary at all (survey data,
ops data, scientific data, ...). Recognized vocabulary only shifts the
ranking, it never disqualifies a column outright.
"""

from __future__ import annotations

import re

# --- Metrics (numeric quantities worth measuring) -------------------------
# Tier 1: outcomes a business/analysis cares about most directly.
_METRIC_TIER_1 = (
    "sales", "revenue", "profit", "margin", "income", "earnings",
)
# Tier 2: still meaningful measures, one step removed from tier 1.
_METRIC_TIER_2 = (
    "quantity", "qty", "units", "discount", "shipping_cost", "shipping",
    "cost", "price", "amount", "total", "spend", "budget", "expense",
)

# --- Dimensions (categorical fields worth grouping/breaking down by) ------
_DIMENSION_TIER_1 = (
    "category", "sub_category", "subcategory", "product", "product_name",
    "gender", "location", "city", "state", "region", "country",
)
_DIMENSION_TIER_2 = (
    "customer_type", "segment", "channel", "department", "team",
    "brand", "store", "warehouse", "type",
)
# Fields that are usually operational/technical metadata rather than an
# analytically interesting way to slice a metric. Still chartable -- just
# deprioritized relative to recognized business dimensions.
_DIMENSION_LOW_PRIORITY = (
    "login_type", "login", "session", "device", "browser", "referrer",
    "user_agent", "ip_address", "ip", "status_code", "http_status",
    "token", "platform_version", "app_version",
)

# --- Time columns -----------------------------------------------------------
_TIME_HINTS = (
    "order_date", "purchase_date", "transaction_date", "date", "timestamp",
    "created_at", "order_time", "datetime",
)

_WORD_RE = re.compile(r"[a-z]+")


def _tokens(column_name: str) -> set[str]:
    """Lowercase word tokens from a column name, splitting snake_case,
    kebab-case, and camelCase boundaries."""
    spaced = re.sub(r"(?<!^)(?=[A-Z])", " ", column_name)
    spaced = spaced.replace("_", " ").replace("-", " ")
    return set(_WORD_RE.findall(spaced.lower()))


def _matches_any(tokens: set[str], hints: tuple[str, ...], full_name: str) -> bool:
    for hint in hints:
        hint_tokens = set(hint.split("_"))
        if hint_tokens <= tokens:
            return True
        # Substring matching is only safe for multi-word hints (contain an
        # underscore) -- a bare short hint like "ip" would otherwise false
        # -positive match inside unrelated words like "shipping".
        if "_" in hint and hint in full_name:
            return True
    return False


def metric_importance(column_name: str) -> float:
    """Score a numeric column's business relevance as a measure. Higher is
    more important. Unrecognized names still score usably (1.0), just
    below recognized business metrics."""
    lowered = column_name.strip().lower()
    tokens = _tokens(column_name)
    if _matches_any(tokens, _METRIC_TIER_1, lowered):
        return 3.0
    if _matches_any(tokens, _METRIC_TIER_2, lowered):
        return 2.0
    return 1.0


def dimension_importance(column_name: str) -> float:
    """Score a categorical column's business relevance as a grouping
    dimension. Higher is more important. Recognized low-signal/operational
    fields (login_type, session_id, ...) are penalized but not excluded --
    they still get charted if nothing better is available."""
    lowered = column_name.strip().lower()
    tokens = _tokens(column_name)
    if _matches_any(tokens, _DIMENSION_LOW_PRIORITY, lowered):
        return 0.3
    if _matches_any(tokens, _DIMENSION_TIER_1, lowered):
        return 3.0
    if _matches_any(tokens, _DIMENSION_TIER_2, lowered):
        return 2.0
    return 1.0


def is_time_named(column_name: str) -> bool:
    tokens = _tokens(column_name)
    lowered = column_name.strip().lower()
    return _matches_any(tokens, _TIME_HINTS, lowered)


# Small synonym map for turning a raw column name into a friendlier label.
# Falls back to generic title-casing for anything not listed here.
_LABEL_OVERRIDES = {
    "qty": "Quantity",
    "amt": "Amount",
    "pct": "Percent",
    "id": "ID",
}


def prettify(column_name: str) -> str:
    """Turn a raw column name into a human-readable label:
    'order_date' -> 'Order Date', 'shippingCost' -> 'Shipping Cost',
    'CustomerID' -> 'Customer ID' (acronym-like runs are preserved)."""
    # Split lower->upper boundaries ("shippingCost" -> "shipping Cost") and
    # acronym->word boundaries ("HTTPServer" -> "HTTP Server"), but do NOT
    # split inside a run of capitals ("ID" stays "ID", not "I D").
    spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", column_name)
    spaced = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", spaced)
    spaced = spaced.replace("_", " ").replace("-", " ").strip()
    words = [w for w in spaced.split(" ") if w]
    if not words:
        return column_name

    pretty_words = []
    for w in words:
        lowered = w.lower()
        if lowered in _LABEL_OVERRIDES:
            pretty_words.append(_LABEL_OVERRIDES[lowered])
        elif w.isupper() and len(w) > 1:
            # Looks like an existing acronym (ID, URL, USA...) -- keep as-is.
            pretty_words.append(w)
        else:
            pretty_words.append(w[:1].upper() + w[1:].lower())
    return " ".join(pretty_words)
