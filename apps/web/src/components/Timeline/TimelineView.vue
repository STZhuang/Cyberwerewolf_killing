<template>
  <div class="timeline-view" ref="timelineRef">
    <div
      class="timeline-container"
      @scroll="handleScroll"
      ref="containerRef"
      role="log"
      aria-live="polite"
      aria-label="游戏消息时间线"
    >
      <!-- Virtual scroll container -->
      <div
        ref="virtualizerRef"
        class="virtualizer-container"
        :style="{ height: `${totalHeight}px` }"
      >
        <!-- Virtual items -->
        <div
          v-for="virtualItem in virtualItems"
          :key="virtualItem.key"
          class="virtual-item"
          :style="{
            position: 'absolute',
            top: `${virtualItem.start}px`,
            left: 0,
            right: 0,
            height: `${virtualItem.size}px`
          }"
        >
          <MessageBubble
            v-bind="virtualItem.data"
            :ref="el => setItemRef(virtualItem.index, el)"
            @vue:mounted="onItemMounted(virtualItem.index)"
            @vue:updated="onItemUpdated(virtualItem.index)"
          />
        </div>
      </div>

      <!-- Loading indicator -->
      <div v-if="isLoadingMore" class="loading-indicator">
        <Spin size="small" />
        <span>加载更多消息...</span>
      </div>

      <!-- Empty state -->
      <div v-else-if="messages.length === 0" class="empty-state">
        <IconMessage class="empty-icon" />
        <p class="empty-text">还没有消息，开始聊天吧！</p>
      </div>
    </div>

    <!-- Scroll to bottom button -->
    <Transition name="fade">
      <Button
        v-if="showScrollToBottom"
        class="scroll-to-bottom"
        type="primary"
        shape="circle"
        size="large"
        @click="scrollToBottom"
        :aria-label="unreadCount > 0 ? `有 ${unreadCount} 条新消息，滚动到底部` : '滚动到底部'"
      >
        <IconDown />
        <Badge
          v-if="unreadCount > 0"
          :count="unreadCount"
          :max-count="99"
          class="unread-badge"
        />
      </Button>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useVirtualList } from '@vueuse/core'
import { Button, Spin, Badge } from '@arco-design/web-vue'
import { IconMessage, IconDown } from '@arco-design/web-vue/es/icon'
import MessageBubble from './MessageBubble.vue'
import type { MessageBubbleProps } from '@/types'
import { useGameStore } from '@/stores'

interface Props {
  messages: MessageBubbleProps[]
  autoScroll?: boolean
  loadMore?: () => Promise<void>
  hasMore?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  autoScroll: true,
  hasMore: false
})

const gameStore = useGameStore()

// Template refs
const timelineRef = ref<HTMLElement>()
const containerRef = ref<HTMLElement>()
const virtualizerRef = ref<HTMLElement>()

// Virtual scrolling state
const itemRefs = new Map<number, HTMLElement>()
const itemHeights = new Map<number, number>()
const estimatedHeight = 120 // Estimated height per message
const overscan = 5 // Number of items to render outside viewport

// Scroll state
const isScrolling = ref(false)
const showScrollToBottom = ref(false)
const isLoadingMore = ref(false)
const unreadCount = ref(0)
const lastReadIndex = ref(0)

// Virtual list setup
const {
  list: virtualItems,
  containerProps,
  wrapperProps,
  scrollTo
} = useVirtualList(
  computed(() => props.messages),
  {
    itemHeight: (index) => itemHeights.get(index) || estimatedHeight,
    overscan: overscan
  }
)

// Computed properties
const totalHeight = computed(() => {
  let height = 0
  for (let i = 0; i < props.messages.length; i++) {
    height += itemHeights.get(i) || estimatedHeight
  }
  return height
})

// Watchers
watch(
  () => props.messages.length,
  async (newLength, oldLength) => {
    if (newLength > oldLength && props.autoScroll && gameStore.isTimelineAtBottom) {
      await nextTick()
      scrollToBottom()
    } else if (newLength > oldLength) {
      unreadCount.value += newLength - oldLength
    }
  }
)

watch(
  () => gameStore.isTimelineAtBottom,
  (isAtBottom) => {
    if (isAtBottom) {
      unreadCount.value = 0
      lastReadIndex.value = props.messages.length - 1
    }
  }
)

// Lifecycle
onMounted(() => {
  // Initial scroll to bottom if needed
  if (props.autoScroll) {
    nextTick(() => scrollToBottom())
  }

  // Setup intersection observer for auto-loading
  if (props.loadMore && props.hasMore) {
    setupIntersectionObserver()
  }

  // Setup resize observer for dynamic heights
  setupResizeObserver()
})

onUnmounted(() => {
  cleanup()
})

// Methods
function setItemRef(index: number, el: any): void {
  if (el?.$el) {
    itemRefs.set(index, el.$el)
  }
}

function onItemMounted(index: number): void {
  measureItemHeight(index)
}

function onItemUpdated(index: number): void {
  measureItemHeight(index)
}

function measureItemHeight(index: number): void {
  const element = itemRefs.get(index)
  if (element) {
    const height = element.getBoundingClientRect().height
    if (height > 0 && height !== itemHeights.get(index)) {
      itemHeights.set(index, height)
    }
  }
}

function handleScroll(event: Event): void {
  const target = event.target as HTMLElement
  if (!target) return

  isScrolling.value = true
  
  // Check if at bottom
  const isAtBottom = target.scrollTop + target.clientHeight >= target.scrollHeight - 10
  gameStore.setTimelineAtBottom(isAtBottom)
  
  // Show/hide scroll to bottom button
  showScrollToBottom.value = !isAtBottom && props.messages.length > 0

  // Reset unread count if at bottom
  if (isAtBottom) {
    unreadCount.value = 0
    lastReadIndex.value = props.messages.length - 1
  }

  // Debounce scroll end
  clearTimeout(scrollEndTimer)
  scrollEndTimer = setTimeout(() => {
    isScrolling.value = false
  }, 150)

  // Load more messages if at top
  if (target.scrollTop < 100 && props.loadMore && props.hasMore && !isLoadingMore.value) {
    loadMoreMessages()
  }
}

