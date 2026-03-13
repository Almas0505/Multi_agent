import type { AgentName, AnalysisStatus } from './analysis'

export interface WebSocketMessage {
  agent: AgentName
  status: AnalysisStatus
  progress: number
  message: string
}

export type WebSocketState = 'connecting' | 'open' | 'closed' | 'error'
