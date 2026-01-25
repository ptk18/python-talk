<template>
  <div class="output-panel" :class="{ 'output-panel--expanded': isExpanded }">
    <div class="output-panel__header">
      <div class="output-panel__header-content">
        <h3>{{ title }}</h3>
        <div class="output-panel__actions">
          <button
            class="output-panel__icon-btn"
            :class="{ 'active': isExpanded }"
            @click="$emit('toggle-expand')"
            aria-label="Expand output"
            title="Expand output to full height"
          >
            <img :src="spanIcon" alt="Span" class="output-panel__icon" />
          </button>
          <button
            class="output-panel__icon-btn"
            @click="$emit('clear')"
            aria-label="Clear output"
            title="Clear output"
          >
            <img :src="clearIcon" alt="Clear" class="output-panel__icon" />
          </button>
        </div>
      </div>
    </div>
    <div class="output-panel__body">
      <div class="output-panel__mode-tabs">
        <button
          class="output-panel__mode-tab"
          :class="{ 'active': isTextMode }"
          @click="$emit('set-mode', 'text')"
          title="Text Mode"
        >
          <img :src="textModeIcon" alt="Text" class="output-panel__mode-icon" />
        </button>
        <button
          class="output-panel__mode-tab"
          :class="{ 'active': !isTextMode }"
          @click="$emit('set-mode', 'graphic')"
          title="Graphic Mode"
        >
          <img :src="graphicModeIcon" alt="Graphic" class="output-panel__mode-icon" />
        </button>
      </div>
      <div class="output-panel__content">
        <div
          v-if="!isTextMode"
          class="output-panel__graphic"
        >
          <div class="output-panel__graphic-label">
            {{ graphicLabel }}
          </div>
          <img
            id="turtle-video"
            class="output-panel__graphic-img"
            alt="Turtle graphics stream"
          />
        </div>
        <pre v-else>{{ output || placeholder }}</pre>
      </div>
    </div>
  </div>
</template>

<script>
import spanIcon from '@/assets/R-span.svg'
import clearIcon from '@/assets/R-clear.svg'
import textModeIcon from '@/assets/R-textmode.svg'
import graphicModeIcon from '@/assets/R-graphicmode.svg'

export default {
  name: 'OutputPanel',
  props: {
    output: {
      type: String,
      default: ''
    },
    isTextMode: {
      type: Boolean,
      default: true
    },
    isExpanded: {
      type: Boolean,
      default: false
    },
    title: {
      type: String,
      default: 'Output'
    },
    placeholder: {
      type: String,
      default: 'Output will appear here...'
    },
    graphicLabel: {
      type: String,
      default: 'Turtle Graphics Stream'
    }
  },
  emits: ['clear', 'set-mode', 'toggle-expand'],
  setup() {
    return {
      spanIcon,
      clearIcon,
      textModeIcon,
      graphicModeIcon
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
  transition: flex 0.3s ease;
}

.output-panel--expanded {
  flex: 1 1 100%;
  min-height: 100%;
}

.output-panel__header {
  display: flex;
  background: #fafafa;
  border-bottom: 1px solid #e8e8e8;
}

.output-panel__header-content {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
}

.output-panel__header h3 {
  font-size: 14px;
  font-weight: 600;
  color: #1a1a1a;
  font-family: 'Jaldi', sans-serif;
  margin: 0;
}

.output-panel__actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.output-panel__icon-btn {
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

.output-panel__icon-btn:hover:not(:disabled) {
  background: rgba(0, 0, 0, 0.08);
}

.output-panel__icon-btn.active {
  background: var(--color-navy);
  color: white;
}

.output-panel__icon-btn.active .output-panel__icon {
  filter: brightness(0) invert(1);
}

.output-panel__icon {
  width: 16px;
  height: 16px;
  object-fit: contain;
}

.output-panel__body {
  flex: 1;
  display: flex;
  min-height: 0;
  overflow: hidden;
}

.output-panel__mode-tabs {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px 4px;
  background: #262525;
  border-right: 1px solid #444;
}

.output-panel__mode-tab {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 6px;
  background: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.output-panel__mode-tab:hover {
  background: rgba(255, 255, 255, 0.1);
}

.output-panel__mode-tab.active {
  background: rgba(255, 255, 255, 0.2);
}

.output-panel__mode-icon {
  width: 16px;
  height: 16px;
  object-fit: contain;
  filter: brightness(0) invert(1);
}

.output-panel__content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background: #1e1e1e;
  color: #d4d4d4;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.6;
  min-height: 0;
}

.output-panel__content pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}

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

.output-panel__content::-webkit-scrollbar {
  width: 8px;
}

.output-panel__content::-webkit-scrollbar-track {
  background: #2d2d2d;
}

.output-panel__content::-webkit-scrollbar-thumb {
  background: #555;
  border-radius: 4px;
}

.output-panel__content::-webkit-scrollbar-thumb:hover {
  background: #666;
}
</style>
