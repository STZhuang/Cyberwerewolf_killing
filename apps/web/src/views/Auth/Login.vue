<template>
  <div class="auth-page">
    <div class="auth-container">
      <div class="auth-card">
        <div class="auth-header">
          <h1 class="auth-title">登录</h1>
          <p class="auth-subtitle">欢迎回到 Cyber Werewolves</p>
        </div>

        <AForm
          ref="formRef"
          :model="form"
          :rules="rules"
          layout="vertical"
          @submit="handleSubmit"
          :disabled="authStore.isLoading"
        >
          <AFormItem label="用户名" field="username" required>
            <AInput
              v-model="form.username"
              placeholder="请输入用户名"
              size="large"
              allow-clear
            >
              <template #prefix>
                <AIcon icon="icon-user" />
              </template>
            </AInput>
          </AFormItem>

          <AFormItem label="密码" field="password" required>
            <AInputPassword
              v-model="form.password"
              placeholder="请输入密码"
              size="large"
              allow-clear
            >
              <template #prefix>
                <AIcon icon="icon-lock" />
              </template>
            </AInputPassword>
          </AFormItem>

          <div class="auth-options">
            <ACheckbox v-model="rememberMe">记住我</ACheckbox>
            <AButton type="text" size="small">忘记密码？</AButton>
          </div>

          <!-- Error display -->
          <AAlert
            v-if="authStore.error"
            type="error"
            :title="authStore.error"
            show-icon
            closable
            @close="authStore.clearError"
            class="auth-error"
          />

          <AFormItem>
            <AButton
              type="primary"
              html-type="submit"
              size="large"
              long
              :loading="authStore.isLoading"
            >
              登录
            </AButton>
          </AFormItem>
        </AForm>

        <div class="auth-footer">
          <p>还没有账户？
            <AButton type="text" @click="router.push('/auth/register')">
              立即注册
            </AButton>
          </p>
        </div>
      </div>

      <!-- Quick login (demo) -->
      <div class="quick-login">
        <h3>快速体验</h3>
        <p class="quick-login-desc">使用演示账户快速体验游戏</p>
        <div class="demo-accounts">
          <AButton
            v-for="account in demoAccounts"
            :key="account.username"
            type="outline"
            @click="quickLogin(account)"
            :loading="isQuickLogging && quickLoginAccount === account.username"
            class="demo-account-btn"
          >
            {{ account.displayName }}
          </AButton>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  AForm,
  AFormItem,
  AInput,
  AInputPassword,
  AButton,
  AIcon,
  ACheckbox,
  AAlert,
  Message
} from '@arco-design/web-vue'
import type { FieldRule } from '@arco-design/web-vue/es/form/interface'
import { useAuthStore } from '@/stores'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const formRef = ref()
const form = ref({
  username: '',
  password: ''
})

const rememberMe = ref(false)
const isQuickLogging = ref(false)
const quickLoginAccount = ref<string | null>(null)

// Demo accounts for quick testing
const demoAccounts = [
  {
    username: 'player1',
    password: 'demo123',
    displayName: '玩家1'
  },
  {
    username: 'player2',
    password: 'demo123',
    displayName: '玩家2'
  }
]

// Form validation rules
const rules: Record<string, FieldRule | FieldRule[]> = {
  username: [
    { required: true, message: '请输入用户名' },
    { minLength: 3, message: '用户名至少3个字符' },
    { maxLength: 20, message: '用户名最多20个字符' }
  ],
  password: [
    { required: true, message: '请输入密码' },
    { minLength: 6, message: '密码至少6个字符' }
  ]
}

onMounted(() => {
  // Clear any previous auth errors
  authStore.clearError()

  // Auto-focus username field
  const usernameInput = document.querySelector('input[placeholder="请输入用户名"]') as HTMLInputElement
  if (usernameInput) {
    usernameInput.focus()
  }
})

async function handleSubmit(data: { values: typeof form.value; errors: any }) {
  if (data.errors) return

  try {
    const success = await authStore.login(form.value)
    
    if (success) {
      Message.success('登录成功')
      
      // Redirect to intended page or home
      const redirect = route.query.redirect as string
      router.push(redirect || '/rooms')
    }
  } catch (error) {
    console.error('Login error:', error)
  }
}

async function quickLogin(account: typeof demoAccounts[0]) {
  isQuickLogging.value = true
  quickLoginAccount.value = account.username

  try {
    const success = await authStore.login({
      username: account.username,
      password: account.password
    })

    if (success) {
      Message.success(`已登录为 ${account.displayName}`)
      router.push('/rooms')
    }
  } catch (error) {
    console.error('Quick login error:', error)
  } finally {
    isQuickLogging.value = false
    quickLoginAccount.value = null
  }
}

// Handle Enter key on form
function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !authStore.isLoading) {
    formRef.value?.submit()
  }
}
</script>

<style scoped lang="scss">
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: linear-gradient(135deg, var(--color-primary-1) 0%, var(--color-bg-1) 100%);
}

.auth-container {
  width: 100%;
  max-width: 900px;
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 40px;
  align-items: start;
}

.auth-card {
  background: var(--color-bg-1);
  border: 1px solid var(--color-neutral-3);
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  width: 100%;
  max-width: 400px;
}

.auth-header {
  text-align: center;
  margin-bottom: 32px;

  .auth-title {
    font-size: 2rem;
    font-weight: 700;
    margin: 0 0 8px 0;
    color: var(--color-text-1);
  }

  .auth-subtitle {
    font-size: 1rem;
    color: var(--color-text-3);
    margin: 0;
  }
}

.auth-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.auth-error {
  margin-bottom: 16px;
}

.auth-footer {
  text-align: center;
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--color-neutral-3);

  p {
    margin: 0;
    color: var(--color-text-3);
    font-size: 0.9rem;
  }
}

.quick-login {
  background: var(--color-bg-2);
  border: 1px solid var(--color-neutral-3);
  border-radius: 12px;
  padding: 24px;
  width: 280px;

  h3 {
    margin: 0 0 8px 0;
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--color-text-1);
  }

  .quick-login-desc {
    margin: 0 0 20px 0;
    font-size: 0.85rem;
    color: var(--color-text-3);
    line-height: 1.4;
  }

  .demo-accounts {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .demo-account-btn {
    justify-content: flex-start;
    font-size: 0.9rem;
  }
}

// Responsive design
@media (max-width: 768px) {
  .auth-container {
    grid-template-columns: 1fr;
    max-width: 400px;
  }

  .auth-card {
    padding: 30px 24px;
  }

  .quick-login {
    width: 100%;
    order: -1;
  }
}

@media (max-width: 480px) {
  .auth-page {
    padding: 16px;
  }

  .auth-card {
    padding: 24px 20px;
    border-radius: 12px;
  }

  .auth-header {
    margin-bottom: 24px;

    .auth-title {
      font-size: 1.5rem;
    }
  }

  .quick-login {
    padding: 20px;
  }
}

// Dark theme
@media (prefers-color-scheme: dark) {
  .auth-page {
    background: linear-gradient(135deg, var(--color-neutral-9) 0%, var(--color-neutral-8) 100%);
  }
}

// High contrast mode
@media (prefers-contrast: high) {
  .auth-card,
  .quick-login {
    border-width: 2px;
  }
}

// Focus styles for better accessibility
:deep(.arco-input-wrapper:focus-within) {
  border-color: var(--color-primary-6);
  box-shadow: 0 0 0 2px var(--color-primary-light-3);
}

:deep(.arco-btn:focus-visible) {
  outline: 2px solid var(--color-primary-6);
  outline-offset: 2px;
}
</style>