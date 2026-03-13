import { useMutation, useQueryClient } from '@tanstack/react-query'
import { startAnalysis } from '../api/analysis'
import type { AnalysisStartResponse } from '../types/analysis'

export function useStartAnalysis() {
  const queryClient = useQueryClient()

  return useMutation<AnalysisStartResponse, Error, string>({
    mutationFn: (ticker: string) => startAnalysis(ticker),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] })
    },
  })
}
