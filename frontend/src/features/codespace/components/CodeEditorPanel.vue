<template>
  <div class="editor-panel">
    <div v-if="refreshNotification" class="editor-panel__notification">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 2a10 10 0 1 0 10 10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        <path d="m9 12 2 2 4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      {{ refreshNotification }}
    </div>

    <div class="editor-panel__header">
      <h3 class="editor-panel__title">Code Editor</h3>
      <div class="editor-panel__actions">
        <button
          class="editor-panel__icon-btn"
          @click="$emit('save')"
          :disabled="isSaving"
          aria-label="Save"
          title="Save changes (Ctrl+S)"
        >
          <svg v-if="isSaving" width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" opacity="0.3"/>
            <path d="M12 2a10 10 0 0110 10" stroke="currentColor" stroke-width="2" stroke-linecap="round">
              <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite"/>
            </path>
          </svg>
          <img v-else :src="saveIcon" alt="Save" class="editor-panel__icon" />
        </button>

        <button
          class="editor-panel__icon-btn"
          @click="$emit('undo')"
          aria-label="Undo"
          title="Undo (Ctrl+Z)"
        >
          <img :src="undoIcon" alt="Undo" class="editor-panel__icon" />
        </button>

        <button
          class="editor-panel__icon-btn"
          @click="$emit('redo')"
          aria-label="Redo"
          title="Redo (Ctrl+Y)"
        >
          <img :src="redoIcon" alt="Redo" class="editor-panel__icon" />
        </button>

        <button
          class="editor-panel__icon-btn"
          @click="$emit('run')"
          :disabled="isRunning"
          aria-label="Run runner.py"
          title="Run runner.py"
        >
          <svg v-if="isRunning" width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" opacity="0.3"/>
            <path d="M12 2a10 10 0 0110 10" stroke="currentColor" stroke-width="2" stroke-linecap="round">
              <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite"/>
            </path>
          </svg>
          <img v-else :src="runCodeIcon" alt="Run" class="editor-panel__icon" />
        </button>
      </div>
    </div>

    <div class="editor-panel__wrapper">
      <div class="editor-panel__content">
        <div class="editor-panel__file-info">
          <span v-if="isRefreshing" class="editor-panel__refresh-indicator" title="Refreshing file content...">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2a10 10 0 0110 10" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite"/>
              </path>
            </svg>
          </span>
          <span class="editor-panel__current-file">{{ currentFile }}</span>
        </div>
        <MonacoEditor
          ref="editorRef"
          :key="editorKey"
          :code="code"
          @update:code="$emit('change', $event)"
          language="python"
        />
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import MonacoEditor from '@/shared/components/MonacoEditor.vue'
import saveIcon from '@/assets/R-save.svg'
import undoIcon from '@/assets/R-undo.svg'
import redoIcon from '@/assets/R-redo.svg'
import runCodeIcon from '@/assets/R-runcode.svg'

export default {
  name: 'CodeEditorPanel',
  components: {
    MonacoEditor
  },
  props: {
    code: {
      type: String,
      default: ''
    },
    currentFile: {
      type: String,
      default: 'runner.py'
    },
    editorKey: {
      type: String,
      default: ''
    },
    isSaving: {
      type: Boolean,
      default: false
    },
    isRunning: {
      type: Boolean,
      default: false
    },
    isRefreshing: {
      type: Boolean,
      default: false
    },
    refreshNotification: {
      type: String,
      default: null
    }
  },
  emits: ['save', 'undo', 'redo', 'run', 'change'],
  setup() {
    const editorRef = ref(null)

    const undo = () => {
      editorRef.value?.undo()
    }

    const redo = () => {
      editorRef.value?.redo()
    }

    const getPosition = () => {
      return editorRef.value?.getPosition()
    }

    const insertText = (text, position) => {
      editorRef.value?.insertText(text, position)
    }

    return {
      editorRef,
      saveIcon,
      undoIcon,
      redoIcon,
      runCodeIcon,
      undo,
      redo,
      getPosition,
      insertText
    }
  }
}
</script>

<style scoped>
.editor-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  border: 1px solid #e8e8e8;
  min-height: 0;
}

.editor-panel__notification {
  background: var(--color-navy);
  color: white;
  padding: 12px 16px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-family: 'Jaldi', sans-serif;
  animation: fadeIn 0.3s ease;
}

.editor-panel__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  border-bottom: 1px solid #e8e8e8;
  background: #fafafa;
  flex-shrink: 0;
}

.editor-panel__title {
  font-size: 14px;
  font-weight: 600;
  color: #1a1a1a;
  font-family: 'Jaldi', sans-serif;
  margin: 0;
}

.editor-panel__actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.editor-panel__icon-btn {
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  background: transparent;
  color: #666;
  padding: 0;
}

.editor-panel__icon-btn:hover:not(:disabled) {
  background: rgba(0, 0, 0, 0.08);
}

.editor-panel__icon-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.editor-panel__icon {
  width: 16px;
  height: 16px;
  object-fit: contain;
}

.editor-panel__wrapper {
  flex: 1;
  overflow: hidden;
  min-height: 0;
  max-height: 100%;
  display: flex;
}

.editor-panel__content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
  max-height: 100%;
}

.editor-panel__file-info {
  padding: 8px 16px;
  background: #f9f9f9;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-family: 'Courier New', monospace;
  color: #666;
  flex-shrink: 0;
}

.editor-panel__current-file {
  font-weight: 500;
  color: #1a1a1a;
}

.editor-panel__refresh-indicator {
  animation: spin 1s linear infinite;
}

.editor-panel__content :deep(.monaco-editor-container) {
  flex: 1;
  min-height: 0;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
