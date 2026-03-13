import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card'
import { KeyMetricGrid } from '../charts/KeyMetricGrid'
import { RatingBadge } from '../reports/RatingBadge'
import { formatCurrency, formatPercent, formatNumber } from '../../utils/formatters'
import type { FundamentalsData } from '../../types/report'

interface FundamentalsSectionProps {
  data: FundamentalsData
}

export function FundamentalsSection({ data }: FundamentalsSectionProps) {
  const valuationMetrics = [
    { label: 'P/E Ratio', value: formatNumber(data.pe_ratio), subtext: 'Price to Earnings' },
    { label: 'P/B Ratio', value: formatNumber(data.pb_ratio), subtext: 'Price to Book' },
    { label: 'EV/EBITDA', value: formatNumber(data.ev_ebitda), subtext: 'Enterprise Value' },
    { label: 'DCF Fair Value', value: formatCurrency(data.dcf_fair_value), positive: true },
  ]

  const financialMetrics = [
    {
      label: 'Revenue Growth',
      value: formatPercent(data.revenue_growth),
      positive: data.revenue_growth > 0,
    },
    {
      label: 'Net Margin',
      value: formatPercent(data.net_margin),
      positive: data.net_margin > 0.1,
    },
    {
      label: 'Free Cash Flow',
      value: formatCurrency(data.free_cash_flow, true),
      positive: data.free_cash_flow > 0,
    },
    {
      label: 'ROE',
      value: formatPercent(data.roe),
      positive: data.roe > 0.15,
    },
    {
      label: 'Debt/Equity',
      value: formatNumber(data.debt_equity),
      positive: data.debt_equity < 1,
    },
  ]

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Valuation Metrics</CardTitle>
            <RatingBadge rating={data.rating} />
          </div>
        </CardHeader>
        <CardContent>
          <KeyMetricGrid metrics={valuationMetrics} columns={4} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Financial Health</CardTitle>
        </CardHeader>
        <CardContent>
          <KeyMetricGrid metrics={financialMetrics} columns={3} />
        </CardContent>
      </Card>

      {data.analysis_text && (
        <Card>
          <CardHeader>
            <CardTitle>Fundamentals Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-slate-300 leading-relaxed">{data.analysis_text}</p>
          </CardContent>
        </Card>
      )}

      {data.sec_summary && (
        <Card>
          <CardHeader>
            <CardTitle>SEC Filing Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-slate-300 leading-relaxed">{data.sec_summary}</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
