/** Semantic color assignment for KPI cards and chart accents.
 *
 * Colors are chosen by *business meaning* (sales/profit/quantity/...),
 * not by dataset -- the same "sales" color is used whether the column is
 * called "Sales", "Revenue", or "Total_Sales". Falls back to a neutral
 * palette for anything that doesn't match a recognized category, so this
 * never breaks on a generic, non-e-commerce dataset.
 */

export type ColorKind =
  | "sales"
  | "profit"
  | "quantity"
  | "discount"
  | "orders"
  | "average"
  | "generic"

interface ColorSet {
  /** Tailwind text color class, for icons/labels. */
  text: string
  /** Tailwind background color class, for icon chips. */
  bg: string
  /** Hex/CSS color, for chart fills (recharts needs a real color value). */
  hex: string
}

const COLOR_SETS: Record<ColorKind, ColorSet> = {
  sales: { text: "text-sky-300", bg: "bg-sky-400/15", hex: "#22d3ee" },
  profit: { text: "text-violet-300", bg: "bg-violet-400/15", hex: "#c084fc" },
  quantity: { text: "text-indigo-300", bg: "bg-indigo-400/15", hex: "#818cf8" },
  discount: { text: "text-amber-300", bg: "bg-amber-400/15", hex: "#fbbf24" },
  orders: { text: "text-emerald-300", bg: "bg-emerald-400/15", hex: "#34d399" },
  average: { text: "text-orange-300", bg: "bg-orange-400/15", hex: "#fb923c" },
  generic: { text: "text-slate-300", bg: "bg-slate-400/15", hex: "#94a3b8" },
}

export function getColorSet(kind: ColorKind): ColorSet {
  return COLOR_SETS[kind] ?? COLOR_SETS.generic
}

/** Best-effort guess at a chart's semantic "kind" from its title/labels,
 * for chart accent coloring (mirrors the backend's `_kpi_kind` heuristic
 * loosely -- doesn't need to be exact, just visually consistent). */
export function inferChartColorKind(text: string): ColorKind {
  const lowered = text.toLowerCase()
  if (/profit|margin|income|earning/.test(lowered)) return "profit"
  if (/sales|revenue/.test(lowered)) return "sales"
  if (/quantity|qty|units/.test(lowered)) return "quantity"
  if (/discount/.test(lowered)) return "discount"
  if (/order|row|count/.test(lowered)) return "orders"
  return "generic"
}

/** A small rotating palette for multi-series charts (pie slices, category
 * breakdowns) where every bar/slice needs its own distinct color.
 * A controlled "premium neon" set -- saturated enough to pop against the
 * dark theme without tipping into a childish/candy look. Assignment is
 * always by array position (chart data index), so it stays deterministic
 * across renders rather than randomized. */
export const CATEGORY_PALETTE = [
  "#22d3ee", // electric cyan
  "#a855f7", // vivid violet
  "#34d399", // neon emerald
  "#fb923c", // vibrant orange
  "#f472b6", // hot magenta/pink
  "#facc15", // vivid amber/yellow
  "#60a5fa", // electric blue
  "#2dd4bf", // bright teal
]

/** Muted, deliberately desaturated color for an "Other" aggregation bucket
 * -- must never be mistaken for one of the vivid real-category colors. */
export const OTHER_BUCKET_COLOR = "#64748b"
