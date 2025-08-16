<template>
  <div class="profile-page">
    <div class="profile-container">
      <div class="profile-header">
        <h1 class="page-title">个人中心</h1>
        <AButton type="text" danger @click="handleLogout">
          <AIcon icon="icon-export" />
          退出登录
        </AButton>
      </div>

      <div class="profile-content">
        <div class="profile-card">
          <div class="user-avatar">
            <span class="avatar-text">{{ userInitials }}</span>
          </div>
          
          <div class="user-info">
            <h2 class="user-name">{{ authStore.user?.display_name }}</h2>
            <p class="user-username">@{{ authStore.user?.username }}</p>
            <p class="user-email">{{ authStore.user?.email }}</p>
          </div>
        </div>

        <div class="stats-section">
          <h3 class="section-title">游戏统计</h3>
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-value">0</div>
              <div class="stat-label">游戏场次</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">0</div>
              <div class="stat-label">胜利次数</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">0%</div>
              <div class="stat-label">胜率</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">0</div>
              <div class="stat-label">在线时长</div>
            </div>
          </div>
        </div>

        <div class="actions-section">
          <h3 class="section-title">快速操作</h3>
          <div class="action-buttons">
            <AButton type="primary" @click="router.push('/rooms')">
              <AIcon icon="icon-apps" />
              房间列表
            </AButton>
            <AButton @click="router.push('/rooms/create')">
              <AIcon icon="icon-plus" />
              创建房间
            </AButton>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { AButton, AIcon, Modal, Message } from '@arco-design/web-vue'
import { useAuthStore } from '@/stores'

const router = useRouter()
const authStore = useAuthStore()

const userInitials = computed(() => {
  const name = authStore.user?.display_name || authStore.user?.username || ''
  return name
    .split(' ')
    .map(word => word.charAt(0))
    .join('')
    .substring(0, 2)
    .toUpperCase()
})

function handleLogout() {
  Modal.confirm({
    title: '确认退出登录？',
    content: '退出后需要重新登录才能继续使用',
    onOk: async () => {
      try {
        await authStore.logout()
        Message.success('已成功退出登录')
        router.push('/')
      } catch (error) {
        console.error('Logout error:', error)
        Message.error('退出登录失败')
      }
    }
  })
}
</script>

<style scoped lang="scss">
.profile-page {
  min-height: 100vh;
  background: var(--color-bg-1);
  padding: 20px;
}

.profile-container {
  max-width: 800px;
  margin: 0 auto;
}

.profile-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--color-neutral-3);

  .page-title {
    font-size: 2rem;
    font-weight: 700;
    margin: 0;
    color: var(--color-text-1);
  }
}

.profile-content {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.profile-card {
  background: var(--color-bg-2);
  border: 1px solid var(--color-neutral-3);
  border-radius: 16px;
  padding: 32px;
  display: flex;
  align-items: center;
  gap: 24px;
}

.user-avatar {
  width: 80px;
  height: 80px;
  background: var(--color-primary-6);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 28px;
  font-weight: 700;
  flex-shrink: 0;
}

.user-info {
  flex: 1;

  .user-name {
    font-size: 1.5rem;
    font-weight: 600;
    margin: 0 0 8px 0;
    color: var(--color-text-1);
  }

  .user-username {
    font-size: 1rem;
    color: var(--color-text-3);
    margin: 0 0 4px 0;
  }

  .user-email {
    font-size: 0.9rem;
    color: var(--color-text-2);
    margin: 0;
  }
}

.stats-section, .actions-section {
  background: var(--color-bg-2);
  border: 1px solid var(--color-neutral-3);
  border-radius: 16px;
  padding: 24px;

  .section-title {
    font-size: 1.2rem;
    font-weight: 600;
    margin: 0 0 20px 0;
    color: var(--color-text-1);
  }
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
}

.stat-card {
  text-align: center;
  padding: 20px;
  background: var(--color-neutral-1);
  border-radius: 12px;

  .stat-value {
    font-size: 2rem;
    font-weight: 700;
    color: var(--color-primary-6);
    margin-bottom: 8px;
  }

  .stat-label {
    font-size: 0.9rem;
    color: var(--color-text-3);
  }
}

.action-buttons {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

@media (max-width: 768px) {
  .profile-page {
    padding: 16px;
  }

  .profile-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }

  .profile-card {
    flex-direction: column;
    text-align: center;
    padding: 24px;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .action-buttons {
    flex-direction: column;

    .arco-btn {
      width: 100%;
    }
  }
}

@media (max-width: 480px) {
  .profile-header .page-title {
    font-size: 1.5rem;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .user-avatar {
    width: 64px;
    height: 64px;
    font-size: 24px;
  }

  .user-info .user-name {
    font-size: 1.3rem;
  }
}
</style>