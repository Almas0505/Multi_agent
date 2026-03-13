import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts'

interface SentimentMeterProps {
  score: number
  label: string
}

export function SentimentMeter({ score, label }: SentimentMeterProps) {
  const clamped = Math.min(10, Math.max(0, score))
  const normalised = (clamped / 10) * 100

  let color = '#f59e0b'
  if (clamped >= 6) color = '#22c55e'
  if (clamped < 4) color = '#ef4444'

  const data = [
    { value: normalised, fill: color },
    { value: 100 - normalised, fill: '#1e293b' },
  ]

  return (
    <div className="flex flex-col items-center">
      <div className="relative" style={{ width: 160, height: 90 }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="100%"
              startAngle={180}
              endAngle={0}
              innerRadius={48}
              outerRadius={68}
              dataKey="value"
              stroke="none"
            >
              {data.map((entry, index) => (
                <Cell key={index} fill={entry.fill} />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 flex flex-col items-center justify-end pb-1">
          <span className="text-2xl font-bold" style={{ color }}>
            {clamped.toFixed(1)}
          </span>
          <span className="text-xs text-slate-400">/10</span>
        </div>
      </div>
      <span
        className="mt-1 text-sm font-semibold"
        style={{ color }}
      >
        {label}
      </span>
    </div>
  )
}
