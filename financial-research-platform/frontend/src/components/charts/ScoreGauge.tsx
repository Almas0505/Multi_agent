import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'
import { getScoreColor } from '../../utils/ratingColor'

interface ScoreGaugeProps {
  score: number
  label?: string
  size?: number
}

export function ScoreGauge({ score, label = 'Score', size = 200 }: ScoreGaugeProps) {
  const clamped = Math.min(100, Math.max(0, score))
  const color = getScoreColor(clamped)

  const data = [
    { value: clamped, fill: color },
    { value: 100 - clamped, fill: '#1e293b' },
  ]

  return (
    <div className="flex flex-col items-center">
      <div style={{ width: size, height: size / 2 + 20 }} className="relative">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="100%"
              startAngle={180}
              endAngle={0}
              innerRadius={size * 0.32}
              outerRadius={size * 0.46}
              dataKey="value"
              stroke="none"
            >
              {data.map((entry, index) => (
                <Cell key={index} fill={entry.fill} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value: number) => [`${value}`, label]}
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '8px',
                color: '#e2e8f0',
              }}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 flex flex-col items-center justify-end pb-2">
          <span className="text-3xl font-bold" style={{ color }}>
            {Math.round(clamped)}
          </span>
          <span className="text-xs text-slate-400">{label}</span>
        </div>
      </div>
    </div>
  )
}
