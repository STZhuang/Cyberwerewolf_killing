/**
 * Game state store
 */

import { defineStore } from 'pinia'
import { websocketService } from '@/services/websocket'
import { apiService } from '@/services/api'
import type { 
  GameRoom, 
  GameEvent, 
  Player, 
  Phase, 
  MessageBubbleProps,
  SystemToastProps
} from '@/types'

interface GameState {
  // Room state
  currentRoom: GameRoom | null
  isInRoom: boolean
  isConnecting: boolean
  connectionError: string | null

  // Game events (timeline messages)
  events: GameEvent[]
  eventMap: Map<string, GameEvent>
  streamingEvents: Map<string, GameEvent>

  // Players
  players: Player[]
  currentPlayer: Player | null

  // Game state
  currentPhase: Phase | null
  phaseEndTime: number | null
  isGameStarted: boolean

  // UI state
  toasts: SystemToastProps[]
  isTimelineAtBottom: boolean
}

export const useGameStore = defineStore('game', {
  state: (): GameState => ({
    currentRoom: null,
    isInRoom: false,
    isConnecting: false,
    connectionError: null,

    events: [],
    eventMap: new Map(),
    streamingEvents: new Map(),

    players: [],
    currentPlayer: null,

    currentPhase: null,
    phaseEndTime: null,
    isGameStarted: false,

    toasts: [],
    isTimelineAtBottom: true
  }),

  getters: {
    /**
     * Convert events to MessageBubbleProps for timeline rendering
     */
    timelineMessages: (state): MessageBubbleProps[] => {
      return state.events
        .sort((a, b) => a.idx - b.idx)
        .map(event => convertEventToMessageBubble(event))
    },

    /**
     * Get current player's seat number
     */
    currentSeat: (state): number | undefined => {
      return state.currentPlayer?.seat
    },

    /**
     * Get phase time remaining in seconds
     */
    phaseTimeRemaining: (state): number => {
      if (!state.phaseEndTime) return 0
      const remaining = Math.max(0, Math.floor((state.phaseEndTime - Date.now()) / 1000))
      return remaining
    },

    /**
     * Get alive players
     */
    alivePlayers: (state): Player[] => {
      return state.players.filter(player => player.is_alive)
    },

    /**
     * Check if current player can perform actions
     */
    canAct: (state): boolean => {
      return state.currentPlayer?.is_alive && state.isGameStarted
    }
  },

  actions: {
    /**
     * Join a game room
     */
    async joinRoom(roomId: string): Promise<boolean> {
      this.isConnecting = true
      this.connectionError = null

      try {
        // Join room via API
        const joinResponse = await apiService.joinRoom({ room_id: roomId })
        if (!joinResponse.success) {
          this.connectionError = joinResponse.error || 'Failed to join room'
          return false
        }

        // Get room data
        const roomResponse = await apiService.getRoom(roomId)
        if (!roomResponse.success || !roomResponse.data) {
          this.connectionError = roomResponse.error || 'Failed to get room data'
          return false
        }

        this.currentRoom = roomResponse.data
        this.players = roomResponse.data.players
        this.isGameStarted = roomResponse.data.status === 'playing'
        this.currentPhase = roomResponse.data.current_phase
        this.phaseEndTime = roomResponse.data.phase_end_time || null

        // Find current player
        this.findCurrentPlayer()

        // Connect to WebSocket
        const token = localStorage.getItem('auth_token')
        if (!token) {
          this.connectionError = 'No authentication token'
          return false
        }

        await websocketService.connect(token, roomId)
        this.setupWebSocketListeners()
        
        this.isInRoom = true
        return true

      } catch (error) {
        this.connectionError = error instanceof Error ? error.message : 'Connection failed'
        return false
      } finally {
        this.isConnecting = false
      }
    },

    /**
     * Leave current room
     */
    async leaveRoom(): Promise<void> {
      if (this.currentRoom) {
        try {
          await apiService.leaveRoom(this.currentRoom.id)
        } catch (error) {
          console.error('Failed to leave room:', error)
        }
      }

      websocketService.disconnect()
      this.resetGameState()
    },

    /**
     * Send chat message
     */
    sendMessage(content: string, visibility: 'public' | 'team' = 'public'): void {
      if (!this.isInRoom) return
      websocketService.sendChatMessage(content, visibility)
    },

    /**
     * Send vote
     */
    vote(target: number | null): void {
      if (!this.canAct) return
      websocketService.vote(target)
    },

    /**
     * Send night action
     */
    nightAction(action: string, target?: number): void {
      if (!this.canAct) return
      websocketService.nightAction(action, target)
    },

    /**
     * Add system toast
     */
    addToast(toast: Omit<SystemToastProps, 'onClose'>): void {
      const id = Math.random().toString(36).substr(2, 9)
      const fullToast: SystemToastProps = {
        ...toast,
        onClose: () => this.removeToast(id)
      }
      
      this.toasts.push(fullToast)

      // Auto-remove after duration
      if (toast.duration !== 0) {
        setTimeout(() => {
          this.removeToast(id)
        }, toast.duration || 5000)
      }
    },

    /**
     * Remove toast
     */
    removeToast(id: string): void {
      const index = this.toasts.findIndex(toast => 
        toast.onClose?.toString().includes(id)
      )
      if (index > -1) {
        this.toasts.splice(index, 1)
      }
    },

    /**
     * Set timeline scroll position
     */
    setTimelineAtBottom(isAtBottom: boolean): void {
      this.isTimelineAtBottom = isAtBottom
    },

    /**
     * Setup WebSocket event listeners
     */
    setupWebSocketListeners(): void {
      websocketService.on('game_event', (event) => {
        this.handleGameEvent(event)
      })

      websocketService.on('room_update', (room) => {
        this.currentRoom = room
        this.players = room.players
        this.isGameStarted = room.status === 'playing'
        this.currentPhase = room.current_phase
        this.phaseEndTime = room.phase_end_time || null
        this.findCurrentPlayer()
      })

      websocketService.on('player_update', (players) => {
        this.players = players
        this.findCurrentPlayer()
      })

      websocketService.on('error', (error) => {
        this.addToast({
          type: 'error',
          title: 'Connection Error',
          message: error.message
        })
      })

      websocketService.on('disconnected', () => {
        this.addToast({
          type: 'warning',
          title: 'Disconnected',
          message: 'Connection lost. Attempting to reconnect...'
        })
      })

      websocketService.on('connected', () => {
        this.addToast({
          type: 'success',
          title: 'Connected',
          message: 'Successfully reconnected to game'
        })
      })
    },

    /**
     * Handle incoming game event
     */
    handleGameEvent(event: GameEvent): void {
      // Check if this is an update to an existing event
      const existingEvent = this.eventMap.get(event.idx.toString())
      
      if (existingEvent) {
        // Update existing event
        const index = this.events.findIndex(e => e.idx === event.idx)
        if (index > -1) {
          this.events[index] = event
        }
      } else {
        // New event
        this.events.push(event)
        this.eventMap.set(event.idx.toString(), event)
      }

      // Handle streaming events
      if (event.status === 'streaming') {
        this.streamingEvents.set(event.idx.toString(), event)
      } else if (event.status === 'final' || event.status === 'error') {
        this.streamingEvents.delete(event.idx.toString())
      }

      // Sort events by idx to maintain order
      this.events.sort((a, b) => a.idx - b.idx)

      // Auto-scroll timeline if at bottom
      if (this.isTimelineAtBottom) {
        this.$nextTick(() => {
          // Scroll timeline to bottom
          const timeline = document.querySelector('.timeline-container')
          if (timeline) {
            timeline.scrollTop = timeline.scrollHeight
          }
        })
      }
    },

    /**
     * Find current player in players list
     */
    findCurrentPlayer(): void {
      const authStore = useAuthStore()
      this.currentPlayer = this.players.find(
        player => player.id === authStore.userId
      ) || null
    },

    /**
     * Reset game state
     */
    resetGameState(): void {
      this.currentRoom = null
      this.isInRoom = false
      this.isConnecting = false
      this.connectionError = null
      this.events = []
      this.eventMap.clear()
      this.streamingEvents.clear()
      this.players = []
      this.currentPlayer = null
      this.currentPhase = null
      this.phaseEndTime = null
      this.isGameStarted = false
      this.toasts = []
      this.isTimelineAtBottom = true
    }
  }
})

/**
 * Convert GameEvent to MessageBubbleProps
 */
function convertEventToMessageBubble(event: GameEvent): MessageBubbleProps {
  return {
    id: event.idx.toString(),
    correlationId: event.correlation_id,
    seat: event.seat,
    authorName: event.author_name,
    roleBadge: event.role_badge as any,
    visibility: event.visibility,
    phase: event.phase,
    timestamp: event.timestamp,
    status: event.status,
    content: {
      text: event.content.text,
      blocks: event.content.blocks,
      citations: event.content.citations
    }
  }
}

// Import useAuthStore to avoid circular dependency
import { useAuthStore } from './auth'