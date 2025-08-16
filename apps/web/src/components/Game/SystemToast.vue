<template>
  <Teleport to="body">
    <Transition
      name="toast"
      @enter="onEnter"
      @leave="onLeave"
    >
      <div
        v-if="visible"
        :class="toastClasses"
        role="alert"
        :aria-live="type === 'error' ? 'assertive' : 'polite'"
        @click="handleClick"
        @keydown="handleKeydown"
        tabindex="0"
      >
        <div class="toast-icon">
          <AIcon :icon="typeIcon" />
        </div>
        
        <div class="toast-content">
          <h4 class="toast-title">{{ title }}</h4>
          <p v-if="message" class="toast-message">{{ message }}</p>
        </div>
        
        <AButton
          v-if="showCloseButton"
          type="text"
          size="mini"
          class="toast-close"
          @click="close"
          aria-label="关闭通知"
        >
          <AIcon icon="icon-close" />
        </AButton>
        
        <div v-if="duration > 0" class="toast-progress">
          <div
            class="progress-bar"
            :style="{ animationDuration: `${duration}ms` }"
          ></div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { AIcon, AButton } from '@arco-design/web-vue'
import type { SystemToastProps } from '@/types'

interface Props extends SystemToastProps {
  visible?: boolean
  showCloseButton?: boolean
  clickToClose?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  visible: true,
  duration: 5000,
  showCloseButton: true,
  clickToClose: true
})

const emit = defineEmits<{
  close: []
}>()

// Internal state
const autoCloseTimer = ref<number | null>(null)
const isPaused = ref(false)
const remainingTime = ref(props.duration)
const startTime = ref(0)

// Computed properties
const toastClasses = computed(() => [
  'system-toast',
  `toast-${props.type}`,
  {
    'toast-clickable': props.clickToClose,
    'toast-paused': isPaused.value
  }
])

const typeIcon = computed(() => {
  const iconMap: Record<string, string> = {
    success: 'icon-check-circle',
    error: 'icon-close-circle',
    warning: 'icon-exclamation-circle',
    info: 'icon-info-circle'
  }
  return iconMap[props.type] || 'icon-info-circle'
})

// Lifecycle
onMounted(() => {
  if (props.duration > 0) {
    startAutoClose()
  }
})

onUnmounted(() => {
  clearAutoClose()
})

// Methods
function startAutoClose(): void {
  if (props.duration <= 0) return
  
  startTime.value = Date.now()
  remainingTime.value = props.duration
  
  autoCloseTimer.value = window.setTimeout(() => {
    close()
  }, props.duration)
}

function pauseAutoClose(): void {
  if (!autoCloseTimer.value) return
  
  clearTimeout(autoCloseTimer.value)
  autoCloseTimer.value = null
  isPaused.value = true
  
  const elapsed = Date.now() - startTime.value
  remainingTime.value = Math.max(0, props.duration - elapsed)
}

function resumeAutoClose(): void {
  if (isPaused.value && remainingTime.value > 0) {
    isPaused.value = false
    startTime.value = Date.now()
    
    autoCloseTimer.value = window.setTimeout(() => {
      close()
    }, remainingTime.value)
  }
}

function clearAutoClose(): void {
  if (autoCloseTimer.value) {
    clearTimeout(autoCloseTimer.value)
    autoCloseTimer.value = null
  }
}

function close(): void {
  clearAutoClose()
  emit('close')
  props.onClose?.()
}

function handleClick(event: MouseEvent): void {
  // Don't close if clicking on the close button
  if ((event.target as Element)?.closest('.toast-close')) return
  
  if (props.clickToClose) {
    close()
  }
}

function handleKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape' || event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    close()
  }
}

function onEnter(el: Element): void {
  // Animation enter callback
  (el as HTMLElement).style.opacity = '0'
  requestAnimationFrame(() => {
    (el as HTMLElement).style.opacity = '1'
  })
}

function onLeave(el: Element): void {
  // Animation leave callback
  (el as HTMLElement).style.opacity = '0'
}

// Mouse events for pause/resume
function handleMouseEnter(): void {
  pauseAutoClose()
}

function handleMouseLeave(): void {
  resumeAutoClose()
}

// Expose methods
defineExpose({
  close,
  pauseAutoClose,
  resumeAutoClose
})
</script>

