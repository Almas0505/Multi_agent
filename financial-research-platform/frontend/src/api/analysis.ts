import { apiClient } from './client'
import type { AnalysisStartResponse, AnalysisStatusResponse } from '../types/analysis'

export const startAnalysis = async (ticker: string): Promise<AnalysisStartResponse> => {
  const { data } = await apiClient.post<AnalysisStartResponse>(`/api/v1/analyze/${ticker}`)
  return data
}

export const getAnalysisStatus = async (taskId: string): Promise<AnalysisStatusResponse> => {
  const { data } = await apiClient.get<AnalysisStatusResponse>(`/api/v1/analyze/${taskId}/status`)
  return data
}
