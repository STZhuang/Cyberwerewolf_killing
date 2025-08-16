/**
 * WebSocket service for real-time game communication
 */

import { io, Socket } from 'socket.io-client'
import type { 
  WebSocketMessage, 
  WSGameEvent, 
  WSRoomUpdate, 
  WSPlayerUpdate, 
  WSError,
  WSSendMessage,
  WSVote,
  WSNightAction
} from '@/types/api'

export interface WebSocketServiceEvents {
  'game_event': (event: WSGameEvent['data']) => void
  'room_update': (room: WSRoomUpdate['data']) => void
  'player_update': (players: WSPlayerUpdate['data']) => void
  'error': (error: WSError['data']) => void
  'connected': () => void
  'disconnected': () => void
  'connection_error': (error: Error) => void
}

export class WebSocketService {
  private socket: Socket | null = null
  private token: string | null = null
  private roomId: string | null = null
  private listeners = new Map<string, Set<Function>>()
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectTimeout: number | null = null

  constructor() {
    this.setupEventHandlers()
  }

  /**
   * Connect to WebSocket server
   */
  connect(token: string, roomId?: string): Promise<void> {
    return new Promise((resolve, reject) => {
      this.token = token
      this.roomId = roomId || null

      const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
      
      this.socket = io(wsUrl, {
        auth: {
          token
        },
        query: roomId ? { room_id: roomId } : {},
        transports: ['websocket'],
        timeout: 10000
      })

      this.socket.on('connect', () => {
        console.log('WebSocket connected')
        this.reconnectAttempts = 0
        this.emit('connected')
        resolve()
      })

      this.socket.on('connect_error', (error) => {
        console.error('WebSocket connection error:', error)
        this.emit('connection_error', error)
        reject(error)
      })

      this.socket.on('disconnect', (reason) => {
        console.log('WebSocket disconnected:', reason)
        this.emit('disconnected')
        
        // Auto-reconnect if not manually disconnected
        if (reason !== 'io client disconnect') {
          this.handleReconnect()
        }
      })

      this.setupMessageHandlers()
    })
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout)
      this.reconnectTimeout = null
    }

    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }
  }

  /**
   * Check if WebSocket is connected
   */
  isConnected(): boolean {
    return this.socket?.connected || false
  }

  /**
   * Send a message through WebSocket
   */
  private sendMessage(message: WebSocketMessage): void {
    if (!this.socket?.connected) {
      throw new Error('WebSocket not connected')
    }

    this.socket.emit('message', message)
  }

  /**
   * Send a chat message
   */
  sendChatMessage(content: string, visibility: 'public' | 'team' = 'public'): void {
    const message: WSSendMessage = {
      type: 'send_message',
      data: {
        content,
        visibility
      },
      timestamp: Date.now()
    }
    this.sendMessage(message)
  }

  /**
   * Send a vote
   */
  vote(target: number | null): void {
    const message: WSVote = {
      type: 'vote',
      data: {
        target
      },
      timestamp: Date.now()
    }
    this.sendMessage(message)
  }

  /**
   * Send a night action
   */
  nightAction(action: string, target?: number): void {
    const message: WSNightAction = {
      type: 'night_action',
      data: {
        action,
        target
      },
      timestamp: Date.now()
    }
    this.sendMessage(message)
  }

  /**
   * Add event listener
   */
  on<K extends keyof WebSocketServiceEvents>(
    event: K, 
    listener: WebSocketServiceEvents[K]
  ): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set())
    }
    this.listeners.get(event)!.add(listener)
  }

  /**
   * Remove event listener
   */
  off<K extends keyof WebSocketServiceEvents>(
    event: K, 
    listener: WebSocketServiceEvents[K]
  ): void {
    const eventListeners = this.listeners.get(event)
    if (eventListeners) {
      eventListeners.delete(listener)
      if (eventListeners.size === 0) {
        this.listeners.delete(event)
      }
    }
  }

  /**
   * Emit event to listeners
   */
  private emit<K extends keyof WebSocketServiceEvents>(
    event: K, 
    ...args: Parameters<WebSocketServiceEvents[K]>
  ): void {
    const eventListeners = this.listeners.get(event)
    if (eventListeners) {
      eventListeners.forEach(listener => {
        try {
          // @ts-ignore - TypeScript can't infer the correct types here
          listener(...args)
        } catch (error) {
          console.error(`Error in WebSocket event listener for ${event}:`, error)
        }
      })
    }
  }

  /**
   * Setup event handlers
   */
  private setupEventHandlers(): void {
    // Handle browser events
    window.addEventListener('beforeunload', () => {
      this.disconnect()
    })

    // Handle visibility changes
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden && !this.isConnected() && this.token) {
        this.handleReconnect()
      }
    })

    // Handle online/offline status
    window.addEventListener('online', () => {
      if (!this.isConnected() && this.token) {
        this.handleReconnect()
      }
    })
  }

  /**
   * Setup message handlers for incoming WebSocket messages
   */
  private setupMessageHandlers(): void {
    if (!this.socket) return

    this.socket.on('game_event', (data: WSGameEvent['data']) => {
      this.emit('game_event', data)
    })

    this.socket.on('room_update', (data: WSRoomUpdate['data']) => {
      this.emit('room_update', data)
    })

    this.socket.on('player_update', (data: WSPlayerUpdate['data']) => {
      this.emit('player_update', data)
    })

    this.socket.on('error', (data: WSError['data']) => {
      console.error('WebSocket error:', data)
      this.emit('error', data)
    })
  }

  /**
   * Handle reconnection logic
   */
  private handleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts || !this.token) {
      return
    }

    this.reconnectAttempts++
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts - 1), 10000)

    console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${delay}ms`)

    this.reconnectTimeout = window.setTimeout(() => {
      if (!this.isConnected() && this.token) {
        this.connect(this.token, this.roomId || undefined).catch(error => {
          console.error('Reconnection failed:', error)
          this.handleReconnect()
        })
      }
    }, delay)
  }
}

// Singleton instance
export const websocketService = new WebSocketService()