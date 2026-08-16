export interface NavItem {
  label: string
  path: string
}

export const navItems: NavItem[] = [
  { label: "Overview", path: "/" },
  { label: "Dataset", path: "/dataset" },
  { label: "Explore", path: "/explore" },
  { label: "Trends", path: "/trends" },
  { label: "Forecast", path: "/forecast" },
  { label: "Risks", path: "/risks" },
  { label: "Competition", path: "/competition" },
  { label: "Recommendations", path: "/recommendations" },
  { label: "Reports", path: "/reports" },
]
