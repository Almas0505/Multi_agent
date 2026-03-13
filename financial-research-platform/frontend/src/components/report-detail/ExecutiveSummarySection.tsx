import { TrendingUp, TrendingDown, AlertTriangle, Zap } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card'
import { ScoreGauge } from '../charts/ScoreGauge'
import { RatingBadge } from '../reports/RatingBadge'
import type { FinalAnalysis } from '../../types/report'

interface ExecutiveSummarySectionProps {
  data: FinalAnalysis
}

export function ExecutiveSummarySection({ data }: ExecutiveSummarySectionProps) {
  return (
    <div className="space-y-6">
      {/* Overview row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="flex flex-col items-center justify-center py-8">
          <ScoreGauge score={data.composite_score} label="Composite Score" />
          <div className="mt-4 text-center">
            <RatingBadge rating={data.final_rating} className="text-base px-4 py-1.5" />
          </div>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Executive Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-slate-300 leading-relaxed">{data.executive_summary}</p>
            <div className="mt-4 flex flex-wrap gap-3">
              <div className="text-center">
                <p className="text-xl font-bold text-slate-100">{data.confidence_score}%</p>
                <p className="text-xs text-slate-500">Confidence</p>
              </div>
              {data.target_price && (
                <div className="text-center">
                  <p className="text-xl font-bold text-green-400">${data.target_price.toFixed(2)}</p>
                  <p className="text-xs text-slate-500">Target Price</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Catalysts & Risks */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-green-400" />
              <CardTitle>Key Catalysts</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            {data.key_catalysts && data.key_catalysts.length > 0 ? (
              <ul className="space-y-2">
                {data.key_catalysts.map((catalyst, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                    <TrendingUp className="h-4 w-4 text-green-400 mt-0.5 shrink-0" />
                    {catalyst}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-slate-500">No catalysts identified</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-red-400" />
              <CardTitle>Key Risks</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            {data.key_risks && data.key_risks.length > 0 ? (
              <ul className="space-y-2">
                {data.key_risks.map((risk, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                    <TrendingDown className="h-4 w-4 text-red-400 mt-0.5 shrink-0" />
                    {risk}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-slate-500">No key risks identified</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
