<template>
  <div :class="bannerClasses" role="banner" :aria-label="ariaLabel">
    <div class="phase-content">
      <!-- Phase icon -->
      <div class="phase-icon">
        <component :is="phaseIcon" />
      </div>

      <!-- Phase info -->
      <div class="phase-info">
        <h2 class="phase-title">{{ title }}</h2>
        <p v-if="description" class="phase-description">{{ description }}</p>
      </div>

      <!-- Timer -->
      <div class="phase-timer" v-if="timeRemaining > 0">
        <div class="timer-circle">
          <svg class="timer-svg" viewBox="0 0 42 42">
            <circle
              class="timer-track"
              cx="21"
              cy="21"
              r="15.5"
              fill="none"
              stroke-width="3"
            />
            <circle
              class="timer-progress"
              cx="21"
              cy="21"
              r="15.5"
              fill="none"
              stroke-width="3"
              :stroke-dasharray="circumference"
              :stroke-dashoffset="dashOffset"
            />
          </svg>
          <div class="timer-text">
            <span class="timer-minutes">{{ minutes }}</span>
            <span class="timer-separator">:</span>
            <span class="timer-seconds">{{ seconds }}</span>
          </div>
        </div>
        <div class="timer-label">剩余时间</div>
      </div>
    </div>

    <!-- Progress bar -->
    <div class="phase-progress">
      <div
        class="progress-fill"
        :style="{ width: `${progressPercentage}%` }"
      ></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { IconMoon, IconSun, IconThumbUp, IconTrophy } from '@arco-design/web-vue/es/icon'
import type { PhaseBannerProps, Phase } from '@/types'

const props = defineProps<PhaseBannerProps>()

// Constants
const phaseDurations: Record<Phase, number> = {
  Night: 120, // 2 minutes
  DayTalk: 300, // 5 minutes
  Vote: 180, // 3 minutes
  Trial: 120, // 2 minutes
  Result: 60, // 1 minute
}

const phaseIcons: Record<Phase, any> = {
  Night: IconMoon,
  DayTalk: IconSun,
  Vote: IconThumbUp,
  Trial: IconThumbUp, // Using thumb up for trial as well since gavel doesn't exist
  Result: IconTrophy
}

const phaseColors: Record<Phase, string> = {
  Night: '#1f2937', // Dark blue-gray
  DayTalk: '#f59e0b', // Amber
  Vote: '#3b82f6', // Blue
  Trial: '#ef4444', // Red
  Result: '#10b981' // Green
}

// Computed properties
const bannerClasses = computed(() => [
  'phase-banner',
  `phase-${props.phase.toLowerCase()}`,
  {
    'phase-urgent': props.timeRemaining <= 30 && props.timeRemaining > 0,
    'phase-critical': props.timeRemaining <= 10 && props.timeRemaining > 0
  }
])

const phaseIcon = computed(() => phaseIcons[props.phase])

const minutes = computed(() => {
  return Math.floor(props.timeRemaining / 60).toString().padStart(2, '0')
})

const seconds = computed(() => {
  return (props.timeRemaining % 60).toString().padStart(2, '0')
})

const progressPercentage = computed(() => {
  const totalDuration = phaseDurations[props.phase]
  if (!totalDuration) return 100
  
  const elapsed = totalDuration - props.timeRemaining
  return Math.min(100, Math.max(0, (elapsed / totalDuration) * 100))
})

const circumference = computed(() => 2 * Math.PI * 15.5)

const dashOffset = computed(() => {
  if (props.timeRemaining <= 0) return circumference.value
  
  const totalDuration = phaseDurations[props.phase]
  const progress = props.timeRemaining / totalDuration
  return circumference.value * (1 - progress)
})

const ariaLabel = computed(() => {
  const timeText = props.timeRemaining > 0 
    ? `，剩余 ${minutes.value} 分 ${seconds.value} 秒`
    : ''
  return `当前阶段：${props.title}${timeText}`
})

// Get dynamic CSS variables
const phaseColor = computed(() => phaseColors[props.phase])
</script>

<style scoped lang="scss">
.phase-banner {
  --phase-color: v-bind(phaseColor);
  
  position: relative;
  background: linear-gradient(135deg, var(--phase-color), color-mix(in srgb, var(--phase-color) 80%, white));
  color: white;
  padding: 20px 24px;
  border-radius: 12px;
  box-shadow: 
    0 4px 12px rgba(0, 0, 0, 0.15),
    0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  margin-bottom: 16px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
  
  &.phase-urgent {
    animation: pulse-urgent 2s infinite;
  }
  
  &.phase-critical {
    animation: pulse-critical 1s infinite;
    box-shadow: 
      0 4px 12px rgba(0, 0, 0, 0.15),
      0 0 0 1px rgba(255, 255, 255, 0.1) inset,
      0 0 20px rgba(239, 68, 68, 0.5);
  }
}

