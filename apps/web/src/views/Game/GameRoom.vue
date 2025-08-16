<template>
  <div class="game-room" :class="{ 'game-active': gameStore.isGameStarted }">
    <!-- Game header -->
    <header class="game-header">
      <div class="room-info">
        <h1 class="room-title">{{ gameStore.currentRoom?.name || 'Game Room' }}</h1>
        <div class="room-meta">
          <span class="player-count">
            {{ gameStore.players.length }}/{{ gameStore.currentRoom?.max_players }}
          </span>
          <span class="room-status" :class="`status-${gameStore.currentRoom?.status}`">
            {{ getRoomStatusText() }}
          </span>
        </div>
      </div>
      
      <div class="header-actions">
        <AButton 
          v-if="!gameStore.isGameStarted && canStartGame"
          type="primary"
          @click="startGame"
          :loading="isStartingGame"
        >
          开始游戏
        </AButton>
        <AButton type="text" @click="leaveRoom" class="leave-button">
          <AIcon icon="icon-export" />
          离开房间
        </AButton>
      </div>
    </header>

    <!-- Connection status -->
    <div v-if="connectionError" class="connection-error">
      <AAlert type="error" :title="connectionError" show-icon />
    </div>

    <!-- Game content -->
    <main class="game-content">
      <!-- Phase banner (only show during game) -->
      <PhaseBanner
        v-if="gameStore.isGameStarted && gameStore.currentPhase"
        :phase="gameStore.currentPhase"
        :time-remaining="gameStore.phaseTimeRemaining"
        :title="getPhaseTitle()"
        :description="getPhaseDescription()"
      />

      <!-- Game layout -->
      <div class="game-layout">
        <!-- Player sidebar -->
        <aside class="player-sidebar">
          <div class="player-list">
            <h3 class="sidebar-title">
              <AIcon icon="icon-user-group" />
              玩家列表
            </h3>
            
            <div class="players">
              <div
                v-for="player in gameStore.players"
                :key="player.id"
                :class="[
                  'player-card',
                  { 
                    'current-player': player.id === authStore.userId,
                    'player-dead': !player.is_alive,
                    'player-agent': player.is_agent
                  }
                ]"
              >
                <div class="player-avatar">
                  <span class="avatar-text">{{ getPlayerInitials(player.name) }}</span>
                  <span v-if="player.is_agent" class="agent-badge" title="AI智能体">🤖</span>
                </div>
                
                <div class="player-info">
                  <div class="player-name">{{ player.name }}</div>
                  <div class="player-meta">
                    <span class="seat-number">#{{ player.seat }}</span>
                    <span v-if="player.role && gameStore.isGameStarted" class="player-role">
                      {{ player.role }}
                    </span>
                    <span v-if="!player.is_alive" class="death-indicator">💀</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Game info -->
          <div v-if="gameStore.isGameStarted" class="game-info">
            <h4 class="info-title">游戏信息</h4>
            <div class="info-stats">
              <div class="stat-item">
                <span class="stat-label">存活玩家</span>
                <span class="stat-value">{{ gameStore.alivePlayers.length }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">当前阶段</span>
                <span class="stat-value">{{ getPhaseTitle() }}</span>
              </div>
            </div>
          </div>
        </aside>

        <!-- Main game area -->
        <div class="main-game-area">
          <!-- Timeline -->
          <div class="timeline-section">
            <TimelineView
              :messages="gameStore.timelineMessages"
              :auto-scroll="true"
              ref="timelineRef"
            />
          </div>

          <!-- Chat input -->
          <div class="chat-section">
            <div class="chat-input-container">
              <ATextarea
                v-model="chatMessage"
                placeholder="输入消息..."
                :max-length="500"
                show-word-limit
                :auto-size="{ minRows: 2, maxRows: 4 }"
                @keydown="handleChatKeydown"
                :disabled="!canSendMessage"
                class="chat-input"
              />
              
              <div class="chat-actions">
                <div class="chat-options">
                  <ARadioGroup v-model="chatVisibility" size="small">
                    <ARadio value="public">公开</ARadio>
                    <ARadio value="team" :disabled="!canSendTeamMessage">队伍</ARadio>
                  </ARadioGroup>
                </div>
                
                <AButton
                  type="primary"
                  @click="sendMessage"
                  :disabled="!canSendChatMessage"
                  :loading="isSendingMessage"
                >
                  发送
                </AButton>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Action panel (only show during game) -->
      <ActionPanel
        v-if="gameStore.isGameStarted && gameActions.length > 0"
        :phase="gameStore.currentPhase || 'DayTalk'"
        :available-actions="gameActions"
        :disabled="!gameStore.canAct"
      />
    </main>

    <!-- Loading overlay -->
    <div v-if="isConnecting" class="loading-overlay">
      <ASpin size="large" />
      <p>连接游戏中...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  Button as AButton,
  Icon as AIcon,
  Alert as AAlert,
  Textarea as ATextarea,
  RadioGroup as ARadioGroup,
  Radio as ARadio,
  Spin as ASpin,
  Message,
  Modal
} from '@arco-design/web-vue'
import PhaseBanner from '@/components/Game/PhaseBanner.vue'
import ActionPanel from '@/components/Game/ActionPanel.vue'
import TimelineView from '@/components/Timeline/TimelineView.vue'
import { useAuthStore, useGameStore } from '@/stores'
import type { GameAction, Phase } from '@/types'

