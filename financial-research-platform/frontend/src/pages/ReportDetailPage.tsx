import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { BarChart2, TrendingUp, Brain, Users, AlertTriangle, FileText } from 'lucide-react'
import { useReport } from '../hooks/useReport'
import { ReportHeader } from '../components/report-detail/ReportHeader'
import { ReportTabs } from '../components/report-detail/ReportTabs'
import { ExecutiveSummarySection } from '../components/report-detail/ExecutiveSummarySection'
import { FundamentalsSection } from '../components/report-detail/FundamentalsSection'
import { SentimentSection } from '../components/report-detail/SentimentSection'
import { TechnicalSection } from '../components/report-detail/TechnicalSection'
import { CompetitorSection } from '../components/report-detail/CompetitorSection'
import { RiskSection } from '../components/report-detail/RiskSection'
import { ErrorAlert } from '../components/ui/ErrorAlert'
import { Spinner } from '../components/ui/Spinner'
import { SkeletonCard } from '../components/ui/Skeleton'
import { EmptyState } from '../components/ui/EmptyState'

type TabId = 'summary' | 'fundamentals' | 'sentiment' | 'technical' | 'competitor' | 'risk'

const TABS = [
  { id: 'summary' as TabId, label: 'Executive Summary', icon: <FileText className="h-4 w-4" /> },
  { id: 'fundamentals' as TabId, label: 'Fundamentals', icon: <BarChart2 className="h-4 w-4" /> },
  { id: 'sentiment' as TabId, label: 'Sentiment', icon: <Brain className="h-4 w-4" /> },
  { id: 'technical' as TabId, label: 'Technical', icon: <TrendingUp className="h-4 w-4" /> },
  { id: 'competitor' as TabId, label: 'Competitors', icon: <Users className="h-4 w-4" /> },
  { id: 'risk' as TabId, label: 'Risk', icon: <AlertTriangle className="h-4 w-4" /> },
]

export function ReportDetailPage() {
  const { reportId } = useParams<{ reportId: string }>()
  const { data: report, isLoading, error } = useReport(reportId)
  const [activeTab, setActiveTab] = useState<TabId>('summary')

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="h-8 w-32 bg-slate-700 animate-pulse rounded-lg" />
          <div className="h-10 w-40 bg-slate-700 animate-pulse rounded-lg" />
        </div>
        <SkeletonCard />
        <SkeletonCard />
      </div>
    )
  }

  if (error) {
    return (
      <ErrorAlert
        title="Failed to load report"
        message={error.message}
      />
    )
  }

  if (!report) {
    return (
      <EmptyState
        title="Report not found"
        description="The requested report could not be found."
      />
    )
  }

  if (report.status !== 'completed') {
    return (
      <div className="space-y-4">
        <ReportHeader report={report} />
        <div className="flex flex-col items-center gap-4 py-16">
          <Spinner size="lg" />
          <p className="text-slate-400">
            Analysis is {report.status}. Please check back shortly.
          </p>
        </div>
      </div>
    )
  }

  const data = report.data

  return (
    <div>
      <ReportHeader report={report} />

      <ReportTabs
        tabs={TABS}
        activeTab={activeTab}
        onChange={(id) => setActiveTab(id as TabId)}
      />

      <div role="tabpanel">
        {activeTab === 'summary' && data.final_analysis && (
          <ExecutiveSummarySection data={data.final_analysis} />
        )}
        {activeTab === 'fundamentals' && data.fundamentals && (
          <FundamentalsSection data={data.fundamentals} />
        )}
        {activeTab === 'sentiment' && data.sentiment && (
          <SentimentSection data={data.sentiment} />
        )}
        {activeTab === 'technical' && data.technical && (
          <TechnicalSection data={data.technical} />
        )}
        {activeTab === 'competitor' && data.competitor && (
          <CompetitorSection data={data.competitor} />
        )}
        {activeTab === 'risk' && data.risk && (
          <RiskSection data={data.risk} />
        )}

        {/* Fallback for missing data sections */}
        {activeTab === 'summary' && !data.final_analysis && (
          <EmptyState title="Summary data not available" description="This section has no data." />
        )}
        {activeTab === 'fundamentals' && !data.fundamentals && (
          <EmptyState title="Fundamentals data not available" description="This section has no data." />
        )}
        {activeTab === 'sentiment' && !data.sentiment && (
          <EmptyState title="Sentiment data not available" description="This section has no data." />
        )}
        {activeTab === 'technical' && !data.technical && (
          <EmptyState title="Technical data not available" description="This section has no data." />
        )}
        {activeTab === 'competitor' && !data.competitor && (
          <EmptyState title="Competitor data not available" description="This section has no data." />
        )}
        {activeTab === 'risk' && !data.risk && (
          <EmptyState title="Risk data not available" description="This section has no data." />
        )}
      </div>
    </div>
  )
}
