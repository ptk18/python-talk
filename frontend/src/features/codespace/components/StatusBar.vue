<template>
  <Transition name="status-fade">
    <div v-if="isTranscribing || isProcessing" class="status-chip">
      <div class="status-chip__spinner">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-dasharray="50" stroke-dashoffset="15">
            <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="0.8s" repeatCount="indefinite"/>
          </circle>
        </svg>
      </div>
      <span class="status-chip__text">
        <template v-if="isTranscribing">{{ language === 'th' ? 'กำลังแปลงเสียง...' : 'Transcribing...' }}</template>
        <template v-else>{{ language === 'th' ? 'กำลังประมวลผล...' : 'Processing...' }}</template>
      </span>
    </div>
  </Transition>
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
.status-chip {
  position: fixed;
  top: 90px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(30, 30, 30, 0.85);
  color: #fff;
  border-radius: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.2);
  z-index: var(--z-modal);
  backdrop-filter: blur(8px);
}

.status-chip__spinner {
  display: flex;
  align-items: center;
  color: #fff;
}

.status-chip__text {
  font-size: 13px;
  font-family: 'Jaldi', sans-serif;
  white-space: nowrap;
}

.status-fade-enter-active,
.status-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.status-fade-enter-from,
.status-fade-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-8px);
}
</style>
