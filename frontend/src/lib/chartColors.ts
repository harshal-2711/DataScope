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
  sales: { text: "text-sky-400", bg: "bg-sky-400/10", hex: "#38bdf8" },
  profit: { text: "text-violet-400", bg: "bg-violet-400/10", hex: "#a78bfa" },
  quantity: { text: "text-indigo-400", bg: "bg-indigo-400/10", hex: "#818cf8" },
  discount: { text: "text-amber-400", bg: "bg-amber-400/10", hex: "#fbbf24" },
  orders: { text: "text-teal-400", bg: "bg-teal-400/10", hex: "#2dd4bf" },
  average: { text: "text-orange-400", bg: "bg-orange-400/10", hex: "#fb923c" },
  generic: { text: "text-slate-400", bg: "bg-slate-400/10", hex: "#94a3b8" },
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
 * breakdowns) where every bar/slice needs its own distinct color. */
export const CATEGORY_PALETTE = [
  "#38bdf8", // sky
  "#a78bfa", // violet
  "#2dd4bf", // teal
  "#fb923c", // orange
  "#f472b6", // pink
  "#facc15", // yellow
]
