import type { ChartDataPoint } from "@/types/dataset"

export interface DateBounds {
  min: string // ISO date, e.g. "2018-01-01"
  max: string
}

/** Min/max ISO date across a series whose `x` values are date strings. */
export function getDateBounds(data: ChartDataPoint[]): DateBounds | null {
  const dates = data
    .map((d) => (typeof d.x === "string" ? d.x.slice(0, 10) : null))
    .filter((d): d is string => d !== null)
    .sort()
  if (dates.length === 0) return null
  return { min: dates[0], max: dates[dates.length - 1] }
}

/** Filter a date-keyed series to points within [start, end] inclusive.
 * start/end are ISO date strings ("2018-03-01"); omit either to leave
 * that side unbounded. */
export function filterByDateRange(
  data: ChartDataPoint[],
  start: string | null,
  end: string | null
): ChartDataPoint[] {
  if (!start && !end) return data
  return data.filter((d) => {
    if (typeof d.x !== "string") return true
    const day = d.x.slice(0, 10)
    if (start && day < start) return false
    if (end && day > end) return false
    return true
  })
}

export interface QuickRange {
  label: string
  start: string
}

/** Quick range buttons scaled to the dataset's own span — e.g. don't offer
 * "6M" for a dataset that only covers 10 days. `end` is always the
 * dataset's max date, so ranges are always "last N ending at the most
 * recent data point", not the calendar's current date. */
export function buildQuickRanges(bounds: DateBounds): QuickRange[] {
  const end = new Date(bounds.max)
  const start = new Date(bounds.min)
  const spanDays = Math.round((end.getTime() - start.getTime()) / 86_400_000)

  const candidates: { label: string; days: number }[] = [
    { label: "7D", days: 7 },
    { label: "30D", days: 30 },
    { label: "3M", days: 90 },
    { label: "6M", days: 182 },
  ]

  const ranges: QuickRange[] = candidates
    .filter((c) => c.days < spanDays)
    .map((c) => {
      const d = new Date(end)
      d.setDate(d.getDate() - c.days)
      const clamped = d < start ? start : d
      return { label: c.label, start: clamped.toISOString().slice(0, 10) }
    })

  // Year-to-date, only meaningful if the dataset's latest point and its
  // Jan 1 both actually fall within the data.
  const yearStart = `${end.getFullYear()}-01-01`
  if (yearStart > bounds.min && yearStart < bounds.max) {
    ranges.push({ label: "YTD", start: yearStart })
  }

  return ranges
}
