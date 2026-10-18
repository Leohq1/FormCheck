import type { AnalysisError, AnalysisResult, ResultVersions } from '@/api/types'

const baseVersions: ResultVersions = {
  pipeline: '2026.10.0',
  pose_estimator: 'mediapipe-0.10',
  feature_schema: '1',
  rule_set: '1',
  corpus: '1',
  embedding: 'text-embedding-3-small',
  generation: 'gpt-placeholder',
  result_schema: '1',
}

function expiresAt(offsetMs: number): string {
  return new Date(Date.now() + offsetMs).toISOString()
}

export function completedResult(analysisId: string): AnalysisResult {
  return {
    schema_version: '1',
    analysis_id: analysisId,
    status: 'completed',
    quality: {
      overall: 0.84,
      warnings: [],
    },
    stroke: {
      type: 'overhead_clear',
      start_time_ms: 4200,
      end_time_ms: 7100,
      contact_time_ms: 6240,
      confidence: 0.78,
    },
    findings: [
      {
        rule_id: 'clear.low_arm_extension.v1',
        label: 'Low arm extension at maximum reach',
        severity: 'moderate',
        confidence: 0.81,
        evidence: [
          {
            feature: 'dominant_elbow_angle_at_max_wrist_height_deg',
            value: 128,
            unit: 'deg',
          },
        ],
        retrieval_tags: ['overhead_clear', 'contact_reach', 'arm_extension'],
      },
    ],
    feedback: {
      summary:
        'The clip suggests the striking arm was short of full extension near the highest wrist height.',
      tips: [
        {
          finding_id: 'clear.low_arm_extension.v1',
          title: 'Reach through contact',
          explanation:
            'Practice a longer arm line at the top of the swing so power travels into the racket.',
          practice_cue:
            'Shadow-swing 10 overhead clears focusing on full arm extension at the top.',
          citations: [
            {
              source_id: 'source-001',
              chunk_id: 'chunk-014',
              locator: 'Section 4.2',
            },
          ],
        },
      ],
      limitations: [
        'Contact time was estimated from body motion because the racket and shuttle were not tracked.',
      ],
      model: 'gpt-placeholder',
      prompt_version: '1',
    },
    versions: baseVersions,
    error: null,
    completed_at: new Date().toISOString(),
    expires_at: expiresAt(24 * 60 * 60 * 1000),
  }
}

export function inconclusiveResult(analysisId: string): AnalysisResult {
  const error: AnalysisError = {
    code: 'POSE_BODY_CROPPED',
    safe_message: 'The full body was not visible throughout the stroke.',
    retryable: false,
    remediation: [
      'Move the camera farther away.',
      'Keep both feet and the hitting arm in the frame.',
    ],
    correlation_id: `corr-${analysisId.slice(0, 8)}`,
  }

  return {
    schema_version: '1',
    analysis_id: analysisId,
    status: 'inconclusive',
    quality: {
      overall: 0.22,
      warnings: ['Dominant ankles left the frame during the swing.'],
    },
    stroke: {
      type: 'overhead_clear',
      start_time_ms: null,
      end_time_ms: null,
      contact_time_ms: null,
      confidence: null,
    },
    findings: [],
    feedback: {
      summary: '',
      tips: [],
      limitations: [
        'Technique findings are withheld when pose quality is insufficient.',
      ],
      model: 'none',
      prompt_version: '1',
    },
    versions: {
      ...baseVersions,
      embedding: 'none',
      generation: 'none',
    },
    error,
    completed_at: new Date().toISOString(),
    expires_at: expiresAt(24 * 60 * 60 * 1000),
  }
}

export function failedResult(analysisId: string): AnalysisResult {
  return {
    schema_version: '1',
    analysis_id: analysisId,
    status: 'failed',
    quality: { overall: 0, warnings: [] },
    stroke: {
      type: 'overhead_clear',
      start_time_ms: null,
      end_time_ms: null,
      contact_time_ms: null,
      confidence: null,
    },
    findings: [],
    feedback: {
      summary: '',
      tips: [],
      limitations: [],
      model: 'none',
      prompt_version: '1',
    },
    versions: {
      ...baseVersions,
      embedding: 'none',
      generation: 'none',
    },
    error: {
      code: 'ANALYSIS_PIPELINE_ERROR',
      safe_message:
        'Something went wrong while analyzing this video. You can try again.',
      retryable: true,
      remediation: [],
      correlation_id: `corr-${analysisId.slice(0, 8)}`,
    },
    completed_at: null,
    expires_at: expiresAt(24 * 60 * 60 * 1000),
  }
}

export function expiredResult(analysisId: string): AnalysisResult {
  return {
    ...completedResult(analysisId),
    status: 'expired',
    completed_at: null,
    expires_at: expiresAt(-60_000),
    error: {
      code: 'ANALYSIS_EXPIRED',
      safe_message: 'This analysis has expired and is no longer available.',
      retryable: false,
      remediation: ['Upload a new recording to start again.'],
      correlation_id: `corr-${analysisId.slice(0, 8)}`,
    },
  }
}
