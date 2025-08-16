<template>
  <div
    :class="bubbleClasses"
    :aria-label="ariaLabel"
    role="article"
    tabindex="0"
  >
    <!-- System messages -->
    <div v-if="visibility === 'system'" class="system-message">
      <div class="system-content">
        <h4 v-if="content.blocks?.[0]?.type === 'markdown'" class="system-title">
          {{ extractTitle(content.blocks[0].content || '') }}
        </h4>
        <div class="system-body">
          <ContentRenderer :content="content" />
        </div>
        <time class="system-time" :datetime="new Date(timestamp).toISOString()">
          {{ formatTime(timestamp) }}
        </time>
      </div>
    </div>

    <!-- Regular messages -->
    <div v-else class="message-bubble">
      <!-- Author info -->
      <div class="message-header">
        <div class="author-info">
          <div class="avatar" :style="{ backgroundColor: avatarColor }">
            {{ authorInitials }}
          </div>
          <div class="author-details">
            <span class="author-name">{{ authorName }}</span>
            <span v-if="roleBadge" :class="['role-badge', `role-${roleBadge.toLowerCase()}`]">
              {{ roleBadge }}
            </span>
            <span v-if="seat" class="seat-number">#{{ seat }}</span>
          </div>
        </div>
        <div class="message-meta">
          <time :datetime="new Date(timestamp).toISOString()">
            {{ formatTime(timestamp) }}
          </time>
          <span v-if="visibility !== 'public'" :class="['visibility-badge', `visibility-${visibility}`]">
            {{ visibilityLabel }}
          </span>
        </div>
      </div>

      <!-- Message content -->
      <div class="message-content">
        <ContentRenderer :content="content" />
        
        <!-- Streaming indicator -->
        <span v-if="status === 'streaming'" class="streaming-indicator" aria-live="polite">
          <span class="cursor">|</span>
        </span>

        <!-- Error state -->
        <div v-if="status === 'error'" class="error-state">
          <IconExclamationCircle class="error-icon" />
          <span class="error-text">Message failed to send</span>
          <Button
            v-if="onRetry"
            size="mini"
            type="text"
            @click="onRetry"
            class="retry-button"
          >
            Retry
          </Button>
        </div>

        <!-- Retracted state -->
        <div v-if="status === 'retracted'" class="retracted-state">
          <IconInfoCircle class="retracted-icon" />
          <span class="retracted-text">This message was retracted</span>
        </div>
      </div>

      <!-- Actions -->
      <div v-if="actions && actions.length > 0" class="message-actions">
        <Button
          v-for="action in actions"
          :key="action.label"
          size="mini"
          type="text"
          @click="action.onClick"
          class="action-button"
        >
          {{ action.label }}
        </Button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Button } from '@arco-design/web-vue'
import { IconExclamationCircle, IconInfoCircle } from '@arco-design/web-vue/es/icon'
import ContentRenderer from './ContentRenderer.vue'
import type { MessageBubbleProps } from '@/types'
import { useAuthStore } from '@/stores'

const props = defineProps<MessageBubbleProps>()

const authStore = useAuthStore()

// Computed properties
const isFromCurrentUser = computed(() => {
  return props.authorName === authStore.userName
})

const bubbleClasses = computed(() => [
  'message-bubble-container',
  `visibility-${props.visibility}`,
  `phase-${props.phase.toLowerCase()}`,
  `status-${props.status || 'final'}`,
  {
    'from-current-user': isFromCurrentUser.value,
    'system-message-container': props.visibility === 'system'
  }
])

const authorInitials = computed(() => {
  return props.authorName
    .split(' ')
    .map(word => word.charAt(0))
    .join('')
    .substring(0, 2)
    .toUpperCase()
})

const avatarColor = computed(() => {
  // Generate a consistent color based on author name
  let hash = 0
  for (let i = 0; i < props.authorName.length; i++) {
    hash = props.authorName.charCodeAt(i) + ((hash << 5) - hash)
  }
  const hue = Math.abs(hash) % 360
  return `hsl(${hue}, 65%, 50%)`
})

const visibilityLabel = computed(() => {
  switch (props.visibility) {
    case 'team': return '队伍'
    case 'private': return '私密'
    case 'system': return '系统'
    default: return '公开'
  }
})

const ariaLabel = computed(() => {
  const timeStr = formatTime(props.timestamp)
  const visibilityStr = props.visibility === 'public' ? '' : ` (${visibilityLabel.value})`
  const seatStr = props.seat ? ` ${props.seat}号` : ''
  const content = extractTextContent(props.content)
  
  return `${seatStr}玩家 ${props.authorName} 在 ${timeStr}${visibilityStr} 说：${content}`
})

