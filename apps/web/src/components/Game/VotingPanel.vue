<template>
  <div class="voting-panel">
    <div class="panel-header">
      <div class="phase-info">
        <a-tag :color="phaseColor" size="large">
          {{ phaseText }}
        </a-tag>
        <div v-if="timeRemaining > 0" class="timer">
          {{ formatTime(timeRemaining) }}
        </div>
      </div>
    </div>

    <div v-if="showVotingOptions" class="voting-section">
      <div class="section-title">
        <icon-user-group />
        <span>投票选择</span>
      </div>
      
      <div class="player-grid">
        <div 
          v-for="player in alivePlayers" 
          :key="player.seat"
          class="player-card"
          :class="{ 
            'selected': selectedTarget === player.seat,
            'self': player.seat === currentSeat,
            'dead': !player.is_alive 
          }"
          @click="selectTarget(player.seat)"
        >
          <div class="player-avatar">
            <a-avatar :size="40">
              {{ player.seat }}
            </a-avatar>
          </div>
          <div class="player-info">
            <div class="player-name">{{ player.name || `${player.seat}号` }}</div>
            <div class="player-role" v-if="player.revealed_role">
              {{ getRoleText(player.revealed_role) }}
            </div>
          </div>
          <div class="vote-count" v-if="voteResults[player.seat]">
            {{ voteResults[player.seat] }}票
          </div>
        </div>
      </div>

      <div class="voting-controls">
        <a-button 
          v-if="selectedTarget !== null"
          type="outline"
          @click="clearSelection"
        >
          取消选择
        </a-button>
        
        <a-button
          type="primary"
          size="large"
          :disabled="!canVote"
          :loading="isSubmitting"
          @click="submitVote"
        >
          {{ selectedTarget ? `投票给${selectedTarget}号` : '弃票' }}
        </a-button>
      </div>
    </div>

    <div v-if="showNightActions" class="night-section">
      <div class="section-title">
        <icon-moon />
        <span>夜间行动</span>
      </div>

      <div class="action-selector">
        <a-select 
          v-model="selectedAction" 
          placeholder="选择技能"
          style="width: 200px"
        >
          <a-option
            v-for="action in availableActions"
            :key="action.id"
            :value="action.id"
          >
            {{ action.name }}
          </a-option>
        </a-select>
      </div>

      <div v-if="selectedAction && requiresTarget(selectedAction)" class="target-selector">
        <div class="subtitle">选择目标</div>
        <div class="player-grid">
          <div 
            v-for="player in getValidTargets(selectedAction)" 
            :key="player.seat"
            class="player-card small"
            :class="{ 'selected': selectedNightTarget === player.seat }"
            @click="selectNightTarget(player.seat)"
          >
            <a-avatar :size="32">{{ player.seat }}</a-avatar>
            <span>{{ player.seat }}号</span>
          </div>
        </div>
      </div>

      <div class="night-controls">
        <a-button
          type="primary"
          size="large"
          :disabled="!canSubmitNightAction"
          :loading="isSubmitting"
          @click="submitNightAction"
        >
          确认行动
        </a-button>
      </div>
    </div>

    <div v-if="showSpeakingPanel" class="speaking-section">
      <div class="section-title">
        <icon-message />
        <span>发言</span>
      </div>
      
      <div class="speak-controls">
        <a-textarea
          v-model="speechContent"
          placeholder="输入你的发言..."
          :max-length="500"
          show-word-limit
          :auto-size="{ minRows: 2, maxRows: 4 }"
        />
        
        <div class="speak-buttons">
          <a-button
            type="primary"
            :disabled="!speechContent.trim()"
            :loading="isSubmitting"
            @click="submitSpeak"
          >
            发言
          </a-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useGameStore } from '@/stores/game'
import { IconUserGroup, IconMoon, IconMessage } from '@arco-design/web-vue/es/icon'

const gameStore = useGameStore()

// Reactive data
const selectedTarget = ref<number | null>(null)
const selectedAction = ref<string>('')
const selectedNightTarget = ref<number | null>(null)
const speechContent = ref('')
const isSubmitting = ref(false)
const voteResults = ref<Record<number, number>>({})

// Computed properties
const currentSeat = computed(() => gameStore.currentSeat)
const currentPhase = computed(() => gameStore.currentPhase)
const timeRemaining = computed(() => gameStore.phaseTimeRemaining)
const alivePlayers = computed(() => gameStore.alivePlayers)
const canAct = computed(() => gameStore.canAct)

const phaseColor = computed(() => {
  const colors: Record<string, string> = {
    'DayTalk': 'blue',
    'Vote': 'red', 
    'Night': 'purple',
    'Trial': 'orange'
  }
  return colors[currentPhase.value || ''] || 'gray'
})

const phaseText = computed(() => {
  const texts: Record<string, string> = {
    'DayTalk': '白天讨论',
    'Vote': '投票阶段',
    'Night': '夜间行动',
    'Trial': '审判阶段',
    'Dawn': '黎明阶段'
  }
  return texts[currentPhase.value || ''] || '未知阶段'
})