.phase-content {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 12px;
}

.phase-icon {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
  
  .arco-icon {
    font-size: 24px;
    color: rgba(255, 255, 255, 0.9);
  }
}

.phase-info {
  flex: 1;
  min-width: 0;
}

.phase-title {
  margin: 0 0 4px 0;
  font-size: 24px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  line-height: 1.2;
}

.phase-description {
  margin: 0;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
  line-height: 1.4;
}

.phase-timer {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.timer-circle {
  position: relative;
  width: 64px;
  height: 64px;
}

.timer-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.timer-track {
  stroke: rgba(255, 255, 255, 0.3);
}

.timer-progress {
  stroke: rgba(255, 255, 255, 0.9);
  stroke-linecap: round;
  transition: stroke-dashoffset 0.5s ease;
}

.timer-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  align-items: baseline;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
}

.timer-minutes,
.timer-seconds {
  font-size: 14px;
  font-feature-settings: 'tnum';
}

.timer-separator {
  font-size: 12px;
  margin: 0 1px;
  opacity: 0.8;
}

.timer-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.7);
  text-align: center;
  font-weight: 500;
}

.phase-progress {
  height: 4px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 2px;
  overflow: hidden;
  backdrop-filter: blur(10px);
}

.progress-fill {
  height: 100%;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 2px;
  transition: width 1s ease-out;
  box-shadow: 0 0 8px rgba(255, 255, 255, 0.5);
}

// Phase-specific styles
.phase-night {
  .phase-icon {
    background: rgba(139, 92, 246, 0.3);
  }
  
  .timer-progress {
    stroke: #c4b5fd;
  }
  
  .progress-fill {
    background: linear-gradient(90deg, #c4b5fd, #8b5cf6);
  }
}

.phase-daytalk {
  .phase-icon {
    background: rgba(245, 158, 11, 0.3);
  }
  
  .timer-progress {
    stroke: #fbbf24;
  }
  
  .progress-fill {
    background: linear-gradient(90deg, #fbbf24, #f59e0b);
  }
}

.phase-vote {
  .phase-icon {
    background: rgba(59, 130, 246, 0.3);
  }
  
  .timer-progress {
    stroke: #60a5fa;
  }
  
  .progress-fill {
    background: linear-gradient(90deg, #60a5fa, #3b82f6);
  }
}

.phase-trial {
  .phase-icon {
    background: rgba(239, 68, 68, 0.3);
  }
  
  .timer-progress {
    stroke: #f87171;
  }
  
  .progress-fill {
    background: linear-gradient(90deg, #f87171, #ef4444);
  }
}

.phase-result {
  .phase-icon {
    background: rgba(16, 185, 129, 0.3);
  }
  
  .timer-progress {
    stroke: #34d399;
  }
  
  .progress-fill {
    background: linear-gradient(90deg, #34d399, #10b981);
  }
}

// Animations
@keyframes pulse-urgent {
  0%, 100% {
    transform: scale(1);
    box-shadow: 
      0 4px 12px rgba(0, 0, 0, 0.15),
      0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  }
  50% {
    transform: scale(1.02);
    box-shadow: 
      0 6px 16px rgba(0, 0, 0, 0.2),
      0 0 0 1px rgba(255, 255, 255, 0.1) inset,
      0 0 15px rgba(245, 158, 11, 0.3);
  }
}

@keyframes pulse-critical {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.03);
  }
}

// Responsive design
@media (max-width: 768px) {
  .phase-banner {
    padding: 16px 20px;
  }
  
  .phase-content {
    gap: 12px;
  }
  
  .phase-icon {
    width: 40px;
    height: 40px;
    
    .arco-icon {
      font-size: 20px;
    }
  }
  
  .phase-title {
    font-size: 20px;
  }
  
  .phase-description {
    font-size: 13px;
  }
  
  .timer-circle {
    width: 56px;
    height: 56px;
  }
  
  .timer-minutes,
  .timer-seconds {
    font-size: 12px;
  }
}

@media (max-width: 480px) {
  .phase-content {
    flex-direction: column;
    text-align: center;
    gap: 8px;
  }
  
  .timer-circle {
    width: 48px;
    height: 48px;
  }
  
  .timer-minutes,
  .timer-seconds {
    font-size: 11px;
  }
}

// High contrast mode
@media (prefers-contrast: high) {
  .phase-banner {
    border: 2px solid white;
  }
  
  .timer-track {
    stroke: rgba(255, 255, 255, 0.5);
  }
  
  .timer-progress {
    stroke: white;
  }
  
  .progress-fill {
    background: white;
  }
}

// Reduced motion
@media (prefers-reduced-motion: reduce) {
  .phase-banner {
    animation: none;
  }
  
  .timer-progress {
    transition: none;
  }
  
  .progress-fill {
    transition: none;
  }
}
</style>