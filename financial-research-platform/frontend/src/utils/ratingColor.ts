import type { Rating } from '../types/report'

export const getRatingColor = (rating: Rating | string): string => {
  switch (rating) {
    case 'BUY':
    case 'STRONG_BUY':
      return 'text-green-400'
    case 'SELL':
    case 'STRONG_SELL':
      return 'text-red-400'
    case 'HOLD':
    default:
      return 'text-amber-400'
  }
}

export const getRatingBg = (rating: Rating | string): string => {
  switch (rating) {
    case 'BUY':
    case 'STRONG_BUY':
      return 'bg-green-500/20 text-green-400 border border-green-500/30'
    case 'SELL':
    case 'STRONG_SELL':
      return 'bg-red-500/20 text-red-400 border border-red-500/30'
    case 'HOLD':
    default:
      return 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
  }
}

export const getSentimentColor = (label: string): string => {
  switch (label) {
    case 'BULLISH':
      return 'text-green-400'
    case 'BEARISH':
      return 'text-red-400'
    default:
      return 'text-amber-400'
  }
}

export const getRiskLevelColor = (level: string): string => {
  switch (level) {
    case 'LOW':
      return 'text-green-400'
    case 'MEDIUM':
      return 'text-amber-400'
    case 'HIGH':
      return 'text-orange-400'
    case 'CRITICAL':
      return 'text-red-400'
    default:
      return 'text-slate-400'
  }
}

export const getRiskLevelBg = (level: string): string => {
  switch (level) {
    case 'LOW':
      return 'bg-green-500/20 text-green-400 border border-green-500/30'
    case 'MEDIUM':
      return 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
    case 'HIGH':
      return 'bg-orange-500/20 text-orange-400 border border-orange-500/30'
    case 'CRITICAL':
      return 'bg-red-500/20 text-red-400 border border-red-500/30'
    default:
      return 'bg-slate-500/20 text-slate-400 border border-slate-500/30'
  }
}

export const getStatusColor = (status: string): string => {
  switch (status) {
    case 'completed':
      return 'bg-green-500/20 text-green-400 border border-green-500/30'
    case 'running':
    case 'pending':
      return 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
    case 'failed':
    case 'error':
      return 'bg-red-500/20 text-red-400 border border-red-500/30'
    default:
      return 'bg-slate-500/20 text-slate-400 border border-slate-500/30'
  }
}

export const getScoreColor = (score: number): string => {
  if (score >= 70) return '#22c55e'
  if (score >= 50) return '#f59e0b'
  return '#ef4444'
}