<style scoped lang="scss">
.system-toast {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
  min-width: 300px;
  max-width: 480px;
  background: var(--color-bg-1);
  border: 1px solid var(--color-neutral-3);
  border-radius: 12px;
  box-shadow: 
    0 8px 24px rgba(0, 0, 0, 0.12),
    0 4px 8px rgba(0, 0, 0, 0.08);
  backdrop-filter: blur(12px);
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  cursor: default;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;

  &:focus {
    outline: 2px solid var(--color-primary-6);
    outline-offset: 2px;
  }

  &.toast-clickable {
    cursor: pointer;

    &:hover {
      transform: translateY(-2px);
      box-shadow: 
        0 12px 32px rgba(0, 0, 0, 0.16),
        0 6px 12px rgba(0, 0, 0, 0.12);
    }
  }

  &.toast-paused {
    .progress-bar {
      animation-play-state: paused;
    }
  }

  // Type-specific styles
  &.toast-success {
    border-left: 4px solid var(--color-success-6);
    
    .toast-icon {
      color: var(--color-success-6);
      background: var(--color-success-light-9);
    }
  }

  &.toast-error {
    border-left: 4px solid var(--color-danger-6);
    
    .toast-icon {
      color: var(--color-danger-6);
      background: var(--color-danger-light-9);
    }
  }

  &.toast-warning {
    border-left: 4px solid var(--color-warning-6);
    
    .toast-icon {
      color: var(--color-warning-6);
      background: var(--color-warning-light-9);
    }
  }

  &.toast-info {
    border-left: 4px solid var(--color-primary-6);
    
    .toast-icon {
      color: var(--color-primary-6);
      background: var(--color-primary-light-9);
    }
  }
}

.toast-icon {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 2px;

  .arco-icon {
    font-size: 16px;
  }
}

.toast-content {
  flex: 1;
  min-width: 0;
}

.toast-title {
  margin: 0 0 4px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-1);
  line-height: 1.4;
}

.toast-message {
  margin: 0;
  font-size: 13px;
  color: var(--color-text-2);
  line-height: 1.5;
  word-wrap: break-word;
}

.toast-close {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  padding: 0;
  color: var(--color-text-3);
  
  &:hover {
    color: var(--color-text-1);
    background: var(--color-neutral-2);
  }

  .arco-icon {
    font-size: 12px;
  }
}

.toast-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--color-neutral-2);
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, var(--color-primary-6), var(--color-primary-5));
  animation: toast-progress linear forwards;
  transform-origin: left;
}

// Toast container for multiple toasts
.toast-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: calc(100vh - 40px);
  overflow: hidden;
}

// Transitions
.toast-enter-active,
.toast-leave-active {
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(100%) scale(0.9);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(100%) scale(0.9);
}

// Animations
@keyframes toast-progress {
  from {
    transform: scaleX(1);
  }
  to {
    transform: scaleX(0);
  }
}

// Mobile responsiveness
@media (max-width: 768px) {
  .system-toast {
    top: 10px;
    right: 10px;
    left: 10px;
    min-width: auto;
    max-width: none;
  }

  .toast-container {
    top: 10px;
    right: 10px;
    left: 10px;
    max-height: calc(100vh - 20px);
  }
}

@media (max-width: 480px) {
  .system-toast {
    padding: 12px;
    gap: 8px;
  }

  .toast-icon {
    width: 28px;
    height: 28px;

    .arco-icon {
      font-size: 14px;
    }
  }

  .toast-title {
    font-size: 13px;
  }

  .toast-message {
    font-size: 12px;
  }
}

// High contrast mode
@media (prefers-contrast: high) {
  .system-toast {
    border-width: 2px;
    box-shadow: 
      0 8px 24px rgba(0, 0, 0, 0.5),
      0 4px 8px rgba(0, 0, 0, 0.3);
  }
}

// Reduced motion
@media (prefers-reduced-motion: reduce) {
  .system-toast {
    transition: opacity 0.3s ease;

    &.toast-clickable:hover {
      transform: none;
      box-shadow: 
        0 8px 24px rgba(0, 0, 0, 0.12),
        0 4px 8px rgba(0, 0, 0, 0.08);
    }
  }

  .toast-enter-active,
  .toast-leave-active {
    transition: opacity 0.3s ease;
  }

  .toast-enter-from,
  .toast-leave-to {
    opacity: 0;
    transform: none;
  }

  .progress-bar {
    animation: none;
    background: var(--color-primary-6);
  }
}

// Dark theme support
@media (prefers-color-scheme: dark) {
  .system-toast {
    background: var(--color-bg-3);
    backdrop-filter: blur(16px);
  }
}

// Print styles
@media print {
  .system-toast {
    display: none;
  }
}
</style>