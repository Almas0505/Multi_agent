import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from 'recharts'

interface RiskMetricsChartProps {
  beta: number
  volatility: number
  sharpeRatio: number
  maxDrawdown: number
  riskScore: number
}

export function RiskMetricsChart({
  beta,
  volatility,
  sharpeRatio,
  maxDrawdown,
  riskScore,
}: RiskMetricsChartProps) {
  const normalise = (value: number, min: number, max: number): number => {
    return Math.min(100, Math.max(0, ((value - min) / (max - min)) * 100))
  }

  const data = [
    {
      metric: 'Beta',
      value: normalise(beta, 0, 3),
      raw: beta.toFixed(2),
    },
    {
      metric: 'Volatility',
      value: normalise(volatility, 0, 0.6),
      raw: `${(volatility * 100).toFixed(1)}%`,
    },
    {
      metric: 'Sharpe',
      value: normalise(sharpeRatio, 0, 3),
      raw: sharpeRatio.toFixed(2),
    },
    {
      metric: 'Drawdown',
      value: normalise(Math.abs(maxDrawdown), 0, 0.5),
      raw: `${(maxDrawdown * 100).toFixed(1)}%`,
    },
    {
      metric: 'Risk Score',
      value: riskScore,
      raw: `${riskScore}/100`,
    },
  ]

  return (
    <ResponsiveContainer width="100%" height={280}>
      <RadarChart data={data}>
        <PolarGrid stroke="#334155" />
        <PolarAngleAxis
          dataKey="metric"
          tick={{ fill: '#94a3b8', fontSize: 12 }}
        />
        <Radar
          name="Risk Metrics"
          dataKey="value"
          stroke="#ef4444"
          fill="#ef4444"
          fillOpacity={0.2}
          strokeWidth={2}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: '#1e293b',
            border: '1px solid #334155',
            borderRadius: '8px',
            color: '#e2e8f0',
          }}
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          formatter={(value: any, name: any, props: any) => [
            props?.payload?.raw ?? value,
            props?.payload?.metric ?? name,
          ]}
        />
      </RadarChart>
    </ResponsiveContainer>
  )
}
