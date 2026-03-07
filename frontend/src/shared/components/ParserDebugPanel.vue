<template>
  <div class="parser-debug">
    <div class="parser-debug__header">
      <span class="parser-debug__title">Parser Log</span>
      <button class="parser-debug__toggle" @click="collapsed = !collapsed">
        {{ collapsed ? '&#9650;' : '&#9660;' }}
      </button>
    </div>
    <div v-if="!collapsed" class="parser-debug__body">
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
    const collapsed = ref(false)
    return { collapsed }
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

.parser-debug__toggle {
  background: none;
  border: none;
  color: #999;
  cursor: pointer;
  font-size: 10px;
  padding: 2px 6px;
}

.parser-debug__toggle:hover {
  color: #555;
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
</style>
