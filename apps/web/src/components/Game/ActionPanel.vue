<template>
  <div class="action-panel" :class="{ disabled }" role="region" aria-label="游戏操作面板">
    <!-- Phase-specific actions -->
    <div v-if="availableActions.length > 0" class="action-groups">
      <!-- Vote actions -->
      <div v-if="voteActions.length > 0" class="action-group vote-group">
        <h3 class="group-title">
          <IconThumbUp />
          投票
        </h3>
        <div class="action-buttons">
          <Button
            v-for="action in voteActions"
            :key="action.id"
            :type="action.enabled ? 'primary' : 'secondary'"
            :disabled="!action.enabled || disabled"
            size="large"
            class="action-button vote-button"
            @click="handleActionClick(action)"
          >
            <IconUser />
            {{ action.label }}
          </Button>
        </div>
        
        <!-- Player selection for voting -->
        <div v-if="showPlayerSelection" class="player-selection">
          <h4 class="selection-title">选择投票目标</h4>
          <div class="player-grid">
            <Button
              v-for="player in selectablePlayers"
              :key="player.seat"
              :type="selectedTarget === player.seat ? 'primary' : 'outline'"
              :disabled="disabled"
              class="player-button"
              @click="selectTarget(player.seat)"
            >
              <div class="player-info">
                <span class="seat-number">#{{ player.seat }}</span>
                <span class="player-name">{{ player.name }}</span>
                <span v-if="!player.is_alive" class="dead-indicator">💀</span>
              </div>
            </Button>
            
            <!-- Abstain option -->
            <Button
              type="outline"
              :disabled="disabled"
              class="player-button abstain-button"
              @click="selectTarget(null)"
            >
              <div class="player-info">
                <span class="abstain-text">弃票</span>
              </div>
            </Button>
          </div>
          
          <div class="selection-actions">
            <Button
              type="primary"
              :disabled="!canConfirmSelection || disabled"
              @click="confirmVote"
            >
              确认投票
            </Button>
            <Button type="text" @click="cancelSelection">取消</Button>
          </div>
        </div>
      </div>

      <!-- Night actions -->
      <div v-if="nightActions.length > 0" class="action-group night-group">
        <h3 class="group-title">
          <IconMoon />
          夜间行动
        </h3>
        <div class="action-buttons">
          <Button
            v-for="action in nightActions"
            :key="action.id"
            :type="action.enabled ? 'primary' : 'secondary'"
            :disabled="!action.enabled || disabled"
            size="large"
            class="action-button night-button"
            @click="handleActionClick(action)"
          >
            <component :is="getActionIcon(action.type)" />
            {{ action.label }}
          </Button>
        </div>
      </div>

      <!-- Special actions -->
      <div v-if="specialActions.length > 0" class="action-group special-group">
        <h3 class="group-title">
          <IconMore />
          特殊能力
        </h3>
        <div class="action-buttons">
          <Button
            v-for="action in specialActions"
            :key="action.id"
            :type="action.enabled ? 'primary' : 'secondary'"
            :disabled="!action.enabled || disabled"
            size="large"
            class="action-button special-button"
            @click="handleActionClick(action)"
          >
            <component :is="getActionIcon(action.type)" />
            {{ action.label }}
            <span v-if="action.description" class="action-description">
              {{ action.description }}
            </span>
          </Button>
        </div>
      </div>
    </div>

    <!-- No actions available -->
    <div v-else class="no-actions">
      <IconClockCircle class="no-actions-icon" />
      <p class="no-actions-text">{{ getNoActionsMessage() }}</p>
    </div>

    <!-- Action confirmation modal -->
    <Modal
      v-model:visible="showConfirmModal"
      title="确认操作"
      :ok-text="confirmAction?.label || '确认'"
      cancel-text="取消"
      @ok="executeConfirmedAction"
      @cancel="cancelConfirmation"
    >
      <p v-if="confirmAction">
        你确定要执行「{{ confirmAction.label }}」吗？
        <span v-if="selectedTarget !== null">
          目标：{{ getPlayerName(selectedTarget) }}
        </span>
      </p>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Button, Modal, Message } from '@arco-design/web-vue'
import { 
  IconThumbUp,
  IconUser,
  IconMoon,
  IconClockCircle,
  IconEye,
  IconSafe,
  IconFire,
  IconHeart,
  IconMore
} from '@arco-design/web-vue/es/icon'
import type { ActionPanelProps, GameAction, Player } from '@/types'
import { useGameStore } from '@/stores'

const props = defineProps<ActionPanelProps>()

const gameStore = useGameStore()

