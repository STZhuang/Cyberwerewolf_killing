<template>
  <div class="llm-config-panel">
    <a-card title="LLM 模型配置" :bordered="false">
      <a-tabs v-model:active-key="activeRole" type="card-gutter">
        <a-tab-pane v-for="role in roles" :key="role.key" :title="role.name">
          <a-form
            :model="configs[role.key]"
            :rules="formRules"
            layout="vertical"
            class="role-config-form"
            @finish="() => saveConfig(role.key)"
          >
            <a-form-item label="快速模板">
              <a-select
                v-model:value="selectedTemplates[role.key]"
                placeholder="选择预设模板或自定义"
                @change="(val) => applyTemplate(role.key, val)"
                allow-clear
              >
                <a-select-option value="openai-gpt4o">OpenAI GPT-4o</a-select-option>
                <a-select-option value="openai-gpt4">OpenAI GPT-4</a-select-option>
                <a-select-option value="local-ollama">本地 Ollama</a-select-option>
                <a-select-option value="custom">自定义</a-select-option>
              </a-select>
            </a-form-item>

            <a-divider />

            <a-form-item label="模型 ID" name="model_id" tooltip="例如: gpt-4o-mini">
              <a-input v-model:value="configs[role.key].model_id" />
            </a-form-item>

            <a-form-item label="API Key" name="api_key" tooltip="留空则使用全局配置">
              <a-input-password v-model:value="configs[role.key].api_key" />
            </a-form-item>

            <a-form-item label="Base URL" name="base_url" tooltip="API 服务地址">
              <a-input v-model:value="configs[role.key].base_url" />
            </a-form-item>

            <a-collapse :default-active-key="[]">
              <a-collapse-panel key="advanced" header="高级配置">
                <a-form-item label="Temperature" tooltip="控制输出随机性 (0-1)">
                  <a-input-number v-model:value="configs[role.key].temperature" :min="0" :max="1" :step="0.1" />
                </a-form-item>
                <a-form-item label="Max Tokens" tooltip="最大输出长度">
                  <a-input-number v-model:value="configs[role.key].max_tokens" :min="1" />
                </a-form-item>
              </a-collapse-panel>
            </a-collapse>
          </a-form>
        </a-tab-pane>
      </a-tabs>

      <a-divider />

      <a-space>
        <a-button type="primary" @click="saveAllConfigs" :loading="saving">
          <template #icon><Icon icon="ant-design:save-outlined" /></template>
          保存所有配置
        </a-button>
        <a-button @click="testCurrentConnection" :loading="testing">
          <template #icon><Icon icon="ant-design:api-outlined" /></template>
          测试当前连接
        </a-button>
        <a-button @click="resetCurrentConfig" status="warning">
          <template #icon><Icon icon="ant-design:reload-outlined" /></template>
          重置当前配置
        </a-button>
      </a-space>

      <a-alert
        v-if="testResult.show"
        :message="testResult.message"
        :type="testResult.type"
        :description="testResult.description"
        show-icon
        closable
        @close="testResult.show = false"
        style="margin-top: 20px"
      />
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Message } from '@arco-design/web-vue'
import { Icon } from '@iconify/vue'
import { apiService } from '@/services/api'

interface LLMConfig {
  model_id: string
  api_key: string
  base_url: string
  temperature: number
  max_tokens: number
}

interface TestResult {
  show: boolean
  type: 'success' | 'error' | 'warning' | 'info'
  message: string
  description?: string
}

const roles = [
  { key: 'gm', name: 'GM' },
  { key: 'werewolf', name: '狼人' },
  { key: 'villager', name: '村民' },
  { key: 'seer', name: '预言家' },
  { key: 'witch', name: '女巫' },
  { key: 'guard', name: '守卫' },
  { key: 'hunter', name: '猎人' },
  { key: 'idiot', name: '白痴' },
]

const activeRole = ref('gm')

