"""Centralized Human-Readable Column Label and Title Formatter.

Converts raw, nested, and flattened column paths (e.g. OCDS paths like
'tender/tender Period/duration In Days' or 'tender/numberOfTenderers')
into professional, clean business labels across all chart titles, axes,
legends, tooltips, and data previews.
"""
from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Optional, Tuple

# Direct override dictionary for known procurement, finance, and enterprise paths
_CANONICAL_OVERRIDES = {
    # Procurement & OCDS flattened paths
    "tender/tender period/duration in days": "Tender Duration (Days)",
    "tender/tenderperiod/durationindays": "Tender Duration (Days)",
    "tender/duration in days": "Tender Duration (Days)",
    "tender/duration_in_days": "Tender Duration (Days)",
    "duration in days": "Duration (Days)",
    "duration_in_days": "Duration (Days)",
    "tender_duration": "Tender Duration (Days)",
    "tender_duration_days": "Tender Duration (Days)",
    "tender/number of tenderers": "Number of Bidders",
    "tender/numberoftenderers": "Number of Bidders",
    "number_of_tenderers": "Number of Bidders",
    "tender/bidders": "Number of Bidders",
    "tenderer_count": "Number of Bidders",
    "bids_received": "Bids Received",
    "bidders_count": "Number of Bidders",
    "tender/main procurement category": "Procurement Category",
    "tender/mainprocurementcategory": "Procurement Category",
    "main_procurement_category": "Procurement Category",
    "procurement_category": "Procurement Category",
    "tender/contract type": "Contract Type",
    "tender/contracttype": "Contract Type",
    "contract_type": "Contract Type",
    "tender/date published": "Publication Date",
    "tender/datepublished": "Publication Date",
    "date_published": "Publication Date",
    "award_date": "Award Date",
    "tender/bidopening/date": "Bid Opening Date",
    "tender/bid opening/date": "Bid Opening Date",
    "bid_opening_date": "Bid Opening Date",
    "tender/value/amount": "Tender Value",
    "tender/value/currency": "Currency",
    "tender/value": "Tender Value",
    "tender_value": "Tender Value",
    "contract_value": "Contract Value",
    "award_value": "Award Value",
    "tender/milestones/duedate": "Milestone Due Date",
    "tender/milestones/due date": "Milestone Due Date",
    "tender/milestones/duedate.1": "Milestone Due Date (Secondary)",
    "tender/milestones/type": "Milestone Type",
    "tender/milestones/type.1": "Milestone Type (Secondary)",
    "tender/milestones/title": "Milestone Title",
    "tender/milestones/title.1": "Milestone Title (Secondary)",
    "tender/milestones/status": "Milestone Status",
    "tender/milestones/id": "Milestone ID",
    "tender/milestones/code": "Milestone Code",
    "tender/procuringentity/name": "Procuring Entity",
    "tender/procuring entity/name": "Procuring Entity",
    "procuring_entity": "Procuring Entity",
    "buyer/name": "Buyer Agency",
    "buyer/id": "Buyer ID",
    "contracting_authority": "Contracting Authority",
    "ocid": "Open Contracting ID (OCID)",
    "fiscal_year": "Fiscal Year",
    "financial_year": "Financial Year",
    "reporting_date": "Reporting Date",
    "initiationtype": "Initiation Type",
    "initiation_type": "Initiation Type",
    "tag": "Release Tag",
    "payment mode": "Payment Mode",
    "payment_mode": "Payment Mode",
    "tenderclassification/description": "Tender Classification",
    "tender/submissionmethoddetails": "Submission Method Details",
    "tender/submission method details": "Submission Method Details",
    "tender/participationfee/0/multicurrencyallowed": "Multi-Currency Allowed",
    "tender/allowtwostagetender": "Two-Stage Tender Allowed",
    "tender/allowpreferentialbidder": "Preferential Bidder Allowed",
    "tender/stage": "Tender Stage",
    "tender/status": "Tender Status",
    "tender/externalreference": "External Reference",
    "tender/title": "Tender Title",
    "tender/procurementmethod": "Procurement Method",
    "tender/documents/id": "Document ID",
    # Common business & operational metrics
    "sales": "Sales Revenue",
    "sales_amount": "Sales Revenue",
    "total_sales": "Sales Revenue",
    "gross_sales": "Sales Revenue",
    "quantity": "Units Sold",
    "qty": "Units Sold",
    "units_sold": "Units Sold",
    "order_quantity": "Units Sold",
    "profit": "Profit",
    "net_profit": "Profit",
    "gross_profit": "Profit",
    "discount": "Discount Rate",
    "discount_amount": "Discount Amount",
    "shipping_cost": "Shipping Cost",
    "shipping": "Shipping Cost",
    "freight_value": "Shipping Cost",
    "freight_cost": "Shipping Cost",
    "aging": "Order Aging",
    "order_aging": "Order Aging",
    "aging_days": "Order Aging (Days)",
    "order_date": "Order Date",
    "ship_date": "Shipping Date",
    "customer_id": "Customer ID",
    "customer_name": "Customer Name",
    "product_id": "Product ID",
    "product_name": "Product Name",
    "unit_price": "Unit Price",
    "total_spend": "Total Spend",
}

