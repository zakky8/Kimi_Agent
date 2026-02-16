import { useState, useEffect, useRef, useCallback } from 'react'

interface WebSocketMessage {
  type: string
  data: any
  timestamp: string
}

export function useWebSocket() {
  const [connected, setConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const ws = useRef<WebSocket | null>(null)
  const reconnectTimeout = useRef<NodeJS.Timeout>()

  const connect = useCallback(() => {
    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8001'
    
    try {
      ws.current = new WebSocket(wsUrl)

      ws.current.onopen = () => {
        console.log('WebSocket connected')
        setConnected(true)
        // Subscribe to all channels
        ws.current?.send(JSON.stringify({ action: 'subscribe', channel: 'all' }))
      }

      ws.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          setLastMessage(message)
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }

      ws.current.onclose = () => {
        console.log('WebSocket disconnected')
        setConnected(false)
        // Reconnect after 5 seconds
        reconnectTimeout.current = setTimeout(connect, 5000)
      }

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error)
      }
    } catch (error) {
      console.error('Error creating WebSocket:', error)
    }
  }, [])

  const disconnect = useCallback(() => {
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current)
    }
    ws.current?.close()
  }, [])

  const send = useCallback((message: any) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message))
    }
  }, [])

  useEffect(() => {
    connect()
    return () => disconnect()
  }, [connect, disconnect])

  return {
    connected,
    lastMessage,
    send,
    connect,
    disconnect,
  }
}
