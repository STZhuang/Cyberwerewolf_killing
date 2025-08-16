import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useGameStore } from '@/stores/game'
import type { WebSocketMessage } from '@/types/websocket'

describe('Game Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('initializes with default state', () => {
    const store = useGameStore()

    expect(store.currentRoom).toBeNull()
    expect(store.gameState).toBeNull()
    expect(store.messages).toEqual([])
    expect(store.players).toEqual([])
    expect(store.isConnected).toBe(false)
  })

  it('updates connection status', () => {
    const store = useGameStore()

    store.setConnectionStatus(true)
    expect(store.isConnected).toBe(true)

    store.setConnectionStatus(false)
    expect(store.isConnected).toBe(false)
  })

  it('sets current room', () => {
    const store = useGameStore()
    const room = {
      id: 'room-1',
      code: 'ABC1',
      status: 'open',
      maxPlayers: 9,
      config: { roles: ['Villager'] },
      host: { id: 'user-1', username: 'Host' },
      members: []
    }

    store.setCurrentRoom(room)
    expect(store.currentRoom).toEqual(room)
  })

  it('updates game state', () => {
    const store = useGameStore()
    const gameState = {
      phase: 'DayTalk',
      round: 1,
      deadline: Date.now() + 60000,
      alive_players: [1, 2, 3]
    }

    store.updateGameState(gameState)
    expect(store.gameState).toEqual(gameState)
  })

  it('adds messages in order', () => {
    const store = useGameStore()
    
    const message1: WebSocketMessage = {
      type: 'speak',
      payload: {
        seat: 1,
        content: 'First message',
        idx: 1
      },
      timestamp: 1000
    }

    const message2: WebSocketMessage = {
      type: 'speak', 
      payload: {
        seat: 2,
        content: 'Second message',
        idx: 2
      },
      timestamp: 2000
    }

    store.addMessage(message1)
    store.addMessage(message2)

    expect(store.messages).toHaveLength(2)
    expect(store.messages[0].payload.content).toBe('First message')
    expect(store.messages[1].payload.content).toBe('Second message')
  })

  it('handles message updates for streaming', () => {
    const store = useGameStore()
    
    const initialMessage: WebSocketMessage = {
      type: 'speak',
      payload: {
        seat: 1,
        content: 'Initial',
        idx: 1,
        status: 'streaming'
      },
      timestamp: 1000
    }

    const updateMessage: WebSocketMessage = {
      type: 'speak',
      payload: {
        seat: 1,
        content: 'Updated content',
        idx: 1,
        status: 'final'
      },
      timestamp: 1000
    }

    store.addMessage(initialMessage)
    expect(store.messages).toHaveLength(1)
    expect(store.messages[0].payload.content).toBe('Initial')

    store.addMessage(updateMessage)
    expect(store.messages).toHaveLength(1) // Should update, not add
    expect(store.messages[0].payload.content).toBe('Updated content')
    expect(store.messages[0].payload.status).toBe('final')
  })

  it('updates player list', () => {
    const store = useGameStore()
    const players = [
      { seat: 1, alive: true, name: 'Player 1' },
      { seat: 2, alive: true, name: 'Player 2' },
      { seat: 3, alive: false, name: 'Player 3' }
    ]

    store.updatePlayers(players)
    expect(store.players).toEqual(players)
  })

  it('gets alive players correctly', () => {
    const store = useGameStore()
    store.updatePlayers([
      { seat: 1, alive: true, name: 'Player 1' },
      { seat: 2, alive: true, name: 'Player 2' },
      { seat: 3, alive: false, name: 'Player 3' }
    ])

    const alivePlayers = store.alivePlayers
    expect(alivePlayers).toHaveLength(2)
    expect(alivePlayers.map(p => p.seat)).toEqual([1, 2])
  })

  it('gets current phase correctly', () => {
    const store = useGameStore()
    
    expect(store.currentPhase).toBe('Lobby')

    store.updateGameState({ phase: 'Night' })
    expect(store.currentPhase).toBe('Night')
  })

  it('calculates time remaining correctly', () => {
    const store = useGameStore()
    const futureDeadline = Date.now() + 60000 // 1 minute from now

    store.updateGameState({
      phase: 'DayTalk',
      deadline: futureDeadline
    })

    const remaining = store.timeRemaining
    expect(remaining).toBeGreaterThan(50000) // Should be close to 60000ms
    expect(remaining).toBeLessThanOrEqual(60000)
  })

  it('clears game data', () => {
    const store = useGameStore()
    
    // Set some data first
    store.setCurrentRoom({
      id: 'room-1',
      code: 'ABC1',
      status: 'open',
      maxPlayers: 9,
      config: {},
      host: { id: 'user-1', username: 'Host' },
      members: []
    })
    store.updateGameState({ phase: 'Night' })
    store.addMessage({
      type: 'speak',
      payload: { content: 'Test' },
      timestamp: Date.now()
    })

    // Clear data
    store.clearGame()

    expect(store.currentRoom).toBeNull()
    expect(store.gameState).toBeNull()
    expect(store.messages).toEqual([])
    expect(store.players).toEqual([])
  })
})