const showVotingOptions = computed(() => {
  return currentPhase.value === 'Vote' && canAct.value
})

const showNightActions = computed(() => {
  return currentPhase.value === 'Night' && canAct.value
})

const showSpeakingPanel = computed(() => {
  return ['DayTalk', 'Trial'].includes(currentPhase.value || '') && canAct.value
})

const canVote = computed(() => {
  return showVotingOptions.value && !isSubmitting.value
})

const availableActions = computed(() => {
  // This would be determined by the player's role
  const player = gameStore.currentPlayer
  if (!player) return []
  
  const actionsByRole: Record<string, Array<{id: string, name: string}>> = {
    'Werewolf': [{ id: 'kill', name: '击杀' }],
    'Seer': [{ id: 'inspect', name: '查验' }],
    'Witch': [{ id: 'save', name: '救人' }, { id: 'poison', name: '毒杀' }],
    'Guard': [{ id: 'guard', name: '守护' }]
  }
  
  return actionsByRole[player.role] || []
})

const canSubmitNightAction = computed(() => {
  if (!selectedAction.value) return false
  if (requiresTarget(selectedAction.value) && !selectedNightTarget.value) return false
  return !isSubmitting.value
})

// Methods
function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function getRoleText(role: string): string {
  const roleTexts: Record<string, string> = {
    'Villager': '村民',
    'Werewolf': '狼人', 
    'Seer': '预言家',
    'Witch': '女巫',
    'Guard': '守卫',
    'Hunter': '猎人'
  }
  return roleTexts[role] || role
}

function selectTarget(seat: number) {
  if (seat === currentSeat.value) return // Can't vote for self
  selectedTarget.value = selectedTarget.value === seat ? null : seat
}

function clearSelection() {
  selectedTarget.value = null
}

function requiresTarget(action: string): boolean {
  return !['skip'].includes(action)
}

function getValidTargets(action: string) {
  const targets = alivePlayers.value.filter(p => {
    if (action === 'guard' && p.seat === currentSeat.value) return false // Can't guard self
    return true
  })
  return targets
}

function selectNightTarget(seat: number) {
  selectedNightTarget.value = selectedNightTarget.value === seat ? null : seat
}

async function submitVote() {
  if (!canVote.value) return
  
  isSubmitting.value = true
  try {
    gameStore.vote(selectedTarget.value)
    selectedTarget.value = null
  } catch (error) {
    console.error('Vote submission failed:', error)
  } finally {
    isSubmitting.value = false
  }
}

async function submitNightAction() {
  if (!canSubmitNightAction.value) return
  
  isSubmitting.value = true
  try {
    gameStore.nightAction(selectedAction.value, selectedNightTarget.value || undefined)
    selectedAction.value = ''
    selectedNightTarget.value = null
  } catch (error) {
    console.error('Night action submission failed:', error)
  } finally {
    isSubmitting.value = false
  }
}

async function submitSpeak() {
  if (!speechContent.value.trim()) return
  
  isSubmitting.value = true
  try {
    gameStore.sendMessage(speechContent.value.trim())
    speechContent.value = ''
  } catch (error) {
    console.error('Speech submission failed:', error)
  } finally {
    isSubmitting.value = false
  }
}

// Watch for phase changes to reset selections
watch(currentPhase, () => {
  selectedTarget.value = null
  selectedAction.value = ''
  selectedNightTarget.value = null
  speechContent.value = ''
})
</script>

<style scoped>
.voting-panel {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #e5e6eb;
}

.phase-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.timer {
  font-size: 18px;
  font-weight: 600;
  color: #f53f3f;
  font-family: monospace;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 15px;
  color: #1d2129;
}

.player-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 10px;
  margin-bottom: 20px;
}

.player-card {
  display: flex;
  align-items: center;
  padding: 12px;
  border: 2px solid #e5e6eb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  gap: 12px;
}

.player-card:hover {
  border-color: #3491fa;
  background-color: #f7f8fa;
}

.player-card.selected {
  border-color: #3491fa;
  background-color: #e8f4ff;
}

.player-card.self {
  border-color: #00d0b6;
  background-color: #e8fff9;
}

.player-card.dead {
  opacity: 0.5;
  cursor: not-allowed;
}

.player-card.small {
  flex-direction: column;
  padding: 8px;
  gap: 4px;
  min-width: 80px;
}

.player-info {
  flex: 1;
}

.player-name {
  font-weight: 500;
  color: #1d2129;
}

.player-role {
  font-size: 12px;
  color: #86909c;
}

.vote-count {
  background: #f53f3f;
  color: white;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.voting-controls, .night-controls, .speak-buttons {
  display: flex;
  justify-content: center;
  gap: 12px;
}

.action-selector {
  margin-bottom: 15px;
}

.target-selector {
  margin-bottom: 20px;
}

.subtitle {
  font-size: 14px;
  color: #4e5969;
  margin-bottom: 10px;
}

.speak-controls {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.speak-buttons {
  justify-content: flex-end;
}

.voting-section, .night-section, .speaking-section {
  margin-top: 20px;
}
</style>