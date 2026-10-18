import type { AnalysisFinding, AnalysisResult, FindingSeverity } from '@/api/types'

const SEVERITY: Record<string, FindingSeverity> = {
  minor: 'low',
  moderate: 'medium',
  major: 'high',
  low: 'low',
  medium: 'medium',
  high: 'high',
}

export function normalizeResult(payload: unknown): AnalysisResult {
  if (!payload || typeof payload !== 'object') {
    throw new Error('Result payload was empty')
  }
  const raw = payload as AnalysisResult & {
    quality?: { overall?: unknown; warnings?: string[]; notes?: string[] }
    stroke?: { type?: string; confidence?: number | null }
    feedback?: {
      summary?: string
      tips?: Array<{
        title?: string
        explanation?: string
        practice_cue?: string
        citations?: Array<{ source_id?: string; chunk_id?: string; locator?: string }>
      }>
      limitations?: string[]
    }
    error?: {
      code?: string
      message?: string
      safe_message?: string
      retryable?: boolean
      retry_may_work?: boolean
      remediation?: string[]
      recording_remediation?: string | null
      correlation_id?: string
    } | null
  }
  if (typeof raw.quality?.overall !== 'number') {
    return raw
  }

  const sourceFindings = Array.isArray(raw.findings) ? raw.findings : []
  const findings: AnalysisFinding[] = sourceFindings.map((item) => {
    const finding = item as AnalysisFinding & { evidence?: unknown; severity?: string }
    const evidence = finding.evidence
    const text = Array.isArray(evidence)
      ? evidence
          .map((entry) => {
            const record = entry as { feature?: string; value?: unknown; unit?: string }
            return `${record.feature ?? 'feature'}=${String(record.value)}${record.unit ?? ''}`
          })
          .join('; ')
      : String(evidence ?? '')
    return {
      rule_id: finding.rule_id,
      label: finding.label,
      severity: SEVERITY[String(finding.severity)] ?? 'medium',
      confidence: finding.confidence,
      evidence: text,
    }
  })

  const tips = raw.feedback?.tips ?? []
  const strokeType = raw.stroke?.type === 'overhead_clear' ? 'clear' : raw.stroke?.type

  return {
    ...raw,
    stroke: (strokeType ?? raw.stroke) as AnalysisResult['stroke'],
    stroke_confidence: raw.stroke?.confidence ?? raw.stroke_confidence ?? null,
    phase_confidence: raw.phase_confidence ?? null,
    quality: {
      overall: raw.quality.overall >= 0.7 ? 'acceptable' : raw.quality.overall >= 0.4 ? 'borderline' : 'poor',
      notes: raw.quality.warnings ?? raw.quality.notes ?? [],
    },
    findings,
    recommendations: tips.map((tip) => ({
      title: tip.title ?? 'Coaching cue',
      body: tip.explanation ?? '',
      exercise: tip.practice_cue ?? null,
      citation_ids: (tip.citations ?? []).map((citation) => citation.chunk_id ?? ''),
    })),
    citations: tips.flatMap((tip) =>
      (tip.citations ?? []).map((citation) => ({
        id: citation.chunk_id ?? '',
        title: citation.source_id ?? '',
        locator: citation.locator ?? '',
      })),
    ),
    limitations: raw.feedback?.limitations ?? raw.limitations ?? [],
    inconclusive_reason: raw.error?.safe_message ?? raw.inconclusive_reason ?? null,
    retake_guidance: raw.error?.remediation ?? raw.retake_guidance ?? [],
    error: raw.error
      ? {
          code: raw.error.code ?? 'UNKNOWN',
          message: raw.error.safe_message ?? raw.error.message ?? 'The analysis could not be completed.',
          retry_may_work: raw.error.retryable ?? raw.error.retry_may_work ?? false,
          recording_remediation: raw.error.remediation?.[0] ?? raw.error.recording_remediation ?? null,
          correlation_id: raw.error.correlation_id ?? '',
        }
      : null,
  }
}