_ACRONYMS = {"id", "ocid", "sku", "kpi", "gpa", "ipl", "ctr", "cpc", "mrr", "arr", "usd", "eur", "gbp", "inr", "fy", "rfp", "rfq", "pk", "fk", "nhm", "pwd"}
_GENERIC_TAILS = {"type", "title", "name", "amount", "date", "status", "id", "code", "value", "description", "category", "count", "rate"}


def format_column_label(column_name: Optional[str]) -> str:
    """Format any raw, nested, or flattened column path into a human-readable business label.
    
    Examples:
        'tender/tender Period/duration In Days' -> 'Tender Duration (Days)'
        'tender/number Of Tenderers' -> 'Number of Bidders'
        'tender/main Procurement Category' -> 'Procurement Category'
        'tender/contract Type' -> 'Contract Type'
        'tender/date Published' -> 'Publication Date'
        'tender/milestones/type' -> 'Milestone Type'
    """
    if not column_name or not isinstance(column_name, str):
        return str(column_name or "")

    raw_clean = column_name.strip()
    lowered = raw_clean.lower().replace("\\", "/")

    # 1. Exact canonical override
    if lowered in _CANONICAL_OVERRIDES:
        return _CANONICAL_OVERRIDES[lowered]

    # Handle duplicate suffix like .1 or _1
    has_dup_suffix = bool(re.search(r"[._](\d+)$", raw_clean))
    dup_num_match = re.search(r"[._](\d+)$", raw_clean)
    dup_suffix_str = f" ({dup_num_match.group(1)})" if dup_num_match else ""
    cleaned_base = re.sub(r"[._]\d+$", "", raw_clean)
    base_lowered = cleaned_base.lower().replace("\\", "/")

    if base_lowered in _CANONICAL_OVERRIDES:
        return f"{_CANONICAL_OVERRIDES[base_lowered]}{dup_suffix_str}"

    # 2. Check path segments if nested (contains / or .)
    if "/" in lowered or "." in lowered:
        parts = [p.strip() for p in re.split(r"[/.]", cleaned_base) if p.strip()]
        if parts:
            tail_lower = parts[-1].lower()
            if tail_lower in _CANONICAL_OVERRIDES:
                return f"{_CANONICAL_OVERRIDES[tail_lower]}{dup_suffix_str}"

            # If tail is too generic (like 'type' in 'tender/milestones/type'), combine with parent
            if tail_lower in _GENERIC_TAILS and len(parts) >= 2:
                parent = parts[-2]
                tail = parts[-1]
                combined = f"{parent}_{tail}".lower()
                if combined in _CANONICAL_OVERRIDES:
                    return f"{_CANONICAL_OVERRIDES[combined]}{dup_suffix_str}"
                return f"{_prettify_word(parent)} {_prettify_word(tail)}{dup_suffix_str}"

            # Otherwise clean segment
            return f"{_clean_segment(parts[-1])}{dup_suffix_str}"

    return f"{_clean_segment(raw_clean)}"


