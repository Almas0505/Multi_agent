import { type ReactNode } from 'react'
import { cn } from '../../utils/cn'

interface EmptyStateProps {
  icon?: ReactNode
  title: string
  description?: string
  action?: ReactNode
  className?: string
}

export function EmptyState({ icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center gap-4 py-16 text-center',
        className
      )}
    >
      {icon && (
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-slate-700 text-slate-400">
          {icon}
        </div>
      )}
      <div className="flex flex-col gap-1">
        <h3 className="text-base font-semibold text-slate-200">{title}</h3>
        {description && (
          <p className="max-w-sm text-sm text-slate-400">{description}</p>
        )}
      </div>
      {action && <div>{action}</div>}
    </div>
  )
}
