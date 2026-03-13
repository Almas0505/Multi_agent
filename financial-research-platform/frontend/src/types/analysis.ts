export type AnalysisStatus =
  | 'pending'
  | 'running'
  | 'completed'
  | 'failed'
  | 'error'

export type AgentName =
  | 'fundamentals'
  | 'sentiment'
  | 'technical'
  | 'competitor'
  | 'risk'
  | 'final_analysis'
  | 'orchestrator'

export interface AnalysisStartResponse {
  task_id: string
  status: AnalysisStatus
  message: string
}

export interface AnalysisStatusResponse {
  agent: AgentName
  status: AnalysisStatus
  progress: number
  message: string
}

export interface AgentStep {
  agent: AgentName
  status: AnalysisStatus
  progress: number
  message: string
  timestamp?: string
}
