import { useMemo } from 'react'
import { AgentStepCard } from './AgentStepCard'
import { ProgressBar } from './ProgressBar'
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card'
import type { AgentStep } from '../../types/analysis'
import type { WebSocketState } from '../../types/websocket'

const AGENT_ORDER: string[] = [
  'orchestrator',
  'fundamentals',
  'sentiment',
  'technical',
  'competitor',
  'risk',
  'final_analysis',
]

interface AnalysisProgressTrackerProps {
  steps: AgentStep[]
  wsState: WebSocketState
  ticker?: string
}

export function AnalysisProgressTracker({
  steps,
  wsState,
  ticker,
}: AnalysisProgressTrackerProps) {
  const stepMap = useMemo(() => {
    const map = new Map<string, AgentStep>()
    for (const step of steps) {
      map.set(step.agent, step)
    }
    return map
  }, [steps])

  const overallProgress = useMemo(() => {
    if (steps.length === 0) return 0
    const latest = steps[steps.length - 1]
    const agentIdx = AGENT_ORDER.indexOf(latest.agent)
    if (agentIdx === -1) return latest.progress

    const baseProgress = (agentIdx / AGENT_ORDER.length) * 100
    const agentShare = (1 / AGENT_ORDER.length) * 100
    return baseProgress + (latest.progress / 100) * agentShare
  }, [steps])

  const activeAgent = steps.length > 0 ? steps[steps.length - 1].agent : null

  const connectionLabel =
    wsState === 'connecting'
      ? 'Connecting...'
      : wsState === 'open'
      ? 'Live'
      : wsState === 'error'
      ? 'Connection error'
      : 'Disconnected'

  const connectionColor =
    wsState === 'open'
      ? 'text-green-400'
      : wsState === 'error'
      ? 'text-red-400'
      : wsState === 'connecting'
      ? 'text-blue-400'
      : 'text-slate-500'

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>
            {ticker ? `Analyzing ${ticker}` : 'Analysis in Progress'}
          </CardTitle>
          <span className={`text-xs font-medium ${connectionColor}`}>
            {connectionLabel}
          </span>
        </div>
      </CardHeader>
      <CardContent>
        <div className="mb-6">
          <div className="flex justify-between mb-2">
            <span className="text-xs text-slate-400">Overall Progress</span>
            <span className="text-xs text-slate-400">{Math.round(overallProgress)}%</span>
          </div>
          <ProgressBar value={overallProgress} size="lg" />
        </div>

        <div className="space-y-3">
          {AGENT_ORDER.map((agentName) => {
            const step = stepMap.get(agentName)
            if (!step) {
              return (
                <AgentStepCard
                  key={agentName}
                  step={{
                    agent: agentName as AgentStep['agent'],
                    status: 'pending',
                    progress: 0,
                    message: 'Waiting...',
                  }}
                  isActive={false}
                />
              )
            }
            return (
              <AgentStepCard
                key={agentName}
                step={step}
                isActive={activeAgent === agentName}
              />
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
