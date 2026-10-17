import type { MockOutcome } from '@/api/types'

/** Pick mock terminal outcome from the uploaded filename for local demos. */
export function outcomeFromFilename(filename: string): MockOutcome {
  const lower = filename.toLowerCase()
  if (lower.includes('inconclusive')) return 'inconclusive'
  if (lower.includes('failed')) return 'failed'
  if (lower.includes('expired')) return 'expired'
  return 'completed'
}
