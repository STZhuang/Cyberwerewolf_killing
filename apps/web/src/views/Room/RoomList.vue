<template>
  <div class="room-list-page">
    <!-- Header -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">游戏房间</h1>
        <p class="page-subtitle">选择或创建一个房间开始游戏</p>
      </div>
      <div class="header-actions">
        <Button type="primary" @click="router.push('/rooms/create')">
          <IconPlus />
          创建房间
        </Button>
        <Button @click="refreshRooms" :loading="isLoading">
          <IconRefresh />
          刷新
        </Button>
      </div>
    </div>

    <!-- Filters -->
    <div class="filters">
      <div class="filter-group">
        <Select
          v-model="statusFilter"
          placeholder="房间状态"
          allow-clear
          style="width: 150px"
        >
          <Option value="waiting">等待中</Option>
          <Option value="playing">游戏中</Option>
          <Option value="finished">已结束</Option>
        </Select>
        
        <InputSearch
          v-model="searchQuery"
          placeholder="搜索房间名称"
          style="width: 200px"
          allow-clear
        />
      </div>
    </div>

    <!-- Room list -->
    <div class="room-list">
      <!-- Loading state -->
      <div v-if="isLoading && rooms.length === 0" class="loading-state">
        <Spin size="large" />
        <p>加载房间中...</p>
      </div>

      <!-- Empty state -->
      <div v-else-if="filteredRooms.length === 0" class="empty-state">
        <IconApps class="empty-icon" />
        <h3 class="empty-title">暂无房间</h3>
        <p class="empty-description">
          {{ searchQuery || statusFilter ? '没有找到匹配的房间' : '还没有房间，创建一个开始游戏吧' }}
        </p>
        <Button type="primary" @click="router.push('/rooms/create')">
          创建房间
        </Button>
      </div>

      <!-- Room cards -->
      <div v-else class="room-grid">
        <div
          v-for="room in filteredRooms"
          :key="room.id"
          class="room-card"
          :class="{ 
            'room-joinable': room.status === 'waiting' && (room.players?.length || 0) < room.max_players,
            'room-full': (room.players?.length || 0) >= room.max_players,
            'room-playing': room.status === 'playing'
          }"
          @click="handleRoomClick(room)"
        >
          <!-- Room status badge -->
          <div class="room-badge" :class="`badge-${room.status}`">
            {{ getRoomStatusText(room.status) }}
          </div>

          <!-- Room header -->
          <div class="room-header">
            <h3 class="room-name">{{ room.name }}</h3>
            <div class="room-meta">
              <span class="player-count">
                <IconUser />
                {{ room.players?.length || 0 }}/{{ room.max_players }}
              </span>
              <span class="created-time">
                {{ formatTime(room.created_at) }}
              </span>
            </div>
          </div>

          <!-- Game settings preview -->
          <div class="room-settings">
            <div class="setting-item">
              <IconUserGroup />
              <span>{{ getRoleCount(room.settings || room.config) }}</span>
            </div>
            <div class="setting-item" v-if="room.settings?.enable_agent || room.config?.enable_agent">
              <IconRobot />
              <span>AI智能体</span>
            </div>
          </div>

          <!-- Players preview -->
          <div class="room-players">
            <div class="players-list">
              <div
                v-for="(player, index) in (room.players || []).slice(0, 4)"
                :key="player.id"
                class="player-avatar"
                :title="player.name"
              >
                {{ getPlayerInitials(player.name) }}
                <span v-if="player.is_agent" class="agent-indicator">🤖</span>
              </div>
              <div v-if="(room.players?.length || 0) > 4" class="more-players">
                +{{ (room.players?.length || 0) - 4 }}
              </div>
            </div>
          </div>

          <!-- Action button -->
          <div class="room-actions">
            <Button
              v-if="room.status === 'waiting' && (room.players?.length || 0) < room.max_players"
              type="primary"
              @click.stop="joinRoom(room)"
              :loading="joiningRoomId === room.id"
            >
              加入房间
            </Button>
            <Button
              v-else-if="room.status === 'playing'"
              type="outline"
              @click.stop="watchRoom(room)"
            >
              观看游戏
            </Button>
            <Button v-else disabled>
              {{ (room.players?.length || 0) >= room.max_players ? '房间已满' : '游戏结束' }}
            </Button>
          </div>
        </div>
      </div>
    </div>

    <!-- Pagination -->
    <div v-if="filteredRooms.length > 0" class="pagination">
      <Pagination
        v-model:current="currentPage"
        :total="filteredRooms.length"
        :page-size="pageSize"
        show-total
        show-jumper
        show-page-size
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Button,
  Select,
  Option,
  InputSearch,
  Spin,
  Pagination,
  Message
} from '@arco-design/web-vue'
import { 
  IconPlus, 
  IconRefresh, 
  IconApps, 
  IconUser, 
  IconUserGroup, 
  IconRobot 
} from '@arco-design/web-vue/es/icon'
import { apiService } from '@/services/api'
import type { GameRoom, GameSettings } from '@/types'

