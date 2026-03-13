import { BarChart2 } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card'
import { KeyMetricGrid } from '../charts/KeyMetricGrid'
import { RatingBadge } from '../reports/RatingBadge'
import { Badge } from '../ui/Badge'
import { formatNumber } from '../../utils/formatters'
import type { TechnicalData } from '../../types/report'

interface TechnicalSectionProps {
  data: TechnicalData
}

export function TechnicalSection({ data }: TechnicalSectionProps) {
  const trendVariant = data.trend === 'BULLISH' ? 'success' : data.trend === 'BEARISH' ? 'danger' : 'warning'

  const oscillatorMetrics = [
    {
      label: 'RSI (14)',
      value: formatNumber(data.rsi),
      positive: data.rsi > 50 && data.rsi < 70,
      subtext: data.rsi > 70 ? 'Overbought' : data.rsi < 30 ? 'Oversold' : 'Neutral',
    },
    {
      label: 'MACD',
      value: formatNumber(data.macd),
      positive: data.macd > data.signal_line,
    },
    {
      label: 'Signal Line',
      value: formatNumber(data.signal_line),
    },
  ]

  const movingAverages = [
    { label: 'SMA 20', value: formatNumber(data.sma20) },
    { label: 'SMA 50', value: formatNumber(data.sma50) },
    { label: 'BB Upper', value: formatNumber(data.bb_upper) },
    { label: 'BB Middle', value: formatNumber(data.bb_middle) },
    { label: 'BB Lower', value: formatNumber(data.bb_lower) },
  ]

  const levelMetrics = [
    { label: 'Support', value: formatNumber(data.support), positive: null },
    { label: 'Resistance', value: formatNumber(data.resistance), positive: null },
  ]

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <BarChart2 className="h-5 w-5 text-blue-400" />
              <CardTitle>Technical Overview</CardTitle>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant={trendVariant}>{data.trend}</Badge>
              <RatingBadge rating={data.rating} />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-lg bg-slate-700/40 border border-slate-700 px-4 py-3 col-span-2 sm:col-span-1">
              <p className="text-xs text-slate-500 mb-1">Current Trend</p>
              <p className={`text-lg font-bold ${trendVariant === 'success' ? 'text-green-400' : trendVariant === 'danger' ? 'text-red-400' : 'text-amber-400'}`}>
                {data.trend}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Oscillators</CardTitle>
        </CardHeader>
        <CardContent>
          <KeyMetricGrid metrics={oscillatorMetrics} columns={3} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Moving Averages & Bollinger Bands</CardTitle>
        </CardHeader>
        <CardContent>
          <KeyMetricGrid metrics={movingAverages} columns={3} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Support & Resistance</CardTitle>
        </CardHeader>
        <CardContent>
          <KeyMetricGrid metrics={levelMetrics} columns={2} />
        </CardContent>
      </Card>

      {data.analysis_text && (
        <Card>
          <CardHeader>
            <CardTitle>Technical Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-slate-300 leading-relaxed">{data.analysis_text}</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
