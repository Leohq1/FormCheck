import { describe, expect, it } from 'vitest'
import { createPoseClock, nextVideoTimestamp, objectFitCover } from '@/lib/poseGeometry'

describe('objectFitCover', () => {
  it('crops the sides when the video is wider than the box', () => {
    const frame = objectFitCover(160, 100, 320, 100)
    expect(frame.drawHeight).toBe(100)
    expect(frame.drawWidth).toBe(320)
    expect(frame.offsetX).toBe(-80)
    expect(frame.offsetY).toBe(0)
  })

  it('keeps real frame spacing when a replay jumps backward', () => {
    const clock = createPoseClock()
    expect(nextVideoTimestamp(40, clock)).toBe(40)
    expect(nextVideoTimestamp(80, clock)).toBe(80)
    expect(nextVideoTimestamp(10, clock)).toBe(1010)
    expect(nextVideoTimestamp(26, clock)).toBe(1026)
  })

  it('crops the top and bottom when the video is taller than the box', () => {
    const frame = objectFitCover(160, 100, 100, 200)
    expect(frame.drawWidth).toBe(160)
    expect(frame.drawHeight).toBe(320)
    expect(frame.offsetX).toBe(0)
    expect(frame.offsetY).toBe(-110)
  })
})
