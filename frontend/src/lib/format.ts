/** Formatting helpers for chart axes/tooltips — avoids scientific notation
 * (1e+03) and renders large numbers as readable, comma-grouped or compact
 * (1K/1.2K/125K/1.5M) values depending on available space. */

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