// Reactive state
const showPlayerSelection = ref(false)
const selectedTarget = ref<number | null>(null)
const showConfirmModal = ref(false)
const confirmAction = ref<GameAction | null>(null)
const pendingAction = ref<GameAction | null>(null)

// Computed properties
const voteActions = computed(() => 
  props.availableActions.filter(action => action.type === 'vote')
)

const nightActions = computed(() => 
  props.availableActions.filter(action => action.type === 'night_action')
)

const specialActions = computed(() => 
  props.availableActions.filter(action => action.type === 'special')
)

const selectablePlayers = computed(() => {
  return gameStore.players.filter(player => {
    // Filter out current player (can't vote for self in most cases)
    if (player.seat === gameStore.currentSeat) return false
    
    // Include alive players and dead players if explicitly allowed
    const action = pendingAction.value
    if (action?.targets && action.targets.length > 0) {
      return action.targets.includes(player.seat)
    }
    
    // Default: only alive players
    return player.is_alive
  })
})

const canConfirmSelection = computed(() => {
  // Always allow abstain (null)
  if (selectedTarget.value === null) return true
  
  // Check if selected target is valid
  return selectablePlayers.value.some(player => player.seat === selectedTarget.value)
})

// Methods
function handleActionClick(action: GameAction): void {
  if (!action.enabled || props.disabled) return

  pendingAction.value = action

  // If action requires target selection, show player selection
  if (action.type === 'vote' || (action.type === 'night_action' && needsTargetSelection(action))) {
    showPlayerSelection.value = true
    selectedTarget.value = null
  } else {
    // Direct action execution
    confirmAction.value = action
    showConfirmModal.value = true
  }
}

function needsTargetSelection(action: GameAction): boolean {
  // Check if action requires target based on action ID or other criteria
  const targetRequiredActions = ['seer_check', 'guard_protect', 'witch_poison', 'witch_heal', 'werewolf_kill']
  return targetRequiredActions.some(targetAction => action.id.includes(targetAction))
}

function selectTarget(seat: number | null): void {
  selectedTarget.value = seat
}

function confirmVote(): void {
  if (!pendingAction.value || !canConfirmSelection.value) return

  confirmAction.value = pendingAction.value
  showConfirmModal.value = true
}

function cancelSelection(): void {
  showPlayerSelection.value = false
  selectedTarget.value = null
  pendingAction.value = null
}

function executeConfirmedAction(): void {
  if (!confirmAction.value) return

  try {
    // Execute the action
    confirmAction.value.onClick(selectedTarget.value || undefined)
    
    // Show success message
    Message.success(`已执行：${confirmAction.value.label}`)
    
    // Reset state
    resetActionState()
  } catch (error) {
    console.error('Failed to execute action:', error)
    Message.error('操作失败，请重试')
  }
}

function cancelConfirmation(): void {
  resetActionState()
}

function resetActionState(): void {
  showPlayerSelection.value = false
  showConfirmModal.value = false
  selectedTarget.value = null
  confirmAction.value = null
  pendingAction.value = null
}

function getActionIcon(type: string): any {
  const iconMap: Record<string, any> = {
    vote: IconThumbUp,
    night_action: IconMoon,
    special: IconMore,
    seer_check: IconEye,
    guard_protect: IconSafe,
    witch_poison: IconFire,
    witch_heal: IconHeart,
    werewolf_kill: IconMore, // Fallback since sword doesn't exist
    hunter_shoot: IconMore // Fallback since target doesn't exist
  }
  
  return iconMap[type] || IconMore
}

function getPlayerName(seat: number | null): string {
  if (seat === null) return '弃票'
  
  const player = gameStore.players.find(p => p.seat === seat)
  return player ? `#${seat} ${player.name}` : `#${seat}`
}

function getNoActionsMessage(): string {
  switch (props.phase) {
    case 'Night':
      return '夜深了，等待其他玩家行动...'
    case 'DayTalk':
      return '自由讨论阶段，可以发言交流'
    case 'Vote':
      return '等待投票开始...'
    case 'Trial':
      return '等待审判结果...'
    case 'Result':
      return '查看游戏结果...'
    default:
      return '暂无可用操作'
  }
}

// Keyboard navigation
function handleKeydown(event: KeyboardEvent): void {
  if (showPlayerSelection.value && event.key === 'Escape') {
    cancelSelection()
  }
  
  if (showConfirmModal.value && event.key === 'Escape') {
    cancelConfirmation()
  }
}

