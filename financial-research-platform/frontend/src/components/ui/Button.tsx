import { type ReactNode, type ButtonHTMLAttributes } from 'react'
import { cn } from '../../utils/cn'

type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost' | 'outline'
type ButtonSize = 'sm' | 'md' | 'lg'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode
  variant?: ButtonVariant
  size?: ButtonSize
  loading?: boolean
  className?: string
}

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    'bg-blue-600 hover:bg-blue-500 text-white border border-blue-500 disabled:bg-blue-800 disabled:border-blue-800',
  secondary:
    'bg-slate-700 hover:bg-slate-600 text-slate-200 border border-slate-600 disabled:bg-slate-800',
  danger:
    'bg-red-600 hover:bg-red-500 text-white border border-red-500 disabled:bg-red-800 disabled:border-red-800',
  ghost:
    'bg-transparent hover:bg-slate-700 text-slate-300 border border-transparent disabled:text-slate-600',
  outline:
    'bg-transparent hover:bg-slate-700 text-slate-300 border border-slate-600 disabled:text-slate-600',
}

const sizeClasses: Record<ButtonSize, string> = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base',
}

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  className,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        'inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-slate-900 disabled:cursor-not-allowed disabled:opacity-60',
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading && (
        <svg
          className="h-4 w-4 animate-spin"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
          />
        </svg>
      )}
      {children}
    </button>
  )
}
