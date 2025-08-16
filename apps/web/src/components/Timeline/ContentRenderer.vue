<template>
  <div class="content-renderer">
    <!-- Text content -->
    <div v-if="textContent" class="text-content" v-html="renderedText"></div>

    <!-- Content blocks -->
    <div v-if="content.blocks && content.blocks.length > 0" class="content-blocks">
      <div
        v-for="(block, index) in content.blocks"
        :key="`block-${index}`"
        :class="['content-block', `block-${block.type}`]"
      >
        <!-- Markdown block -->
        <div v-if="block.type === 'markdown'" class="markdown-block" v-html="renderMarkdown(block.content || '')"></div>

        <!-- Table block -->
        <div v-else-if="block.type === 'table'" class="table-block">
          <ATable
            :columns="tableColumns(block)"
            :data="tableData(block)"
            :pagination="false"
            size="mini"
            class="content-table"
          />
        </div>

        <!-- Image block -->
        <div v-else-if="block.type === 'image'" class="image-block">
          <img
            :src="block.src"
            :alt="block.alt || 'Image'"
            class="content-image"
            loading="lazy"
          />
        </div>

        <!-- Code block -->
        <div v-else-if="block.type === 'code'" class="code-block">
          <div class="code-header">
            <span class="code-language">{{ block.language || 'text' }}</span>
            <AButton
              size="mini"
              type="text"
              @click="copyCode(block.code || '')"
              class="copy-button"
            >
              <AIcon icon="icon-copy" />
            </AButton>
          </div>
          <pre class="code-content"><code :class="`language-${block.language || 'text'}`" v-html="highlightCode(block.code || '', block.language)"></code></pre>
        </div>

        <!-- Vote summary block -->
        <div v-else-if="block.type === 'vote_summary'" class="vote-summary-block">
          <h4 class="vote-title">投票结果</h4>
          <div class="vote-list">
            <div
              v-for="(vote, voteIndex) in block.votes"
              :key="`vote-${voteIndex}`"
              class="vote-item"
            >
              <span class="voter">#{{ vote.from }}</span>
              <AIcon icon="icon-arrow-right" class="vote-arrow" />
              <span class="target">
                {{ vote.to === null ? '弃票' : `#${vote.to}` }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Citations -->
    <div v-if="content.citations && content.citations.length > 0" class="citations">
      <h5 class="citations-title">引用来源</h5>
      <div class="citations-list">
        <ATag
          v-for="citation in content.citations"
          :key="citation.source_id"
          size="mini"
          class="citation-tag"
        >
          {{ citation.label }}
        </ATag>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ATable, AButton, AIcon, ATag, Message } from '@arco-design/web-vue'
import { marked } from 'marked'
import hljs from 'highlight.js'
import type { MessageContent, ContentBlock, StreamingText } from '@/types'

interface Props {
  content: MessageContent
}

const props = defineProps<Props>()

// Computed properties
const textContent = computed(() => {
  if (typeof props.content.text === 'string') {
    return props.content.text
  } else if (props.content.text && 'chunks' in props.content.text) {
    return (props.content.text as StreamingText).chunks.join('')
  }
  return ''
})

const renderedText = computed(() => {
  if (!textContent.value) return ''
  
  // Simple text processing (convert URLs to links, etc.)
  return textContent.value
    .replace(/\n/g, '<br>')
    .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>')
})

// Helper functions
function renderMarkdown(markdown: string): string {
  try {
    return marked(markdown, {
      breaks: true,
      sanitize: false // Be careful with this in production
    })
  } catch (error) {
    console.error('Markdown render error:', error)
    return markdown
  }
}

function highlightCode(code: string, language?: string): string {
  if (!language || !hljs.getLanguage(language)) {
    return hljs.highlightAuto(code).value
  }
  
  try {
    return hljs.highlight(code, { language }).value
  } catch (error) {
    console.error('Code highlight error:', error)
    return code
  }
}

function tableColumns(block: ContentBlock) {
  if (!block.headers) return []
  
  return block.headers.map((header, index) => ({
    title: header,
    dataIndex: `col_${index}`,
    key: `col_${index}`
  }))
}

