import { useEffect, useMemo, useState } from "react"
import { AlertCircle, ChevronLeft, ChevronRight, Loader2, RotateCcw } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ChartRenderer } from "@/components/charts/ChartRenderer"
import { KpiRow } from "@/components/dashboard/KpiRow"
import { fetchDrilldown, type DrilldownFilter } from "@/lib/datasetApi"
import { buildQuickRanges, filterByDateRange, getDateBounds } from "@/lib/dateRange"
import type { ChartSpec, DrilldownResponse } from "@/types/dataset"

const CHART_TYPE_LABEL: Record<ChartSpec["chart_type"], string> = {
  bar: "Bar",
  line: "Line",
  pie: "Pie",
  histogram: "Histogram",
  scatter: "Scatter",
}

type DrillState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: DrilldownResponse }
  | { status: "error"; message: string }

export function ChartDetailModal({
  chart,
  datasetId,
  datasetName,
  open,
  onOpenChange,
}: {
  chart: ChartSpec | null
  datasetId: string
  datasetName: string
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const [start, setStart] = useState<string>("")
  const [end, setEnd] = useState<string>("")
  // Empty stack = showing the overview chart as-is. Each entry is one
  // drilled level (dimension + selected value) -- arbitrary depth, fully
  // generic: works for whatever dimension/value the backend reports at
  // each level, never hard-coded to Product/Category/etc.
  const [drillStack, setDrillStack] = useState<DrilldownFilter[]>([])
  const [drillState, setDrillState] = useState<DrillState>({ status: "idle" })

  const isDrilled = drillStack.length > 0

  useEffect(() => {
    if (!open || drillStack.length === 0) return
    let cancelled = false
    setDrillState({ status: "loading" })
    fetchDrilldown(datasetId, drillStack)
      .then((data) => {
        if (!cancelled) setDrillState({ status: "success", data })
      })
      .catch((err) => {
        if (!cancelled) {
          setDrillState({
            status: "error",
            message: err instanceof Error ? err.message : "Something went wrong.",
          })
        }
      })
    return () => {
      cancelled = true
    }
  }, [open, drillStack, datasetId])

  // The date-bucketed series currently on screen -- the overview chart's
  // own data when not drilled (only meaningful for a line chart), or the
  // current drill level's trend chart once drilled. Date-range state is
  // shared across every level so switching drill depth doesn't reset it.
  const activeDateSeries: ChartSpec | null = useMemo(() => {
    if (isDrilled) {
      return drillState.status === "success" ? drillState.data.trend_chart : null
    }
    return chart && chart.chart_type === "line" ? chart : null
  }, [isDrilled, drillState, chart])

  const bounds = useMemo(
    () => (activeDateSeries ? getDateBounds(activeDateSeries.data) : null),
    [activeDateSeries]
  )
  const quickRanges = useMemo(() => (bounds ? buildQuickRanges(bounds) : []), [bounds])

  const filteredActiveData = useMemo(() => {
    if (!activeDateSeries) return []
    if (!bounds) return activeDateSeries.data
    return filterByDateRange(activeDateSeries.data, start || null, end || null)
  }, [activeDateSeries, bounds, start, end])

  if (!chart) return null

  const resetRange = () => {
    setStart("")
    setEnd("")
  }

  const resetDrill = () => {
    setDrillStack([])
    setDrillState({ status: "idle" })
  }

  const goToLevel = (levelIndex: number) => {
    // levelIndex === -1 means "Overview" (the root, i.e. clear the stack).
    setDrillStack((prev) => prev.slice(0, levelIndex + 1))
    setDrillState({ status: "idle" })
  }

  const goBack = () => goToLevel(drillStack.length - 2)

  const handleOpenChange = (next: boolean) => {
    if (!next) {
      resetRange()
      resetDrill()
    }
    onOpenChange(next)
  }

  // Drilling from the overview chart: start a fresh stack.
  const handleOverviewCategoryClick = (rawValue: string) => {
    if (!chart.dimension_column) return
    setDrillStack([{ dimension: chart.dimension_column, value: rawValue }])
    setDrillState({ status: "idle" })
  }

  // Drilling further from the current level's secondary breakdown chart:
  // push one more level onto the existing stack.
  const handleSecondaryCategoryClick = (rawValue: string) => {
    if (drillState.status !== "success" || !drillState.data.secondary_dimension) return
    setDrillStack((prev) => [
      ...prev,
      { dimension: drillState.data.secondary_dimension as string, value: rawValue },
    ])
    setDrillState({ status: "idle" })
  }

  const currentLevel = drillStack[drillStack.length - 1]
  const currentLabel =
    drillState.status === "success" ? drillState.data.dimension_label : currentLevel?.dimension

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="flex h-[90vh] max-h-[90vh] w-[95vw] max-w-[1400px] flex-col overflow-hidden p-0">
        <DialogHeader className="shrink-0 border-b px-6 pt-5 pb-4">
          {/* Breadcrumb -- one segment per drilled level, fully dynamic. */}
          <div className="flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground">
            <button
              type="button"
              onClick={() => goToLevel(-1)}
              className={isDrilled ? "hover:text-foreground hover:underline" : "text-foreground"}
            >
              Overview
            </button>
            {drillStack.map((level, i) => {
              const isLast = i === drillStack.length - 1
              return (
                <span key={i} className="flex items-center gap-1.5">
                  <ChevronRight className="h-3 w-3" />
                  {!isLast ? (
                    <button
                      type="button"
                      onClick={() => goToLevel(i)}
                      className="hover:text-foreground hover:underline"
                    >
                      {level.value}
                    </button>
                  ) : (
                    <span className="font-medium text-foreground">{level.value}</span>
                  )}
                </span>
              )
            })}
          </div>

          <div className="flex items-start justify-between gap-3 pr-8">
            <div className="flex items-start gap-2">
              {isDrilled && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="mt-0.5 h-6 w-6 shrink-0"
                  onClick={goBack}
                  aria-label="Back one level"
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
              )}
              <div>
                <DialogTitle>
                  {isDrilled ? `${currentLevel.value} — Analysis` : chart.title}
                </DialogTitle>
                <DialogDescription className="mt-1">
                  {isDrilled
                    ? `Detailed performance for ${currentLabel} = "${currentLevel.value}".`
                    : chart.description}
                </DialogDescription>
              </div>
            </div>
            {!isDrilled && (
              <Badge variant="secondary" className="shrink-0">
                {CHART_TYPE_LABEL[chart.chart_type]}
              </Badge>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
            <span>Dataset: {datasetName}</span>
            {!isDrilled && (
              <>
                <span>X: {chart.x_label}</span>
                <span>Y: {chart.y_label}</span>
              </>
            )}
          </div>
        </DialogHeader>

        {/* Date range controls -- shown whenever a date-bucketed series is
            active, at any drill depth. */}
        {bounds && (
          <div className="flex shrink-0 flex-wrap items-center gap-3 border-b px-6 py-3">
            <div className="flex items-center gap-2">
              <label className="text-xs text-muted-foreground" htmlFor="chart-start-date">
                Start
              </label>
              <Input
                id="chart-start-date"
                type="date"
                className="h-8 w-36"
                min={bounds.min}
                max={end || bounds.max}
                value={start}
                onChange={(e) => setStart(e.target.value)}
              />
            </div>
            <div className="flex items-center gap-2">
              <label className="text-xs text-muted-foreground" htmlFor="chart-end-date">
                End
              </label>
              <Input
                id="chart-end-date"
                type="date"
                className="h-8 w-36"
                min={start || bounds.min}
                max={bounds.max}
                value={end}
                onChange={(e) => setEnd(e.target.value)}
              />
            </div>
            <div className="flex flex-wrap items-center gap-1.5">
              {quickRanges.map((r) => (
                <Button
                  key={r.label}
                  variant="outline"
                  size="sm"
                  className="h-7 px-2 text-xs"
                  onClick={() => {
                    setStart(r.start)
                    setEnd(bounds.max)
                  }}
                >
                  {r.label}
                </Button>
              ))}
              <Button variant="outline" size="sm" className="h-7 px-2 text-xs" onClick={resetRange}>
                All
              </Button>
              {(start || end) && (
                <Button variant="ghost" size="sm" className="h-7 px-2 text-xs" onClick={resetRange}>
                  <RotateCcw className="h-3 w-3" />
                  Reset
                </Button>
              )}
            </div>
            {(start || end) && (
              <span className="ml-auto text-xs text-muted-foreground">
                Showing {start || bounds.min} to {end || bounds.max}
              </span>
            )}
          </div>
        )}

        {/* Scrollable body */}
        <div className="flex-1 overflow-y-auto px-6 py-5">
          {!isDrilled ? (
            <div className="space-y-4">
              {chart.chart_type === "bar" && chart.dimension_column && (
                <p className="text-xs text-muted-foreground">
                  Click a bar to see a detailed breakdown for that value.
                </p>
              )}
              <div key={`${start}-${end}`} className="animate-chart-in">
                <ChartRenderer
                  chart={
                    bounds
                      ? { ...chart, data: filteredActiveData }
                      : chart
                  }
                  height={420}
                  variant="detail"
                  onCategoryClick={
                    chart.chart_type === "bar" && chart.dimension_column
                      ? handleOverviewCategoryClick
                      : undefined
                  }
                />
              </div>
              {bounds && filteredActiveData.length === 0 && (
                <div className="flex h-24 items-center justify-center rounded-md border border-dashed text-sm text-muted-foreground">
                  No data in the selected date range.
                </div>
              )}
            </div>
          ) : (
            <DrilldownView
              state={drillState}
              activeDateSeries={activeDateSeries}
              filteredTrendData={filteredActiveData}
              hasDateFilter={Boolean(start || end)}
              rangeKey={`${start}-${end}`}
              onSecondaryCategoryClick={handleSecondaryCategoryClick}
            />
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}

function DrilldownView({
  state,
  activeDateSeries,
  filteredTrendData,
  hasDateFilter,
  rangeKey,
  onSecondaryCategoryClick,
}: {
  state: DrillState
  activeDateSeries: ChartSpec | null
  filteredTrendData: ReturnType<typeof filterByDateRange>
  hasDateFilter: boolean
  rangeKey: string
  onSecondaryCategoryClick: (rawValue: string) => void
}) {
  if (state.status === "idle" || state.status === "loading") {
    return (
      <div className="flex flex-col items-center justify-center gap-3 py-20 text-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        <p className="text-sm text-muted-foreground">Loading detailed breakdown…</p>
      </div>
    )
  }

  if (state.status === "error") {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Couldn't load this breakdown</AlertTitle>
        <AlertDescription>{state.message}</AlertDescription>
      </Alert>
    )
  }

  const { data } = state
  const trend = activeDateSeries
  // The secondary breakdown is itself drillable into a further level only
  // when the backend reports a further meaningful dimension -- otherwise
  // it's shown as a plain (non-clickable) chart, since drilling into a
  // dead end isn't useful.
  const secondaryIsDrillable = Boolean(data.secondary_dimension) && Boolean(data.secondary_chart)

  return (
    <div className="animate-chart-in space-y-6">
      <KpiRow kpis={data.kpis} />
      <p className="text-xs text-muted-foreground">
        {data.row_count.toLocaleString()} matching rows.
      </p>

      {/* The child breakdown (what's actually inside this selection) is
          the main analytical content at this level -- "which products
          make up Fashion" answers a real question; the aggregate KPIs
          above only answer "how much did Fashion sell". It gets the wide
          primary slot; the trend line is the smaller companion. */}
      <div className="grid gap-4 lg:grid-cols-3">
        {data.secondary_chart && (
          <div className={trend ? "lg:col-span-2 rounded-lg border p-4" : "lg:col-span-3 rounded-lg border p-4"}>
            <p className="mb-1 text-sm font-medium">{data.secondary_chart.title}</p>
            {secondaryIsDrillable && (
              <p className="mb-2 text-[11px] text-muted-foreground">
                Click a bar to drill in further.
              </p>
            )}
            <ChartRenderer
              chart={data.secondary_chart}
              height={secondaryIsDrillable ? 340 : 300}
              variant="detail"
              onCategoryClick={secondaryIsDrillable ? onSecondaryCategoryClick : undefined}
            />
          </div>
        )}
        {trend && (
          <div className={data.secondary_chart ? "lg:col-span-1 rounded-lg border p-4" : "lg:col-span-3 rounded-lg border p-4"}>
            <p className="mb-2 text-sm font-medium">{trend.title}</p>
            <div key={rangeKey} className="animate-chart-in">
              <ChartRenderer
                chart={hasDateFilter ? { ...trend, data: filteredTrendData } : trend}
                height={data.secondary_chart ? 260 : 300}
                variant="detail"
              />
            </div>
            {hasDateFilter && filteredTrendData.length === 0 && (
              <div className="mt-2 flex h-16 items-center justify-center rounded-md border border-dashed text-xs text-muted-foreground">
                No data in the selected date range.
              </div>
            )}
          </div>
        )}
        {!trend && !data.secondary_chart && (
          <div className="lg:col-span-3 flex h-32 items-center justify-center rounded-md border border-dashed text-sm text-muted-foreground">
            No further breakdown is available for this selection.
          </div>
        )}
      </div>
    </div>
  )
}
