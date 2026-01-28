<template>
  <div v-if="isTranscribing" class="status-bar status-bar--transcribing">
    <div class="status-bar__content">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="status-bar__spinner">
        <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-dasharray="60" stroke-dashoffset="0">
          <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite"/>
        </circle>
      </svg>
      <span class="status-bar__text">{{ language === 'th' ? 'กำลังแปลงเสียงของคุณ...' : 'Transcribing your voice...' }}</span>
      <div class="status-bar__progress">
        <div class="status-bar__progress-bar"></div>
      </div>
    </div>
  </div>

  <div v-if="isProcessing" class="status-bar status-bar--processing">
    <div class="status-bar__content">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="status-bar__spinner">
        <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-dasharray="60" stroke-dashoffset="0">
          <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite"/>
        </circle>
      </svg>
      <span class="status-bar__text">{{ language === 'th' ? 'กำลังประมวลผลและจับคู่คำสั่ง...' : 'Processing and mapping command...' }}</span>
      <div class="status-bar__progress">
        <div class="status-bar__progress-bar"></div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'StatusBar',
  props: {
    isTranscribing: {
      type: Boolean,
      default: false
    },
    isProcessing: {
      type: Boolean,
      default: false
    },
    language: {
      type: String,
      default: 'en'
    }
  }
}
</script>

<style scoped>
.status-bar {
  position: fixed;
  top: 80px;
  left: var(--sidebar-total);
  right: 0;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  padding: 12px 24px;
  z-index: var(--z-modal);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.status-bar__content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-bar__spinner {
  animation: spin 1s linear infinite;
}

.status-bar__text {
  font-size: 14px;
  font-family: 'Jaldi', sans-serif;
  color: #1a1a1a;
}

.status-bar__progress {
  flex: 1;
  height: 4px;
  background: #e8e8e8;
  border-radius: 2px;
  overflow: hidden;
}

.status-bar__progress-bar {
  height: 100%;
  background: var(--color-navy);
  animation: progress 2s ease-in-out infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes progress {
  0% { width: 0%; }
  50% { width: 70%; }
  100% { width: 100%; }
}
</style>
