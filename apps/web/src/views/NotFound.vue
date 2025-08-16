<template>
  <div class="not-found">
    <div class="not-found-content">
      <div class="error-visual">
        <div class="error-code">404</div>
        <IconFaceFrownFill class="error-icon" />
      </div>
      
      <h1 class="error-title">页面未找到</h1>
      <p class="error-description">
        抱歉，您访问的页面不存在或已被移动。
      </p>
      
      <div class="error-actions">
        <Button type="primary" @click="goHome">
          <IconHome />
          返回首页
        </Button>
        <Button @click="goBack">
          <IconLeft />
          返回上页
        </Button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { Button } from '@arco-design/web-vue'
import { IconFaceFrownFill, IconHome, IconLeft } from '@arco-design/web-vue/es/icon'

const router = useRouter()

function goHome() {
  router.push('/')
}

function goBack() {
  if (window.history.length > 1) {
    router.go(-1)
  } else {
    router.push('/')
  }
}
</script>

<style scoped lang="scss">
.not-found {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: var(--color-bg-1);
}

.not-found-content {
  text-align: center;
  max-width: 500px;
}

.error-visual {
  position: relative;
  margin-bottom: 32px;
}

.error-code {
  font-size: 8rem;
  font-weight: 800;
  color: var(--color-primary-6);
  opacity: 0.3;
  line-height: 1;
  margin-bottom: 16px;
}

.error-icon {
  font-size: 64px;
  color: var(--color-text-3);
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.error-title {
  font-size: 2rem;
  font-weight: 600;
  color: var(--color-text-1);
  margin: 0 0 16px 0;
}

.error-description {
  font-size: 1rem;
  color: var(--color-text-3);
  line-height: 1.6;
  margin: 0 0 32px 0;
}

.error-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
}

@media (max-width: 480px) {
  .error-code {
    font-size: 6rem;
  }

  .error-icon {
    font-size: 48px;
  }

  .error-title {
    font-size: 1.5rem;
  }

  .error-actions {
    flex-direction: column;
    align-items: center;
  }
}
</style>