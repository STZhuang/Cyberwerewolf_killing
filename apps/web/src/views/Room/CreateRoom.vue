<template>
  <div class="create-room-page">
    <div class="page-container">
      <div class="page-header">
        <h1 class="page-title">创建房间</h1>
        <p class="page-subtitle">设置游戏参数，创建你的专属房间</p>
      </div>

      <div class="create-form">
        <Form
          ref="formRef"
          :model="form"
          :rules="rules"
          layout="vertical"
          @submit="handleSubmit"
        >
          <!-- Basic settings -->
          <div class="form-section">
            <h3 class="section-title">基本设置</h3>
            
            <FormItem label="房间名称" field="name" required>
              <Input
                v-model="form.name"
                placeholder="请输入房间名称"
                allow-clear
                :max-length="30"
                show-word-limit
              />
            </FormItem>

            <FormItem label="最大玩家数" field="max_players" required>
              <InputNumber
                v-model="form.max_players"
                :min="6"
                :max="20"
                :step="1"
                placeholder="6-20人"
              />
              <template #help>
                建议6-12人，支持最多20人同时游戏
              </template>
            </FormItem>
          </div>

          <!-- Role configuration -->
          <div class="form-section">
            <h3 class="section-title">角色配置</h3>
            
            <div class="role-grid">
              <FormItem label="狼人" field="settings.werewolf_count" required>
                <InputNumber
                  v-model="form.settings.werewolf_count"
                  :min="1"
                  :max="5"
                  :step="1"
                />
              </FormItem>

              <FormItem label="村民" field="settings.villager_count" required>
                <InputNumber
                  v-model="form.settings.villager_count"
                  :min="1"
                  :max="10"
                  :step="1"
                />
              </FormItem>

              <FormItem label="预言家" field="settings.seer_count">
                <InputNumber
                  v-model="form.settings.seer_count"
                  :min="0"
                  :max="2"
                  :step="1"
                />
              </FormItem>

              <FormItem label="守卫" field="settings.guard_count">
                <InputNumber
                  v-model="form.settings.guard_count"
                  :min="0"
                  :max="2"
                  :step="1"
                />
              </FormItem>

              <FormItem label="女巫" field="settings.witch_count">
                <InputNumber
                  v-model="form.settings.witch_count"
                  :min="0"
                  :max="1"
                  :step="1"
                />
              </FormItem>

              <FormItem label="猎人" field="settings.hunter_count">
                <InputNumber
                  v-model="form.settings.hunter_count"
                  :min="0"
                  :max="1"
                  :step="1"
                />
              </FormItem>
            </div>

            <div class="role-summary">
              <Alert
                :type="roleValidation.valid ? 'success' : 'warning'"
                :title="roleValidation.message"
                show-icon
              />
            </div>
          </div>

          <!-- Time settings -->
          <div class="form-section">
            <h3 class="section-title">时间设置</h3>
            
            <div class="time-grid">
              <FormItem label="白天讨论时间" field="settings.day_duration">
                <InputNumber
                  v-model="form.settings.day_duration"
                  :min="60"
                  :max="600"
                  :step="30"
                />
                <template #suffix>秒</template>
              </FormItem>

              <FormItem label="夜晚时间" field="settings.night_duration">
                <InputNumber
                  v-model="form.settings.night_duration"
                  :min="30"
                  :max="300"
                  :step="15"
                />
                <template #suffix>秒</template>
              </FormItem>

              <FormItem label="投票时间" field="settings.vote_duration">
                <InputNumber
                  v-model="form.settings.vote_duration"
                  :min="30"
                  :max="300"
                  :step="15"
                />
                <template #suffix>秒</template>
              </FormItem>
            </div>
          </div>

          <!-- AI settings -->
          <div class="form-section">
            <h3 class="section-title">AI设置</h3>
            
            <FormItem label="启用AI智能体" field="settings.enable_agent">
              <Switch v-model="form.settings.enable_agent" />
              <template #help>
                AI智能体将自动填补空缺位置，提供更好的游戏体验
              </template>
            </FormItem>

            <FormItem 
              v-if="form.settings.enable_agent" 
              label="AI难度" 
              field="settings.agent_difficulty"
            >
              <RadioGroup v-model="form.settings.agent_difficulty">
                <Radio value="easy">简单</Radio>
                <Radio value="medium">中等</Radio>
                <Radio value="hard">困难</Radio>
              </RadioGroup>
            </FormItem>
          </div>

          <!-- Submit buttons -->
          <div class="form-actions">
            <Button @click="router.push('/rooms')">取消</Button>
            <Button 
              type="primary" 
              html-type="submit"
              :loading="isCreating"
              :disabled="!roleValidation.valid"
            >
              创建房间
            </Button>
          </div>
        </Form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  Form,
  FormItem,
  Input,
  InputNumber,
  Button,
  Switch,
  RadioGroup,
  Radio,
  Alert,
  Message
} from '@arco-design/web-vue'
import type { FieldRule } from '@arco-design/web-vue/es/form/interface'
import { apiService } from '@/services/api'
import type { CreateRoomRequest } from '@/types'