# Alias for backwards compatibility
humanize_column_name = format_column_label



def _prettify_word(text: str) -> str:
    """Clean and title case a single token or short segment."""
    spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", text)
    spaced = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", spaced)
    spaced = spaced.replace("_", " ").replace("-", " ").replace(".", " ").strip()
    words = [w for w in spaced.split() if w]
    clean_words = []
    for w in words:
        wl = w.lower()
        if wl in _ACRONYMS:
            clean_words.append(wl.upper())
        elif w.isupper() and len(w) > 1:
            clean_words.append(w)
        else:
            clean_words.append(w[:1].upper() + w[1:].lower())
    return " ".join(clean_words)


def _clean_segment(segment: str) -> str:
    """Clean a segment and handle unit patterns like 'in days'."""
    lowered = segment.lower().strip()
    if lowered in _CANONICAL_OVERRIDES:
        return _CANONICAL_OVERRIDES[lowered]

    # Split camelCase
    spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", segment)
    spaced = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", spaced)
    spaced = spaced.replace("_", " ").replace("-", " ").replace("/", " ").replace(".", " ").strip()

    # Match 'in days', 'in hours', 'in usd'
    spaced = re.sub(r"\bin days\b", "(Days)", spaced, flags=re.IGNORECASE)
    spaced = re.sub(r"\bin hours\b", "(Hours)", spaced, flags=re.IGNORECASE)
    spaced = re.sub(r"\bin usd\b", "(USD)", spaced, flags=re.IGNORECASE)
    spaced = re.sub(r"\bin eur\b", "(EUR)", spaced, flags=re.IGNORECASE)

    words = [w for w in spaced.split() if w]
    clean_words = []
    for w in words:
        if w.startswith("(") and w.endswith(")"):
            clean_words.append(w[:2].upper() + w[2:])
            continue
        wl = w.lower()
        if wl in _ACRONYMS:
            clean_words.append(wl.upper())
        elif wl in ("of", "in", "by", "for", "to", "per", "on", "at") and clean_words:
            clean_words.append(wl)
        elif w.isupper() and len(w) > 1:
            clean_words.append(w)
        else:
            clean_words.append(w[:1].upper() + w[1:].lower())

    res = " ".join(clean_words)
    # Deduplicate repeated words like 'Tender Tender'
    res = re.sub(r"\b(\w+)\s+\1\b", r"\1", res, flags=re.IGNORECASE)
    return res


def format_business_chart_title(
    metric_col: Optional[str],
    dim_col: Optional[str],
    agg: str = "sum",
    chart_type: str = "bar",
    domain_id: Optional[str] = None,
) -> str:
    """Generate a clean, business-friendly chart title without raw paths.
    
    Examples:
        'Average Tender Duration by Procurement Category'
        'Average Number of Bidders by Contract Type'
        'Number of Tenders by Procurement Category'
        'Average Number of Bidders Over Time'
        'Procurement Category Share of Total Tenders'
    """
    pretty_dim = format_column_label(dim_col) if dim_col else ""
    pretty_metric = format_column_label(metric_col) if metric_col else ""

    is_tender_domain = (
        domain_id == "government_procurement"
        or "tender" in (dim_col or "").lower()
        or "tender" in (metric_col or "").lower()
        or "ocid" in (dim_col or "").lower()
    )

    if not metric_col or metric_col == dim_col:
        # Categorical frequency breakdown
        if is_tender_domain:
            return f"Number of Tenders by {pretty_dim}"
        return f"Number of Records by {pretty_dim}"

    agg_lower = agg.lower()
    
    # Check if metric inherently implies average or count or total
    metric_lower = pretty_metric.lower()
    if metric_lower.startswith("average ") or metric_lower.startswith("mean "):
        metric_str = pretty_metric
    elif agg_lower in ("mean", "avg", "average"):
        metric_str = f"Average {pretty_metric}"
    elif agg_lower == "count":
        metric_str = f"Count of {pretty_metric}"
    else:
        metric_str = pretty_metric

    if chart_type == "line" or any(kw in (dim_col or "").lower() for kw in ("date", "time", "year")):
        return f"{metric_str} Over Time"

    clean_metric_title = re.sub(r"\s*\([^)]*\)$", "", metric_str)

    if chart_type == "pie":
        if is_tender_domain:
            return f"{pretty_dim} Share of Total Tenders"
        return f"{pretty_dim} Share of Total {clean_metric_title}"

    return f"{clean_metric_title} by {pretty_dim}"


