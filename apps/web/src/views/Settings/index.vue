<template>
  <div class="settings-page">
    <div class="settings-container">
      <a-row :gutter="24">
        <a-col :span="6">
          <!-- 设置导航 -->
          <a-card title="设置分类" :bordered="false">
            <a-menu
              v-model:selectedKeys="selectedMenu"
              mode="vertical"
              @menu-item-click="switchMenu"
            >
              <a-menu-item key="llm">
                <template #icon>
                  <Icon icon="ant-design:robot-outlined" />
                </template>
                LLM 模型配置
              </a-menu-item>
              <a-menu-item key="game">
                <template #icon>
                  <Icon icon="ant-design:setting-outlined" />
                </template>
                游戏设置
              </a-menu-item>
              <a-menu-item key="system">
                <template #icon>
                  <Icon icon="ant-design:tool-outlined" />
                </template>
                系统设置
              </a-menu-item>
            </a-menu>
          </a-card>
        </a-col>
        
        <a-col :span="18">
          <!-- 设置内容区域 -->
          <div class="settings-content">
            <!-- LLM 配置 -->
            <LLMConfigPanel v-if="activeMenu === 'llm'" />
            
            <!-- 游戏设置 -->
            <a-card v-else-if="activeMenu === 'game'" title="游戏设置" :bordered="false">
              <a-form layout="vertical">
                <a-form-item label="默认游戏时间">
                  <a-input-number
                    :min="30"
                    :max="600"
                    addon-after="秒"
                    style="width: 200px"
                  />
                </a-form-item>
                
                <a-form-item label="允许观战">
                  <a-switch />
                </a-form-item>
                
                <a-form-item label="自动开始游戏">
                  <a-switch />
                </a-form-item>
              </a-form>
            </a-card>
            
            <!-- 系统设置 -->
            <a-card v-else-if="activeMenu === 'system'" title="系统设置" :bordered="false">
              <a-form layout="vertical">
                <a-form-item label="日志级别">
                  <a-select style="width: 200px">
                    <a-select-option value="DEBUG">DEBUG</a-select-option>
                    <a-select-option value="INFO">INFO</a-select-option>
                    <a-select-option value="WARNING">WARNING</a-select-option>
                    <a-select-option value="ERROR">ERROR</a-select-option>
                  </a-select>
                </a-form-item>
                
                <a-form-item label="数据库备份">
                  <a-space>
                    <a-button type="primary">立即备份</a-button>
                    <a-button>恢复备份</a-button>
                  </a-space>
                </a-form-item>
              </a-form>
            </a-card>
          </div>
        </a-col>
      </a-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Icon } from '@iconify/vue'
import LLMConfigPanel from '@/components/Settings/LLMConfigPanel.vue'

// 当前选中的菜单
const selectedMenu = ref(['llm'])
const activeMenu = ref('llm')

// 切换菜单
const switchMenu = (key: string) => {
  activeMenu.value = key
}
</script>

<style scoped>
.settings-page {
  padding: 24px;
  min-height: calc(100vh - 64px);
  background: #f0f2f5;
}

.settings-container {
  max-width: 1200px;
  margin: 0 auto;
}

.settings-content {
  min-height: 500px;
}

:deep(.arco-card) {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

:deep(.arco-menu-vertical) {
  border-right: none;
}

:deep(.arco-menu-item) {
  margin-bottom: 4px;
  border-radius: 6px;
}
</style>