interface Props {
  id: string
}

const props = defineProps<Props>()
const router = useRouter()
const route = useRoute()

const authStore = useAuthStore()
const gameStore = useGameStore()

// Reactive state
const isConnecting = ref(false)
const connectionError = ref<string | null>(null)
const isStartingGame = ref(false)
const chatMessage = ref('')
const chatVisibility = ref<'public' | 'team'>('public')
const isSendingMessage = ref(false)
const timelineRef = ref<InstanceType<typeof TimelineView> | null>(null)

// Computed properties
const canStartGame = computed(() => {
  const room = gameStore.currentRoom
  if (!room || room.status !== 'waiting') return false
  
  // Check if current user can start game (room creator or admin)
  return gameStore.players.length >= 4 // Minimum players for werewolf game
})

const canSendMessage = computed(() => {
  return gameStore.isInRoom && authStore.isLoggedIn
})

const canSendTeamMessage = computed(() => {
  // Can send team messages if player has a team role (werewolf, etc.)
  const currentPlayer = gameStore.currentPlayer
  return currentPlayer?.role && ['werewolf'].includes(currentPlayer.role.toLowerCase())
})

const canSendChatMessage = computed(() => {
  return canSendMessage.value && chatMessage.value.trim().length > 0
})

const gameActions = computed((): GameAction[] => {
  if (!gameStore.isGameStarted || !gameStore.currentPhase || !gameStore.canAct) {
    return []
  }

  const actions: GameAction[] = []
  const currentPlayer = gameStore.currentPlayer

  switch (gameStore.currentPhase) {
    case 'Vote':
      actions.push({
        id: 'vote',
        type: 'vote',
        label: '投票',
        description: '选择要投票的玩家',
        enabled: true,
        onClick: (target) => gameStore.vote(target ?? null)
      })
      break

    case 'Night':
      if (currentPlayer?.role) {
        switch (currentPlayer.role.toLowerCase()) {
          case 'werewolf':
            actions.push({
              id: 'werewolf_kill',
              type: 'night_action',
              label: '杀害',
              description: '选择要杀害的玩家',
              enabled: true,
              onClick: (target) => target && gameStore.nightAction('kill', target)
            })
            break

          case 'seer':
            actions.push({
              id: 'seer_check',
              type: 'night_action',
              label: '查验',
              description: '查验一名玩家的身份',
              enabled: true,
              onClick: (target) => target && gameStore.nightAction('check', target)
            })
            break

          case 'guard':
            actions.push({
              id: 'guard_protect',
              type: 'night_action',
              label: '守护',
              description: '守护一名玩家',
              enabled: true,
              onClick: (target) => target && gameStore.nightAction('protect', target)
            })
            break

          case 'witch':
            actions.push({
              id: 'witch_heal',
              type: 'night_action',
              label: '救人',
              description: '使用解药救人',
              enabled: true,
              onClick: (target) => target && gameStore.nightAction('heal', target)
            }, {
              id: 'witch_poison',
              type: 'night_action',
              label: '毒杀',
              description: '使用毒药杀害玩家',
              enabled: true,
              onClick: (target) => target && gameStore.nightAction('poison', target)
            })
            break
        }
      }
      break
  }

  return actions
})

