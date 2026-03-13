import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FileText, Plus, RefreshCw } from 'lucide-react'
import { useReports, useDeleteReport } from '../hooks/useReports'
import { ReportCard } from '../components/reports/ReportCard'
import { TickerSearchForm } from '../components/analysis/TickerSearchForm'
import { useStartAnalysis } from '../hooks/useAnalysis'
import { Button } from '../components/ui/Button'
import { EmptyState } from '../components/ui/EmptyState'
import { ErrorAlert } from '../components/ui/ErrorAlert'
import { SkeletonCard } from '../components/ui/Skeleton'

export function ReportsPage() {
  const navigate = useNavigate()
  const { data: reports, isLoading, error, refetch, isFetching } = useReports()
  const deleteReport = useDeleteReport()
  const startMutation = useStartAnalysis()
  const [showSearch, setShowSearch] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const handleDelete = (id: string) => {
    setDeletingId(id)
    deleteReport.mutate(id, {
      onSettled: () => setDeletingId(null),
    })
  }

  const handleAnalyze = (ticker: string) => {
    startMutation.mutate(ticker, {
      onSuccess: (res) => navigate(`/analysis/${res.task_id}`),
    })
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100">Research Reports</h2>
          <p className="text-sm text-slate-400 mt-0.5">
            {reports ? `${reports.length} report${reports.length !== 1 ? 's' : ''}` : ''}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => refetch()}
            loading={isFetching}
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => setShowSearch(!showSearch)}
          >
            <Plus className="h-4 w-4" />
            New Analysis
          </Button>
        </div>
      </div>

      {showSearch && (
        <div className="rounded-xl border border-blue-500/20 bg-blue-500/5 p-4">
          <TickerSearchForm
            onSubmit={handleAnalyze}
            loading={startMutation.isPending}
            error={startMutation.error?.message}
          />
        </div>
      )}

      {error && (
        <ErrorAlert message={error.message} title="Failed to load reports" />
      )}

      {isLoading && (
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      )}

      {!isLoading && reports && reports.length === 0 && (
        <EmptyState
          icon={<FileText className="h-8 w-8" />}
          title="No reports yet"
          description="Start by analyzing a stock ticker to generate your first research report."
          action={
            <Button variant="primary" onClick={() => setShowSearch(true)}>
              <Plus className="h-4 w-4" />
              New Analysis
            </Button>
          }
        />
      )}

      {reports && reports.length > 0 && (
        <div className="space-y-4">
          {reports.map((report) => (
            <ReportCard
              key={report.id}
              report={report}
              onDelete={handleDelete}
              isDeleting={deletingId === report.id}
            />
          ))}
        </div>
      )}
    </div>
  )
}
