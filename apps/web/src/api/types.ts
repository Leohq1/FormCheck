import type { Handedness, StrokeId, ViewHint } from '@/sports/config'

export const ANALYSIS_STATUSES = [
  'created',
  'uploading',
  'queued',
  'preprocessing',
  'pose_estimation',
  'phase_detection',
  'rule_evaluation',
  'retrieval',
  'generating',
  'completed',
  'inconclusive',
  'failed',
  'cancelled',
  'expired',
  'deleted',
] as const

export type AnalysisStatus = (typeof ANALYSIS_STATUSES)[number]

export const TERMINAL_STATUSES: AnalysisStatus[] = [
  'completed',
  'inconclusive',
  'failed',
  'cancelled',
  'expired',
  'deleted',
]

export function isTerminalStatus(status: AnalysisStatus): boolean {
  return TERMINAL_STATUSES.includes(status)
}

export interface CreateAnalysisRequest {
  stroke: StrokeId
  handedness: Handedness
  view_hint: ViewHint
  consent: boolean
  filename: string
  content_type: string
  byte_size: number
}

export interface CreateAnalysisResponse {
  schema_version: string
  analysis_id: string
  capability_token: string
  upload_url: string
  status: AnalysisStatus
}

export interface CompleteUploadResponse {
  schema_version: string
  analysis_id: string
  status: AnalysisStatus
}

export interface AnalysisProgress {
  schema_version: string
  analysis_id: string
  status: AnalysisStatus
  stage: string | null
  progress: number | null
  message_key: string | null
  updated_at: string
  expires_at: string | null
}

export type FindingSeverity = 'low' | 'medium' | 'high'

export interface AnalysisFinding {
  rule_id: string
  label: string
  severity: FindingSeverity
  confidence: number
  evidence: string
}

export interface CoachingRecommendation {
  title: string
  body: string
  exercise: string | null
  citation_ids: string[]
}

export interface Citation {
  id: string
  title: string
  locator: string
}

export interface QualityReport {
  overall: 'acceptable' | 'borderline' | 'poor'
  notes: string[]
}

export interface AnalysisResult {
  schema_version: string
  analysis_id: string
  status: AnalysisStatus
  stroke: StrokeId
  quality: QualityReport
  stroke_confidence: number | null
  phase_confidence: number | null
  findings: AnalysisFinding[]
  recommendations: CoachingRecommendation[]
  citations: Citation[]
  limitations: string[]
  inconclusive_reason: string | null
  retake_guidance: string[]
  error: AnalysisError | null
  completed_at: string | null
  expires_at: string | null
  versions: Record<string, string>
}

export interface AnalysisError {
  code: string
  message: string
  retry_may_work: boolean
  recording_remediation: string | null
  correlation_id: string
}

export type MockOutcome = 'completed' | 'inconclusive' | 'failed' | 'expired'
