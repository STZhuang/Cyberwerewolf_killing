<template>
  <div class="auth-page">
    <div class="auth-container">
      <div class="auth-card">
        <div class="auth-header">
          <h1 class="auth-title">注册</h1>
          <p class="auth-subtitle">加入 Cyber Werewolves 社区</p>
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

          <AFormItem label="显示名称" field="display_name" required>
            <AInput
              v-model="form.display_name"
              placeholder="请输入显示名称"
              size="large"
              allow-clear
            >
              <template #prefix>
                <AIcon icon="icon-user" />
              </template>
            </AInput>
          </AFormItem>

          <AFormItem label="邮箱" field="email" required>
            <AInput
              v-model="form.email"
              placeholder="请输入邮箱地址"
              size="large"
              allow-clear
            >
              <template #prefix>
                <AIcon icon="icon-email" />
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

          <AFormItem label="确认密码" field="confirmPassword" required>
            <AInputPassword
              v-model="form.confirmPassword"
              placeholder="请再次输入密码"
              size="large"
              allow-clear
            >
              <template #prefix>
                <AIcon icon="icon-lock" />
              </template>
            </AInputPassword>
          </AFormItem>

          <!-- Terms and conditions -->
          <AFormItem field="agreedToTerms" required>
            <ACheckbox v-model="form.agreedToTerms">
              我同意<AButton type="text" size="small">服务条款</AButton>和
              <AButton type="text" size="small">隐私政策</AButton>
            </ACheckbox>
          </AFormItem>

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
              注册
            </AButton>
          </AFormItem>
        </AForm>

        <div class="auth-footer">
          <p>已有账户？
            <AButton type="text" @click="router.push('/auth/login')">
              立即登录
            </AButton>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Form as AForm,
  FormItem as AFormItem,
  Input as AInput,
  InputPassword as AInputPassword,
  Button as AButton,
  Icon as AIcon,
  Checkbox as ACheckbox,
  Alert as AAlert,
  Message
} from '@arco-design/web-vue'
import type { FieldRule } from '@arco-design/web-vue/es/form/interface'
import { useAuthStore } from '@/stores'

const router = useRouter()
const authStore = useAuthStore()

const formRef = ref()
const form = ref({
  username: '',
  display_name: '',
  email: '',
  password: '',
  confirmPassword: '',
  agreedToTerms: false
})

// Email validation regex
const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

// Form validation rules
const rules: Record<string, FieldRule | FieldRule[]> = {
  username: [
    { required: true, message: '请输入用户名' },
    { minLength: 3, message: '用户名至少3个字符' },
    { maxLength: 20, message: '用户名最多20个字符' },
    {
      validator: (value: string, callback: (error?: string) => void) => {
        if (!/^[a-zA-Z0-9_]+$/.test(value)) {
          callback('用户名只能包含字母、数字和下划线')
        } else {
          callback()
        }
      }
    }
  ],
  display_name: [
    { required: true, message: '请输入显示名称' },
    { minLength: 2, message: '显示名称至少2个字符' },
    { maxLength: 30, message: '显示名称最多30个字符' }
  ],
  email: [
    { required: true, message: '请输入邮箱地址' },
    {
      validator: (value: string, callback: (error?: string) => void) => {
        if (!emailRegex.test(value)) {
          callback('请输入有效的邮箱地址')
        } else {
          callback()
        }
      }
    }
  ],
  password: [
    { required: true, message: '请输入密码' },
    { minLength: 6, message: '密码至少6个字符' },
    {
      validator: (value: string, callback: (error?: string) => void) => {
        if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(value)) {
          callback('密码必须包含大小写字母和数字')
        } else {
          callback()
        }
      }
    }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码' },
    {
      validator: (value: string, callback: (error?: string) => void) => {
        if (value !== form.value.password) {
          callback('两次输入的密码不一致')
        } else {
          callback()
        }
      }
    }
  ],
  agreedToTerms: [
    {
      validator: (value: boolean, callback: (error?: string) => void) => {
        if (!value) {
          callback('请同意服务条款和隐私政策')
        } else {
          callback()
        }
      }
    }
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
    const success = await authStore.register({
      username: form.value.username,
      display_name: form.value.display_name,
      email: form.value.email,
      password: form.value.password
    })
    
    if (success) {
      Message.success('注册成功，正在登录...')
      router.push('/rooms')
    }
  } catch (error) {
    console.error('Registration error:', error)
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
  max-width: 450px;
}

.auth-card {
  background: var(--color-bg-1);
  border: 1px solid var(--color-neutral-3);
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
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

// Responsive design
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
}

// Dark theme
@media (prefers-color-scheme: dark) {
  .auth-page {
    background: linear-gradient(135deg, var(--color-neutral-9) 0%, var(--color-neutral-8) 100%);
  }
}

// High contrast mode
@media (prefers-contrast: high) {
  .auth-card {
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

:deep(.arco-checkbox:focus-visible) {
  outline: 2px solid var(--color-primary-6);
  outline-offset: 2px;
}
</style>