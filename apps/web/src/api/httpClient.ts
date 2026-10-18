import type { AnalysisApi } from '@/api/client'
import { normalizeResult } from '@/api/normalizeResult'
import type {
  AnalysisProgress,
  AnalysisResult,
  CompleteUploadResponse,
  CreateAnalysisRequest,
  CreateAnalysisResponse,
} from '@/api/types'

async function requestJson<T>(
  baseUrl: string,
  path: string,
  init: RequestInit & { capabilityToken?: string } = {},
): Promise<T> {
  const { capabilityToken, headers, ...rest } = init
  const response = await fetch(`${baseUrl}${path}`, {
    ...rest,
    headers: {
      'Content-Type': 'application/json',
      ...(capabilityToken
        ? { Authorization: `Bearer ${capabilityToken}` }
        : {}),
      ...headers,
    },
  })

  if (!response.ok) {
    throw new Error(`API request failed (${response.status})`)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

export function createHttpClient(baseUrl: string): AnalysisApi {
  const root = baseUrl.replace(/\/$/, '')

  return {
    createAnalysis(request: CreateAnalysisRequest) {
      return requestJson<CreateAnalysisResponse>(root, '/api/v1/analyses', {
        method: 'POST',
        body: JSON.stringify(request),
      })
    },

    completeUpload(analysisId: string, capabilityToken: string) {
      return requestJson<CompleteUploadResponse>(
        root,
        `/api/v1/analyses/${analysisId}/complete-upload`,
        { method: 'POST', capabilityToken },
      )
    },

    getAnalysis(analysisId: string, capabilityToken: string) {
      return requestJson<AnalysisProgress>(
        root,
        `/api/v1/analyses/${analysisId}`,
        { capabilityToken },
      )
    },

    async getResult(analysisId: string, capabilityToken: string) {
      const payload = await requestJson<AnalysisResult>(
        root,
        `/api/v1/analyses/${analysisId}/result`,
        { capabilityToken },
      )
      return normalizeResult(payload)
    },

    async deleteAnalysis(analysisId: string, capabilityToken: string) {
      await requestJson<void>(root, `/api/v1/analyses/${analysisId}`, {
        method: 'DELETE',
        capabilityToken,
      })
    },
  }
}
