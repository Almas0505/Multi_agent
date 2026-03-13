import { cn } from '../../utils/cn'

interface ProgressBarProps {
  value: number
  max?: number
  className?: string
  barClassName?: string
  showLabel?: boolean
  size?: 'sm' | 'md' | 'lg'
}

const sizeClasses = {
  sm: 'h-1',
  md: 'h-2',
  lg: 'h-3',
}

export function ProgressBar({
  value,
  max = 100,
  className,
  barClassName,
  showLabel = false,
  size = 'md',
}: ProgressBarProps) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100))

  return (
    <div className={cn('w-full', className)}>
      {showLabel && (
        <div className="mb-1 flex justify-end">
          <span className="text-xs text-slate-400">{Math.round(pct)}%</span>
        </div>
      )}
      <div className={cn('w-full overflow-hidden rounded-full bg-slate-700', sizeClasses[size])}>
        <div
          className={cn(
            'h-full rounded-full bg-blue-500 transition-all duration-500 ease-out',
            barClassName
          )}
          style={{ width: `${pct}%` }}
          role="progressbar"
          aria-valuenow={Math.round(pct)}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
    </div>
  )
}