// Watch for keyboard events
onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped lang="scss">
.action-panel {
  background: var(--color-bg-2);
  border: 1px solid var(--color-neutral-3);
  border-radius: 12px;
  padding: 20px;
  margin-top: 16px;

  &.disabled {
    opacity: 0.6;
    pointer-events: none;
  }
}

.action-groups {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.action-group {
  .group-title {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 0 0 12px 0;
    font-size: 16px;
    font-weight: 600;
    color: var(--color-text-1);
    
    .arco-icon {
      color: var(--color-primary-6);
    }
  }
  
  .action-buttons {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
  }
}

.action-button {
  min-width: 120px;
  height: 48px;
  border-radius: 8px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s ease;

  &:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }

  &:active:not(:disabled) {
    transform: translateY(0);
  }

  .action-description {
    font-size: 12px;
    color: var(--color-text-3);
    margin-left: 4px;
  }
}

.vote-button {
  background: var(--color-primary-6);
  border-color: var(--color-primary-6);

  &:hover:not(:disabled) {
    background: var(--color-primary-5);
    border-color: var(--color-primary-5);
  }
}

.night-button {
  background: var(--color-purple-6);
  border-color: var(--color-purple-6);

  &:hover:not(:disabled) {
    background: var(--color-purple-5);
    border-color: var(--color-purple-5);
  }
}

.special-button {
  background: var(--color-orange-6);
  border-color: var(--color-orange-6);

  &:hover:not(:disabled) {
    background: var(--color-orange-5);
    border-color: var(--color-orange-5);
  }
}

.player-selection {
  margin-top: 16px;
  padding: 16px;
  background: var(--color-neutral-1);
  border-radius: 8px;
  border: 1px solid var(--color-neutral-3);

  .selection-title {
    margin: 0 0 12px 0;
    font-size: 14px;
    font-weight: 600;
    color: var(--color-text-1);
  }
}

.player-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 8px;
  margin-bottom: 16px;
}

.player-button {
  height: 56px;
  padding: 8px 12px;
  border-radius: 6px;
  
  .player-info {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
  }
  
  .seat-number {
    font-size: 12px;
    font-weight: 600;
    color: var(--color-text-2);
  }
  
  .player-name {
    font-size: 13px;
    color: var(--color-text-1);
    text-align: center;
    line-height: 1.2;
  }
  
  .dead-indicator {
    font-size: 10px;
    opacity: 0.7;
  }

  &.abstain-button {
    border: 2px dashed var(--color-neutral-4);
    
    .abstain-text {
      font-size: 14px;
      color: var(--color-text-2);
      font-style: italic;
    }
    
    &:hover {
      border-color: var(--color-primary-6);
      
      .abstain-text {
        color: var(--color-primary-6);
      }
    }
  }
}

.selection-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding-top: 12px;
  border-top: 1px solid var(--color-neutral-3);
}

.no-actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 16px;
  text-align: center;
  color: var(--color-text-3);

  .no-actions-icon {
    font-size: 32px;
    margin-bottom: 12px;
    opacity: 0.6;
  }

  .no-actions-text {
    margin: 0;
    font-size: 14px;
    line-height: 1.5;
  }
}

// Phase-specific styling
.vote-group {
  .group-title .arco-icon {
    color: var(--color-primary-6);
  }
}

.night-group {
  .group-title .arco-icon {
    color: var(--color-purple-6);
  }
}

.special-group {
  .group-title .arco-icon {
    color: var(--color-orange-6);
  }
}

// Responsive design
@media (max-width: 768px) {
  .action-panel {
    padding: 16px;
  }
  
  .action-buttons {
    flex-direction: column;
  }
  
  .action-button {
    width: 100%;
    justify-content: center;
  }
  
  .player-grid {
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  }
  
  .selection-actions {
    flex-direction: column-reverse;
    
    .arco-btn {
      width: 100%;
    }
  }
}

@media (max-width: 480px) {
  .player-grid {
    grid-template-columns: 1fr 1fr;
  }
  
  .player-button {
    height: 48px;
  }
}

// High contrast mode
@media (prefers-contrast: high) {
  .action-panel {
    border-width: 2px;
  }
  
  .player-selection {
    border-width: 2px;
  }
  
  .action-button {
    border-width: 2px;
  }
}

// Reduced motion
@media (prefers-reduced-motion: reduce) {
  .action-button {
    transition: none;
    
    &:hover:not(:disabled) {
      transform: none;
    }
    
    &:active:not(:disabled) {
      transform: none;
    }
  }
}

// Focus styles for accessibility
.action-button:focus-visible,
.player-button:focus-visible {
  outline: 2px solid var(--color-primary-6);
  outline-offset: 2px;
}
</style>