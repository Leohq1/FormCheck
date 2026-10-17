const TOKEN_PREFIX = 'formcheck:capability:'

export function storeCapabilityToken(
  analysisId: string,
  token: string,
): void {
  sessionStorage.setItem(`${TOKEN_PREFIX}${analysisId}`, token)
}

export function getCapabilityToken(analysisId: string): string | null {
  return sessionStorage.getItem(`${TOKEN_PREFIX}${analysisId}`)
}

export function clearCapabilityToken(analysisId: string): void {
  sessionStorage.removeItem(`${TOKEN_PREFIX}${analysisId}`)
}
