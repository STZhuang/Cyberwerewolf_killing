<template>
  <div class="llm-config-panel">
    <a-card title="LLM 模型配置" :bordered="false">
      <a-form
        :model="configForm"
        :rules="formRules"
        layout="vertical"
        @finish="saveConfig"
      >
        <!-- 配置模板选择 -->
        <a-form-item label="快速模板">
          <a-select
            v-model:value="selectedTemplate"
            placeholder="选择预设模板或自定义"
            @change="applyTemplate"
            allow-clear
          >
            <a-select-option value="openai-gpt4">OpenAI GPT-4</a-select-option>
            <a-select-option value="openai-gpt35">OpenAI GPT-3.5</a-select-option>
            <a-select-option value="local-ollama">本地 Ollama</a-select-option>
            <a-select-option value="custom">自定义配置</a-select-option>
          </a-select>
        </a-form-item>

        <a-divider />

        <!-- 模型ID配置 -->
        <a-form-item
          label="模型 ID"
          name="model_id"
          tooltip="指定要使用的具体模型，如 gpt-4, gpt-3.5-turbo 等"
        >
          <a-input
            v-model:value="configForm.model_id"
            placeholder="例如: gpt-4o-mini"
          />
        </a-form-item>

        <!-- API Key配置 -->
        <a-form-item
          label="API Key"
          name="api_key"
          tooltip="模型服务的API密钥，留空则使用环境变量"
        >
          <a-input-password
            v-model:value="configForm.api_key"
            placeholder="例如: sk-xxxx 或留空使用环境变量"
            autocomplete="off"
          />
        </a-form-item>

        <!-- Base URL配置 -->
        <a-form-item
          label="Base URL"
          name="base_url"
          tooltip="API服务地址，用于兼容OpenAI格式的自定义服务"
        >
          <a-input
            v-model:value="configForm.base_url"
            placeholder="例如: http://localhost:11434/v1"
          />
        </a-form-item>

        <!-- 高级配置 -->
        <a-collapse>
          <a-collapse-panel key="advanced" header="高级配置">
            <a-form-item label="Temperature" tooltip="控制输出随机性，0-1之间">
              <a-input-number
                v-model:value="configForm.temperature"
                :min="0"
                :max="1"
                :step="0.1"
                style="width: 100%"
              />
            </a-form-item>

            <a-form-item label="Max Tokens" tooltip="最大输出长度">
              <a-input-number
                v-model:value="configForm.max_tokens"
                :min="1"
                :max="8192"
                style="width: 100%"
              />
            </a-form-item>

            <a-form-item label="超时时间 (秒)">
              <a-input-number
                v-model:value="configForm.timeout"
                :min="5"
                :max="120"
                style="width: 100%"
              />
            </a-form-item>
          </a-collapse-panel>
        </a-collapse>

        <!-- 测试连接 -->
        <a-form-item>
          <a-space>
            <a-button
              type="primary"
              @click="testConnection"
              :loading="testing"
            >
              <template #icon>
                <Icon icon="ant-design:api-outlined" />
              </template>
              测试连接
            </a-button>
            
            <a-button type="default" @click="resetForm">
              <template #icon>
                <Icon icon="ant-design:reload-outlined" />
              </template>
              重置
            </a-button>
          </a-space>
        </a-form-item>

        <!-- 测试结果 -->
        <a-alert
          v-if="testResult.show"
          :message="testResult.message"
          :type="testResult.type"
          :description="testResult.description"
          show-icon
          closable
          @close="testResult.show = false"
          style="margin-bottom: 16px"
        />

        <!-- 保存配置 -->
        <a-form-item>
          <a-button type="primary" html-type="submit" block>
            <template #icon>
              <Icon icon="ant-design:save-outlined" />
            </template>
            保存配置
          </a-button>
        </a-form-item>
      </a-form>
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
  timeout: number
}

interface TestResult {
  show: boolean
  type: 'success' | 'error' | 'warning' | 'info'
  message: string
  description?: string
}

