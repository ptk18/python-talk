<template>
  <div v-if="visible" class="dialog-overlay" @click.self="handleClose">
    <div class="dialog">
      <div class="dialog-header">
        <h2 class="dialog-title">{{ t.home.createNewApp || 'Create New App' }}</h2>
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
            @keydown.enter="handleCreate"
          />
        </div>

        <!-- App Image (Optional) - Moved after App Name -->
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

        <!-- App Type -->
        <div class="form-group">
          <label class="form-label">{{ t.home.appType || 'App Type' }}</label>
          <div class="radio-group">
            <label class="radio-label">
              <input type="radio" v-model="appType" value="import" />
              <span class="radio-text">{{ t.home.importLibrary || 'Import Library' }}</span>
            </label>
            <label class="radio-label">
              <input type="radio" v-model="appType" value="upload" />
              <span class="radio-text">{{ t.home.uploadFile || 'Upload Python File' }}</span>
            </label>
          </div>
        </div>

        <!-- Conditional: Library Dropdown (for import) -->
        <div v-if="appType === 'import'" class="form-group">
          <label class="form-label">{{ t.home.selectLibrary || 'Select Library' }}</label>
          <select class="form-select" v-model="selectedLibrary">
            <option value="turtle">turtle</option>
          </select>
        </div>

        <!-- Conditional: File Upload (for upload) -->
        <div v-if="appType === 'upload'" class="form-group">
          <label class="form-label">{{ t.home.pythonFile || 'Python File' }} *</label>
          <div class="file-upload-area" @click="triggerFileInput" @dragover.prevent @drop.prevent="handleDrop">
            <input
              type="file"
              ref="fileInput"
              accept=".py"
              @change="handleFileChange"
              class="file-input-hidden"
            />
            <div v-if="!selectedFile" class="file-placeholder">
              <span class="file-icon">📄</span>
              <span>{{ t.home.dropOrClick || 'Drop file here or click to browse' }}</span>
            </div>
            <div v-else class="file-selected">
              <span class="file-icon">✅</span>
              <span>{{ selectedFile.name }}</span>
            </div>
          </div>
        </div>

        <!-- Error Message -->
        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>
      </div>

      <div class="dialog-footer">
        <button class="btn btn-secondary" @click="handleClose">
          {{ t.home.cancel || 'Cancel' }}
        </button>
        <button
          class="btn btn-primary"
          @click="handleCreate"
          :disabled="!isValid || isCreating"
        >
          <span v-if="isCreating" class="spinner"></span>
          {{ isCreating ? (t.home.creating || 'Creating...') : (t.home.create || 'Create') }}
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
  name: 'NewAppDialog',
  props: {
    visible: {
      type: Boolean,
      default: false
    }
  },
  emits: ['close', 'create'],
  setup(props, { emit }) {
    const { language } = useLanguage()
    const t = computed(() => useTranslations(language.value))

    const appName = ref('')
    const appType = ref('import')
    const selectedLibrary = ref('turtle')
    const selectedFile = ref(null)
    const fileContent = ref('')
    const errorMessage = ref('')
    const isCreating = ref(false)
    const fileInput = ref(null)
    const imageInput = ref(null)
    const appImagePreview = ref(null)

    const isValid = computed(() => {
      if (!appName.value.trim()) return false
      if (appType.value === 'upload' && !selectedFile.value) return false
      return true
    })

    const resetForm = () => {
      appName.value = ''
      appType.value = 'import'
      selectedLibrary.value = 'turtle'
      selectedFile.value = null
      fileContent.value = ''
      errorMessage.value = ''
      isCreating.value = false
      appImagePreview.value = null
    }

    watch(() => props.visible, (newVal) => {
      if (!newVal) {
        resetForm()
      }
    })

    const triggerFileInput = () => {
      fileInput.value?.click()
    }

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

    const handleFileChange = async (event) => {
      const file = event.target.files[0]
      if (file) {
        await processFile(file)
      }
    }

    const handleDrop = async (event) => {
      const file = event.dataTransfer.files[0]
      if (file && file.name.endsWith('.py')) {
        await processFile(file)
      } else {
        errorMessage.value = t.value.home?.invalidFile || 'Please select a Python (.py) file'
      }
    }

    const processFile = async (file) => {
      if (!file.name.endsWith('.py')) {
        errorMessage.value = t.value.home?.invalidFile || 'Please select a Python (.py) file'
        return
      }
      selectedFile.value = file
      errorMessage.value = ''

      try {
        const text = await file.text()
        fileContent.value = text
      } catch (err) {
        errorMessage.value = t.value.home?.fileReadError || 'Failed to read file'
        selectedFile.value = null
      }
    }

    const handleClose = () => {
      emit('close')
    }

    const handleCreate = async () => {
      if (!isValid.value || isCreating.value) return

      errorMessage.value = ''
      isCreating.value = true

      try {
        const appData = {
          title: appName.value.trim(),
          app_type: appType.value === 'import' ? 'turtle' : 'upload',
          app_image: appImagePreview.value
        }

        if (appType.value === 'import') {
          // For turtle import, backend will generate default code
          appData.code = null
          appData.file_name = null
        } else {
          // For upload, include file content
          appData.code = fileContent.value
          appData.file_name = selectedFile.value.name
        }

        emit('create', appData)
      } catch (err) {
        errorMessage.value = err.message
        isCreating.value = false
      }
    }

    return {
      t,
      appName,
      appType,
      selectedLibrary,
      selectedFile,
      fileInput,
      imageInput,
      appImagePreview,
      errorMessage,
      isCreating,
      isValid,
      triggerFileInput,
      triggerImageInput,
      handleFileChange,
      handleImageChange,
      handleDrop,
      handleClose,
      handleCreate,
      removeImage
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

.form-select {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  background: white;
  cursor: pointer;
}

.form-select:focus {
  outline: none;
  border-color: #024A14;
}

.radio-group {
  display: flex;
  gap: 24px;
}

.radio-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.radio-label input[type="radio"] {
  width: 18px;
  height: 18px;
  accent-color: #024A14;
}

.radio-text {
  font-size: 14px;
  color: #333;
}

.file-upload-area {
  border: 2px dashed #ddd;
  border-radius: 8px;
  padding: 32px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.2s, background-color 0.2s;
}

.file-upload-area:hover {
  border-color: #024A14;
  background-color: #f8fdf9;
}

.file-input-hidden {
  display: none;
}

.file-placeholder,
.file-selected {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: #666;
  font-size: 14px;
}

.file-icon {
  font-size: 32px;
}

.file-selected {
  color: #024A14;
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

.error-message {
  color: #d32f2f;
  font-size: 13px;
  margin-top: 8px;
  padding: 8px 12px;
  background: #ffebee;
  border-radius: 6px;
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