def format_chart_description(
    metric_col: Optional[str],
    dim_col: Optional[str],
    agg: str = "sum",
    chart_type: str = "bar",
    domain_id: Optional[str] = None,
    coverage_note: str = "",
) -> str:
    """Generate an analytical question-driven or explanatory description for charts."""
    pretty_dim = format_column_label(dim_col) if dim_col else ""
    pretty_metric = format_column_label(metric_col) if metric_col else ""
    
    agg_lower = agg.lower()
    is_tender_domain = (
        domain_id == "government_procurement"
        or "tender" in (dim_col or "").lower()
        or "tender" in (metric_col or "").lower()
    )

    if chart_type == "histogram":
        return (
            f"Shows how frequently observations fall within different '{pretty_metric}' ranges, "
            f"identifying typical values, concentration, and outliers."
        )

    if chart_type == "scatter":
        return f"Evaluates the empirical relationship and dispersion between '{pretty_dim}' and '{pretty_metric}'."

    if not metric_col or metric_col == dim_col:
        subject = "tenders" if is_tender_domain else "records"
        return f"Compares the number of {subject} across distinct '{pretty_dim}' categories.{coverage_note}"

    if chart_type == "pie":
        return f"Displays the proportional share of total {pretty_metric} contributed by each '{pretty_dim}'.{coverage_note}"

    if chart_type == "line" or any(kw in (dim_col or "").lower() for kw in ("date", "time", "year")):
        agg_label = "average" if agg_lower in ("mean", "avg", "average") else "total"
        return f"Tracks the historical trajectory of {agg_label} {pretty_metric} over time."

    if agg_lower in ("mean", "avg", "average"):
        return f"Compares the average '{pretty_metric}' across distinct '{pretty_dim}' groups.{coverage_note}"
    
    return f"Compares total '{pretty_metric}' grouped by '{pretty_dim}'.{coverage_note}"


# --- Unit Detection & Value Formatting ---------------------------------------

_CURRENCY_KEYWORDS = (
    "price", "cost", "revenue", "sales", "profit", "amount", "budget", "salary",
    "wage", "fee", "charge", "spend", "expense", "income", "tender_value",
    "contract_value", "award_value", "freight_value", "freight_cost", "aov", "mrr",
    "arr", "arpu", "acv", "deal_value", "cpc", "ad_spend", "total_spend", "tax",
)

_PERCENTAGE_KEYWORDS = (
    "discount", "discount_rate", "rate", "pct", "percent", "percentage", "margin",
    "profit_margin", "win_rate", "churn", "churn_rate", "bounce_rate", "tax_rate",
    "roi", "ctr", "click_through_rate", "conversion_rate", "packet_loss", "cpu_utilization",
    "cpu_pct", "attrition_rate", "oee", "defects_pct", "otif_rate", "yield_rate",
    "engagement_rate", "cap_rate", "share", "ratio",
)

_QUANTITY_KEYWORDS = (
    "quantity", "qty", "units_sold", "units", "volume", "stock", "inventory",
    "headcount", "runs", "wickets", "pageviews", "views", "clicks", "impressions",
    "bugs", "vulnerabilities", "followers", "likes", "shares", "reactions", "violations",
    "story_points", "points", "goals", "baskets", "assists", "deliveries",
)

