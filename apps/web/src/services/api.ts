/**
 * API service for HTTP requests
 */

import type { 
  ApiResponse, 
  LoginRequest, 
  LoginResponse, 
  RegisterRequest,
  CreateRoomRequest,
  JoinRoomRequest,
  GameRoom,
  User
} from '@/types/api'

export class ApiService {
  private baseUrl: string
  private token: string | null = null

  constructor() {
    this.baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  }

  /**
   * Set authentication token
   */
  setToken(token: string): void {
    this.token = token
  }

  /**
   * Clear authentication token
   */
  clearToken(): void {
    this.token = null
  }

  /**
   * Make HTTP request
   */
  private async request<T = any>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers
    }

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      return {
        success: true,
        data
      }
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error)
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      }
    }
  }

  /**
   * User Authentication
   */
  async login(credentials: LoginRequest): Promise<ApiResponse<LoginResponse>> {
    return this.request<LoginResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials)
    })
  }

  async register(userData: RegisterRequest): Promise<ApiResponse<User>> {
    return this.request<User>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData)
    })
  }

  async getCurrentUser(): Promise<ApiResponse<User>> {
    return this.request<User>('/auth/me')
  }

  async logout(): Promise<ApiResponse<void>> {
    const result = await this.request<void>('/auth/logout', {
      method: 'POST'
    })
    this.clearToken()
    return result
  }

  /**
   * Room Management
   */
  async getRooms(): Promise<ApiResponse<GameRoom[]>> {
    return this.request<GameRoom[]>('/rooms')
  }

  async getRoom(roomId: string): Promise<ApiResponse<GameRoom>> {
    return this.request<GameRoom>(`/rooms/${roomId}`)
  }

  async createRoom(roomData: CreateRoomRequest): Promise<ApiResponse<GameRoom>> {
    return this.request<GameRoom>('/rooms', {
      method: 'POST',
      body: JSON.stringify(roomData)
    })
  }

  async joinRoom(request: JoinRoomRequest): Promise<ApiResponse<void>> {
    return this.request<void>(`/rooms/${request.room_id}/join`, {
      method: 'POST'
    })
  }

  async leaveRoom(roomId: string): Promise<ApiResponse<void>> {
    return this.request<void>(`/rooms/${roomId}/leave`, {
      method: 'POST'
    })
  }

  async startGame(roomId: string): Promise<ApiResponse<void>> {
    return this.request<void>(`/rooms/${roomId}/start`, {
      method: 'POST'
    })
  }

  /**
   * Health check
   */
  async health(): Promise<ApiResponse<{ status: string }>> {
    return this.request<{ status: string }>('/health')
  }
}

// Singleton instance
export const apiService = new ApiService()