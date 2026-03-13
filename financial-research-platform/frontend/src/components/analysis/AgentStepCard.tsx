import { CheckCircle2, XCircle, Loader2, Clock, ChevronRight } from 'lucide-react'
import { cn } from '../../utils/cn'
import { formatAgentName } from '../../utils/formatters'
import { ProgressBar } from './ProgressBar'
import type { AgentStep } from '../../types/analysis'

interface AgentStepCardProps {
  step: AgentStep
  isActive?: boolean
}

function StatusIcon({ status }: { status: string }) {
  switch (status) {
    case 'completed':
      return <CheckCircle2 className="h-5 w-5 text-green-400" />
    case 'failed':
    case 'error':
      return <XCircle className="h-5 w-5 text-red-400" />
    case 'running':
      return <Loader2 className="h-5 w-5 text-blue-400 animate-spin" />
    default:
      return <Clock className="h-5 w-5 text-slate-500" />
  }
}

function statusBorderColor(status: string, isActive: boolean): string {
  if (status === 'completed') return 'border-green-500/30'
  if (status === 'failed' || status === 'error') return 'border-red-500/30'
  if (isActive || status === 'running') return 'border-blue-500/30'
  return 'border-slate-700'
}

function statusBgColor(status: string, isActive: boolean): string {
  if (status === 'completed') return 'bg-green-500/5'
  if (status === 'failed' || status === 'error') return 'bg-red-500/5'
  if (isActive || status === 'running') return 'bg-blue-500/5'
  return ''
}

export function AgentStepCard({ step, isActive = false }: AgentStepCardProps) {
  return (
    <div
      className={cn(
        'flex items-start gap-4 rounded-lg border p-4 transition-all duration-300',
        statusBorderColor(step.status, isActive),
        statusBgColor(step.status, isActive)
      )}
    >
      <div className="mt-0.5 shrink-0">
        <StatusIcon status={step.status} />
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2 mb-1">
          <span className="text-sm font-medium text-slate-200">
            {formatAgentName(step.agent)}
          </span>
          {(step.status === 'running' || step.status === 'completed') && (
            <span className="text-xs text-slate-500 shrink-0">{step.progress}%</span>
          )}
        </div>

        {step.message && (
          <p className="text-xs text-slate-400 mb-2 truncate">{step.message}</p>
        )}

        {(step.status === 'running' || step.status === 'completed') && (
          <ProgressBar
            value={step.progress}
            size="sm"
            barClassName={step.status === 'completed' ? 'bg-green-500' : 'bg-blue-500'}
          />
        )}
      </div>

      {step.status === 'pending' && (
        <ChevronRight className="h-4 w-4 text-slate-600 shrink-0 mt-0.5" />
      )}
    </div>
  )
}