_DURATION_KEYWORDS = (
    "duration", "duration_in_days", "aging", "aging_days", "order_aging", "lead_time",
    "transit_time", "resolution_time", "turnaround", "cycle_time", "session_duration",
    "tenure", "days_on_market", "mttd", "latency", "ping_ms", "hours_spent", "days_to",
)

_COUNT_KEYWORDS = (
    "order_id", "orders", "tender_id", "tenders", "bidders", "tenderers", "lead_id",
    "leads", "patient_id", "patients", "student_id", "students", "employee_id",
    "employees", "transaction_id", "transactions", "ticket_id", "tickets", "records",
    "shipment_id", "shipments", "properties", "deals",
)


def detect_column_unit(
    column_name: Optional[str],
    series: Optional[Any] = None,
    domain_id: Optional[str] = None,
    dataset_currency: Optional[str] = None,
    series_or_samples: Optional[Any] = None,
) -> Tuple[str, str, Optional[str]]:
    """Detect the semantic unit label, semantic type, and currency symbol for any metric/column.
    
    Returns:
        (unit_label, semantic_type, currency_symbol)
        
    Examples:
        "profit" -> ("₹", "currency", "₹") or ("$", "currency", "$")
        "units_sold" -> ("units", "quantity", None)
        "discount" -> ("%", "percentage", None)
        "aging_days" -> ("days", "duration", None)
        "total_records" -> ("records", "count", None)
    """
    if not column_name:
        return ("units", "number", None)

    col_clean = str(column_name).lower().strip().replace("\\", "/")
    col_tail = col_clean.split("/")[-1].replace("-", "_").replace(" ", "_")
    tokens = set(re.findall(r"[a-z0-9]+", col_clean))

    # 1. Currency
    # Check specific currency code in column name
    if any(k in col_clean for k in ("_inr", "inr_", "in_inr", "rs_", "_rs", "rupee")) or "inr" in tokens:
        return ("₹", "currency", "₹")
    if any(k in col_clean for k in ("_usd", "usd_", "in_usd", "(usd)")) or "usd" in tokens:
        return ("$", "currency", "$")
    if any(k in col_clean for k in ("_eur", "eur_", "in_eur", "(eur)")) or "eur" in tokens:
        return ("€", "currency", "€")
    if any(k in col_clean for k in ("_gbp", "gbp_", "in_gbp", "(gbp)")) or "gbp" in tokens:
        return ("£", "currency", "£")

    if any(k in tokens for k in _CURRENCY_KEYWORDS) or any(k in col_tail for k in ("price", "cost", "revenue", "sales", "profit", "amount", "budget", "salary", "spend", "expense", "tender_value", "contract_value", "freight_value", "freight_cost", "total_spend")):
        sym = dataset_currency or "₹"
        return (sym, "currency", sym)

    # 2. Duration / Time first (so duration doesn't trigger ratio)
    if "ms" in tokens or "latency" in tokens or "ping_ms" in col_clean or "response_time_ms" in col_clean:
        return ("ms", "duration", None)
    if "sec" in tokens or "seconds" in tokens or "duration_seconds" in col_clean:
        return ("s", "duration", None)
    if "min" in tokens or "mins" in tokens or "minutes" in col_clean:
        return ("mins", "duration", None)
    if "hour" in tokens or "hours" in tokens or "hrs" in col_clean:
        return ("hrs", "duration", None)
    if "day" in tokens or "days" in tokens or "aging" in tokens or "duration" in tokens or "lead_time" in col_clean or "tenure_days" in col_clean or "delivery_days" in col_clean:
        return ("days", "duration", None)
    if "year" in tokens or "years" in tokens or "tenure" in tokens or "tenure_months" in col_clean:
        return ("yrs", "duration", None)

    # 3. Percentage & Rate
    if any(k in tokens for k in ("discount", "rate", "pct", "percent", "percentage", "margin", "churn", "roi", "ctr", "oee", "yield", "ratio", "share")) or any(k in col_tail for k in ("discount", "discount_rate", "rate", "pct", "percent", "margin", "churn")):
        return ("%", "percentage", None)

    # 4. ID / Primary Key / Record count
    if col_tail.endswith("_id") or col_tail == "id" or "record" in tokens or "records" in tokens:
        return ("records", "count", None)

    # 5. Domain-specific counts & metrics
    if "patient" in tokens or "patients" in tokens:
        return ("patients", "count", None)
    if "student" in tokens or "students" in tokens:
        return ("students", "count", None)
    if "employee" in tokens or "employees" in tokens or "headcount" in tokens:
        return ("employees", "count", None)
    if "run" in tokens or "runs" in tokens:
        return ("runs", "quantity", None)
    if "wicket" in tokens or "wickets" in tokens:
        return ("wickets", "quantity", None)
    if "view" in tokens or "views" in tokens or "pageview" in tokens:
        return ("views", "quantity", None)
    if "click" in tokens or "clicks" in tokens:
        return ("clicks", "quantity", None)
    if "stream" in tokens or "streams" in tokens:
        return ("streams", "quantity", None)
    if "bidder" in tokens or "bidders" in tokens or "tenderer" in tokens or "tenderers" in tokens:
        return ("bidders", "count", None)
    if "tender" in tokens or "tenders" in tokens:
        return ("tenders", "count", None)
    if "order" in tokens or "orders" in tokens:
        return ("orders", "count", None)
    if "deal" in tokens or "deals" in tokens:
        return ("deals", "count", None)
    if "lead" in tokens or "leads" in tokens:
        return ("leads", "count", None)

    # 6. Quantity & Count
    if any(k in tokens for k in ("quantity", "qty", "units", "volume", "stock", "inventory", "points", "goals", "baskets")):
        return ("units", "quantity", None)
    if any(k in tokens for k in ("transactions", "tickets", "shipments", "properties")):
        return ("records", "count", None)

    # 6. Score / Rating / Area
    if "sqft" in tokens or "sq_ft" in col_tail:
        return ("sqft", "number", None)
    if "rating" in tokens:
        return ("/ 10", "score", None)
    if "score" in tokens:
        return ("pts", "score", None)

    return ("units", "number", None)


