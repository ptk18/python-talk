<template>
  <div
    :class="['voice-input', { 'voice-input--recording': isRecording }]"
    @click="$emit('click')"
  >
    <svg
      class="voice-input__icon"
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M12 14C13.66 14 15 12.66 15 11V5C15 3.34 13.66 2 12 2C10.34 2 9 3.34 9 5V11C9 12.66 10.34 14 12 14Z"
        fill="currentColor"
      />
      <path
        d="M17 11C17 13.76 14.76 16 12 16C9.24 16 7 13.76 7 11H5C5 14.53 7.61 17.43 11 17.92V21H13V17.92C16.39 17.43 19 14.53 19 11H17Z"
        fill="currentColor"
      />
    </svg>
  </div>
</template>

<script>
export default {
  name: 'VoiceInput',
  props: {
    isRecording: {
      type: Boolean,
      default: false
    }
  },
  emits: ['click']
}
</script>

<style scoped>
.voice-input {
  width: 44px;
  height: 44px;
  border: none;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  background: var(--color-primary);
  color: white;
  flex-shrink: 0;
}

.voice-input:hover {
  background: var(--color-primary-dark);
  transform: scale(1.05);
}

.voice-input--recording {
  background: #dc3545;
  animation: pulse 1.5s infinite;
}

.voice-input__icon {
  width: 20px;
  height: 20px;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
}
</style>
