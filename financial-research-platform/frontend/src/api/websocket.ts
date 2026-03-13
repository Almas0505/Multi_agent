export const getWebSocketUrl = (taskId: string): string => {
  const wsBase = import.meta.env.VITE_WS_BASE_URL ?? ''
  if (wsBase) {
    return `${wsBase}/ws/analysis/${taskId}`
  }
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  return `${protocol}//${host}/ws/analysis/${taskId}`
}