function tableData(block: ContentBlock) {
  if (!block.rows) return []
  
  return block.rows.map((row, rowIndex) => {
    const rowData: Record<string, string> = { key: `row_${rowIndex}` }
    row.forEach((cell, colIndex) => {
      rowData[`col_${colIndex}`] = cell
    })
    return rowData
  })
}

async function copyCode(code: string): Promise<void> {
  try {
    await navigator.clipboard.writeText(code)
    Message.success('代码已复制到剪贴板')
  } catch (error) {
    console.error('Failed to copy code:', error)
    Message.error('复制失败')
  }
}
</script>

<style scoped lang="scss">
.content-renderer {
  .text-content {
    margin-bottom: 8px;
    word-wrap: break-word;

    :deep(a) {
      color: var(--color-primary-6);
      text-decoration: none;

      &:hover {
        text-decoration: underline;
      }
    }
  }

  .content-blocks {
    .content-block {
      margin-bottom: 12px;

      &:last-child {
        margin-bottom: 0;
      }
    }
  }
}

.markdown-block {
  :deep(h1), :deep(h2), :deep(h3), :deep(h4), :deep(h5), :deep(h6) {
    margin: 8px 0 4px 0;
    color: var(--color-text-1);
  }

  :deep(p) {
    margin: 4px 0;
    line-height: 1.6;
  }

  :deep(ul), :deep(ol) {
    margin: 4px 0;
    padding-left: 20px;
  }

  :deep(blockquote) {
    margin: 8px 0;
    padding: 8px 12px;
    border-left: 3px solid var(--color-neutral-4);
    background: var(--color-neutral-1);
    color: var(--color-text-2);
  }

  :deep(code) {
    padding: 2px 4px;
    background: var(--color-neutral-2);
    border-radius: 3px;
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
    font-size: 0.9em;
  }
}

.table-block {
  margin: 8px 0;
  
  .content-table {
    font-size: 12px;
    
    :deep(.arco-table-cell) {
      padding: 6px 8px;
    }
  }
}

.image-block {
  margin: 8px 0;
  text-align: center;
  
  .content-image {
    max-width: 100%;
    height: auto;
    border-radius: 6px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }
}

.code-block {
  margin: 8px 0;
  border: 1px solid var(--color-neutral-3);
  border-radius: 6px;
  overflow: hidden;
  
  .code-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 12px;
    background: var(--color-neutral-2);
    border-bottom: 1px solid var(--color-neutral-3);
  }
  
  .code-language {
    font-size: 12px;
    color: var(--color-text-3);
    font-weight: 500;
  }
  
  .copy-button {
    padding: 4px;
    height: auto;
    
    .arco-icon {
      font-size: 14px;
    }
  }
  
  .code-content {
    margin: 0;
    padding: 12px;
    background: var(--color-bg-2);
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
    font-size: 13px;
    line-height: 1.4;
    overflow-x: auto;
    
    code {
      background: none;
      padding: 0;
      color: var(--color-text-1);
    }
  }
}

.vote-summary-block {
  margin: 8px 0;
  padding: 12px;
  background: var(--color-neutral-1);
  border-radius: 6px;
  border: 1px solid var(--color-neutral-3);
  
  .vote-title {
    margin: 0 0 8px 0;
    font-size: 14px;
    font-weight: 600;
    color: var(--color-text-1);
  }
  
  .vote-list {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  
  .vote-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    
    .voter {
      font-weight: 500;
      color: var(--color-text-1);
      min-width: 32px;
    }
    
    .vote-arrow {
      color: var(--color-text-3);
      font-size: 12px;
    }
    
    .target {
      color: var(--color-text-2);
    }
  }
}

.citations {
  margin-top: 12px;
  padding-top: 8px;
  border-top: 1px solid var(--color-neutral-3);
  
  .citations-title {
    margin: 0 0 6px 0;
    font-size: 12px;
    font-weight: 500;
    color: var(--color-text-3);
  }
  
  .citations-list {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }
  
  .citation-tag {
    font-size: 10px;
    background: var(--color-neutral-2);
    border: 1px solid var(--color-neutral-4);
  }
}

// Dark theme support
@media (prefers-color-scheme: dark) {
  .code-block .code-content {
    background: #1e1e1e;
  }
}

// High contrast theme
@media (prefers-contrast: high) {
  .code-block, .vote-summary-block {
    border-width: 2px;
  }
  
  .content-image {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  }
}
</style>