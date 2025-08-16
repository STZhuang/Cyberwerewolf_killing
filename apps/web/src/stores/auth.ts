/**
 * Authentication store
 */

import { defineStore } from 'pinia'
import { apiService } from '@/services/api'
import { websocketService } from '@/services/websocket'
import type { User, LoginRequest, RegisterRequest } from '@/types/api'

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: null,
    token: localStorage.getItem('auth_token'),
    isAuthenticated: false,
    isLoading: false,
    error: null
  }),

  getters: {
    isLoggedIn: (state) => state.isAuthenticated && state.user !== null,
    userName: (state) => state.user?.display_name || state.user?.username || '',
    userId: (state) => state.user?.id || ''
  },

  actions: {
    /**
     * Initialize auth state from stored token
     */
    async init(): Promise<void> {
      if (this.token) {
        apiService.setToken(this.token)
        await this.getCurrentUser()
      }
    },

    /**
     * Login user
     */
    async login(credentials: LoginRequest): Promise<boolean> {
      this.isLoading = true
      this.error = null

      try {
        const response = await apiService.login(credentials)
        
        if (response.success && response.data) {
          this.user = response.data.user
          this.token = response.data.token
          this.isAuthenticated = true

          // Store token
          localStorage.setItem('auth_token', this.token)
          apiService.setToken(this.token)

          return true
        } else {
          this.error = response.error || 'Login failed'
          return false
        }
      } catch (error) {
        this.error = error instanceof Error ? error.message : 'Login failed'
        return false
      } finally {
        this.isLoading = false
      }
    },

    /**
     * Register new user
     */
    async register(userData: RegisterRequest): Promise<boolean> {
      this.isLoading = true
      this.error = null

      try {
        const response = await apiService.register(userData)
        
        if (response.success) {
          // After successful registration, login with the same credentials
          return await this.login({
            username: userData.username,
            password: userData.password
          })
        } else {
          this.error = response.error || 'Registration failed'
          return false
        }
      } catch (error) {
        this.error = error instanceof Error ? error.message : 'Registration failed'
        return false
      } finally {
        this.isLoading = false
      }
    },

    /**
     * Get current user data
     */
    async getCurrentUser(): Promise<void> {
      if (!this.token) return

      try {
        const response = await apiService.getCurrentUser()
        
        if (response.success && response.data) {
          this.user = response.data
          this.isAuthenticated = true
        } else {
          // Token might be invalid
          this.logout()
        }
      } catch (error) {
        console.error('Failed to get current user:', error)
        this.logout()
      }
    },

    /**
     * Logout user
     */
    async logout(): Promise<void> {
      try {
        // Disconnect WebSocket
        websocketService.disconnect()
        
        // Call logout API
        if (this.token) {
          await apiService.logout()
        }
      } catch (error) {
        console.error('Logout error:', error)
      } finally {
        // Clear local state
        this.user = null
        this.token = null
        this.isAuthenticated = false
        this.error = null

        // Clear stored token
        localStorage.removeItem('auth_token')
        apiService.clearToken()
      }
    },

    /**
     * Clear auth error
     */
    clearError(): void {
      this.error = null
    }
  }
})