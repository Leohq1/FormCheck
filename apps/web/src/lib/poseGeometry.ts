export interface PoseClock {
  lastMedia: number
  lastStamp: number
  offset: number
}

export function createPoseClock(): PoseClock {
  return { lastMedia: -1, lastStamp: -1, offset: 0 }
}

/**
 * MediaPipe video mode needs increasing timestamps, and the gap between them
 * has to match how far the clip actually moved. A replay jumps backward, so
 * the clock starts a fresh stretch instead of squeezing the whole swing into
 * one millisecond per frame.
 */
export function nextVideoTimestamp(mediaMs: number, clock: PoseClock): number {
  const media = Math.max(0, Math.round(mediaMs))
  if (clock.lastMedia >= 0 && media + 5 < clock.lastMedia) {
    clock.offset = clock.lastStamp + 1000 - media
  }
  const stamp = media + clock.offset
  const timestamp = stamp > clock.lastStamp ? stamp : clock.lastStamp + 1
  clock.lastMedia = media
  clock.lastStamp = timestamp
  return timestamp
}

export interface CoverFrame {
  offsetX: number
  offsetY: number
  drawWidth: number
  drawHeight: number
}

/** Map a normalized landmark onto an element that paints the video with object-fit: cover. */
export function objectFitCover(
  boxWidth: number,
  boxHeight: number,
  mediaWidth: number,
  mediaHeight: number,
): CoverFrame {
  const safeMediaWidth = Math.max(mediaWidth, 1)
  const safeMediaHeight = Math.max(mediaHeight, 1)
  const mediaRatio = safeMediaWidth / safeMediaHeight
  const boxRatio = boxWidth / Math.max(boxHeight, 1)
  if (mediaRatio > boxRatio) {
    const drawHeight = boxHeight
    const drawWidth = boxHeight * mediaRatio
    return {
      offsetX: (boxWidth - drawWidth) / 2,
      offsetY: 0,
      drawWidth,
      drawHeight,
    }
  }
  const drawWidth = boxWidth
  const drawHeight = boxWidth / mediaRatio
  return {
    offsetX: 0,
    offsetY: (boxHeight - drawHeight) / 2,
    drawWidth,
    drawHeight,
  }
}

export const POSE_CONNECTIONS: ReadonlyArray<readonly [number, number]> = [
  [0, 1],
  [1, 2],
  [2, 3],
  [3, 7],
  [0, 4],
  [4, 5],
  [5, 6],
  [6, 8],
  [9, 10],
  [11, 12],
  [11, 13],
  [13, 15],
  [15, 17],
  [15, 19],
  [15, 21],
  [17, 19],
  [12, 14],
  [14, 16],
  [16, 18],
  [16, 20],
  [16, 22],
  [18, 20],
  [11, 23],
  [12, 24],
  [23, 24],
  [23, 25],
  [25, 27],
  [27, 29],
  [27, 31],
  [29, 31],
  [24, 26],
  [26, 28],
  [28, 30],
  [28, 32],
  [30, 32],
]
