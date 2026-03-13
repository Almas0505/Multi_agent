import { Download, ArrowLeft } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { Button } from '../ui/Button'
import { RatingBadge } from '../reports/RatingBadge'
import { StatusBadge } from '../reports/StatusBadge'
import { formatDate } from '../../utils/formatters'
import { getReportDownloadUrl } from '../../api/reports'
import type { ReportResponse } from '../../types/report'

interface ReportHeaderProps {
  report: ReportResponse
}

export function ReportHeader({ report }: ReportHeaderProps) {
  const navigate = useNavigate()
  const final = report.data?.final_analysis

  return (
    <div className="flex flex-col gap-4 mb-6">
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="sm" onClick={() => navigate('/reports')}>
          <ArrowLeft className="h-4 w-4" />
          Back to Reports
        </Button>
      </div>

      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-3xl font-bold text-slate-100">{report.ticker}</h1>
            <StatusBadge status={report.status} />
            {final?.final_rating && (
              <RatingBadge rating={final.final_rating} className="text-sm px-3 py-1" />
            )}
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Report ID: <span className="font-mono text-slate-500">{report.id}</span>
          </p>
          <p className="text-sm text-slate-500 mt-0.5">
            Generated {formatDate(report.created_at)}
          </p>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          {final && (
            <div className="flex gap-4 text-center">
              <div>
                <p className="text-2xl font-bold text-blue-400">{final.composite_score}</p>
                <p className="text-xs text-slate-500">Composite Score</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-300">{final.confidence_score}%</p>
                <p className="text-xs text-slate-500">Confidence</p>
              </div>
              {final.target_price && (
                <div>
                  <p className="text-2xl font-bold text-green-400">${final.target_price}</p>
                  <p className="text-xs text-slate-500">Target Price</p>
                </div>
              )}
            </div>
          )}
          {report.status === 'completed' && (
            <Button
              variant="primary"
              size="sm"
              onClick={() => window.open(getReportDownloadUrl(report.id), '_blank')}
            >
              <Download className="h-4 w-4" />
              Download PDF
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