// 表单数据
const configForm = reactive<LLMConfig>({
  model_id: 'gpt-4o-mini',
  api_key: '',
  base_url: 'https://api.openai.com/v1',
  temperature: 0.7,
  max_tokens: 2048,
  timeout: 30
})

// 表单验证规则
const formRules = {
  model_id: [
    { required: true, message: '请输入模型ID' },
    { min: 1, max: 100, message: '模型ID长度应在1-100之间' }
  ],
  base_url: [
    { required: true, message: '请输入API地址' },
    { type: 'url', message: '请输入有效的URL地址' }
  ]
}

// 状态管理
const selectedTemplate = ref<string>('')
const testing = ref(false)
const testResult = reactive<TestResult>({
  show: false,
  type: 'info',
  message: '',
  description: ''
})

// 预设模板
const templates: Record<string, Partial<LLMConfig>> = {
  'openai-gpt4': {
    model_id: 'gpt-4o',
    base_url: 'https://api.openai.com/v1',
    temperature: 0.7,
    max_tokens: 4096
  },
  'openai-gpt35': {
    model_id: 'gpt-3.5-turbo',
    base_url: 'https://api.openai.com/v1',
    temperature: 0.8,
    max_tokens: 2048
  },
  'local-ollama': {
    model_id: 'llama3.1:8b',
    base_url: 'http://localhost:11434/v1',
    api_key: 'ollama',
    temperature: 0.7,
    max_tokens: 2048
  }
}

// 应用模板配置
const applyTemplate = (templateKey: string) => {
  if (!templateKey || templateKey === 'custom') return
  
  const template = templates[templateKey]
  if (template) {
    Object.assign(configForm, template)
    Message.success(`已应用 ${templateKey} 模板配置`)
  }
}

// 测试连接
const testConnection = async () => {
  testing.value = true
  testResult.show = false

  try {
    const response = await apiService.request('/admin/llm/test-config', {
      method: 'POST',
      body: JSON.stringify(configForm)
    })

    if (response.success) {
      testResult.type = 'success'
      testResult.message = '连接测试成功'
      testResult.description = `模型响应正常，延迟: ${response.data?.latency || 'N/A'}ms`
    } else {
      testResult.type = 'error'
      testResult.message = '连接测试失败'
      testResult.description = response.error || '未知错误'
    }
  } catch (error: any) {
    testResult.type = 'error'
    testResult.message = '连接测试失败'
    testResult.description = error.message || '网络错误'
  } finally {
    testResult.show = true
    testing.value = false
  }
}

// 重置表单
const resetForm = () => {
  Object.assign(configForm, {
    model_id: 'gpt-4o-mini',
    api_key: '',
    base_url: 'https://api.openai.com/v1',
    temperature: 0.7,
    max_tokens: 2048,
    timeout: 30
  })
  selectedTemplate.value = ''
  Message.info('已重置为默认配置')
}

// 保存配置
const saveConfig = async () => {
  try {
    const response = await apiService.request('/admin/llm/save-config', {
      method: 'POST',
      body: JSON.stringify(configForm)
    })

    if (response.success) {
      Message.success('LLM配置已保存')
    } else {
      Message.error(response.error || '保存失败')
    }
  } catch (error: any) {
    Message.error('保存失败：' + error.message)
  }
}

// 加载已保存的配置
const loadSavedConfig = async () => {
  try {
    const response = await apiService.request('/admin/llm/get-config')
    
    if (response.success && response.data) {
      Object.assign(configForm, response.data)
    }
  } catch (error) {
    console.warn('加载配置失败，使用默认配置')
  }
}

// 组件挂载时加载配置
onMounted(() => {
  loadSavedConfig()
})
</script>

<style scoped>
.llm-config-panel {
  max-width: 600px;
  margin: 0 auto;
}

.llm-config-panel :deep(.arco-card-body) {
  padding: 24px;
}

.llm-config-panel :deep(.arco-form-item-label-col) {
  font-weight: 500;
}

.llm-config-panel :deep(.arco-collapse) {
  margin-bottom: 16px;
}
</style>