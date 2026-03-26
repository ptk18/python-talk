<template>
  <div class="output-panel">
    <div class="output-panel__tabs">
      <button
        class="output-panel__tab"
        :class="{ 'active': activeTab === 'history' }"
        @click="$emit('set-tab', 'history')"
      >
        <img :src="textModeIcon" alt="" class="output-panel__tab-icon" />
        <span>Text</span>
      </button>
      <button
        class="output-panel__tab"
        :class="{ 'active': activeTab === 'terminal' }"
        @click="$emit('set-tab', 'terminal')"
      >
        <svg class="output-panel__tab-icon-svg" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M13 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18z" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          <path d="M13 7v5l3 3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M3 12h2M5.5 5.5l1.5 1.5M5.5 18.5l1.5-1.5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <span>Terminal</span>
      </button>
      <button
        class="output-panel__tab"
        :class="{ 'active': activeTab === 'graphic' }"
        @click="$emit('set-tab', 'graphic')"
      >
        <img :src="graphicModeIcon" alt="" class="output-panel__tab-icon" />
        <span>Graphic</span>
      </button>
    </div>
    <div class="output-panel__body">
      <div class="output-panel__content">
        <!-- Terminal Tab (Command History — IDLE style) -->
        <div v-if="activeTab === 'history'" ref="historyRef" class="output-panel__history">
          <div v-if="commandHistory.length === 0" class="output-panel__history-empty">
            {{ historyPlaceholder }}
          </div>
          <div v-else class="output-panel__history-list">
            <div
              v-for="entry in orderedHistory"
              :key="entry.id"
              class="output-panel__history-entry"
            >
              <div class="output-panel__history-line">
                <span :class="['output-panel__history-prompt', `output-panel__history-prompt--${entry.status}`]">&gt;&gt;&gt;</span>
                <span class="output-panel__history-text">{{ entry.text }}</span>
                <span class="output-panel__history-time">{{ formatTime(entry.timestamp) }}</span>
              </div>
              <div v-if="entry.translatedText" class="output-panel__history-line">
                <span class="output-panel__history-prompt output-panel__history-prompt--sub">...</span>
                <span class="output-panel__history-translated">{{ entry.translatedText }}</span>
              </div>
              <div v-if="entry.executables && entry.executables.length" v-for="(exec, i) in entry.executables" :key="i" class="output-panel__history-line">
                <span :class="['output-panel__history-prompt', `output-panel__history-prompt--${entry.status}`]">&gt;&gt;&gt;</span>
                <code class="output-panel__history-exec">{{ exec }}</code>
              </div>
              <div v-if="entry.error && entry.status !== 'success'" class="output-panel__history-line">
                <span class="output-panel__history-prompt output-panel__history-prompt--error">&gt;&gt;&gt;</span>
                <span class="output-panel__history-error">{{ entry.error }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Text Tab -->
        <div v-else-if="activeTab === 'terminal'" class="output-panel__terminal">
          <div class="output-panel__gutter">
            <span class="output-panel__gutter-prompt">&gt;&gt;&gt;</span>
          </div>
          <pre class="output-panel__terminal-text">{{ output || terminalPlaceholder }}</pre>
        </div>

        <!-- Graphic Tab -->
        <div v-else-if="activeTab === 'graphic'" class="output-panel__graphic">
          <div class="output-panel__graphic-label">{{ graphicLabel }}</div>
          <img
            v-if="streamFrame"
            :src="streamFrame"
            class="output-panel__graphic-img"
            alt="Turtle graphics stream"
          />
          <div v-else class="output-panel__graphic-placeholder">
            {{ graphicPlaceholder }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { computed, ref, watch, nextTick } from 'vue'
import textModeIcon from '@/assets/R-textmode.svg'
import graphicModeIcon from '@/assets/R-graphicmode.svg'

export default {
  name: 'EnhancedOutputPanel',
  props: {
    output: {
      type: String,
      default: ''
    },
    streamFrame: {
      type: String,
      default: null
    },
    commandHistory: {
      type: Array,
      default: () => []
    },
    activeTab: {
      type: String,
      default: 'history'
    },
    terminalPlaceholder: {
      type: String,
      default: 'Output will appear here...'
    },
    graphicPlaceholder: {
      type: String,
      default: 'Waiting for turtle stream...'
    },
    historyPlaceholder: {
      type: String,
      default: 'No commands yet...'
    },
    graphicLabel: {
      type: String,
      default: 'Turtle Graphics Stream'
    }
  },
  emits: ['set-tab'],
  setup(props) {
    const historyRef = ref(null)

    const orderedHistory = computed(() => {
      return [...props.commandHistory]
    })

    const formatTime = (timestamp) => {
      if (!timestamp) return ''
      const d = new Date(timestamp)
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    }

    watch(() => props.commandHistory.length, () => {
      nextTick(() => {
        if (historyRef.value) {
          historyRef.value.scrollTop = historyRef.value.scrollHeight
        }
      })
    })

    return {
      textModeIcon,
      graphicModeIcon,
      orderedHistory,
      historyRef,
      formatTime
    }
  }
}
</script>

<style scoped>
.output-panel {
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

.output-panel__tabs {
  display: flex;
  background: #fafafa;
  border-bottom: 1px solid #e8e8e8;
  flex-shrink: 0;
}

.output-panel__tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px 16px;
  border: none;
  background: transparent;
  color: #999;
  font-family: 'Jaldi', sans-serif;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: color 0.2s ease;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
}

.output-panel__tab:hover {
  color: #555;
}

.output-panel__tab.active {
  color: #1a1a1a;
  font-weight: 600;
  border-bottom-color: #2196f3;
}

.output-panel__tab-icon {
  width: 14px;
  height: 14px;
  object-fit: contain;
  filter: brightness(0) invert(0.6);
}

.output-panel__tab.active .output-panel__tab-icon {
  filter: brightness(0);
}

.output-panel__tab-icon-svg {
  width: 14px;
  height: 14px;
  color: inherit;
}

.output-panel__body {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.output-panel__content {
  flex: 1;
  overflow-y: auto;
  background: #1e1e1e;
  color: #d4d4d4;
  font-family: 'Consolas', 'Menlo', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.6;
  min-height: 0;
}

/* Terminal tab — IDLE style with left gutter */
.output-panel__terminal {
  display: flex;
  min-height: 100%;
}

.output-panel__gutter {
  width: 48px;
  flex-shrink: 0;
  border-right: 2px solid #444;
  padding: 12px 4px 12px 8px;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  background: #1a1a1a;
}

.output-panel__gutter-prompt {
  color: #4caf50;
  font-weight: 700;
  font-size: 14px;
  font-family: 'Consolas', 'Menlo', 'Monaco', 'Courier New', monospace;
}

.output-panel__terminal-text {
  margin: 0;
  padding: 12px 16px;
  white-space: pre-wrap;
  word-wrap: break-word;
  flex: 1;
  font-family: 'Consolas', 'Menlo', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
}

/* Graphic tab */
.output-panel__graphic {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: #1e1e1e;
  padding: 10px;
}

.output-panel__graphic-label {
  margin-bottom: 10px;
  color: #d4d4d4;
  font-size: 14px;
}

.output-panel__graphic-img {
  width: 100%;
  height: calc(100% - 40px);
  object-fit: contain;
  border: 1px solid #444;
  border-radius: 4px;
  background-color: #000;
}

.output-panel__graphic-placeholder {
  color: #666;
  font-size: 14px;
}

/* History tab — Python IDLE style with left gutter */
.output-panel__history {
  position: relative;
  min-height: 100%;
  overflow-y: auto;
}

/* Continuous gutter background + vertical line */
.output-panel__history::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  width: 48px;
  background: #1a1a1a;
  border-right: 2px solid #444;
}

.output-panel__history-empty {
  color: #666;
  font-size: 14px;
  text-align: center;
  padding: 40px 20px;
  margin-left: 50px;
}

.output-panel__history-list {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 4px 0;
}

.output-panel__history-entry {
}

.output-panel__history-line {
  display: flex;
  align-items: baseline;
  line-height: 1.6;
}

.output-panel__history-prompt {
  width: 48px;
  flex-shrink: 0;
  text-align: right;
  padding: 0 6px 0 8px;
  font-weight: 700;
  font-size: 14px;
  font-family: 'Consolas', 'Menlo', 'Monaco', 'Courier New', monospace;
}

.output-panel__history-prompt--success {
  color: #4caf50;
}

.output-panel__history-prompt--error {
  color: #f44336;
}

.output-panel__history-prompt--suggestion {
  color: #ff9800;
}

.output-panel__history-prompt--sub {
  color: #888;
}

.output-panel__history-text {
  font-size: 14px;
  color: #ccc;
  flex: 1;
  padding: 0 12px;
}

.output-panel__history-time {
  font-size: 14px;
  color: #666;
  flex-shrink: 0;
  padding-right: 12px;
}

.output-panel__history-translated {
  font-size: 14px;
  color: #999;
  font-style: italic;
  padding: 0 8px;
}

.output-panel__history-exec {
  font-size: 14px;
  color: #9cdcfe;
  padding: 0 8px;
}

.output-panel__history-error {
  font-size: 14px;
  color: #f44336;
  padding: 0 8px;
}

/* Scrollbar */
.output-panel__content::-webkit-scrollbar,
.output-panel__history::-webkit-scrollbar {
  width: 8px;
}

.output-panel__content::-webkit-scrollbar-track,
.output-panel__history::-webkit-scrollbar-track {
  background: #2d2d2d;
}

.output-panel__content::-webkit-scrollbar-thumb,
.output-panel__history::-webkit-scrollbar-thumb {
  background: #555;
  border-radius: 4px;
}

.output-panel__content::-webkit-scrollbar-thumb:hover,
.output-panel__history::-webkit-scrollbar-thumb:hover {
  background: #666;
}
</style>
