import { useEffect, useRef, useState, useCallback } from 'react'
import { useAuth } from './useAuth'

export interface WSMessage {
  type: string
  timestamp: string
  [key: string]: any
}

export interface TelemetryUpdate extends WSMessage {
  type: 'telemetry_update'
  charger_id: number
  power_output_kw: number
  voltage_v?: number
  current_a?: number
  energy_delivered_kwh: number
  session_duration_minutes: number
  status: string
}

export interface ChargerStatusUpdate extends WSMessage {
  type: 'charger_update'
  charger_id: number
  status: string
  is_active: boolean
}

export interface BookingUpdate extends WSMessage {
  type: 'booking_update'
  booking_id: number
  status: string
  payment_status?: string
}

interface UseWebSocketOptions {
  path: string
  onMessage?: (message: WSMessage) => void
  onError?: (error: Event) => void
  onConnect?: () => void
  onDisconnect?: () => void
  reconnectDelay?: number
  maxReconnectAttempts?: number
}

export function useWebSocket(options: UseWebSocketOptions) {
  const { user } = useAuth()
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttemptsRef = useRef(0)
  
  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [lastError, setLastError] = useState<string | null>(null)

  const {
    path,
    onMessage,
    onError,
    onConnect,
    onDisconnect,
    reconnectDelay = 3000,
    maxReconnectAttempts = 5
  } = options

  const connect = useCallback(() => {
    if (!user || isConnecting || isConnected) return

    setIsConnecting(true)
    setLastError(null)

    try {
      const token = localStorage.getItem('chargemitra_auth')
      const authData = token ? JSON.parse(token) : null
      
      if (!authData?.token) {
        throw new Error('No authentication token available')
      }

      // Create WebSocket URL
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const host = import.meta.env.VITE_API_URL?.replace(/^https?:\/\//, '') || window.location.host
      const wsUrl = `${protocol}//${host}/api/v1/ws${path}?token=${authData.token}`

      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        console.log(`WebSocket connected: ${path}`)
        setIsConnected(true)
        setIsConnecting(false)
        setLastError(null)
        reconnectAttemptsRef.current = 0
        onConnect?.()
      }

      ws.onmessage = (event) => {
        try {
          const message: WSMessage = JSON.parse(event.data)
          onMessage?.(message)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      ws.onerror = (error) => {
        console.error(`WebSocket error on ${path}:`, error)
        setLastError('Connection error occurred')
        onError?.(error)
      }

      ws.onclose = (event) => {
        console.log(`WebSocket closed: ${path}`, event.code, event.reason)
        setIsConnected(false)
        setIsConnecting(false)
        wsRef.current = null
        onDisconnect?.()

        // Attempt to reconnect if not a normal closure
        if (event.code !== 1000 && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++
          setLastError(`Reconnecting... (${reconnectAttemptsRef.current}/${maxReconnectAttempts})`)
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, reconnectDelay)
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          setLastError('Connection failed after maximum retry attempts')
        }
      }

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      setIsConnecting(false)
      setLastError(error instanceof Error ? error.message : 'Connection failed')
    }
  }, [user, path, onMessage, onError, onConnect, onDisconnect, reconnectDelay, maxReconnectAttempts, isConnecting, isConnected])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'User disconnected')
      wsRef.current = null
    }

    setIsConnected(false)
    setIsConnecting(false)
    setLastError(null)
    reconnectAttemptsRef.current = 0
  }, [])

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current && isConnected) {
      wsRef.current.send(JSON.stringify(message))
      return true
    }
    return false
  }, [isConnected])

  // Auto-connect when user is available
  useEffect(() => {
    if (user) {
      connect()
    } else {
      disconnect()
    }

    return () => {
      disconnect()
    }
  }, [user, connect, disconnect])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect()
    }
  }, [disconnect])

  return {
    isConnected,
    isConnecting,
    lastError,
    connect,
    disconnect,
    sendMessage
  }
}

// Specialized hooks for different WebSocket endpoints
export function useChargerWebSocket(
  chargerId: number,
  onTelemetryUpdate?: (data: TelemetryUpdate) => void,
  onStatusUpdate?: (data: ChargerStatusUpdate) => void
) {
  const handleMessage = useCallback((message: WSMessage) => {
    switch (message.type) {
      case 'telemetry_update':
        if (message.charger_id === chargerId) {
          onTelemetryUpdate?.(message as TelemetryUpdate)
        }
        break
      case 'charger_update':
        if (message.charger_id === chargerId) {
          onStatusUpdate?.(message as ChargerStatusUpdate)
        }
        break
      case 'pong':
        // Handle ping/pong for keepalive
        break
      default:
        console.log('Unknown message type:', message.type)
    }
  }, [chargerId, onTelemetryUpdate, onStatusUpdate])

  const { isConnected, isConnecting, lastError, sendMessage } = useWebSocket({
    path: `/chargers/${chargerId}`,
    onMessage: handleMessage
  })

  const requestTelemetry = useCallback(() => {
    return sendMessage({ type: 'get_telemetry' })
  }, [sendMessage])

  const ping = useCallback(() => {
    return sendMessage({ type: 'ping' })
  }, [sendMessage])

  // Send periodic pings to keep connection alive
  useEffect(() => {
    if (isConnected) {
      const pingInterval = setInterval(() => {
        ping()
      }, 30000) // Ping every 30 seconds

      return () => clearInterval(pingInterval)
    }
  }, [isConnected, ping])

  return {
    isConnected,
    isConnecting,
    lastError,
    requestTelemetry,
    ping
  }
}

export function useBookingWebSocket(
  bookingId: number,
  onBookingUpdate?: (data: BookingUpdate) => void,
  onSessionUpdate?: (data: any) => void
) {
  const handleMessage = useCallback((message: WSMessage) => {
    switch (message.type) {
      case 'booking_update':
        if (message.booking_id === bookingId) {
          onBookingUpdate?.(message as BookingUpdate)
        }
        break
      case 'session_update':
        if (message.booking_id === bookingId) {
          onSessionUpdate?.(message)
        }
        break
      case 'pong':
        break
      default:
        console.log('Unknown booking message type:', message.type)
    }
  }, [bookingId, onBookingUpdate, onSessionUpdate])

  const { isConnected, isConnecting, lastError, sendMessage } = useWebSocket({
    path: `/bookings/${bookingId}`,
    onMessage: handleMessage
  })

  const ping = useCallback(() => {
    return sendMessage({ type: 'ping' })
  }, [sendMessage])

  // Keep alive pings
  useEffect(() => {
    if (isConnected) {
      const pingInterval = setInterval(() => {
        ping()
      }, 30000)

      return () => clearInterval(pingInterval)
    }
  }, [isConnected, ping])

  return {
    isConnected,
    isConnecting, 
    lastError
  }
}