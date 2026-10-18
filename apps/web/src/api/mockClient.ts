import type { AnalysisApi } from '@/api/client'
import {
  completedResult,
  expiredResult,
  failedResult,
  inconclusiveResult,
} from '@/api/fixtures/results'
import { outcomeFromFilename } from '@/api/mockOutcome'
import type {
  AnalysisProgress,
  AnalysisResult,
  AnalysisStatus,
  CompleteUploadResponse,
  CreateAnalysisRequest,
  CreateAnalysisResponse,
  MockOutcome,
} from '@/api/types'

interface MockRecord {
  status: AnalysisStatus
  outcome: MockOutcome
  createdAt: number
  deleted: boolean
  filename: string
}

const PROCESSING_STAGES: AnalysisStatus[] = [
  'queued',
  'preprocessing',
  'pose_estimation',
  'phase_detection',
  'rule_evaluation',
  'retrieval',
  'generating',
]

const STAGE_MS = 350

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms)
  })
}

function createId(): string {
  return crypto.randomUUID()
}

function createToken(): string {
  const bytes = new Uint8Array(24)
  crypto.getRandomValues(bytes)
  return Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('')
}

function resultForOutcome(
  analysisId: string,
  outcome: MockOutcome,
): AnalysisResult {
  switch (outcome) {
    case 'inconclusive':
      return inconclusiveResult(analysisId)
    case 'failed':
      return failedResult(analysisId)
    case 'expired':
      return expiredResult(analysisId)
    case 'completed':
      return completedResult(analysisId)
  }
}

export function createMockClient(): AnalysisApi {
  const store = new Map<string, MockRecord>()
  const tokens = new Map<string, string>()

  function requireToken(analysisId: string, capabilityToken: string): void {
    const expected = tokens.get(analysisId)
    if (!expected || expected !== capabilityToken) {
      throw new Error('Unauthorized')
    }
  }

  function advanceStatus(record: MockRecord): AnalysisStatus {
    if (record.deleted) return 'deleted'
    if (record.outcome === 'expired') return 'expired'

    const elapsed = Date.now() - record.createdAt
    const index = Math.floor(elapsed / STAGE_MS)

    if (index < PROCESSING_STAGES.length) {
      return PROCESSING_STAGES[index]
    }

    return record.outcome
  }

  return {
    async createAnalysis(
      request: CreateAnalysisRequest,
    ): Promise<CreateAnalysisResponse> {
      await delay(200)
      if (request.stroke !== 'overhead_clear') {
        throw new Error('Unsupported stroke type')
      }
      if (!request.consent) {
        throw new Error('Consent is required')
      }

      const analysisId = createId()
      const capabilityToken = createToken()
      tokens.set(analysisId, capabilityToken)
      store.set(analysisId, {
        status: 'created',
        outcome: outcomeFromFilename(request.filename),
        createdAt: Date.now(),
        deleted: false,
        filename: request.filename,
      })

      return {
        schema_version: '1',
        analysis_id: analysisId,
        capability_token: capabilityToken,
        upload_url: `mock://upload/${analysisId}`,
        status: 'created',
      }
    },

    async uploadFile(): Promise<void> {
      await delay(50)
    },

    async completeUpload(
      analysisId: string,
      capabilityToken: string,
    ): Promise<CompleteUploadResponse> {
      await delay(250)
      requireToken(analysisId, capabilityToken)
      const record = store.get(analysisId)
      if (!record) throw new Error('Not found')

      record.status = 'queued'
      record.createdAt = Date.now()

      return {
        schema_version: '1',
        analysis_id: analysisId,
        status: 'queued',
      }
    },

    async getAnalysis(
      analysisId: string,
      capabilityToken: string,
    ): Promise<AnalysisProgress> {
      await delay(120)
      requireToken(analysisId, capabilityToken)
      const record = store.get(analysisId)
      if (!record) throw new Error('Not found')

      const status = advanceStatus(record)
      record.status = status

      return {
        schema_version: '1',
        analysis_id: analysisId,
        status,
        stage: status,
        progress: null,
        message_key: null,
        updated_at: new Date().toISOString(),
        expires_at: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
      }
    },

    async getResult(
      analysisId: string,
      capabilityToken: string,
    ): Promise<AnalysisResult> {
      await delay(150)
      requireToken(analysisId, capabilityToken)
      const record = store.get(analysisId)
      if (!record) throw new Error('Not found')
      if (record.deleted) {
        return {
          ...resultForOutcome(analysisId, 'failed'),
          error: {
            code: 'ANALYSIS_DELETED',
            safe_message: 'This analysis was deleted.',
            retryable: false,
            remediation: [],
            correlation_id: `corr-${analysisId.slice(0, 8)}`,
          },
        }
      }

      const status = advanceStatus(record)
      if (
        status !== 'completed' &&
        status !== 'inconclusive' &&
        status !== 'failed' &&
        status !== 'expired'
      ) {
        throw new Error('Result not ready')
      }

      return resultForOutcome(analysisId, record.outcome)
    },

    async deleteAnalysis(
      analysisId: string,
      capabilityToken: string,
    ): Promise<void> {
      await delay(150)
      requireToken(analysisId, capabilityToken)
      const record = store.get(analysisId)
      if (!record) throw new Error('Not found')
      record.deleted = true
      record.status = 'deleted'
    },
  }
}
