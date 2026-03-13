import { type ReactNode } from 'react'
import { cn } from '../../utils/cn'

type BadgeVariant = 'default' | 'success' | 'danger' | 'warning' | 'info' | 'neutral'

interface BadgeProps {
  children: ReactNode
  variant?: BadgeVariant
  className?: string
}

const variantClasses: Record<BadgeVariant, string> = {
  default: 'bg-slate-700 text-slate-300 border border-slate-600',
  success: 'bg-green-500/20 text-green-400 border border-green-500/30',
  danger: 'bg-red-500/20 text-red-400 border border-red-500/30',
  warning: 'bg-amber-500/20 text-amber-400 border border-amber-500/30',
  info: 'bg-blue-500/20 text-blue-400 border border-blue-500/30',
  neutral: 'bg-slate-500/20 text-slate-400 border border-slate-500/30',
}

export function Badge({ children, variant = 'default', className }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold',
        variantClasses[variant],
        className
      )}
    >
      {children}
    </span>
  )
}