const router = useRouter()

// Reactive state
const rooms = ref<GameRoom[]>([])
const isLoading = ref(false)
const joiningRoomId = ref<string | null>(null)

// Filters
const statusFilter = ref<string>('')
const searchQuery = ref('')

// Pagination
const currentPage = ref(1)
const pageSize = ref(12)

// Computed properties
const filteredRooms = computed(() => {
  let filtered = rooms.value

  // Status filter
  if (statusFilter.value) {
    filtered = filtered.filter(room => room.status === statusFilter.value)
  }

  // Search filter
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(room => 
      room.name.toLowerCase().includes(query)
    )
  }

  return filtered
})

const paginatedRooms = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredRooms.value.slice(start, end)
})

// Lifecycle
onMounted(() => {
  loadRooms()
  
  // Auto-refresh every 30 seconds
  const interval = setInterval(loadRooms, 30000)
  
  // Cleanup on unmount
  onUnmounted(() => {
    clearInterval(interval)
  })
})

// Methods
async function loadRooms() {
  isLoading.value = true
  
  try {
    const response = await apiService.getRooms()
    if (response.success && response.data) {
      rooms.value = response.data
    } else {
      Message.error('加载房间列表失败')
    }
  } catch (error) {
    console.error('Failed to load rooms:', error)
    Message.error('加载房间列表失败')
  } finally {
    isLoading.value = false
  }
}

async function refreshRooms() {
  await loadRooms()
  Message.success('房间列表已刷新')
}

async function joinRoom(room: GameRoom) {
  joiningRoomId.value = room.id
  
  try {
    const response = await apiService.joinRoom({ room_id: room.id })
    if (response.success) {
      router.push(`/room/${room.id}`)
    } else {
      Message.error(response.error || '加入房间失败')
    }
  } catch (error) {
    console.error('Failed to join room:', error)
    Message.error('加入房间失败')
  } finally {
    joiningRoomId.value = null
  }
}

function watchRoom(room: GameRoom) {
  router.push(`/room/${room.id}?mode=watch`)
}

function handleRoomClick(room: GameRoom) {
  // Navigate to room details or join directly based on status
  if (room.status === 'waiting' && (room.players?.length || 0) < room.max_players) {
    joinRoom(room)
  } else {
    router.push(`/room/${room.id}`)
  }
}

function getRoomStatusText(status: string): string {
  switch (status) {
    case 'waiting': return '等待中'
    case 'playing': return '游戏中'
    case 'finished': return '已结束'
    default: return '未知'
  }
}

function getRoleCount(settings: GameSettings | undefined): string {
  if (!settings) return '未配置'
  
  const werewolfCount = settings.werewolf_count || 0
  const villagerCount = settings.villager_count || 0
  const seerCount = settings.seer_count || 0
  const guardCount = settings.guard_count || 0
  const witchCount = settings.witch_count || 0
  const hunterCount = settings.hunter_count || 0
  
  const total = werewolfCount + villagerCount + seerCount + guardCount + witchCount + hunterCount
  return total > 0 ? `${total}人局` : '未配置'
}

function getPlayerInitials(name: string): string {
  return name
    .split(' ')
    .map(word => word.charAt(0))
    .join('')
    .substring(0, 2)
    .toUpperCase()
}