def format_metric_display(
    value: Any,
    unit: Optional[str] = None,
    semantic_type: Optional[str] = None,
    currency_symbol: Optional[str] = None,
    compact: bool = False,
    precision: int = 2,
) -> str:
    """Format any numeric metric value with its unit and correct notation.
    
    Examples:
        format_metric_display(70.41, unit="₹", semantic_type="currency") -> "₹70.41"
        format_metric_display(767147, unit="₹", semantic_type="currency") -> "₹767,147"
        format_metric_display(2.5, unit="units", semantic_type="quantity") -> "2.5 units"
        format_metric_display(0.3, unit="%", semantic_type="percentage") -> "0.3%"
        format_metric_display(30, unit="%", semantic_type="percentage") -> "30%"
        format_metric_display(150, unit="records", semantic_type="count") -> "150 records"
    """
    if value is None:
        return "N/A"

    try:
        n = float(value)
    except (ValueError, TypeError):
        return str(value)

    if math.isnan(n) or math.isinf(n):
        return "N/A"

    sym = currency_symbol or (unit if unit in ("₹", "$", "€", "£", "¥") else "")

    # 1. Currency
    if semantic_type == "currency" or sym in ("₹", "$", "€", "£", "¥"):
        currency_sym = sym or "₹"
        if compact:
            abs_n = abs(n)
            if abs_n >= 1_000_000_000:
                return f"{currency_sym}{n / 1_000_000_000:.2f}B"
            if abs_n >= 1_000_000:
                return f"{currency_sym}{n / 1_000_000:.2f}M"
            if abs_n >= 1_000:
                return f"{currency_sym}{n:,.0f}"
        if n % 1 == 0 and abs(n) >= 100:
            return f"{currency_sym}{int(n):,}"
        return f"{currency_sym}{n:,.{precision}f}"

    # 2. Percentage / Rate
    if semantic_type == "percentage" or unit == "%":
        # Do not multiply blindly: preserve the raw value and display with %
        if n % 1 == 0:
            return f"{int(n)}%"
        return f"{n:.{precision}f}%"

    # 3. Count / Integer
    if semantic_type == "count" or unit in ("records", "orders", "tenders", "bidders", "items", "runs", "wickets", "views", "clicks"):
        u_label = f" {unit}" if unit else ""
        if compact:
            abs_n = abs(n)
            if abs_n >= 1_000_000:
                return f"{n / 1_000_000:.1f}M{u_label}"
            if abs_n >= 1_000:
                return f"{n / 1_000:.1f}K{u_label}"
        if n % 1 == 0:
            return f"{int(n):,}{u_label}"
        return f"{n:,.{precision}f}{u_label}"

    # 4. Quantity
    if semantic_type == "quantity" or (semantic_type != "number" and unit in ("qty", "volume", "stock")):
        u_label = f" {unit}" if unit else " units"
        if n % 1 == 0:
            return f"{int(n):,}{u_label}"
        return f"{n:,.{precision}f}{u_label}"

    # 5. Duration
    if semantic_type == "duration" or unit in ("days", "hrs", "mins", "s", "ms", "yrs"):
        u_label = f" {unit}" if unit else ""
        if n % 1 == 0:
            return f"{int(n):,}{u_label}"
        return f"{n:,.{precision}f}{u_label}"

    # 6. Score / Rating
    if semantic_type == "score" or (unit and (unit.startswith("/") or unit == "pts")):
        u_label = f" {unit}" if unit else ""
        return f"{n:.{precision}f}{u_label}"

    # 7. General / Neutral numeric
    u_label = f" {unit}" if unit and unit not in ("units", "") and semantic_type != "number" else ""
    if compact and abs(n) >= 1000:
        if abs(n) >= 1_000_000:
            return f"{n / 1_000_000:.2f}M{u_label}"
        return f"{n / 1_000:.1f}K{u_label}"
    if n % 1 == 0 and abs(n) >= 100:
        return f"{int(n):,}{u_label}"
    return f"{n:,.{precision}f}{u_label}".rstrip("0").rstrip(".") if "." in f"{n:.{precision}f}" and n % 1 == 0 else f"{n:,.{precision}f}{u_label}"


