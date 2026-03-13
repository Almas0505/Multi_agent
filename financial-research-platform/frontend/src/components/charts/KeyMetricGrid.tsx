import { cn } from '../../utils/cn'

interface Metric {
  label: string
  value: string
  subtext?: string
  positive?: boolean | null
}

interface KeyMetricGridProps {
  metrics: Metric[]
  columns?: 2 | 3 | 4
}

export function KeyMetricGrid({ metrics, columns = 3 }: KeyMetricGridProps) {
  const gridCols = {
    2: 'grid-cols-2',
    3: 'grid-cols-2 sm:grid-cols-3',
    4: 'grid-cols-2 sm:grid-cols-4',
  }

  return (
    <div className={cn('grid gap-3', gridCols[columns])}>
      {metrics.map((metric, i) => (
        <div
          key={i}
          className="rounded-lg bg-slate-700/40 border border-slate-700 px-4 py-3"
        >
          <p className="text-xs text-slate-500 mb-1">{metric.label}</p>
          <p
            className={cn(
              'text-lg font-bold',
              metric.positive === true
                ? 'text-green-400'
                : metric.positive === false
                ? 'text-red-400'
                : 'text-slate-100'
            )}
          >
            {metric.value}
          </p>
          {metric.subtext && (
            <p className="text-xs text-slate-500 mt-0.5">{metric.subtext}</p>
          )}
        </div>
      ))}
    </div>
  )
}
