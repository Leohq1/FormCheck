import { describe, expect, it } from 'vitest'
import { STROKE_OPTIONS } from '@/sports/config'

describe('stroke options', () => {
  it('offers only the contracted overhead clear stroke', () => {
    expect(STROKE_OPTIONS.map((option) => option.id)).toEqual(['overhead_clear'])
  })
})