function formatTime(timestamp: number): string {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  
  if (diffMins < 1) return '刚刚'
  if (diffMins < 60) return `${diffMins}分钟前`
  
  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}小时前`
  
  return date.toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric'
  })
}
</script>

<style scoped lang="scss">
.room-list-page {
  min-height: 100vh;
  background: var(--color-bg-1);
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--color-neutral-3);

  .header-content {
    .page-title {
      font-size: 2rem;
      font-weight: 700;
      margin: 0 0 8px 0;
      color: var(--color-text-1);
    }

    .page-subtitle {
      font-size: 1rem;
      color: var(--color-text-3);
      margin: 0;
    }
  }

  .header-actions {
    display: flex;
    gap: 12px;
  }
}

.filters {
  margin-bottom: 24px;

  .filter-group {
    display: flex;
    gap: 16px;
    align-items: center;
  }
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: var(--color-text-3);

  p {
    margin-top: 16px;
    font-size: 14px;
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: var(--color-text-3);

  .empty-icon {
    font-size: 64px;
    margin-bottom: 20px;
    opacity: 0.6;
  }

  .empty-title {
    font-size: 18px;
    font-weight: 600;
    margin: 0 0 8px 0;
    color: var(--color-text-2);
  }

  .empty-description {
    font-size: 14px;
    line-height: 1.5;
    margin: 0 0 24px 0;
    text-align: center;
  }
}

.room-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.room-card {
  background: var(--color-bg-2);
  border: 1px solid var(--color-neutral-3);
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;

  &:hover {
    border-color: var(--color-primary-6);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
    transform: translateY(-2px);
  }

  &.room-joinable {
    border-color: var(--color-success-6);

    &:hover {
      border-color: var(--color-success-5);
      box-shadow: 0 4px 16px rgba(34, 197, 94, 0.2);
    }
  }

  &.room-full {
    opacity: 0.7;
    cursor: default;

    &:hover {
      transform: none;
      border-color: var(--color-neutral-3);
      box-shadow: none;
    }
  }

  &.room-playing {
    border-color: var(--color-warning-6);

    &:hover {
      border-color: var(--color-warning-5);
    }
  }
}

.room-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;

  &.badge-waiting {
    background: var(--color-success-light-9);
    color: var(--color-success-6);
  }

  &.badge-playing {
    background: var(--color-warning-light-9);
    color: var(--color-warning-6);
  }

  &.badge-finished {
    background: var(--color-neutral-2);
    color: var(--color-text-3);
  }
}

.room-header {
  margin-bottom: 16px;

  .room-name {
    font-size: 18px;
    font-weight: 600;
    margin: 0 0 8px 0;
    color: var(--color-text-1);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .room-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 13px;
    color: var(--color-text-3);

    .player-count {
      display: flex;
      align-items: center;
      gap: 4px;
      font-weight: 500;
    }
  }
}

.room-settings {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;

  .setting-item {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    color: var(--color-text-2);

    .arco-icon {
      color: var(--color-primary-6);
    }
  }
}

.room-players {
  margin-bottom: 20px;

  .players-list {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .player-avatar {
    position: relative;
    width: 32px;
    height: 32px;
    background: var(--color-primary-6);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: 600;
    color: white;
    border: 2px solid var(--color-bg-2);

    .agent-indicator {
      position: absolute;
      top: -4px;
      right: -4px;
      font-size: 12px;
    }
  }

  .more-players {
    width: 32px;
    height: 32px;
    background: var(--color-neutral-4);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    color: var(--color-text-1);
    border: 2px solid var(--color-bg-2);
  }
}

.room-actions {
  .arco-btn {
    width: 100%;
  }
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 40px;
}

// Responsive design
@media (max-width: 768px) {
  .room-list-page {
    padding: 16px;
  }

  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;

    .header-actions {
      justify-content: flex-start;
    }
  }

  .filters .filter-group {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;

    .arco-select,
    .arco-input-search {
      width: 100% !important;
    }
  }

  .room-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .room-card {
    padding: 16px;
  }
}

@media (max-width: 480px) {
  .page-header .header-content .page-title {
    font-size: 1.5rem;
  }

  .room-card {
    padding: 14px;
  }

  .room-header .room-name {
    font-size: 16px;
  }
}

// High contrast mode
@media (prefers-contrast: high) {
  .room-card {
    border-width: 2px;
  }
}

// Reduced motion
@media (prefers-reduced-motion: reduce) {
  .room-card {
    transition: none;

    &:hover {
      transform: none;
    }
  }
}
</style>