let scrollEndTimer: number | null = null

async function loadMoreMessages(): Promise<void> {
  if (!props.loadMore || !props.hasMore || isLoadingMore.value) return

  isLoadingMore.value = true
  try {
    await props.loadMore()
  } catch (error) {
    console.error('Failed to load more messages:', error)
  } finally {
    isLoadingMore.value = false
  }
}

function scrollToBottom(): void {
  if (!containerRef.value) return

  containerRef.value.scrollTo({
    top: containerRef.value.scrollHeight,
    behavior: 'smooth'
  })
}

function scrollToIndex(index: number): void {
  if (index < 0 || index >= props.messages.length) return
  
  scrollTo(index)
}

function scrollToMessage(messageId: string): void {
  const index = props.messages.findIndex(msg => msg.id === messageId)
  if (index > -1) {
    scrollToIndex(index)
  }
}

// Intersection Observer for auto-loading
let intersectionObserver: IntersectionObserver | null = null

function setupIntersectionObserver(): void {
  if (!containerRef.value || intersectionObserver) return

  intersectionObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting && entry.target.classList.contains('load-trigger')) {
          loadMoreMessages()
        }
      })
    },
    {
      root: containerRef.value,
      threshold: 0.1
    }
  )
}

// Resize Observer for dynamic heights
let resizeObserver: ResizeObserver | null = null

function setupResizeObserver(): void {
  if (!('ResizeObserver' in window) || resizeObserver) return

  resizeObserver = new ResizeObserver((entries) => {
    entries.forEach((entry) => {
      const element = entry.target as HTMLElement
      const index = Array.from(itemRefs.entries()).find(([, el]) => el === element)?.[0]
      
      if (typeof index === 'number') {
        const height = entry.contentRect.height
        if (height > 0) {
          itemHeights.set(index, height)
        }
      }
    })
  })

  // Observe all existing items
  itemRefs.forEach((element) => {
    resizeObserver!.observe(element)
  })
}

function cleanup(): void {
  if (scrollEndTimer) {
    clearTimeout(scrollEndTimer)
  }

  if (intersectionObserver) {
    intersectionObserver.disconnect()
    intersectionObserver = null
  }

  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }

  itemRefs.clear()
  itemHeights.clear()
}

// Keyboard navigation
function handleKeydown(event: KeyboardEvent): void {
  if (event.target !== containerRef.value) return

  switch (event.key) {
    case 'Home':
      event.preventDefault()
      scrollTo(0)
      break
    case 'End':
      event.preventDefault()
      scrollToBottom()
      break
    case 'PageUp':
      event.preventDefault()
      containerRef.value?.scrollBy({ top: -containerRef.value.clientHeight * 0.8 })
      break
    case 'PageDown':
      event.preventDefault()
      containerRef.value?.scrollBy({ top: containerRef.value.clientHeight * 0.8 })
      break
  }
}

// Expose methods for parent component
defineExpose({
  scrollToBottom,
  scrollToIndex,
  scrollToMessage,
  loadMoreMessages
})
</script>

<style scoped lang="scss">
.timeline-view {
  position: relative;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.timeline-container {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 16px;
  scroll-behavior: smooth;

  &:focus {
    outline: 2px solid var(--color-primary-6);
    outline-offset: -2px;
  }

  // Custom scrollbar
  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-track {
    background: var(--color-neutral-2);
    border-radius: 3px;
  }

  &::-webkit-scrollbar-thumb {
    background: var(--color-neutral-4);
    border-radius: 3px;

    &:hover {
      background: var(--color-neutral-5);
    }
  }
}

.virtualizer-container {
  position: relative;
  width: 100%;
  min-height: 100%;
}

.virtual-item {
  padding: 0 4px;
}

.loading-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px;
  color: var(--color-text-3);
  font-size: 14px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--color-text-3);

  .empty-icon {
    font-size: 48px;
    margin-bottom: 16px;
    opacity: 0.5;
  }

  .empty-text {
    margin: 0;
    font-size: 16px;
  }
}

.scroll-to-bottom {
  position: absolute;
  bottom: 24px;
  right: 24px;
  z-index: 10;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);

  .unread-badge {
    position: absolute;
    top: -8px;
    right: -8px;
  }
}

// Transitions
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

// High contrast support
@media (prefers-contrast: high) {
  .timeline-container {
    &::-webkit-scrollbar-thumb {
      background: var(--color-text-1);
    }
  }

  .scroll-to-bottom {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
  }
}

// Reduced motion support
@media (prefers-reduced-motion: reduce) {
  .timeline-container {
    scroll-behavior: auto;
  }

  .scroll-to-bottom {
    transition: none;
  }

  .fade-enter-active,
  .fade-leave-active {
    transition: none;
  }
}

// Mobile responsiveness
@media (max-width: 768px) {
  .timeline-container {
    padding: 12px 8px;
  }

  .virtual-item {
    padding: 0 2px;
  }

  .scroll-to-bottom {
    bottom: 16px;
    right: 16px;
  }
}

// Dark theme support
@media (prefers-color-scheme: dark) {
  .timeline-container {
    &::-webkit-scrollbar-track {
      background: var(--color-neutral-8);
    }

    &::-webkit-scrollbar-thumb {
      background: var(--color-neutral-6);

      &:hover {
        background: var(--color-neutral-5);
      }
    }
  }
}
</style>