const defaultConfig: LLMConfig = {
  model_id: 'gpt-4o-mini',
  api_key: '',
  base_url: 'https://api.openai.com/v1',
  temperature: 0.7,
  max_tokens: 2048,
}

const configs = reactive<Record<string, LLMConfig>>({})
const selectedTemplates = reactive<Record<string, string>>({})

roles.forEach(role => {
  configs[role.key] = { ...defaultConfig }
  if (role.key === 'gm') {
      configs[role.key].model_id = 'gpt-4o' // GM uses a stronger model by default
  }
  selectedTemplates[role.key] = ''
})

const formRules = {
  model_id: [{ required: true, message: '请输入模型ID' }],
  base_url: [{ required: true, message: '请输入API地址' }, { type: 'url', message: '请输入有效的URL' }],
}

const testing = ref(false)
const saving = ref(false)
const testResult = reactive<TestResult>({
  show: false,
  type: 'info',
  message: '',
})

const templates: Record<string, Partial<LLMConfig>> = {
  'openai-gpt4o': { model_id: 'gpt-4o', base_url: 'https://api.openai.com/v1' },
  'openai-gpt4': { model_id: 'gpt-4-turbo', base_url: 'https://api.openai.com/v1' },
  'local-ollama': { model_id: 'llama3.1:8b', base_url: 'http://localhost:11434/v1', api_key: 'ollama' },
}

const applyTemplate = (roleKey: string, templateKey: string) => {
  if (!templateKey || templateKey === 'custom') return
  const template = templates[templateKey]
  if (template) {
    configs[roleKey] = { ...defaultConfig, ...template }
    Message.success(`已为 ${roles.find(r => r.key === roleKey)?.name} 应用模板`)
  }
}

const testCurrentConnection = async () => {
  testing.value = true
  testResult.show = false
  try {
    const response = await apiService.request('/admin/llm/test-config', {
      method: 'POST',
      body: JSON.stringify(configs[activeRole.value])
    })
    testResult.type = response.success ? 'success' : 'error'
    testResult.message = response.success ? '连接测试成功' : '连接测试失败'
    testResult.description = response.success ? `模型响应正常, 延迟: ${response.data?.latency || 'N/A'}ms` : (response.error || '未知错误')
  } catch (error: any) {
    testResult.type = 'error'
    testResult.message = '连接测试失败'
    testResult.description = error.message
  } finally {
    testResult.show = true
    testing.value = false
  }
}

const resetCurrentConfig = () => {
  configs[activeRole.value] = { ...defaultConfig }
    if (activeRole.value === 'gm') {
      configs[activeRole.value].model_id = 'gpt-4o'
  }
  selectedTemplates[activeRole.value] = ''
  Message.info(`已重置 ${roles.find(r => r.key === activeRole.value)?.name} 的配置`)
}

const saveAllConfigs = async () => {
  saving.value = true
  try {
    const response = await apiService.request('/admin/llm/save-configs', {
      method: 'POST',
      body: JSON.stringify(configs)
    })
    if (response.success) {
      Message.success('所有 LLM 配置已保存')
    } else {
      Message.error(response.error || '保存失败')
    }
  } catch (error: any) {
    Message.error('保存失败: ' + error.message)
  } finally {
    saving.value = false
  }
}

const loadSavedConfigs = async () => {
  try {
    const response = await apiService.request('/admin/llm/get-configs')
    if (response.success && response.data) {
      // Merge saved configs with defaults to ensure all roles are present
      roles.forEach(role => {
        if (response.data[role.key]) {
          configs[role.key] = { ...defaultConfig, ...response.data[role.key] }
        }
      })
    }
  } catch (error) {
    console.warn('加载配置失败，使用默认配置')
  }
}

onMounted(loadSavedConfigs)
</script>

<style scoped>
.llm-config-panel {
  max-width: 800px;
  margin: 0 auto;
}
.role-config-form {
  margin-top: 16px;
}
</style>