const router = useRouter()
const formRef = ref()
const isCreating = ref(false)

const form = ref({
  name: '',
  max_players: 8,
  settings: {
    werewolf_count: 2,
    villager_count: 3,
    seer_count: 1,
    guard_count: 1,
    witch_count: 1,
    hunter_count: 0,
    day_duration: 300,
    night_duration: 120,
    vote_duration: 180,
    enable_agent: true,
    agent_difficulty: 'medium' as 'easy' | 'medium' | 'hard'
  }
})

const rules: Record<string, FieldRule | FieldRule[]> = {
  name: [
    { required: true, message: '请输入房间名称' },
    { minLength: 2, message: '房间名称至少2个字符' },
    { maxLength: 30, message: '房间名称最多30个字符' }
  ],
  max_players: [
    { required: true, message: '请设置最大玩家数' },
    { type: 'number', min: 6, message: '最少需要6名玩家' },
    { type: 'number', max: 20, message: '最多支持20名玩家' }
  ],
  'settings.werewolf_count': [
    { required: true, message: '请设置狼人数量' },
    { type: 'number', min: 1, message: '至少需要1个狼人' }
  ],
  'settings.villager_count': [
    { required: true, message: '请设置村民数量' },
    { type: 'number', min: 1, message: '至少需要1个村民' }
  ]
}

const roleValidation = computed(() => {
  const settings = form.value.settings
  const totalRoles = settings.werewolf_count + settings.villager_count +
                    settings.seer_count + settings.guard_count +
                    settings.witch_count + settings.hunter_count

  if (totalRoles === form.value.max_players) {
    return {
      valid: true,
      message: `角色配置完整：共${totalRoles}个角色`
    }
  } else if (totalRoles < form.value.max_players) {
    const missing = form.value.max_players - totalRoles
    return {
      valid: true,
      message: `还需要${missing}个角色，${form.value.settings.enable_agent ? 'AI将自动填补' : '请调整角色数量'}`
    }
  } else {
    const excess = totalRoles - form.value.max_players
    return {
      valid: false,
      message: `角色数量超出${excess}个，请减少角色数量或增加最大玩家数`
    }
  }
})

async function handleSubmit(data: { values: typeof form.value; errors: any }) {
  if (data.errors || !roleValidation.value.valid) return

  isCreating.value = true

  try {
    const requestData: CreateRoomRequest = {
      name: form.value.name,
      max_players: form.value.max_players,
      settings: form.value.settings
    }

    const response = await apiService.createRoom(requestData)
    
    if (response.success && response.data) {
      Message.success('房间创建成功')
      router.push(`/room/${response.data.id}`)
    } else {
      Message.error(response.error || '创建房间失败')
    }
  } catch (error) {
    console.error('Failed to create room:', error)
    Message.error('创建房间失败')
  } finally {
    isCreating.value = false
  }
}
</script>

<style scoped lang="scss">
.create-room-page {
  min-height: 100vh;
  background: var(--color-bg-1);
  padding: 20px;
}

.page-container {
  max-width: 800px;
  margin: 0 auto;
}

.page-header {
  text-align: center;
  margin-bottom: 40px;

  .page-title {
    font-size: 2rem;
    font-weight: 700;
    margin: 0 0 8px 0;
    color: var(--color-text-1);
  }

  .page-subtitle {
    font-size: 1rem;
    color: var(--color-text-3);
    margin: 0;
  }
}

.create-form {
  background: var(--color-bg-2);
  border: 1px solid var(--color-neutral-3);
  border-radius: 16px;
  padding: 32px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.form-section {
  margin-bottom: 32px;

  &:last-child {
    margin-bottom: 0;
  }

  .section-title {
    font-size: 1.2rem;
    font-weight: 600;
    margin: 0 0 20px 0;
    color: var(--color-text-1);
    padding-bottom: 8px;
    border-bottom: 2px solid var(--color-primary-6);
  }
}

.role-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.role-summary {
  margin-top: 16px;
}

.time-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.form-actions {
  display: flex;
  gap: 16px;
  justify-content: flex-end;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid var(--color-neutral-3);
}

@media (max-width: 768px) {
  .create-room-page {
    padding: 16px;
  }

  .create-form {
    padding: 24px 20px;
  }

  .role-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }

  .time-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .form-actions {
    flex-direction: column-reverse;

    .arco-btn {
      width: 100%;
    }
  }
}

@media (max-width: 480px) {
  .page-header .page-title {
    font-size: 1.5rem;
  }

  .role-grid {
    grid-template-columns: 1fr;
  }

  .form-section .section-title {
    font-size: 1.1rem;
  }
}
</style>