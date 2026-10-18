/** In-memory clip URLs for the current browser session (upload → results). */
const clipUrls = new Map<string, string>()

export function storeAnalysisClip(analysisId: string, file: File): string {
  const previous = clipUrls.get(analysisId)
  if (previous) URL.revokeObjectURL(previous)
  const url = URL.createObjectURL(file)
  clipUrls.set(analysisId, url)
  return url
}

export function getAnalysisClip(analysisId: string): string | null {
  return clipUrls.get(analysisId) ?? null
}

export function clearAnalysisClip(analysisId: string): void {
  const url = clipUrls.get(analysisId)
  if (url) URL.revokeObjectURL(url)
  clipUrls.delete(analysisId)
}
