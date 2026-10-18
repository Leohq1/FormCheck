import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import type { AnalysisResult } from '@/api/types'
import { ResultsPanel } from '@/components/ResultsPanel'

function result(overrides: Partial<AnalysisResult> = {}): AnalysisResult {
  return {
    schema_version: '1',
    analysis_id: '11111111-1111-4111-8111-111111111111',
    status: 'completed',
    quality: { overall: 0.84, warnings: ['Lighting was uneven.'] },
    stroke: {
      type: 'overhead_clear',
      start_time_ms: 4200,
      end_time_ms: 7100,
      contact_time_ms: 6240,
      confidence: 0.78,
    },
    findings: [],
    feedback: {
      summary: 'No supported fault was confirmed for this clip.',
      tips: [],
      limitations: ['This is technique guidance, not medical advice.'],
      model: 'test-model',
      prompt_version: '1',
    },
    versions: {
      pipeline: '2026.10.0',
      pose_estimator: 'mediapipe-0.10',
      feature_schema: '1',
      rule_set: '1',
      corpus: '1',
      embedding: 'test-embed',
      generation: 'test-model',
      result_schema: '1',
    },
    error: null,
    completed_at: '2026-10-17T20:01:00Z',
    expires_at: '2026-10-18T20:01:00Z',
    ...overrides,
  }
}

describe('ResultsPanel', () => {
  afterEach(() => {
    cleanup()
  })

  it('says coaching did not come back when there are no tips', () => {
    render(<ResultsPanel result={result()} />)
    expect(screen.getByText('Practice session')).toBeInTheDocument()
    expect(
      screen.getByText(/Coaching for this shot did not come back/i),
    ).toBeInTheDocument()
  })

  it('renders side-by-side form comparison tapes', () => {
    render(<ResultsPanel result={result()} />)
    expect(screen.getByText('Form comparison')).toBeInTheDocument()
    expect(screen.getByText('Your swing')).toBeInTheDocument()
    expect(screen.getByText('Reference overhead clear')).toBeInTheDocument()
  })

  it('shows the practice session as three cards', () => {
    render(
      <ResultsPanel
        result={result({
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
              retrieval_tags: ['overhead_clear', 'contact_reach'],
            },
          ],
          feedback: {
            summary: 'The striking arm was short of full extension.',
            tips: [
              {
                finding_id: 'clear.low_arm_extension.v1',
                title: 'Reach through contact',
                explanation: 'Practice a longer arm line at the top of the swing.',
                practice_cue: 'Shadow-swing 10 overhead clears.',
                citations: [
                  {
                    source_id: 'source-001',
                    chunk_id: 'chunk-014',
                    locator: 'Section 4.2',
                  },
                ],
              },
            ],
            limitations: ['Racket and shuttle were not tracked.'],
            model: 'test-model',
            prompt_version: '1',
          },
        })}
      />,
    )

    expect(screen.getByText('Practice session')).toBeInTheDocument()
    expect(screen.getByText('Reach through contact')).toBeInTheDocument()
    expect(screen.getByText('Shadow-swing 10 overhead clears.')).toBeInTheDocument()
    expect(screen.queryByText(/dominant_elbow_angle_at_max_wrist_height_deg/)).not.toBeInTheDocument()
    expect(screen.queryByText(/overhead_clear, contact_reach/)).not.toBeInTheDocument()
  })
})
