import type { AnalysisApi } from '@/api/client'
import { createHttpClient } from '@/api/httpClient'
import { createMockClient } from '@/api/mockClient'

let singleton: AnalysisApi | null = null

export function getAnalysisApi(): AnalysisApi {
  if (singleton) return singleton

  const baseUrl = import.meta.env.VITE_API_BASE_URL as string | undefined
  singleton = baseUrl ? createHttpClient(baseUrl) : createMockClient()
  return singleton
}

/** Test helper to replace the API singleton. */
export function setAnalysisApiForTests(api: AnalysisApi | null): void {
  singleton = api
}
