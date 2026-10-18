import { describe, expect, it } from 'vitest'
import { referenceClipFor, STROKE_OPTIONS } from '@/sports/config'

describe('stroke options', () => {
  it('offers overhead clear, smash, and drop', () => {
    expect(STROKE_OPTIONS.map((option) => option.id)).toEqual([
      'overhead_clear',
      'smash',
      'drop',
    ])
  })

  it('pairs each upload choice with its reference clip', () => {
    expect(referenceClipFor('overhead_clear')).toBe('/reference/clear.mov')
    expect(referenceClipFor('smash')).toBe('/reference/smash.mov')
    expect(referenceClipFor('drop')).toBe('/reference/drop.mov')
  })
})
