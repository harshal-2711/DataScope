"""Centralized Human-Readable Column Label and Title Formatter.

Converts raw, nested, and flattened column paths (e.g. OCDS paths like
'tender/tender Period/duration In Days' or 'tender/numberOfTenderers')
into professional, clean business labels across all chart titles, axes,
legends, tooltips, and data previews.
"""
from __future__ import annotations

import re
from typing import Optional

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
