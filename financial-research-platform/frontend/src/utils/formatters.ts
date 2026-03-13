export const formatCurrency = (value: number, compact = false): string => {
  if (compact) {
    const absValue = Math.abs(value)
    if (absValue >= 1e12) return `$${(value / 1e12).toFixed(2)}T`
    if (absValue >= 1e9) return `$${(value / 1e9).toFixed(2)}B`
    if (absValue >= 1e6) return `$${(value / 1e6).toFixed(2)}M`
    if (absValue >= 1e3) return `$${(value / 1e3).toFixed(2)}K`
  }
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
}

export const formatPercent = (value: number, decimals = 2): string => {
  return `${(value * 100).toFixed(decimals)}%`
}

export const formatNumber = (value: number, decimals = 2): string => {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value)
}

export const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export const formatAgentName = (agent: string): string => {
  const names: Record<string, string> = {
    fundamentals: 'Fundamentals Agent',
    sentiment: 'Sentiment Agent',
    technical: 'Technical Agent',
    competitor: 'Competitor Agent',
    risk: 'Risk Agent',
    final_analysis: 'Final Analysis Agent',
    orchestrator: 'Orchestrator',
  }
  return names[agent] ?? agent.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

export const formatRiskScore = (score: number): string => {
  if (score <= 30) return 'Low'
  if (score <= 60) return 'Medium'
  if (score <= 80) return 'High'
  return 'Critical'
}
