/**
 * Core types for Cyber Werewolves - mirrors Python models
 */

export enum GamePhase {
  LOBBY = "Lobby",
  ASSIGN_ROLES = "AssignRoles",
  NIGHT = "Night", 
  DAWN = "Dawn",
  DAY_TALK = "DayTalk",
  VOTE = "Vote",
  TRIAL = "Trial",
  DAY_RESULT = "DayResult",
  END = "End"
}

export enum Role {
  VILLAGER = "Villager",
  WEREWOLF = "Werewolf", 
  SEER = "Seer",
  WITCH = "Witch",
  GUARD = "Guard",
  HUNTER = "Hunter",
  IDIOT = "Idiot"
}

export enum Alignment {
  VILLAGE = "Village",
  WEREWOLF = "Werewolf"
}

export enum RoomStatus {
  OPEN = "open",
  PLAYING = "playing",
  CLOSED = "closed"
}

export enum MessageType {
  SPEAK = "speak",
  VOTE = "vote",
  NIGHT_ACTION = "night_action", 
  SYSTEM = "system",
  STATE = "state",
  ACK = "ack",
  ERROR = "error"
}

export enum Visibility {
  PUBLIC = "public",
  TEAM = "team",
  PRIVATE = "private", 
  SYSTEM = "system"
}

export interface User {
  id: string
  username: string
  avatar_url?: string
  created_at: string
  banned: boolean
}

export interface RoomConfig {
  roles: Role[]
  phase_durations: Record<string, number>
  max_players: number
}

export interface Room {
  id: string
  code: string
  host_id: string
  status: RoomStatus
  config: RoomConfig
  created_at: string
}

export interface Game {
  id: string
  room_id: string
  seed: string
  started_at?: string
  ended_at?: string
  config: RoomConfig
  version: number
  current_phase: GamePhase
  current_round: number
}

export interface GamePlayer {
  game_id: string
  user_id: string
  seat: number
  role: Role
  alive: boolean
  alignment: Alignment
  is_bot: boolean
  agent_id?: string
}

export interface WebSocketMessage {
  type: MessageType
  req_id?: string
  timestamp: number
  payload: Record<string, any>
}

export interface MessageBubbleContent {
  text?: string | { chunks: readonly string[] }
  blocks?: Array<
    | { type: "markdown"; content: string }
    | { type: "table"; headers: string[]; rows: string[][] }
    | { type: "image"; src: string; alt?: string }
    | { type: "code"; language: string; code: string }
    | { type: "vote_summary"; votes: { from: number; to: number | null }[] }
  >
  citations?: Array<{ label: string; source_id: string }>
}