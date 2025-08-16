/**
 * Core game types following D02 specification
 */

export type Visibility = "public" | "team" | "private" | "system"

export type MessageStatus = "pending" | "streaming" | "final" | "error" | "retracted"

export type Phase = "Night" | "DayTalk" | "Vote" | "Trial" | "Result"

export type MessageType = "speak" | "vote" | "night_action" | "system" | "agent_tool"

export type MessageSubType = 
  | "public" | "team" | "submit" | "result" | "phase" | "timer" | "notice" 
  | "call" | "error"

export interface ContentBlock {
  type: "markdown" | "table" | "image" | "code" | "vote_summary"
  content?: string
  headers?: string[]
  rows?: string[][]
  src?: string
  alt?: string
  language?: string
  code?: string
  votes?: Array<{ from: number; to: number | null }>
}

export interface StreamingText {
  chunks: readonly string[]
}

export interface Citation {
  label: string
  source_id: string
}

export interface MessageContent {
  text?: string | StreamingText
  blocks?: ContentBlock[]
  citations?: Citation[]
}

export interface MessageAction {
  label: string
  onClick: () => void
}

/**
 * MessageBubble component props interface following D02 spec
 */
export interface MessageBubbleProps {
  // --- 核心标识 ---
  id: string
  correlationId?: string
  seat?: number
  authorName: string
  roleBadge?: "GM" | "Spectator" | string

  // --- 可见性与上下文 ---
  visibility: Visibility
  phase: Phase
  timestamp: number

  // --- 状态与内容 ---
  status?: MessageStatus
  content: MessageContent

  // --- 交互 ---
  actions?: MessageAction[]
  onRetry?: () => void
}

/**
 * Game event from backend
 */
export interface GameEvent {
  idx: number
  type: MessageType
  sub_type: MessageSubType
  timestamp: number
  seat?: number
  author_name: string
  visibility: Visibility
  phase: Phase
  content: Record<string, any>
  correlation_id?: string
  status?: MessageStatus
  role_badge?: string
}

/**
 * Player information
 */
export interface Player {
  id: string
  seat: number
  name: string
  role?: string
  is_alive: boolean
  is_agent: boolean
  avatar?: string
}

/**
 * Game room information
 */
export interface GameRoom {
  id: string
  name: string
  status: "waiting" | "playing" | "finished"
  current_phase: Phase
  phase_end_time?: number
  players: Player[]
  max_players: number
  created_at: number
  settings: GameSettings
}

/**
 * Game settings
 */
export interface GameSettings {
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

/**
 * Vote information
 */
export interface VoteInfo {
  from: number
  to: number | null
  timestamp: number
}

/**
 * Phase banner props
 */
export interface PhaseBannerProps {
  phase: Phase
  timeRemaining: number
  title: string
  description?: string
}

/**
 * Action panel props
 */
export interface ActionPanelProps {
  phase: Phase
  availableActions: GameAction[]
  disabled?: boolean
}

/**
 * Game action
 */
export interface GameAction {
  id: string
  type: "vote" | "night_action" | "special"
  label: string
  description?: string
  targets?: number[]
  enabled: boolean
  onClick: (target?: number) => void
}

/**
 * System toast props
 */
export interface SystemToastProps {
  type: "success" | "error" | "warning" | "info"
  title: string
  message?: string
  duration?: number
  onClose?: () => void
}