import { useState, useCallback, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { CheckCircle2, FileText, Search } from 'lucide-react'
import { AnalysisProgressTracker } from '../components/analysis/AnalysisProgressTracker'
import { TickerSearchForm } from '../components/analysis/TickerSearchForm'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { ErrorAlert } from '../components/ui/ErrorAlert'
import { Spinner } from '../components/ui/Spinner'
import { useWebSocket } from '../hooks/useWebSocket'
import { useStartAnalysis } from '../hooks/useAnalysis'
import type { AgentStep } from '../types/analysis'
import type { WebSocketMessage } from '../types/websocket'

export function AnalysisPage() {
  const { taskId } = useParams<{ taskId?: string }>()
  const navigate = useNavigate()
  const startMutation = useStartAnalysis()

  const [steps, setSteps] = useState<AgentStep[]>([])
  const [isCompleted, setIsCompleted] = useState(false)
  const [isFailed, setIsFailed] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [ticker, setTicker] = useState<string | undefined>()

  const handleMessage = useCallback((msg: WebSocketMessage) => {
    setSteps((prev) => {
      const idx = prev.findIndex((s) => s.agent === msg.agent)
      const updated: AgentStep = {
        agent: msg.agent,
        status: msg.status,
        progress: msg.progress,
        message: msg.message,
        timestamp: new Date().toISOString(),
      }
      if (idx === -1) return [...prev, updated]
      const next = [...prev]
      next[idx] = updated
      return next
    })

    if (msg.status === 'completed' && msg.agent === 'final_analysis') {
      setIsCompleted(true)
    }
    if (msg.status === 'failed' || msg.status === 'error') {
      setIsFailed(true)
      setErrorMessage(msg.message)
    }
  }, [])

  const handleWsError = useCallback(() => {
    setErrorMessage('WebSocket connection failed. The analysis may still be running.')
  }, [])

  const { state: wsState } = useWebSocket(taskId, {
    onMessage: handleMessage,
    onError: handleWsError,
    enabled: !!taskId && !isCompleted && !isFailed,
  })

  useEffect(() => {
    const orchestratorStep = steps.find((s) => s.agent === 'orchestrator')
    if (orchestratorStep?.message) {
      const match = orchestratorStep.message.match(/\b([A-Z]{1,10})\b/)
      if (match) setTicker(match[1])
    }
  }, [steps])

  const handleAnalyze = (sym: string) => {
    setTicker(sym)
    setSteps([])
    setIsCompleted(false)
    setIsFailed(false)
    setErrorMessage(null)
    startMutation.mutate(sym, {
      onSuccess: (res) => navigate(`/analysis/${res.task_id}`),
    })
  }

  // No taskId — show the search form
  if (!taskId) {
    return (
      <div className="max-w-2xl mx-auto space-y-6">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Search className="h-5 w-5 text-blue-400" />
              <CardTitle>Start New Analysis</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-slate-400 mb-4">
              Enter a stock ticker to begin a comprehensive multi-agent financial analysis.
            </p>
            <TickerSearchForm
              onSubmit={handleAnalyze}
              loading={startMutation.isPending}
              error={startMutation.error?.message}
            />
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {wsState === 'connecting' && steps.length === 0 && (
        <Card>
          <CardContent className="py-8">
            <Spinner size="lg" label="Connecting to analysis stream..." />
          </CardContent>
        </Card>
      )}

      {errorMessage && !isFailed && (
        <ErrorAlert
          title="Connection Warning"
          message={errorMessage}
          onDismiss={() => setErrorMessage(null)}
        />
      )}

      {steps.length > 0 && (
        <AnalysisProgressTracker
          steps={steps}
          wsState={wsState}
          ticker={ticker}
        />
      )}

      {isCompleted && (
        <Card>
          <CardContent className="py-8 flex flex-col items-center gap-4 text-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-green-500/20">
              <CheckCircle2 className="h-8 w-8 text-green-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-slate-100">Analysis Complete!</h3>
              <p className="text-sm text-slate-400 mt-1">
                Your financial research report is ready to view.
              </p>
            </div>
            <Button
              variant="primary"
              size="lg"
              onClick={() => navigate(`/reports/${taskId}`)}
            >
              <FileText className="h-5 w-5" />
              View Full Report
            </Button>
          </CardContent>
        </Card>
      )}

      {isFailed && (
        <Card>
          <CardContent className="py-8 flex flex-col items-center gap-4 text-center">
            <div>
              <h3 className="text-lg font-semibold text-red-400">Analysis Failed</h3>
              <p className="text-sm text-slate-400 mt-1">
                {errorMessage ?? 'An error occurred during analysis.'}
              </p>
            </div>
            <Button variant="secondary" onClick={() => navigate('/analysis')}>
              Try Again
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
