<template>
  <!-- Backdrop overlay when expanded -->
  <div v-if="expanded" class="parser-debug__overlay" @click="expanded = false"></div>

  <div :class="['parser-debug', { 'parser-debug--expanded': expanded }]">
    <div class="parser-debug__header">
      <span class="parser-debug__title">Parser Log</span>
      <button class="parser-debug__expand" @click="expanded = !expanded" :title="expanded ? 'Close' : 'Expand'">
        <!-- Expand icon: 4 corner arrows -->
        <svg v-if="!expanded" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="15 3 21 3 21 9" />
          <polyline points="9 21 3 21 3 15" />
          <polyline points="21 3 14 10" />
          <polyline points="3 21 10 14" />
        </svg>
        <!-- Collapse icon: 4 corner arrows inward -->
        <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="4 14 10 14 10 20" />
          <polyline points="20 10 14 10 14 4" />
          <polyline points="14 10 21 3" />
          <polyline points="10 14 3 21" />
        </svg>
      </button>
    </div>
    <div class="parser-debug__body">
      <div v-if="!data" class="parser-debug__empty">
        No command processed yet.
      </div>
      <pre v-else class="parser-debug__json">{{ JSON.stringify(data, null, 2) }}</pre>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'ParserDebugPanel',
  props: {
    data: {
      type: Object,
      default: null
    }
  },
  setup() {
    const expanded = ref(false)
    return { expanded }
  }
}
</script>

<style scoped>
.parser-debug {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #1e1e1e;
  border-radius: 12px;
  border: 1px solid #e8e8e8;
  overflow: hidden;
  min-height: 0;
}

.parser-debug__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background: #fafafa;
  border-bottom: 1px solid #e8e8e8;
  flex-shrink: 0;
}

.parser-debug__title {
  font-size: 14px;
  font-weight: 600;
  color: #1a1a1a;
  font-family: 'Jaldi', sans-serif;
}

.parser-debug__expand {
  background: none;
  border: none;
  color: #999;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.parser-debug__expand:hover {
  color: #555;
  background: #eee;
}

.parser-debug__body {
  flex: 1;
  overflow-y: auto;
  padding: 10px 14px;
  min-height: 0;
}

.parser-debug__empty {
  color: #666;
  font-family: 'Consolas', 'Menlo', 'Monaco', 'Courier New', monospace;
  font-size: 12px;
  text-align: center;
  padding: 20px;
}

.parser-debug__json {
  margin: 0;
  font-family: 'Consolas', 'Menlo', 'Monaco', 'Courier New', monospace;
  font-size: 11px;
  line-height: 1.5;
  color: #d4d4d4;
  white-space: pre-wrap;
  word-break: break-word;
}

/* Backdrop overlay */
.parser-debug__overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1099;
}

/* Expanded modal mode */
.parser-debug--expanded {
  position: fixed;
  top: 32px;
  left: 32px;
  right: 32px;
  bottom: 32px;
  z-index: 1100;
  border-radius: 16px;
  border: 1px solid #444;
  max-height: none !important;
  flex: none !important;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
}

.parser-debug--expanded .parser-debug__header {
  padding: 14px 20px;
  background: #2d2d2d;
  border-bottom: 1px solid #444;
}

.parser-debug--expanded .parser-debug__title {
  color: #fff;
  font-size: 16px;
}

.parser-debug--expanded .parser-debug__expand {
  color: #ccc;
}

.parser-debug--expanded .parser-debug__expand:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.1);
}

.parser-debug--expanded .parser-debug__body {
  padding: 20px 24px;
}

.parser-debug--expanded .parser-debug__json {
  font-size: 13px;
}

.parser-debug--expanded .parser-debug__empty {
  font-size: 14px;
  padding: 40px;
}

/* Scrollbar */
.parser-debug__body::-webkit-scrollbar {
  width: 6px;
}

.parser-debug__body::-webkit-scrollbar-track {
  background: #2d2d2d;
}

.parser-debug__body::-webkit-scrollbar-thumb {
  background: #555;
  border-radius: 3px;
}

/* Tablet & Mobile: shrink parser debug to give more space to editor */
@media (max-width: 1024px) {
  .parser-debug:not(.parser-debug--expanded) {
    flex: 0 0 auto;
    max-height: 150px;
  }
}

@media (max-width: 768px) {
  .parser-debug:not(.parser-debug--expanded) {
    max-height: 120px;
  }

  .parser-debug:not(.parser-debug--expanded) .parser-debug__header {
    padding: 6px 12px;
  }

  .parser-debug:not(.parser-debug--expanded) .parser-debug__title {
    font-size: 13px;
  }

  .parser-debug:not(.parser-debug--expanded) .parser-debug__body {
    padding: 8px 10px;
  }

  .parser-debug:not(.parser-debug--expanded) .parser-debug__json {
    font-size: 10px;
  }

  .parser-debug--expanded {
    top: 16px;
    left: 16px;
    right: 16px;
    bottom: 16px;
    border-radius: 12px;
  }
}
</style>
