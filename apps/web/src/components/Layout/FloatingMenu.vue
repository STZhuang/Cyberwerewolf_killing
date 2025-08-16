<template>
  <div class="floating-menu">
    <!-- 主菜单按钮 -->
    <a-button
      type="primary"
      shape="circle"
      size="large"
      class="menu-trigger"
      @click="toggleMenu"
    >
      <template #icon>
        <Icon 
          :icon="isOpen ? 'ant-design:close-outlined' : 'ant-design:menu-outlined'" 
          class="menu-icon"
        />
      </template>
    </a-button>

    <!-- 菜单项 -->
    <Transition name="menu-items">
      <div v-show="isOpen" class="menu-items">
        <a-tooltip content="设置" placement="left">
          <a-button
            shape="circle"
            class="menu-item"
            @click="goToSettings"
          >
            <template #icon>
              <Icon icon="ant-design:setting-outlined" />
            </template>
          </a-button>
        </a-tooltip>

        <a-tooltip content="房间列表" placement="left">
          <a-button
            shape="circle"
            class="menu-item"
            @click="goToRooms"
          >
            <template #icon>
              <Icon icon="ant-design:home-outlined" />
            </template>
          </a-button>
        </a-tooltip>

        <a-tooltip content="个人中心" placement="left">
          <a-button
            shape="circle"
            class="menu-item"
            @click="goToProfile"
          >
            <template #icon>
              <Icon icon="ant-design:user-outlined" />
            </template>
          </a-button>
        </a-tooltip>

        <a-tooltip content="帮助" placement="left">
          <a-button
            shape="circle"
            class="menu-item"
            @click="showHelp"
          >
            <template #icon>
              <Icon icon="ant-design:question-circle-outlined" />
            </template>
          </a-button>
        </a-tooltip>

        <a-tooltip v-if="authStore.isLoggedIn" content="退出登录" placement="left">
          <a-button
            shape="circle"
            class="menu-item logout"
            @click="logout"
          >
            <template #icon>
              <Icon icon="ant-design:logout-outlined" />
            </template>
          </a-button>
        </a-tooltip>
      </div>
    </Transition>

    <!-- 遮罩层 -->
    <div
      v-show="isOpen"
      class="menu-overlay"
      @click="toggleMenu"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { Icon } from '@iconify/vue'
import { useAuthStore } from '@/stores'

const router = useRouter()
const authStore = useAuthStore()

const isOpen = ref(false)

const toggleMenu = () => {
  isOpen.value = !isOpen.value
}

const goToSettings = () => {
  router.push('/settings')
  toggleMenu()
}

const goToRooms = () => {
  router.push('/rooms')
  toggleMenu()
}

const goToProfile = () => {
  router.push('/profile')
  toggleMenu()
}

const showHelp = () => {
  // 这里可以打开帮助对话框或跳转到帮助页面
  Message.info('帮助功能开发中...')
  toggleMenu()
}

const logout = async () => {
  try {
    await authStore.logout()
    Message.success('已退出登录')
    router.push('/')
  } catch (error: any) {
    Message.error('退出登录失败: ' + error.message)
  }
  toggleMenu()
}

// 点击外部区域关闭菜单
document.addEventListener('click', (e) => {
  const target = e.target as Element
  if (!target.closest('.floating-menu')) {
    isOpen.value = false
  }
})
</script>

<style scoped>
.floating-menu {
  position: fixed;
  bottom: 30px;
  right: 30px;
  z-index: 1000;
}

.menu-trigger {
  width: 56px;
  height: 56px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.menu-trigger:hover {
  transform: scale(1.05);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.4);
}

.menu-icon {
  font-size: 20px;
  transition: transform 0.3s ease;
}

.menu-items {
  position: absolute;
  bottom: 70px;
  right: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 48px;
}

.menu-item {
  width: 48px;
  height: 48px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 0, 0, 0.1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.menu-item:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
  background: rgba(255, 255, 255, 1);
}

.menu-item.logout {
  color: #f56565;
  border-color: rgba(245, 101, 101, 0.3);
}

.menu-item.logout:hover {
  background: rgba(245, 101, 101, 0.1);
  border-color: #f56565;
}

.menu-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: transparent;
  z-index: -1;
}

/* 动画效果 */
.menu-items-enter-active,
.menu-items-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.menu-items-enter-from,
.menu-items-leave-to {
  opacity: 0;
  transform: translateX(20px) scale(0.8);
}

.menu-items-enter-to,
.menu-items-leave-from {
  opacity: 1;
  transform: translateX(0) scale(1);
}

/* 移动端适配 */
@media (max-width: 768px) {
  .floating-menu {
    bottom: 20px;
    right: 20px;
  }
  
  .menu-trigger {
    width: 50px;
    height: 50px;
  }
  
  .menu-items {
    bottom: 60px;
  }
  
  .menu-item {
    width: 44px;
    height: 44px;
  }
}

/* 深色主题适配 */
[data-theme='dark'] .menu-item {
  background: rgba(31, 41, 55, 0.95);
  border-color: rgba(255, 255, 255, 0.1);
  color: #f3f4f6;
}

[data-theme='dark'] .menu-item:hover {
  background: rgba(31, 41, 55, 1);
  border-color: rgba(255, 255, 255, 0.2);
}
</style>