// Lifecycle
onMounted(async () => {
  await joinRoom()
})

onUnmounted(() => {
  // Clean up when leaving component
  if (gameStore.isInRoom) {
    gameStore.leaveRoom()
  }
})

// Methods
async function joinRoom(): Promise<void> {
  isConnecting.value = true
  connectionError.value = null

  try {
    const success = await gameStore.joinRoom(props.id)
    if (!success) {
      connectionError.value = gameStore.connectionError || 'Failed to join room'
    }
  } catch (error) {
    console.error('Failed to join room:', error)
    connectionError.value = 'Connection failed'
  } finally {
    isConnecting.value = false
  }
}

async function startGame(): Promise<void> {
  isStartingGame.value = true

  try {
    const response = await apiService.startGame(props.id)
    if (response.success) {
      Message.success('Game started!')
    } else {
      Message.error(response.error || 'Failed to start game')
    }
  } catch (error) {
    console.error('Failed to start game:', error)
    Message.error('Failed to start game')
  } finally {
    isStartingGame.value = false
  }
}

async function leaveRoom(): Promise<void> {
  Modal.confirm({
    title: '确认离开房间？',
    content: '离开后将无法继续参与当前游戏',
    onOk: async () => {
      try {
        await gameStore.leaveRoom()
        router.push('/rooms')
      } catch (error) {
        console.error('Failed to leave room:', error)
        Message.error('离开房间失败')
      }
    }
  })
}

async function sendMessage(): Promise<void> {
  if (!canSendChatMessage.value) return

  isSendingMessage.value = true

  try {
    gameStore.sendMessage(chatMessage.value.trim(), chatVisibility.value)
    chatMessage.value = ''
    
    // Auto-scroll timeline to bottom
    await nextTick()
    timelineRef.value?.scrollToBottom()
  } catch (error) {
    console.error('Failed to send message:', error)
    Message.error('发送消息失败')
  } finally {
    isSendingMessage.value = false
  }
}

function handleChatKeydown(event: KeyboardEvent): void {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

function getPlayerInitials(name: string): string {
  return name
    .split(' ')
    .map(word => word.charAt(0))
    .join('')
    .substring(0, 2)
    .toUpperCase()
}

function getRoomStatusText(): string {
  switch (gameStore.currentRoom?.status) {
    case 'waiting': return '等待中'
    case 'playing': return '游戏中'
    case 'finished': return '已结束'
    default: return '未知'
  }
}

function getPhaseTitle(): string {
  switch (gameStore.currentPhase) {
    case 'Night': return '天黑请闭眼'
    case 'DayTalk': return '白天讨论'
    case 'Vote': return '投票阶段'
    case 'Trial': return '审判阶段'
    case 'Result': return '结果公布'
    default: return ''
  }
}

function getPhaseDescription(): string {
  switch (gameStore.currentPhase) {
    case 'Night': return '狼人和其他特殊角色进行夜间行动'
    case 'DayTalk': return '所有玩家可以自由讨论，寻找狼人线索'
    case 'Vote': return '投票选择要淘汰的玩家'
    case 'Trial': return '被投票玩家进行最后陈述'
    case 'Result': return '公布投票结果和游戏状态'
    default: return ''
  }
}
</script>

<style scoped lang="scss">
.game-room {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-1);
}

.game-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: var(--color-bg-2);
  border-bottom: 1px solid var(--color-neutral-3);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.room-info {
  .room-title {
    margin: 0 0 4px 0;
    font-size: 20px;
    font-weight: 600;
    color: var(--color-text-1);
  }

  .room-meta {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 14px;
    color: var(--color-text-3);

    .player-count {
      font-weight: 500;
    }

    .room-status {
      padding: 2px 8px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 500;

      &.status-waiting {
        background: var(--color-warning-light-9);
        color: var(--color-warning-6);
      }

      &.status-playing {
        background: var(--color-success-light-9);
        color: var(--color-success-6);
      }

      &.status-finished {
        background: var(--color-neutral-2);
        color: var(--color-text-3);
      }
    }
  }
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;

  .leave-button {
    color: var(--color-text-3);

    &:hover {
      color: var(--color-danger-6);
    }
  }
}

