import { VIDEO_CONSTRAINTS } from '@/sports/config'

export interface VideoValidationResult {
  ok: boolean
  errors: string[]
}

export function validateVideoFile(file: File | null): VideoValidationResult {
  const errors: string[] = []

  if (!file) {
    return { ok: false, errors: ['Choose a video file to upload.'] }
  }

  const lowerName = file.name.toLowerCase()
  const hasExtension = VIDEO_CONSTRAINTS.acceptedExtensions.some((ext) =>
    lowerName.endsWith(ext),
  )

  if (!hasExtension) {
    errors.push('Use an MP4 or MOV file.')
  }

  const mimeOk =
    file.type === '' ||
    VIDEO_CONSTRAINTS.acceptedMimeTypes.includes(
      file.type as (typeof VIDEO_CONSTRAINTS.acceptedMimeTypes)[number],
    )

  if (!mimeOk) {
    errors.push('File type must be video/mp4 or video/quicktime.')
  }

  if (file.size > VIDEO_CONSTRAINTS.maxSizeBytes) {
    errors.push('File must be 100 MB or smaller.')
  }

  if (file.size === 0) {
    errors.push('File appears to be empty.')
  }

  return { ok: errors.length === 0, errors }
}

export function formatConfidence(value: number): string {
  const pct = Math.round(value * 100)
  return `About ${pct}% model confidence`
}
