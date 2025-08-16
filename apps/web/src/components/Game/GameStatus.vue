<template>
  <div class="game-status">
    <div class="status-header">
      <div class="game-info">
        <h3>游戏状态</h3>
        <div class="game-meta">
          <span>第 {{ currentRound }} 回合</span>
          <a-divider type="vertical" />
          <span>{{ currentPhase }}</span>
        </div>
      </div>
      
      <div class="player-info" v-if="currentPlayer">
        <a-avatar :size="40">
          {{ currentPlayer.seat }}
        </a-avatar>
        <div class="player-details">
          <div class="player-name">{{ currentPlayer.name || `${currentPlayer.seat}号` }}</div>
          <div class="player-role">{{ getRoleText(currentPlayer.role) }}</div>
        </div>
        <a-tag 
          :color="currentPlayer.is_alive ? 'green' : 'red'"
          size="small"
        >
          {{ currentPlayer.is_alive ? '存活' : '死亡' }}
        </a-tag>
      </div>
    </div>

    <div class="players-overview">
      <div class="overview-header">
        <h4>玩家概览</h4>
        <div class="stats">
          <span>存活: {{ aliveCount }}/{{ totalPlayers }}</span>
        </div>
      </div>
      
      <div class="players-grid">
        <div 
          v-for="player in players" 
          :key="player.seat"
          class="player-status"
          :class="{ 
            'current': player.seat === currentSeat,
            'dead': !player.is_alive,
            'suspected': suspectedPlayers.includes(player.seat)
          }"
        >
          <div class="player-avatar">
            <a-avatar :size="32">
              {{ player.seat }}
            </a-avatar>
            <div v-if="!player.is_alive" class="death-marker">
              <icon-close />
            </div>
          </div>
          
          <div class="player-basic-info">
            <div class="seat-number">{{ player.seat }}号</div>
            <div v-if="player.revealed_role" class="revealed-role">
              {{ getRoleText(player.revealed_role) }}
            </div>
          </div>
          
          <div class="player-indicators">
            <a-tag v-if="player.is_bot" size="mini" color="blue">AI</a-tag>
            <a-tag v-if="votedPlayers[player.seat]" size="mini" color="orange">已投票</a-tag>
            <a-tag v-if="actedPlayers[player.seat]" size="mini" color="purple">已行动</a-tag>
          </div>
        </div>
      </div>
    </div>

    <div class="game-progress" v-if="showProgress">
      <div class="progress-header">
        <h4>阶段进度</h4>
        <div class="time-remaining" v-if="timeRemaining > 0">
          剩余时间: {{ formatTime(timeRemaining) }}
        </div>
      </div>
      
      <div class="progress-details">
        <div class="voting-progress" v-if="currentPhase === 'Vote'">
          <div class="progress-stat">
            <span class="label">已投票:</span>
            <span class="value">{{ votedCount }}/{{ aliveCount }}</span>
          </div>
          <a-progress 
            :percent="(votedCount / aliveCount) * 100" 
            :show-text="false"
            size="small"
          />
        </div>
        
        <div class="night-progress" v-if="currentPhase === 'Night'">
          <div class="progress-stat">
            <span class="label">已行动:</span>
            <span class="value">{{ actedCount }}/{{ nightActionRequiredCount }}</span>
          </div>
          <a-progress 
            :percent="nightActionRequiredCount ? (actedCount / nightActionRequiredCount) * 100 : 100" 
            :show-text="false"
            size="small"
          />
        </div>
      </div>
    </div>

    <div class="recent-events" v-if="recentEvents.length > 0">
      <div class="events-header">
        <h4>最近事件</h4>
        <a-button type="text" size="mini" @click="showAllEvents = !showAllEvents">
          {{ showAllEvents ? '收起' : '展开' }}
        </a-button>
      </div>
      
      <div class="events-list">
        <div 
          v-for="event in displayedEvents" 
          :key="event.id"
          class="event-item"
          :class="`event-${event.type}`"
        >
          <div class="event-time">{{ formatEventTime(event.timestamp) }}</div>
          <div class="event-content">{{ formatEventContent(event) }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useGameStore } from '@/stores/game'
import { IconClose } from '@arco-design/web-vue/es/icon'

const gameStore = useGameStore()
const showAllEvents = ref(false)

// Computed properties
const currentPlayer = computed(() => gameStore.currentPlayer)
const currentSeat = computed(() => gameStore.currentSeat)
const currentPhase = computed(() => gameStore.currentPhase?.value || '未知')
const currentRound = computed(() => gameStore.currentRoom?.current_round || 0)
const players = computed(() => gameStore.players)
const alivePlayers = computed(() => gameStore.alivePlayers)
const timeRemaining = computed(() => gameStore.phaseTimeRemaining)
const recentEvents = computed(() => gameStore.events.slice(-10))

