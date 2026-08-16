const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"

export interface HealthStatus {
  status: string
  service: string
}

export async function checkBackendHealth(): Promise<HealthStatus> {
  const res = await fetch(`${API_BASE_URL}/api/health`)
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`)
  return res.json()
}
