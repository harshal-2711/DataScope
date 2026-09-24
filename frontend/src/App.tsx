import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import { AppShell } from "@/components/layout/AppShell"
import { ThemeProvider } from "@/components/theme/ThemeProvider"
import { AuthProvider, useAuth } from "@/context/AuthContext"
import { DatasetProvider } from "@/context/DatasetContext"

import Login from "@/pages/Auth/Login"
import Register from "@/pages/Auth/Register"
import ForgotPasswordPage from "@/pages/Auth/ForgotPassword"
import ResetPasswordPage from "@/pages/Auth/ResetPassword"
import OnboardingPage from "@/pages/Auth/Onboarding"
import Overview from "@/pages/Overview"
import Dataset from "@/pages/Dataset"
import ConnectDataSource from "@/pages/ConnectDataSource"
import DataManagement from "@/pages/DataManagement"
import Explore from "@/pages/Explore"
import Trends from "@/pages/Trends"
import Forecast from "@/pages/Forecast"
import Risks from "@/pages/Risks"
import Competition from "@/pages/Competition"
import Recommendations from "@/pages/Recommendations"
import Reports from "@/pages/Reports"
import SettingsPage from "@/pages/Settings"

import { InitializationScreen } from "@/components/common/InitializationScreen"

function ProtectedLayout() {
  const { isAuthenticated, isLoading, retryInit } = useAuth()

  if (isLoading) {
    return <InitializationScreen onRetry={retryInit} />
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <AppShell />
}

function AppRoutes() {
  const { isAuthenticated, isLoading, retryInit } = useAuth()

  if (isLoading) {
    return <InitializationScreen onRetry={retryInit} />
  }

  return (
    <Routes>
      {/* Public Pages */}
      <Route path="/" element={isAuthenticated ? <Navigate to="/overview" replace /> : <Navigate to="/login" replace />} />
      <Route path="/login" element={!isAuthenticated ? <Login /> : <Navigate to="/overview" replace />} />
      <Route path="/register" element={!isAuthenticated ? <Register /> : <Navigate to="/overview" replace />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />
      <Route path="/onboarding" element={isAuthenticated ? <OnboardingPage /> : <Navigate to="/login" replace />} />

      {/* Main Authenticated Workspace Routes */}
      <Route element={<ProtectedLayout />}>
        <Route path="/overview" element={<Overview />} />
        <Route path="/dataset" element={<Dataset />} />
        <Route path="/connect-data" element={<ConnectDataSource />} />
        <Route path="/live-data" element={<Navigate to="/connect-data" replace />} />
        <Route path="/data-management" element={<DataManagement />} />
        <Route path="/explore" element={<Explore />} />
        <Route path="/trends" element={<Trends />} />
        <Route path="/forecast" element={<Forecast />} />
        <Route path="/risks" element={<Risks />} />
        <Route path="/competition" element={<Competition />} />
        <Route path="/recommendations" element={<Recommendations />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to={isAuthenticated ? "/overview" : "/"} replace />} />
    </Routes>
  )
}


function App() {
  return (
    <ThemeProvider defaultTheme="system" storageKey="datascope-theme">
      <AuthProvider>
        <DatasetProvider>
          <BrowserRouter>
            <AppRoutes />
          </BrowserRouter>
        </DatasetProvider>
      </AuthProvider>
    </ThemeProvider>
  )
}

export default App
