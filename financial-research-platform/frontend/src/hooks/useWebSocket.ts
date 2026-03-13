import { useEffect, useRef, useCallback, useState } from 'react'
import { getWebSocketUrl } from '../api/websocket'
import type { WebSocketMessage, WebSocketState } from '../types/websocket'

const TERMINAL_STATUSES = new Set(['completed', 'failed', 'error'])
const MAX_RETRIES = 3
const BASE_DELAY_MS = 1000

interface UseWebSocketOptions {
  onMessage: (msg: WebSocketMessage) => void
  onError?: (event: Event) => void
  enabled?: boolean
}

interface UseWebSocketReturn {
  state: WebSocketState
  disconnect: () => void
}

export function useWebSocket(
  taskId: string | undefined,
  options: UseWebSocketOptions
): UseWebSocketReturn {
  const { onMessage, onError, enabled = true } = options
  const [state, setState] = useState<WebSocketState>('closed')
  const wsRef = useRef<WebSocket | null>(null)
  const retriesRef = useRef(0)
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const unmountedRef = useRef(false)
  const shouldConnectRef = useRef(true)

  const onMessageRef = useRef(onMessage)
  const onErrorRef = useRef(onError)
  useEffect(() => {
    onMessageRef.current = onMessage
  }, [onMessage])
  useEffect(() => {
    onErrorRef.current = onError
  }, [onError])

  const cleanup = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
      timeoutRef.current = null
    }
    if (wsRef.current) {
      wsRef.current.onopen = null
      wsRef.current.onmessage = null
      wsRef.current.onerror = null
      wsRef.current.onclose = null
      if (
        wsRef.current.readyState === WebSocket.OPEN ||
        wsRef.current.readyState === WebSocket.CONNECTING
      ) {
        wsRef.current.close(1000, 'cleanup')
      }
      wsRef.current = null
    }
  }, [])

  const connect = useCallback(() => {
    if (!taskId || unmountedRef.current || !shouldConnectRef.current) return

    cleanup()
    setState('connecting')

    const url = getWebSocketUrl(taskId)
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      if (unmountedRef.current) return
      retriesRef.current = 0
      setState('open')
    }

    ws.onmessage = (event: MessageEvent) => {
      if (unmountedRef.current) return
      try {
        const msg: WebSocketMessage = JSON.parse(event.data as string)
        onMessageRef.current(msg)
        if (TERMINAL_STATUSES.has(msg.status)) {
          shouldConnectRef.current = false
          cleanup()
          setState('closed')
        }
      } catch {
        // ignore parse errors
      }
    }

    ws.onerror = (event: Event) => {
      if (unmountedRef.current) return
      setState('error')
      onErrorRef.current?.(event)
    }

    ws.onclose = (event: CloseEvent) => {
      if (unmountedRef.current || !shouldConnectRef.current) return
      wsRef.current = null

      if (!event.wasClean && retriesRef.current < MAX_RETRIES) {
        const delay = BASE_DELAY_MS * Math.pow(2, retriesRef.current)
        retriesRef.current += 1
        setState('connecting')
        timeoutRef.current = setTimeout(() => {
          if (!unmountedRef.current && shouldConnectRef.current) {
            connect()
          }
        }, delay)
      } else {
        setState('closed')
      }
    }
  }, [taskId, cleanup])

  const disconnect = useCallback(() => {
    shouldConnectRef.current = false
    cleanup()
    setState('closed')
  }, [cleanup])

  useEffect(() => {
    unmountedRef.current = false
    shouldConnectRef.current = true
    retriesRef.current = 0

    if (enabled && taskId) {
      connect()
    }

    return () => {
      unmountedRef.current = true
      cleanup()
    }
  }, [taskId, enabled, connect, cleanup])

  return { state, disconnect }
}
