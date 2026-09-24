export interface NavItem {
  label: string
  path: string
}

export const navItems: NavItem[] = [
  { label: "Overview", path: "/overview" },
  { label: "Dataset Upload", path: "/dataset" },
  { label: "Connect Data Source", path: "/connect-data" },
  { label: "Live Data Editor", path: "/data-management" },
  { label: "Explore", path: "/explore" },
  { label: "Trends", path: "/trends" },
  { label: "Forecast", path: "/forecast" },
  { label: "Risks", path: "/risks" },
  { label: "Competition", path: "/competition" },
  { label: "Recommendations", path: "/recommendations" },
  { label: "Reports", path: "/reports" },
  { label: "Settings", path: "/settings" },
]
