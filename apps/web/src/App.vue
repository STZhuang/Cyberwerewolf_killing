<template>
  <div id="app">
    <!-- Toast container -->
    <div id="toast-container" class="toast-container">
      <SystemToast
        v-for="toast in gameStore.toasts"
        :key="`toast-${toast.title}-${Date.now()}`"
        v-bind="toast"
        @close="gameStore.removeToast(toast.title)"
      />
    </div>

    <!-- Main router view -->
    <router-view />
    
    <!-- Floating menu (只在登录后显示) -->
    <FloatingMenu v-if="authStore.isLoggedIn" />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import SystemToast from '@/components/Game/SystemToast.vue'
import FloatingMenu from '@/components/Layout/FloatingMenu.vue'
import { useAuthStore, useGameStore } from '@/stores'

const authStore = useAuthStore()
const gameStore = useGameStore()

onMounted(async () => {
  // Initialize auth store
  await authStore.init()
})
</script>

<style lang="scss">
#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: var(--color-text-1);
  background: var(--color-bg-1);
  min-height: 100vh;
}

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
  pointer-events: none;

  > * {
    pointer-events: auto;
  }
}

// Mobile responsiveness
@media (max-width: 768px) {
  .toast-container {
    top: 10px;
    right: 10px;
    left: 10px;
    max-height: calc(100vh - 20px);
  }
}
</style>