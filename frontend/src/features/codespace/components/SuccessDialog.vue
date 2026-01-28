<template>
  <Transition name="dialog-fade">
    <div v-if="visible" class="success-dialog__overlay" @click="$emit('close')">
      <div class="success-dialog" @click.stop>
        <div class="success-dialog__icon">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" fill="var(--color-navy)"/>
            <path d="M8 12l2.5 2.5L16 9" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <p class="success-dialog__message">{{ message }}</p>
      </div>
    </div>
  </Transition>
</template>

<script>
export default {
  name: 'SuccessDialog',
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    message: {
      type: String,
      default: ''
    }
  },
  emits: ['close']
}
</script>

<style scoped>
.success-dialog__overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  cursor: pointer;
}

.success-dialog {
  background: white;
  border-radius: 12px;
  padding: 24px 32px;
  text-align: center;
  box-shadow: 0 4px 20px rgba(0, 31, 63, 0.15);
  border-left: 4px solid var(--color-navy);
  display: flex;
  align-items: center;
  gap: 16px;
  cursor: default;
}

.success-dialog__icon {
  flex-shrink: 0;
}

.success-dialog__message {
  font-size: 16px;
  font-weight: 500;
  color: #1a1a1a;
  font-family: 'Jaldi', sans-serif;
  margin: 0;
}

.dialog-fade-enter-active,
.dialog-fade-leave-active {
  transition: opacity 0.2s ease;
}

.dialog-fade-enter-from,
.dialog-fade-leave-to {
  opacity: 0;
}

.dialog-fade-enter-active .success-dialog,
.dialog-fade-leave-active .success-dialog {
  transition: transform 0.2s ease;
}

.dialog-fade-enter-from .success-dialog {
  transform: translateY(-10px);
}

.dialog-fade-leave-to .success-dialog {
  transform: translateY(-10px);
}
</style>
