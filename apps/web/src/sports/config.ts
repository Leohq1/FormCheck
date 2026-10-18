export type SportId = 'badminton'

export type StrokeId = 'overhead_clear' | 'smash' | 'drop'

export type Handedness = 'left' | 'right'

export type ViewHint = 'side' | 'rear_three_quarter'

export interface StrokeConfig {
  id: StrokeId
  label: string
  description: string
}

export interface SportConfig {
  id: SportId
  label: string
  strokes: StrokeConfig[]
}

/** MVP exposes badminton only; add sports here without rewriting pages. */
export const SPORTS: SportConfig[] = [
  {
    id: 'badminton',
    label: 'Badminton',
    strokes: [
      {
        id: 'overhead_clear',
        label: 'Overhead clear',
        description: 'One controlled overhead clear with the full body visible.',
      },
      {
        id: 'smash',
        label: 'Smash',
        description: 'One overhead smash with the full body visible.',
      },
      {
        id: 'drop',
        label: 'Drop',
        description: 'One overhead drop shot with the full body visible.',
      },
    ],
  },
]

export const MVP_SPORT = SPORTS[0]
export const MVP_STROKE = MVP_SPORT.strokes[0]
export const STROKE_OPTIONS = MVP_SPORT.strokes

/** Reference swings served from apps/web/public/reference. Drop is a clear until a drop clip exists. */
export const REFERENCE_CLIPS: Record<StrokeId, string> = {
  overhead_clear: '/reference/clear.mov',
  smash: '/reference/smash.mov',
  drop: '/reference/drop.mov',
}

export function referenceClipFor(stroke: string): string {
  if (stroke === 'smash' || stroke === 'drop' || stroke === 'overhead_clear') {
    return REFERENCE_CLIPS[stroke]
  }
  return REFERENCE_CLIPS.overhead_clear
}

export const VIDEO_CONSTRAINTS = {
  maxSizeBytes: 100 * 1024 * 1024,
  maxDurationSeconds: 30,
  acceptedExtensions: ['.mp4', '.mov'] as const,
  acceptedMimeTypes: ['video/mp4', 'video/quicktime'] as const,
  preferredFps: 60,
  minResolutionLabel: '720p',
} as const

export const RECORDING_TIPS: string[] = [
  'Record exactly one clip of your swing.',
  'Keep your whole body visible in frame.',
  'Use a side or rear three-quarter camera view.',
  'Prefer 60 frames per second when your device allows it.',
  'Use steady lighting and keep the camera still.',
  'Avoid slow-motion, edited, or variable-speed footage.',
  'Keep the clip under 30 seconds and under 100 MB (MP4 or MOV).',
]
