import { useQuery } from '@tanstack/react-query'
import { getReport } from '../api/reports'
import type { ReportResponse } from '../types/report'

export function useReport(reportId: string | undefined) {
  return useQuery<ReportResponse, Error>({
    queryKey: ['report', reportId],
    queryFn: () => getReport(reportId!),
    enabled: !!reportId,
    staleTime: 30000,
  })
}
