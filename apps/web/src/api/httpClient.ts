import type { AnalysisApi } from '@/api/client'
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

  const body = await response.text()
  if (!body) {
    return undefined as T
  }

  return JSON.parse(body) as T
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

    async uploadFile(
      analysisId: string,
      capabilityToken: string,
      file: File,
      contentType: string,
    ) {
      const response = await fetch(`${root}/api/v1/analyses/${analysisId}/upload`, {
        method: 'PUT',
        headers: {
          'Content-Type': contentType,
          Authorization: `Bearer ${capabilityToken}`,
        },
        body: file,
      })
      if (!response.ok) {
        throw new Error(`Upload failed (${response.status})`)
      }
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

    getResult(analysisId: string, capabilityToken: string) {
      return requestJson<AnalysisResult>(
        root,
        `/api/v1/analyses/${analysisId}/result`,
        { capabilityToken },
      )
    },

    async deleteAnalysis(analysisId: string, capabilityToken: string) {
      await requestJson<void>(root, `/api/v1/analyses/${analysisId}`, {
        method: 'DELETE',
        capabilityToken,
      })
    },
  }
}