def build_metric_tooltip_details(
    metric_name: str,
    value: Any,
    unit: Optional[str] = None,
    aggregation: Optional[str] = None,
    source_column: Optional[str] = None,
    semantic_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate structured tooltip details for any metric card."""
    formatted = format_metric_display(value, unit=unit, semantic_type=semantic_type)
    full_formatted = format_metric_display(value, unit=unit, semantic_type=semantic_type, compact=False, precision=4)
    
    agg_method = aggregation.upper() if aggregation else "SUM"
    rule_desc = (
        f"Currency monetary amount formatted with symbol '{unit}'" if semantic_type == "currency"
        else f"Percentage rate formatted with '{unit}'" if semantic_type == "percentage"
        else f"Quantity volume formatted with '{unit}'" if semantic_type == "quantity"
        else f"Discrete observation count of records" if semantic_type == "count"
        else f"Time duration measured in {unit}" if semantic_type == "duration"
        else f"Standard numeric aggregation ({agg_method})"
    )

    return {
        "metric_name": metric_name,
        "value": value,
        "formatted_value": formatted,
        "full_value": full_formatted,
        "unit": unit or "units",
        "aggregation_method": agg_method,
        "source_column": source_column or metric_name,
        "semantic_type": semantic_type or "number",
        "formatting_rule": rule_desc,
    }

