import { AlertCircle, X } from 'lucide-react'
import { cn } from '../../utils/cn'

interface ErrorAlertProps {
  title?: string
  message: string
  onDismiss?: () => void
  className?: string
}

export function ErrorAlert({ title = 'Error', message, onDismiss, className }: ErrorAlertProps) {
  return (
    <div
      role="alert"
      className={cn(
        'flex items-start gap-3 rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-red-400',
        className
      )}
    >
      <AlertCircle className="mt-0.5 h-5 w-5 shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="font-semibold text-sm">{title}</p>
        <p className="text-sm text-red-300 mt-0.5">{message}</p>
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="shrink-0 rounded p-0.5 hover:bg-red-500/20 transition-colors"
          aria-label="Dismiss"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  )
}
