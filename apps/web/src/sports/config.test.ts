import { describe, expect, it } from 'vitest'
import { STROKE_OPTIONS } from '@/sports/config'

describe('stroke options', () => {
  it('offers overhead clear, smash, and drop', () => {
    expect(STROKE_OPTIONS.map((option) => option.id)).toEqual([
      'overhead_clear',
      'smash',
      'drop',
    ])
  })
})
