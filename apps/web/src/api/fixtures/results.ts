import type { AnalysisError, AnalysisResult } from '@/api/types'

const baseVersions = {
  pipeline: '0.1.0-mock',
  pose: 'mediapipe-mock',
  feature: '0.1.0',
  rule: '0.1.0',
  corpus: 'mock-corpus-1',
  embedding: 'mock-embed',
  generation: 'mock-gen',
  result_schema: '1.0.0',
}

export function completedResult(analysisId: string): AnalysisResult {
  return {
    schema_version: '1.0.0',
    analysis_id: analysisId,
    status: 'completed',
    stroke: 'clear',
    quality: {
      overall: 'acceptable',
      notes: [
        'Player remained fully visible.',
        'Lighting was adequate for pose estimation.',
      ],
    },
    stroke_confidence: 0.86,
    phase_confidence: 0.78,
    findings: [
      {
        rule_id: 'oc-reach-001',
        label: 'Limited contact reach',
        severity: 'medium',
        confidence: 0.74,
        evidence:
          'The clip suggests contact occurred with the striking arm short of full extension.',
      },
      {
        rule_id: 'oc-elbow-002',
        label: 'Late elbow extension',
        severity: 'low',
        confidence: 0.61,
        evidence:
          'Elbow extension appears to finish after the estimated contact window.',
      },
    ],
    recommendations: [
      {
        title: 'Reach through contact',
        body: 'Practice hitting the shuttle at a higher contact point with a longer arm line so power travels up through the racket.',
        exercise:
          'Shadow-swing 10 overhead clears focusing on full arm extension at the top of the swing.',
        citation_ids: ['cite-1'],
      },
      {
        title: 'Time the elbow release',
        body: 'Start extending the elbow slightly earlier in the forward swing so the arm is nearly straight at contact.',
        exercise:
          'Slow-motion clears against a wall target, pausing briefly at full extension.',
        citation_ids: ['cite-2'],
      },
    ],
    citations: [
      {
        id: 'cite-1',
        title: 'Overhead clear fundamentals',
        locator: 'Section 3 — Contact height',
      },
      {
        id: 'cite-2',
        title: 'Arm path in defensive clears',
        locator: 'pp. 12–14',
      },
    ],
    limitations: [
      'Analysis covers one selected stroke (clear, smash, or drop) per clip.',
      'Confidence reflects model certainty, not a guarantee.',
      'This is technique guidance, not medical advice.',
    ],
    inconclusive_reason: null,
    retake_guidance: [],
    error: null,
    completed_at: new Date().toISOString(),
    expires_at: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
    versions: baseVersions,
  }
}

export function inconclusiveResult(analysisId: string): AnalysisResult {
  return {
    schema_version: '1.0.0',
    analysis_id: analysisId,
    status: 'inconclusive',
    stroke: 'clear',
    quality: {
      overall: 'poor',
      notes: [
        'Lower body was cropped out of frame.',
        'Camera angle made phase detection unreliable.',
      ],
    },
    stroke_confidence: null,
    phase_confidence: null,
    findings: [],
    recommendations: [],
    citations: [],
    limitations: [
      'No technique findings are shown when quality checks fail.',
    ],
    inconclusive_reason:
      'The system could not reliably estimate pose and stroke phases from this clip.',
    retake_guidance: [
      'Step farther from the camera so your full body is visible.',
      'Use a side or rear three-quarter view.',
      'Record one clear stroke with steady lighting.',
    ],
    error: null,
    completed_at: new Date().toISOString(),
    expires_at: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
    versions: baseVersions,
  }
}

export function failedResult(analysisId: string): AnalysisResult {
  const error: AnalysisError = {
    code: 'ANALYSIS_PIPELINE_ERROR',
    message: 'Something went wrong while analyzing this video. You can try again.',
    retry_may_work: true,
    recording_remediation: null,
    correlation_id: `corr-${analysisId.slice(0, 8)}`,
  }

  return {
    schema_version: '1.0.0',
    analysis_id: analysisId,
    status: 'failed',
    stroke: 'clear',
    quality: {
      overall: 'borderline',
      notes: [],
    },
    stroke_confidence: null,
    phase_confidence: null,
    findings: [],
    recommendations: [],
    citations: [],
    limitations: [],
    inconclusive_reason: null,
    retake_guidance: [],
    error,
    completed_at: null,
    expires_at: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
    versions: baseVersions,
  }
}

export function expiredResult(analysisId: string): AnalysisResult {
  return {
    schema_version: '1.0.0',
    analysis_id: analysisId,
    status: 'expired',
    stroke: 'clear',
    quality: {
      overall: 'acceptable',
      notes: [],
    },
    stroke_confidence: null,
    phase_confidence: null,
    findings: [],
    recommendations: [],
    citations: [],
    limitations: ['Results and raw video are removed after 24 hours.'],
    inconclusive_reason: null,
    retake_guidance: [],
    error: {
      code: 'ANALYSIS_EXPIRED',
      message: 'This analysis has expired and is no longer available.',
      retry_may_work: false,
      recording_remediation: 'Upload a new recording to start again.',
      correlation_id: `corr-${analysisId.slice(0, 8)}`,
    },
    completed_at: null,
    expires_at: new Date(Date.now() - 60_000).toISOString(),
    versions: baseVersions,
  }
}
