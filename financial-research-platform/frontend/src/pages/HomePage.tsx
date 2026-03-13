import { useNavigate } from 'react-router-dom'
import { TrendingUp, FileText, BarChart2, ArrowRight, Activity } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { TickerSearchForm } from '../components/analysis/TickerSearchForm'
import { useStartAnalysis } from '../hooks/useAnalysis'
import { useReports } from '../hooks/useReports'
import { StatusBadge } from '../components/reports/StatusBadge'
import { RatingBadge } from '../components/reports/RatingBadge'
import { formatDate } from '../utils/formatters'

export function HomePage() {
  const navigate = useNavigate()
  const startMutation = useStartAnalysis()
  const { data: reports } = useReports()

  const handleAnalyze = (ticker: string) => {
    startMutation.mutate(ticker, {
      onSuccess: (response) => {
        navigate(`/analysis/${response.task_id}`)
      },
    })
  }

  const recentReports = reports?.slice(0, 5) ?? []
  const completedCount = reports?.filter((r) => r.status === 'completed').length ?? 0
  const runningCount = reports?.filter((r) => r.status === 'running' || r.status === 'pending').length ?? 0

  return (
    <div className="space-y-8">
      {/* Hero */}
      <div className="rounded-2xl bg-gradient-to-br from-blue-600/20 to-purple-600/10 border border-blue-500/20 p-8">
        <div className="max-w-2xl">
          <div className="flex items-center gap-2 mb-3">
            <Activity className="h-5 w-5 text-blue-400" />
            <span className="text-sm font-medium text-blue-400">AI-Powered Analysis</span>
          </div>
          <h2 className="text-2xl font-bold text-slate-100 mb-2">
            Research Any Stock in Minutes
          </h2>
          <p className="text-slate-400 text-sm mb-6">
            Our multi-agent AI system analyzes fundamentals, sentiment, technicals, competitors,
            and risk — generating comprehensive research reports automatically.
          </p>
          <TickerSearchForm
            onSubmit={handleAnalyze}
            loading={startMutation.isPending}
            error={startMutation.error?.message}
          />
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-500/20">
            <FileText className="h-6 w-6 text-blue-400" />
          </div>
          <div>
            <p className="text-2xl font-bold text-slate-100">{reports?.length ?? 0}</p>
            <p className="text-sm text-slate-500">Total Reports</p>
          </div>
        </Card>

        <Card className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-green-500/20">
            <BarChart2 className="h-6 w-6 text-green-400" />
          </div>
          <div>
            <p className="text-2xl font-bold text-slate-100">{completedCount}</p>
            <p className="text-sm text-slate-500">Completed</p>
          </div>
        </Card>

        <Card className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-amber-500/20">
            <TrendingUp className="h-6 w-6 text-amber-400" />
          </div>
          <div>
            <p className="text-2xl font-bold text-slate-100">{runningCount}</p>
            <p className="text-sm text-slate-500">In Progress</p>
          </div>
        </Card>
      </div>

      {/* Recent Reports */}
      {recentReports.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Recent Reports</CardTitle>
              <Button variant="ghost" size="sm" onClick={() => navigate('/reports')}>
                View All
                <ArrowRight className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="divide-y divide-slate-700/50">
              {recentReports.map((report) => (
                <div
                  key={report.id}
                  className="flex items-center justify-between py-3 cursor-pointer hover:bg-slate-700/20 -mx-2 px-2 rounded-lg transition-colors"
                  onClick={() => report.status === 'completed' && navigate(`/reports/${report.id}`)}
                >
                  <div className="flex items-center gap-3">
                    <span className="font-bold text-slate-200 w-16">{report.ticker}</span>
                    <StatusBadge status={report.status} />
                    {report.data?.final_analysis?.final_rating && (
                      <RatingBadge rating={report.data.final_analysis.final_rating} />
                    )}
                  </div>
                  <span className="text-xs text-slate-500 hidden sm:block">
                    {formatDate(report.created_at)}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* How it works */}
      <Card>
        <CardHeader>
          <CardTitle>How It Works</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            {[
              {
                step: '01',
                title: 'Enter a Ticker',
                desc: 'Type in any stock ticker symbol to start a comprehensive analysis.',
                color: 'text-blue-400',
              },
              {
                step: '02',
                title: 'AI Agents Analyze',
                desc: '6 specialized agents simultaneously analyze fundamentals, sentiment, technicals, competitors, and risk.',
                color: 'text-purple-400',
              },
              {
                step: '03',
                title: 'Get Your Report',
                desc: 'Receive a detailed research report with ratings, targets, and actionable insights.',
                color: 'text-green-400',
              },
            ].map((item) => (
              <div key={item.step} className="flex flex-col gap-2">
                <span className={`text-3xl font-bold ${item.color}`}>{item.step}</span>
                <h4 className="font-semibold text-slate-200">{item.title}</h4>
                <p className="text-sm text-slate-400">{item.desc}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
