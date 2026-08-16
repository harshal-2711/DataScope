import { BrowserRouter, Routes, Route } from "react-router-dom"
import { AppShell } from "@/components/layout/AppShell"
import { ThemeProvider } from "@/components/theme/ThemeProvider"
import Overview from "@/pages/Overview"
import Dataset from "@/pages/Dataset"
import Explore from "@/pages/Explore"
import Trends from "@/pages/Trends"
import Forecast from "@/pages/Forecast"
import Risks from "@/pages/Risks"
import Competition from "@/pages/Competition"
import Recommendations from "@/pages/Recommendations"
import Reports from "@/pages/Reports"

function App() {
  return (
    <ThemeProvider defaultTheme="system" storageKey="datascope-theme">
      <BrowserRouter>
        <AppShell>
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/dataset" element={<Dataset />} />
            <Route path="/explore" element={<Explore />} />
            <Route path="/trends" element={<Trends />} />
            <Route path="/forecast" element={<Forecast />} />
            <Route path="/risks" element={<Risks />} />
            <Route path="/competition" element={<Competition />} />
            <Route path="/recommendations" element={<Recommendations />} />
            <Route path="/reports" element={<Reports />} />
          </Routes>
        </AppShell>
      </BrowserRouter>
    </ThemeProvider>
  )
}

export default App
