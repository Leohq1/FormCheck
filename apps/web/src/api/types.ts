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

export type ResultStatus =
  | 'completed'
  | 'inconclusive'
  | 'failed'
  | 'expired'
  | 'cancelled'

export type FindingSeverity = 'minor' | 'moderate' | 'major'

export interface EvidenceItem {
  feature: string
  value: number
  unit: string
}

export interface AnalysisFinding {
  rule_id: string
  label: string
  severity: FindingSeverity
  confidence: number
  evidence: EvidenceItem[]
  retrieval_tags: string[]
}

export interface Citation {
  source_id: string
  chunk_id: string
  locator: string
}

export interface FeedbackTip {
  finding_id: string
  title: string
  explanation: string
  practice_cue: string
  citations: Citation[]
}

export interface Feedback {
  summary: string
  tips: FeedbackTip[]
  limitations: string[]
  model: string
  prompt_version: string
}

export interface QualityReport {
  overall: number
  warnings: string[]
}

export interface StrokeInfo {
  type: StrokeId
  start_time_ms: number | null
  end_time_ms: number | null
  contact_time_ms: number | null
  confidence: number | null
}

export interface ResultVersions {
  pipeline: string
  pose_estimator: string
  feature_schema: string
  rule_set: string
  corpus: string
  embedding: string
  generation: string
  result_schema: '1'
}

export interface AnalysisResult {
  schema_version: '1'
  analysis_id: string
  status: ResultStatus
  quality: QualityReport
  stroke: StrokeInfo
  findings: AnalysisFinding[]
  feedback: Feedback
  versions: ResultVersions
  error: AnalysisError | null
  completed_at: string | null
  expires_at: string
}

export interface AnalysisError {
  code: string
  safe_message: string
  retryable: boolean
  remediation: string[]
  correlation_id: string
}

export type MockOutcome = 'completed' | 'inconclusive' | 'failed' | 'expired'
