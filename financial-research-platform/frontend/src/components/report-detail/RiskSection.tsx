import { AlertTriangle, TrendingDown } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card'
import { KeyMetricGrid } from '../charts/KeyMetricGrid'
import { RiskMetricsChart } from '../charts/RiskMetricsChart'
import { RatingBadge } from '../reports/RatingBadge'
import { cn } from '../../utils/cn'
import { getRiskLevelBg, getRiskLevelColor } from '../../utils/ratingColor'
import { formatNumber, formatPercent } from '../../utils/formatters'
import type { RiskData } from '../../types/report'

interface RiskSectionProps {
  data: RiskData
}

export function RiskSection({ data }: RiskSectionProps) {
  const riskMetrics = [
    {
      label: 'Beta',
      value: formatNumber(data.beta),
      positive: data.beta < 1.5,
    },
    {
      label: 'VaR (95%)',
      value: formatPercent(data.var_95),
      positive: data.var_95 > -0.05,
    },
    {
      label: 'Max Drawdown',
      value: formatPercent(data.max_drawdown),
      positive: data.max_drawdown > -0.2,
    },
    {
      label: 'Volatility',
      value: formatPercent(data.volatility),
      positive: data.volatility < 0.3,
    },
    {
      label: 'Sharpe Ratio',
      value: formatNumber(data.sharpe_ratio),
      positive: data.sharpe_ratio > 1,
    },
    {
      label: 'Risk Score',
      value: `${data.risk_score}/100`,
      positive: data.risk_score < 50,
    },
  ]

  return (
    <div className="space-y-6">
      {/* Risk Overview */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-amber-400" />
              <CardTitle>Risk Assessment</CardTitle>
            </div>
            <div className="flex items-center gap-2">
              <span className={cn('text-sm font-semibold px-3 py-1 rounded-full', getRiskLevelBg(data.risk_level))}>
                {data.risk_level}
              </span>
              <RatingBadge rating={data.rating} />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4 mb-4">
            <div className="text-4xl font-bold" style={{ color: data.risk_score > 60 ? '#ef4444' : data.risk_score > 30 ? '#f59e0b' : '#22c55e' }}>
              {data.risk_score}
            </div>
            <div>
              <p className="text-sm font-medium text-slate-200">Risk Score</p>
              <p className={cn('text-sm', getRiskLevelColor(data.risk_level))}>
                {data.risk_level} Risk
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Risk Metrics Grid */}
      <Card>
        <CardHeader>
          <CardTitle>Risk Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <KeyMetricGrid metrics={riskMetrics} columns={3} />
        </CardContent>
      </Card>

      {/* Radar Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Risk Profile</CardTitle>
        </CardHeader>
        <CardContent>
          <RiskMetricsChart
            beta={data.beta}
            volatility={data.volatility}
            sharpeRatio={data.sharpe_ratio}
            maxDrawdown={data.max_drawdown}
            riskScore={data.risk_score}
          />
        </CardContent>
      </Card>

      {/* Key Risks */}
      {data.key_risks && data.key_risks.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Key Risk Factors</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {data.key_risks.map((risk, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                  <TrendingDown className="h-4 w-4 text-red-400 mt-0.5 shrink-0" />
                  {risk}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {data.analysis_text && (
        <Card>
          <CardHeader>
            <CardTitle>Risk Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-slate-300 leading-relaxed">{data.analysis_text}</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