const totalPlayers = computed(() => players.value.length)
const aliveCount = computed(() => alivePlayers.value.length)

// Mock data - in real app these would come from the game store
const votedPlayers = ref<Record<number, boolean>>({})
const actedPlayers = ref<Record<number, boolean>>({})
const suspectedPlayers = ref<number[]>([])

const votedCount = computed(() => Object.keys(votedPlayers.value).length)
const actedCount = computed(() => Object.keys(actedPlayers.value).length)
const nightActionRequiredCount = computed(() => {
  // Calculate based on roles that need to act at night
  return Math.max(1, Math.floor(alivePlayers.value.length / 4))
})

const showProgress = computed(() => {
  return ['Vote', 'Night'].includes(currentPhase.value)
})

const displayedEvents = computed(() => {
  return showAllEvents.value ? recentEvents.value : recentEvents.value.slice(-3)
})

// Methods
function getRoleText(role: string): string {
  const roleTexts: Record<string, string> = {
    'Villager': '村民',
    'Werewolf': '狼人',
    'Seer': '预言家',
    'Witch': '女巫',
    'Guard': '守卫',
    'Hunter': '猎人',
    'Idiot': '白痴'
  }
  return roleTexts[role] || role
}

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function formatEventTime(timestamp: number): string {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit',
    second: '2-digit'
  })
}

function formatEventContent(event: any): string {
  // Simplified event formatting
  switch (event.type) {
    case 'speak':
      return `${event.seat}号发言: ${event.content?.text?.substring(0, 50) || ''}...`
    case 'vote':
      return `${event.seat}号投票给${event.target || '弃票'}`
    case 'phase_change':
      return `阶段变更: ${event.from_phase} → ${event.to_phase}`
    case 'player_died':
      return `${event.seat}号玩家死亡`
    default:
      return `系统事件: ${event.type}`
  }
}
</script>

<style scoped>
.game-status {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  height: fit-content;
}

.status-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e5e6eb;
}

.game-info h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  color: #1d2129;
}

.game-meta {
  display: flex;
  align-items: center;
  font-size: 14px;
  color: #4e5969;
}

.player-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.player-details {
  text-align: left;
}

.player-name {
  font-weight: 500;
  color: #1d2129;
}

.player-role {
  font-size: 12px;
  color: #86909c;
}

.overview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.overview-header h4 {
  margin: 0;
  font-size: 16px;
}

.stats {
  font-size: 14px;
  color: #4e5969;
}

.players-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
  margin-bottom: 24px;
}

.player-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 8px;
  border: 1px solid #e5e6eb;
  border-radius: 6px;
  background: #fafbfc;
  position: relative;
}

.player-status.current {
  border-color: #00d0b6;
  background: #e8fff9;
}

.player-status.dead {
  opacity: 0.6;
  background: #f7f8fa;
}

.player-status.suspected {
  border-color: #f53f3f;
  background: #fff1f1;
}

.player-avatar {
  position: relative;
  margin-bottom: 8px;
}

.death-marker {
  position: absolute;
  top: -2px;
  right: -2px;
  background: #f53f3f;
  color: white;
  border-radius: 50%;
  width: 14px;
  height: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
}

.player-basic-info {
  text-align: center;
  margin-bottom: 8px;
}

.seat-number {
  font-weight: 500;
  color: #1d2129;
}

.revealed-role {
  font-size: 11px;
  color: #86909c;
  margin-top: 2px;
}

.player-indicators {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  justify-content: center;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.progress-header h4 {
  margin: 0;
  font-size: 16px;
}

.time-remaining {
  font-size: 14px;
  color: #f53f3f;
  font-weight: 500;
  font-family: monospace;
}

.progress-details {
  margin-bottom: 24px;
}

.progress-stat {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
}

.label {
  color: #4e5969;
}

.value {
  font-weight: 500;
  color: #1d2129;
}

.events-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.events-header h4 {
  margin: 0;
  font-size: 16px;
}

.events-list {
  max-height: 200px;
  overflow-y: auto;
}

.event-item {
  display: flex;
  gap: 12px;
  padding: 8px 12px;
  margin-bottom: 4px;
  border-radius: 4px;
  background: #fafbfc;
  border-left: 3px solid #e5e6eb;
}

.event-speak {
  border-left-color: #3491fa;
}

.event-vote {
  border-left-color: #f53f3f;
}

.event-system {
  border-left-color: #86909c;
}

.event-time {
  font-size: 12px;
  color: #86909c;
  min-width: 60px;
  font-family: monospace;
}

.event-content {
  font-size: 13px;
  color: #4e5969;
  flex: 1;
}

.players-overview, .game-progress, .recent-events {
  margin-top: 24px;
}
</style>