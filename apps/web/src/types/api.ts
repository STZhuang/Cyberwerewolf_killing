/**
 * API types for backend communication
 */

import type { GameRoom, Player, GameEvent } from './game'

export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  token: string
  user: User
}

export interface RegisterRequest {
  username: string
  password: string
  email: string
  display_name: string
}

export interface User {
  id: string
  username: string
  display_name: string
  email: string
  avatar?: string
  created_at: number
}

export interface CreateRoomRequest {
  name: string
  max_players: number
  settings: {
    werewolf_count: number
    villager_count: number
    seer_count: number
    guard_count: number
    witch_count: number
    hunter_count: number
    day_duration: number
    night_duration: number
    vote_duration: number
    enable_agent: boolean
    agent_difficulty: "easy" | "medium" | "hard"
  }
}

export interface JoinRoomRequest {
  room_id: string
}

export interface WebSocketMessage {
  type: string
  data: any
  timestamp?: number
}

// WebSocket message types
export interface WSGameEvent extends WebSocketMessage {
  type: 'game_event'
  data: GameEvent
}

export interface WSRoomUpdate extends WebSocketMessage {
  type: 'room_update'
  data: GameRoom
}

export interface WSPlayerUpdate extends WebSocketMessage {
  type: 'player_update'
  data: Player[]
}

export interface WSError extends WebSocketMessage {
  type: 'error'
  data: {
    message: string
    code?: string
  }
}

export interface WSSendMessage extends WebSocketMessage {
  type: 'send_message'
  data: {
    content: string
    visibility?: 'public' | 'team'
  }
}

export interface WSVote extends WebSocketMessage {
  type: 'vote'
  data: {
    target: number | null
  }
}

export interface WSNightAction extends WebSocketMessage {
  type: 'night_action'
  data: {
    action: string
    target?: number
  }
}