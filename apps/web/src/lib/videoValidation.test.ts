import { describe, expect, it } from 'vitest'
import { formatConfidence, validateVideoFile } from '@/lib/videoValidation'

describe('validateVideoFile', () => {
  it('rejects a missing file', () => {
    const result = validateVideoFile(null)
    expect(result.ok).toBe(false)
    expect(result.errors[0]).toMatch(/choose a video/i)
  })

  it('accepts a valid mp4 under the size limit', () => {
    const file = new File([new Uint8Array([1, 2, 3])], 'clear.mp4', {
      type: 'video/mp4',
    })
    const result = validateVideoFile(file)
    expect(result.ok).toBe(true)
    expect(result.errors).toEqual([])
  })

  it('rejects unsupported extensions', () => {
    const file = new File([new Uint8Array([1])], 'clip.avi', {
      type: 'video/avi',
    })
    const result = validateVideoFile(file)
    expect(result.ok).toBe(false)
    expect(result.errors.some((error) => /mp4 or mov/i.test(error))).toBe(true)
  })

  it('rejects oversized files', () => {
    const big = new File([new Uint8Array(10)], 'clear.mp4', {
      type: 'video/mp4',
    })
    Object.defineProperty(big, 'size', { value: 101 * 1024 * 1024 })
    const result = validateVideoFile(big)
    expect(result.ok).toBe(false)
    expect(result.errors.some((error) => /100 mb/i.test(error))).toBe(true)
  })
})

describe('formatConfidence', () => {
  it('formats confidence without claiming certainty', () => {
    expect(formatConfidence(0.74)).toBe('About 74% model confidence')
  })
})
