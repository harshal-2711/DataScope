/** Formatting helpers for chart axes, tooltips, and column labels —
 * avoids raw technical paths (tender/mainProcurementCategory) and renders
 * human-readable business labels, comma-grouped numbers, and clean dates.
 */

const FULL_FORMATTER = new Intl.NumberFormat("en-US", {
  maximumFractionDigits: 2,
})

const COMPACT_FORMATTER = new Intl.NumberFormat("en-US", {
  notation: "compact",
  maximumFractionDigits: 1,
})

/** Full, comma-grouped number for tooltips: 125000 -> "125,000". */
export function formatNumberFull(value: unknown): string {
  const n = toFiniteNumber(value)
  if (n === null) return String(value ?? "")
  return FULL_FORMATTER.format(n)
}

/** Compact axis-label number: 125000 -> "125K", 1500000 -> "1.5M". */
export function formatNumberCompact(value: unknown): string {
  const n = toFiniteNumber(value)
  if (n === null) return String(value ?? "")
  if (Math.abs(n) < 1000) return FULL_FORMATTER.format(n)
  return COMPACT_FORMATTER.format(n)
}

function toFiniteNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value
  if (typeof value === "string" && value.trim() !== "" && Number.isFinite(Number(value))) {
    return Number(value)
  }
  return null
}

/** ISO date/timestamp -> "2018-01-21" (drops any time-of-day component). */
export function formatDateLabel(value: unknown): string {
  if (typeof value !== "string") return String(value ?? "")
  const isoDateMatch = value.match(/^(\d{4}-\d{2}-\d{2})/)
  if (isoDateMatch) return isoDateMatch[1]
  const parsed = new Date(value)
  if (!Number.isNaN(parsed.getTime())) {
    return parsed.toISOString().slice(0, 10)
  }
  return value
}

/** True if every data point's `x` looks like an ISO date/timestamp string
 * ("2018-01-21" or "2018-01-21T00:00:00.000"). Used to decide whether a
 * chart is eligible for date-range filtering. */
export function looksLikeDateSeries(values: unknown[]): boolean {
  if (values.length === 0) return false
  const isoDate = /^\d{4}-\d{2}-\d{2}/
  return values.every((v) => typeof v === "string" && isoDate.test(v))
}

const CANONICAL_OVERRIDES: Record<string, string> = {
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
  "order_id": "Order ID",
  "order_date": "Order Date",
  "product_name": "Product Name",
  "unit_price": "Unit Price",
  "total_spend": "Total Spend",
}

const ACRONYMS = new Set(["id", "ocid", "sku", "kpi", "gpa", "ipl", "ctr", "cpc", "mrr", "arr", "usd", "eur", "gbp", "inr", "fy", "rfp", "rfq", "pk", "fk", "nhm", "pwd"])
const GENERIC_TAILS = new Set(["type", "title", "name", "amount", "date", "status", "id", "code", "value", "description", "category", "count", "rate"])

/** Format any raw, nested, or flattened column path into a human-readable business label. */
export function formatColumnLabel(columnName?: string | null): string {
  if (!columnName || typeof columnName !== "string") return String(columnName ?? "")

  const rawClean = columnName.trim()
  const lowered = rawClean.toLowerCase().replace(/\\/g, "/")

  if (CANONICAL_OVERRIDES[lowered]) {
    return CANONICAL_OVERRIDES[lowered]
  }

  const dupMatch = rawClean.match(/[._](\d+)$/)
  const dupSuffixStr = dupMatch ? ` (${dupMatch[1]})` : ""
  const cleanedBase = rawClean.replace(/[._]\d+$/, "")
  const baseLowered = cleanedBase.toLowerCase().replace(/\\/g, "/")

  if (CANONICAL_OVERRIDES[baseLowered]) {
    return `${CANONICAL_OVERRIDES[baseLowered]}${dupSuffixStr}`
  }

  if (lowered.includes("/") || lowered.includes(".")) {
    const parts = cleanedBase.split(/[/.]/).map((p) => p.trim()).filter(Boolean)
    if (parts.length > 0) {
      const tailLower = parts[parts.length - 1].toLowerCase()
      if (CANONICAL_OVERRIDES[tailLower]) {
        return `${CANONICAL_OVERRIDES[tailLower]}${dupSuffixStr}`
      }
      if (GENERIC_TAILS.has(tailLower) && parts.length >= 2) {
        const parent = parts[parts.length - 2]
        const tail = parts[parts.length - 1]
        const combined = `${parent}_${tail}`.toLowerCase()
        if (CANONICAL_OVERRIDES[combined]) {
          return `${CANONICAL_OVERRIDES[combined]}${dupSuffixStr}`
        }
        return `${prettifyWord(parent)} ${prettifyWord(tail)}${dupSuffixStr}`
      }
      return `${cleanSegment(parts[parts.length - 1])}${dupSuffixStr}`
    }
  }

  return cleanSegment(rawClean)
}

function prettifyWord(text: string): string {
  const spaced = text
    .replace(/(?<=[a-z0-9])(?=[A-Z])/g, " ")
    .replace(/(?<=[A-Z])(?=[A-Z][a-z])/g, " ")
    .replace(/[-_.]/g, " ")
    .trim()
  const words = spaced.split(/\s+/).filter(Boolean)
  return words
    .map((w) => {
      const wl = w.toLowerCase()
      if (ACRONYMS.has(wl)) return wl.toUpperCase()
      if (w === w.toUpperCase() && w.length > 1) return w
      return w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()
    })
    .join(" ")
}

function cleanSegment(segment: string): string {
  const lowered = segment.toLowerCase().trim()
  if (CANONICAL_OVERRIDES[lowered]) return CANONICAL_OVERRIDES[lowered]

  let spaced = segment
    .replace(/(?<=[a-z0-9])(?=[A-Z])/g, " ")
    .replace(/(?<=[A-Z])(?=[A-Z][a-z])/g, " ")
    .replace(/[-_./]/g, " ")
    .trim()

  spaced = spaced.replace(/\bin days\b/gi, "(Days)")
  spaced = spaced.replace(/\bin hours\b/gi, "(Hours)")
  spaced = spaced.replace(/\bin usd\b/gi, "(USD)")

  const words = spaced.split(/\s+/).filter(Boolean)
  const cleanWords: string[] = []
  for (const w of words) {
    if (w.startsWith("(") && w.endsWith(")")) {
      cleanWords.push(w.charAt(0) + w.charAt(1).toUpperCase() + w.slice(2))
      continue
    }
    const wl = w.toLowerCase()
    if (ACRONYMS.has(wl)) {
      cleanWords.push(wl.toUpperCase())
    } else if (["of", "in", "by", "for", "to", "per", "on", "at"].includes(wl) && cleanWords.length > 0) {
      cleanWords.push(wl)
    } else if (w === w.toUpperCase() && w.length > 1) {
      cleanWords.push(w)
    } else {
      cleanWords.push(w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    }
  }

  let res = cleanWords.join(" ")
  res = res.replace(/\b(\w+)\s+\1\b/gi, "$1")
  return res
}

/** Formats a business-friendly chart title, cleaning any raw column paths. */
export function formatBusinessTitle(title?: string | null): string {
  if (!title) return ""
  // If title contains technical paths with slashes
  if (title.includes("/") || title.includes("tender/")) {
    return title
      .split(" by ")
      .map((part) => {
        return part
          .split(" ")
          .map((word) => (word.includes("/") ? formatColumnLabel(word) : word))
          .join(" ")
      })
      .map((p) => formatColumnLabel(p))
      .join(" by ")
  }
  return title
}
