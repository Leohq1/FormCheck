import { describe, expect, it } from 'vitest'
import { outcomeFromFilename } from '@/api/mockOutcome'

describe('outcomeFromFilename', () => {
  it('defaults to completed', () => {
    expect(outcomeFromFilename('overhead-clear.mp4')).toBe('completed')
  })

  it('detects inconclusive, failed, and expired tokens', () => {
    expect(outcomeFromFilename('trial-inconclusive.mov')).toBe('inconclusive')
    expect(outcomeFromFilename('failed-run.mp4')).toBe('failed')
    expect(outcomeFromFilename('expired-demo.mp4')).toBe('expired')
  })
})
