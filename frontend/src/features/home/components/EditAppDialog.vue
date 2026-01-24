<template>
  <div v-if="visible" class="dialog-overlay" @click.self="handleClose">
    <div class="dialog">
      <div class="dialog-header">
        <h2 class="dialog-title">{{ t.home.editApp || 'Edit App' }}</h2>
        <button class="dialog-close" @click="handleClose">&times;</button>
      </div>

      <div class="dialog-body">
        <!-- App Name -->
        <div class="form-group">
          <label class="form-label">{{ t.home.appName || 'App Name' }} *</label>
          <input
            type="text"
            class="form-input"
            v-model="appName"
            :placeholder="t.home.enterAppName || 'Enter app name'"
            @keydown.enter="handleSave"
          />
        </div>

        <!-- App Image -->
        <div class="form-group">
          <label class="form-label">{{ t.home.appImage || 'App Image' }} ({{ t.home.optional || 'Optional' }})</label>
          <div class="image-upload-area" @click="triggerImageInput">
            <input
              type="file"
              ref="imageInput"
              accept="image/*"
              @change="handleImageChange"
              class="file-input-hidden"
            />
            <div v-if="!appImagePreview" class="image-placeholder">
              <span class="image-icon">🖼️</span>
              <span>{{ t.home.clickToUploadImage || 'Click to upload image' }}</span>
            </div>
            <div v-else class="image-preview-container">
              <img :src="appImagePreview" alt="App preview" class="image-preview" />
              <button class="remove-image-btn" @click.stop="removeImage">&times;</button>
            </div>
          </div>
        </div>
      </div>

      <div class="dialog-footer">
        <button class="btn btn-secondary" @click="handleClose">
          {{ t.home.cancel || 'Cancel' }}
        </button>
        <button
          class="btn btn-primary"
          @click="handleSave"
          :disabled="!isValid || isSaving"
        >
          <span v-if="isSaving" class="spinner"></span>
          {{ isSaving ? (t.home.saving || 'Saving...') : (t.home.saveChanges || 'Save Changes') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue'
import { useLanguage } from '@py-talk/shared'
import { useTranslations } from '@/utils/translations'

export default {
  name: 'EditAppDialog',
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    app: {
      type: Object,
      default: null
    }
  },
  emits: ['close', 'save'],
  setup(props, { emit }) {
    const { language } = useLanguage()
    const t = computed(() => useTranslations(language.value))

    const appName = ref('')
    const appImagePreview = ref(null)
    const imageInput = ref(null)
    const isSaving = ref(false)

    const isValid = computed(() => appName.value.trim().length > 0)

    // Reset form when dialog opens
    watch(() => props.visible, (newVal) => {
      if (newVal && props.app) {
        appName.value = props.app.name || ''
        // Check if icon is a data URI (user-uploaded image)
        const icon = props.app.icon
        if (typeof icon === 'string' && icon.startsWith('data:')) {
          appImagePreview.value = icon
        } else {
          appImagePreview.value = null
        }
        isSaving.value = false
      }
    })

    const triggerImageInput = () => {
      imageInput.value?.click()
    }

    const handleImageChange = (event) => {
      const file = event.target.files[0]
      if (file) {
        const reader = new FileReader()
        reader.onload = (e) => {
          appImagePreview.value = e.target.result
        }
        reader.readAsDataURL(file)
      }
    }

    const removeImage = () => {
      appImagePreview.value = null
      if (imageInput.value) {
        imageInput.value.value = ''
      }
    }

    const handleClose = () => {
      emit('close')
    }

    const handleSave = () => {
      if (!isValid.value || isSaving.value) return
      isSaving.value = true
      emit('save', {
        id: props.app.appId,
        title: appName.value.trim(),
        app_image: appImagePreview.value
      })
    }

    return {
      t,
      appName,
      appImagePreview,
      imageInput,
      isSaving,
      isValid,
      triggerImageInput,
      handleImageChange,
      removeImage,
      handleClose,
      handleSave
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
  max-width: 480px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  overflow: hidden;
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

.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 8px;
}

.form-input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.form-input:focus {
  outline: none;
  border-color: #024A14;
}

.image-upload-area {
  border: 2px dashed #ddd;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.2s, background-color 0.2s;
  min-height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-upload-area:hover {
  border-color: #024A14;
  background-color: #f8fdf9;
}

.file-input-hidden {
  display: none;
}

.image-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: #666;
  font-size: 14px;
}

.image-icon {
  font-size: 32px;
}

.image-preview-container {
  position: relative;
  display: inline-block;
}

.image-preview {
  max-width: 150px;
  max-height: 100px;
  border-radius: 8px;
  object-fit: cover;
}

.remove-image-btn {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #d32f2f;
  color: white;
  border: none;
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.remove-image-btn:hover {
  background: #b71c1c;
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

.btn-primary {
  background: linear-gradient(180deg, #024A14 0%, #01350e 100%);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: linear-gradient(180deg, #035a1a 0%, #024512 100%);
}

.btn-primary:disabled {
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
