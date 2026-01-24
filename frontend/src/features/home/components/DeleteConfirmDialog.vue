<template>
  <div v-if="visible" class="dialog-overlay" @click.self="handleClose">
    <div class="dialog delete-dialog">
      <div class="dialog-header">
        <h2 class="dialog-title">{{ t.home.deleteApp || 'Delete App' }}</h2>
        <button class="dialog-close" @click="handleClose">&times;</button>
      </div>

      <div class="dialog-body">
        <div class="warning-icon">⚠️</div>
        <p class="delete-message">
          {{ t.home.deleteConfirmMessage || 'Are you sure you want to delete' }}
          <strong>"{{ appName }}"</strong>?
        </p>
        <p class="delete-warning">
          {{ t.home.deleteWarning || 'This action cannot be undone.' }}
        </p>
      </div>

      <div class="dialog-footer">
        <button class="btn btn-secondary" @click="handleClose">
          {{ t.home.cancel || 'Cancel' }}
        </button>
        <button
          class="btn btn-danger"
          @click="handleConfirm"
          :disabled="isDeleting"
        >
          <span v-if="isDeleting" class="spinner"></span>
          {{ isDeleting ? (t.home.deleting || 'Deleting...') : (t.home.delete || 'Delete') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useLanguage } from '@py-talk/shared'
import { useTranslations } from '@/utils/translations'

export default {
  name: 'DeleteConfirmDialog',
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    appName: {
      type: String,
      default: ''
    },
    appId: {
      type: Number,
      default: null
    }
  },
  emits: ['close', 'confirm'],
  setup(props, { emit }) {
    const { language } = useLanguage()
    const t = computed(() => useTranslations(language.value))

    const isDeleting = ref(false)

    const handleClose = () => {
      isDeleting.value = false
      emit('close')
    }

    const handleConfirm = () => {
      isDeleting.value = true
      emit('confirm', props.appId)
    }

    return {
      t,
      isDeleting,
      handleClose,
      handleConfirm
    }
  }
}
</script>

<style scoped>
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog {
  background: white;
  border-radius: 16px;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  overflow: hidden;
}

.delete-dialog .dialog-body {
  text-align: center;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e8e8e8;
}

.dialog-title {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
  font-family: 'Jaldi', sans-serif;
  margin: 0;
}

.dialog-close {
  background: none;
  border: none;
  font-size: 24px;
  color: #666;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

.dialog-close:hover {
  color: #333;
}

.dialog-body {
  padding: 24px;
}

.warning-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.delete-message {
  font-size: 16px;
  color: #333;
  margin: 0 0 8px 0;
}

.delete-warning {
  font-size: 14px;
  color: #666;
  margin: 0;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #e8e8e8;
  background: #fafafa;
}

.btn {
  padding: 10px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-secondary {
  background: #e8e8e8;
  color: #333;
}

.btn-secondary:hover {
  background: #ddd;
}

.btn-danger {
  background: linear-gradient(180deg, #d32f2f 0%, #b71c1c 100%);
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background: linear-gradient(180deg, #e53935 0%, #c62828 100%);
}

.btn-danger:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
