import { apiClient } from './client'
import type { ReportResponse } from '../types/report'

export const getReports = async (): Promise<ReportResponse[]> => {
  const { data } = await apiClient.get<ReportResponse[]>('/api/v1/reports/')
  return data
}

export const getReport = async (reportId: string): Promise<ReportResponse> => {
  const { data } = await apiClient.get<ReportResponse>(`/api/v1/reports/${reportId}`)
  return data
}

export const deleteReport = async (reportId: string): Promise<void> => {
  await apiClient.delete(`/api/v1/reports/${reportId}`)
}

export const getReportDownloadUrl = (reportId: string): string => {
  const base = import.meta.env.VITE_API_BASE_URL ?? ''
  return `${base}/api/v1/reports/${reportId}/download`
}
