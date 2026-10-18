import type {
  AnalysisProgress,
  AnalysisResult,
  CompleteUploadResponse,
  CreateAnalysisRequest,
  CreateAnalysisResponse,
} from '@/api/types'

export interface AnalysisApi {
  createAnalysis(request: CreateAnalysisRequest): Promise<CreateAnalysisResponse>
  uploadFile(
    uploadUrl: string,
    file: File,
    contentType: string,
  ): Promise<void>
  completeUpload(
    analysisId: string,
    capabilityToken: string,
  ): Promise<CompleteUploadResponse>
  getAnalysis(
    analysisId: string,
    capabilityToken: string,
  ): Promise<AnalysisProgress>
  getResult(
    analysisId: string,
    capabilityToken: string,
  ): Promise<AnalysisResult>
  deleteAnalysis(
    analysisId: string,
    capabilityToken: string,
  ): Promise<void>
}