// Helper functions
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
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function extractTitle(markdown: string): string {
  const match = markdown.match(/^#\s+(.+)$/m)
  return match ? match[1] : ''
}

function extractTextContent(content: MessageBubbleProps['content']): string {
  let text = ''
  
  if (typeof content.text === 'string') {
    text = content.text
  } else if (content.text && 'chunks' in content.text) {
    text = content.text.chunks.join('')
  }
  
  if (content.blocks) {
    const blockTexts = content.blocks.map(block => {
      switch (block.type) {
        case 'markdown':
          return block.content || ''
        case 'code':
          return block.code || ''
        case 'table':
          return `表格 (${block.headers?.length || 0} 列)`
        case 'vote_summary':
          return `投票汇总 (${block.votes?.length || 0} 票)`
        default:
          return ''
      }
    })
    text += ' ' + blockTexts.join(' ')
  }
  
  return text.trim().substring(0, 100) + (text.length > 100 ? '...' : '')
}
</script>

<style scoped lang="scss">
.message-bubble-container {
  margin-bottom: 12px;
  animation: fadeIn 0.3s ease-out;

  &.from-current-user .message-bubble {
    margin-left: auto;
    margin-right: 0;
    background: var(--color-primary-light-1);
    border-color: var(--color-primary-light-2);

    .message-header .author-details .author-name {
      color: var(--color-primary-6);
      font-weight: 600;
    }
  }

  &.visibility-team {
    .message-bubble {
      background: var(--color-warning-light-9);
      border-left: 3px solid var(--color-warning-6);
    }

    .visibility-badge {
      background: var(--color-warning-light-2);
      color: var(--color-warning-6);
    }
  }

  &.visibility-private {
    .message-bubble {
      background: var(--color-success-light-9);
      border-left: 3px solid var(--color-success-6);
    }

    .visibility-badge {
      background: var(--color-success-light-2);
      color: var(--color-success-6);
    }
  }

  &.status-streaming {
    .streaming-indicator {
      display: inline-flex;
      align-items: center;
      margin-left: 4px;
      
      .cursor {
        animation: blink 1s infinite;
        font-weight: bold;
        color: var(--color-primary-6);
      }
    }
  }

  &.status-error {
    .message-bubble {
      background: var(--color-danger-light-9);
      border-color: var(--color-danger-light-6);
    }
  }

  &.status-retracted {
    opacity: 0.6;
    
    .message-content {
      position: relative;
      
      &::after {
        content: '';
        position: absolute;
        top: 50%;
        left: 0;
        right: 0;
        height: 1px;
        background: var(--color-text-3);
        transform: translateY(-50%);
      }
    }
  }

  &.system-message-container {
    margin: 16px 0;
  }
}

.system-message {
  display: flex;
  justify-content: center;
  
  .system-content {
    max-width: 600px;
    text-align: center;
    padding: 16px 24px;
    background: var(--color-neutral-2);
    border-radius: 12px;
    border: 1px solid var(--color-neutral-3);
  }
  
  .system-title {
    margin: 0 0 8px 0;
    font-size: 16px;
    font-weight: 600;
    color: var(--color-text-1);
  }
  
  .system-body {
    margin-bottom: 8px;
    color: var(--color-text-2);
  }
  
  .system-time {
    font-size: 12px;
    color: var(--color-text-3);
  }
}

.message-bubble {
  max-width: 70%;
  padding: 12px 16px;
  background: var(--color-bg-2);
  border: 1px solid var(--color-neutral-3);
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;

  &:hover {
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
  }

  &:focus-within {
    outline: 2px solid var(--color-primary-6);
    outline-offset: 2px;
  }
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.author-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 12px;
  font-weight: 600;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.author-details {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.author-name {
  font-weight: 500;
  color: var(--color-text-1);
}

.role-badge {
  padding: 2px 6px;
  font-size: 10px;
  font-weight: 500;
  border-radius: 4px;
  text-transform: uppercase;

  &.role-gm {
    background: var(--color-gold-2);
    color: var(--color-gold-7);
  }

  &.role-spectator {
    background: var(--color-neutral-2);
    color: var(--color-neutral-6);
  }
}

.seat-number {
  font-size: 12px;
  color: var(--color-text-3);
}

.message-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--color-text-3);
}

.visibility-badge {
  padding: 2px 6px;
  font-size: 10px;
  border-radius: 4px;
  background: var(--color-neutral-2);
  color: var(--color-neutral-7);
}

.message-content {
  color: var(--color-text-1);
  line-height: 1.5;
  word-wrap: break-word;
}

.error-state, .retracted-state {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  padding: 8px;
  border-radius: 6px;
  font-size: 12px;
}

.error-state {
  background: var(--color-danger-light-9);
  color: var(--color-danger-6);

  .error-icon {
    color: var(--color-danger-6);
  }

  .retry-button {
    margin-left: auto;
    color: var(--color-danger-6);
  }
}

.retracted-state {
  background: var(--color-neutral-2);
  color: var(--color-text-3);

  .retracted-icon {
    color: var(--color-text-3);
  }
}

.message-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--color-neutral-3);
}

.action-button {
  font-size: 12px;
  height: 24px;
  color: var(--color-primary-6);

  &:hover {
    background: var(--color-primary-light-9);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes blink {
  0%, 50% {
    opacity: 1;
  }
  51%, 100% {
    opacity: 0;
  }
}

// High contrast theme support
@media (prefers-contrast: high) {
  .message-bubble {
    border-width: 2px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  }

  .system-message .system-content {
    border-width: 2px;
  }
}

// Reduce motion for accessibility
@media (prefers-reduced-motion: reduce) {
  .message-bubble-container {
    animation: none;
  }

  .streaming-indicator .cursor {
    animation: none;
  }

  .message-bubble {
    transition: none;
  }
}
</style>