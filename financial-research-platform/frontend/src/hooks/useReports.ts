import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getReports, deleteReport } from '../api/reports'
import type { ReportResponse } from '../types/report'

export function useReports() {
  return useQuery<ReportResponse[], Error>({
    queryKey: ['reports'],
    queryFn: getReports,
    refetchInterval: 10000,
  })
}

export function useDeleteReport() {
  const queryClient = useQueryClient()

  return useMutation<void, Error, string>({
    mutationFn: (reportId: string) => deleteReport(reportId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] })
    },
  })
}