.connection-error {
  margin: 16px 24px 0;
}

.game-content {
  flex: 1;
  min-height: 0;
  padding: 16px 24px;
  display: flex;
  flex-direction: column;
}

.game-layout {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 20px;
  margin-top: 16px;
}

.player-sidebar {
  background: var(--color-bg-2);
  border: 1px solid var(--color-neutral-3);
  border-radius: 12px;
  padding: 16px;
  height: fit-content;
  max-height: calc(100vh - 300px);
  overflow-y: auto;

  .sidebar-title {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 0 0 16px 0;
    font-size: 16px;
    font-weight: 600;
    color: var(--color-text-1);

    .arco-icon {
      color: var(--color-primary-6);
    }
  }
}

.players {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.player-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  border: 1px solid var(--color-neutral-3);
  background: var(--color-bg-1);
  transition: all 0.2s ease;

  &:hover {
    border-color: var(--color-primary-6);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  &.current-player {
    border-color: var(--color-primary-6);
    background: var(--color-primary-light-9);
  }

  &.player-dead {
    opacity: 0.6;
    background: var(--color-neutral-1);
  }

  &.player-agent {
    border-left: 3px solid var(--color-purple-6);
  }
}

.player-avatar {
  position: relative;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--color-primary-6);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 12px;
  font-weight: 600;

  .agent-badge {
    position: absolute;
    top: -4px;
    right: -4px;
    font-size: 14px;
  }
}

.player-info {
  flex: 1;
  min-width: 0;

  .player-name {
    font-size: 14px;
    font-weight: 500;
    color: var(--color-text-1);
    margin-bottom: 2px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .player-meta {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: var(--color-text-3);

    .seat-number {
      font-weight: 500;
    }

    .player-role {
      color: var(--color-success-6);
      font-weight: 500;
    }

    .death-indicator {
      font-size: 10px;
    }
  }
}

.game-info {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--color-neutral-3);

  .info-title {
    margin: 0 0 12px 0;
    font-size: 14px;
    font-weight: 600;
    color: var(--color-text-1);
  }

  .info-stats {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .stat-item {
    display: flex;
    justify-content: space-between;
    font-size: 13px;

    .stat-label {
      color: var(--color-text-3);
    }

    .stat-value {
      color: var(--color-text-1);
      font-weight: 500;
    }
  }
}

.main-game-area {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.timeline-section {
  flex: 1;
  min-height: 0;
  background: var(--color-bg-2);
  border: 1px solid var(--color-neutral-3);
  border-radius: 12px;
  margin-bottom: 16px;
}

.chat-section {
  flex-shrink: 0;
}

.chat-input-container {
  background: var(--color-bg-2);
  border: 1px solid var(--color-neutral-3);
  border-radius: 12px;
  padding: 16px;

  .chat-input {
    margin-bottom: 12px;
  }

  .chat-actions {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .chat-options {
      display: flex;
      align-items: center;
      gap: 12px;
    }
  }
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(4px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  z-index: 100;

  p {
    margin: 0;
    color: var(--color-text-2);
    font-size: 14px;
  }
}

// Responsive design
@media (max-width: 1024px) {
  .game-layout {
    grid-template-columns: 240px 1fr;
    gap: 16px;
  }

  .player-sidebar {
    padding: 12px;
  }
}

@media (max-width: 768px) {
  .game-header {
    padding: 12px 16px;
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .game-content {
    padding: 12px 16px;
  }

  .game-layout {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr;
    gap: 12px;
  }

  .player-sidebar {
    order: -1;
    max-height: 200px;

    .players {
      flex-direction: row;
      overflow-x: auto;
      gap: 8px;
      padding-bottom: 4px;
    }

    .player-card {
      flex: 0 0 120px;
    }
  }

  .chat-actions {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
}

// Dark theme
@media (prefers-color-scheme: dark) {
  .loading-overlay {
    background: rgba(0, 0, 0, 0.8);
  }
}
</style>