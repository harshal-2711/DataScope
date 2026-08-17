import type { DatasetSummary } from "@/types/dataset"

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"

export async function uploadDataset(file: File): Promise<DatasetSummary> {
  const formData = new FormData()
  formData.append("file", file)

  let res: Response
  try {
    res = await fetch(`${API_BASE_URL}/api/dataset/upload`, {
      method: "POST",
      body: formData,
    })
  } catch {
    throw new Error(
      "Could not reach the backend. Make sure the server is running on " +
        API_BASE_URL
    )
  }

  if (!res.ok) {
    let detail = "The dataset could not be processed."
    try {
      const body = await res.json()
      if (typeof body?.detail === "string") detail = body.detail
    } catch {
      // response wasn't JSON — fall back to the default message
    }
    throw new Error(detail)
  }

  return res.json()
}
