<template>
  <aside class="app-sidebar">
    <!-- Back Button -->
    <div class="app-sidebar__back" @click="goBack">
      <svg class="back-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polyline points="15 18 9 12 15 6"></polyline>
      </svg>
      <span>{{ t.appSidebar?.allApps || 'All Apps' }}</span>
    </div>

    <!-- App Info -->
    <div class="app-sidebar__info">
      <div class="app-icon-wrapper">
        <img
          v-if="appIcon && !isEmoji(appIcon)"
          :src="appIcon"
          :alt="appName"
          class="app-icon-img"
        />
        <span v-else-if="appIcon && isEmoji(appIcon)" class="app-icon-emoji">{{ appIcon }}</span>
        <span v-else class="app-icon-default">{{ getInitial(appName) }}</span>
      </div>
      <h3 class="app-name">{{ appName }}</h3>
    </div>

    <!-- Expandable Sections -->
    <div class="app-sidebar__sections">
      <!-- Available Methods Section -->
      <div class="section">
        <button class="section__header" @click="toggleSection('methods')">
          <svg
            class="chevron-icon"
            :class="{ expanded: expandedSections.methods }"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <polyline points="9 18 15 12 9 6"></polyline>
          </svg>
          <span>{{ t.appSidebar?.availableMethods || 'Available Methods' }}</span>
          <span v-if="methodsLoading" class="loading-spinner"></span>
        </button>

        <div v-if="expandedSections.methods" class="section__content">
          <div v-if="methodsLoading" class="section__loading">
            {{ t.appSidebar?.loading || 'Loading...' }}
          </div>
          <div v-else-if="methodsList.length === 0 && Object.keys(methodsClasses).length === 0" class="section__empty">
            {{ t.appSidebar?.noMethods || 'No methods available' }}
          </div>
          <div v-else class="methods-list">
            <!-- For turtle apps - flat list grouped by category -->
            <template v-if="appType === 'turtle'">
              <div v-for="(categoryMethods, category) in methodsByCategory" :key="category" class="method-category">
                <div class="category-name">{{ category }}</div>
                <button
                  v-for="method in categoryMethods"
                  :key="method.name"
                  class="method-item"
                  @click="handleMethodClick(method)"
                  :title="method.docstring"
                >
                  {{ method.name }}({{ method.params?.join(', ') || '' }})
                </button>
              </div>
            </template>
            <!-- For codespace apps - grouped by class -->
            <template v-else>
              <div v-for="(classData, className) in methodsClasses" :key="className" class="method-category">
                <div class="category-name">{{ className }}</div>
                <button
                  v-for="method in classData.methods"
                  :key="method.name"
                  class="method-item"
                  @click="handleMethodClick(method)"
                  :title="method.docstring"
                >
                  {{ method.name }}({{ method.required_parameters?.join(', ') || '' }})
                </button>
              </div>
            </template>
          </div>
        </div>
      </div>

      <!-- Files Section -->
      <div class="section" v-if="appType !== 'turtle'">
        <button class="section__header" @click="toggleSection('files')">
          <svg
            class="chevron-icon"
            :class="{ expanded: expandedSections.files }"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <polyline points="9 18 15 12 9 6"></polyline>
          </svg>
          <span>{{ t.appSidebar?.files || 'Files' }}</span>
          <span v-if="filesLoading" class="loading-spinner"></span>
        </button>

        <div v-if="expandedSections.files" class="section__content">
          <div v-if="filesLoading" class="section__loading">
            {{ t.appSidebar?.loading || 'Loading...' }}
          </div>
          <div v-else-if="filesList.length === 0" class="section__empty">
            {{ t.appSidebar?.noFiles || 'No files' }}
          </div>
          <div v-else class="files-list">
            <button
              v-for="file in filesList"
              :key="file"
              class="file-item"
              :class="{ active: file === currentFile }"
              @click="handleFileClick(file)"
            >
              <svg class="file-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
              </svg>
              <span class="file-name">{{ file }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </aside>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useLanguage, conversationAPI, fileAPI, turtleAPI } from '@py-talk/shared'
import { useTranslations } from '@/utils/translations'

export default {
  name: 'AppSidebar',
  props: {
    appId: {
      type: [Number, String],
      default: null
    },
    appName: {
      type: String,
      required: true
    },
    appIcon: {
      type: String,
      default: null
    },
    appType: {
      type: String,
      default: 'codespace'
    },
    currentFile: {
      type: String,
      default: null
    }
  },
  emits: ['insert-method', 'select-file'],
  setup(props, { emit }) {
    const router = useRouter()
    const { language } = useLanguage()
    const t = computed(() => useTranslations(language.value))

    // Section expand states
    const expandedSections = ref({
      methods: false,
      files: false
    })

    // Data states
    const methodsList = ref([])
    const methodsClasses = ref({})
    const filesList = ref([])

    // Loading states
    const methodsLoading = ref(false)
    const filesLoading = ref(false)

    // Computed: methods grouped by category (for turtle)
    const methodsByCategory = computed(() => {
      const grouped = {}
      methodsList.value.forEach(method => {
        const category = method.category || 'General'
        if (!grouped[category]) {
          grouped[category] = []
        }
        grouped[category].push(method)
      })
      return grouped
    })

    // Check if string is emoji
    const isEmoji = (str) => {
      if (!str) return false
      const emojiRegex = /[\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]/u
      return emojiRegex.test(str)
    }

    // Get initial letter for default icon
    const getInitial = (name) => {
      return name ? name.charAt(0).toUpperCase() : 'A'
    }

    // Navigation
    const goBack = () => {
      router.push('/')
    }

    // Toggle section expand
    const toggleSection = async (section) => {
      expandedSections.value[section] = !expandedSections.value[section]

      // Lazy load data when expanding
      if (expandedSections.value[section]) {
        if (section === 'methods' && methodsList.value.length === 0 && Object.keys(methodsClasses.value).length === 0) {
          await fetchMethods()
        }
        if (section === 'files' && filesList.value.length === 0) {
          await fetchFiles()
        }
      }

      // Persist expand state
      try {
        localStorage.setItem('appSidebar_expandedSections', JSON.stringify(expandedSections.value))
      } catch (e) {
        console.warn('Failed to persist expand state:', e)
      }
    }

    // Fetch methods
    const fetchMethods = async () => {
      if (!props.appId && props.appType !== 'turtle') return

      methodsLoading.value = true
      try {
        if (props.appType === 'turtle') {
          const response = await turtleAPI.getMethods()
          if (response.success && response.methods) {
            methodsList.value = response.methods
          }
        } else {
          const response = await conversationAPI.getAvailableMethods(props.appId)
          if (response.classes) {
            methodsClasses.value = response.classes
          }
        }
      } catch (error) {
        console.error('Failed to fetch methods:', error)
      } finally {
        methodsLoading.value = false
      }
    }

    // Fetch files
    const fetchFiles = async () => {
      if (!props.appId || props.appType === 'turtle') return

      filesLoading.value = true
      try {
        const response = await fileAPI.listFiles(props.appId)
        filesList.value = response.files || []
      } catch (error) {
        console.error('Failed to fetch files:', error)
      } finally {
        filesLoading.value = false
      }
    }

    // Handle method click
    const handleMethodClick = (method) => {
      const methodCall = props.appType === 'turtle'
        ? `${method.name}(${method.params?.join(', ') || ''})`
        : `${method.name}(${method.required_parameters?.join(', ') || ''})`

      emit('insert-method', methodCall)
    }

    // Handle file click
    const handleFileClick = (filename) => {
      emit('select-file', filename)
    }

    // Restore expand state
    onMounted(() => {
      try {
        const saved = localStorage.getItem('appSidebar_expandedSections')
        if (saved) {
          expandedSections.value = JSON.parse(saved)
          // Auto-fetch if already expanded
          if (expandedSections.value.methods) {
            fetchMethods()
          }
          if (expandedSections.value.files) {
            fetchFiles()
          }
        }
      } catch (e) {
        console.warn('Failed to restore expand state:', e)
      }
    })

    // Re-fetch when appId changes
    watch(() => props.appId, (newId) => {
      if (newId) {
        methodsList.value = []
        methodsClasses.value = {}
        filesList.value = []
        if (expandedSections.value.methods) {
          fetchMethods()
        }
        if (expandedSections.value.files) {
          fetchFiles()
        }
      }
    })

    return {
      t,
      expandedSections,
      methodsList,
      methodsClasses,
      methodsByCategory,
      filesList,
      methodsLoading,
      filesLoading,
      isEmoji,
      getInitial,
      goBack,
      toggleSection,
      handleMethodClick,
      handleFileClick
    }
  }
}
</script>

<style scoped>
.app-sidebar {
  position: fixed;
  top: 48px;
  left: 80px;
  width: 220px;
  height: calc(100vh - 48px);
  background: white;
  border-right: 1px solid #e8e8e8;
  z-index: 100;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Back Button */
.app-sidebar__back {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px;
  cursor: pointer;
  color: #024A14;
  font-size: 14px;
  font-weight: 500;
  font-family: 'Jaldi', sans-serif;
  transition: background 0.2s ease;
}

.app-sidebar__back:hover {
  background: #f5f5f5;
}

.back-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

/* App Info */
.app-sidebar__info {
  padding: 20px 16px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 12px;
}

.app-icon-wrapper {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f7f2;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.app-icon-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.app-icon-emoji {
  font-size: 32px;
}

.app-icon-default {
  font-size: 28px;
  font-weight: 600;
  color: #024A14;
  font-family: 'Jaldi', sans-serif;
}

.app-name {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  font-family: 'Jaldi', sans-serif;
  margin: 0;
  text-align: left;
  word-break: break-word;
}

/* Sections */
.app-sidebar__sections {
  flex: 1;
  overflow-y: auto;
}

.section {
  /* No border-bottom for cleaner look */
}

.section__header {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: #333;
  font-family: 'Jaldi', sans-serif;
  transition: background 0.2s ease;
}

.section__header:hover {
  background: #f5f5f5;
}

.chevron-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  transition: transform 0.2s ease;
}

.chevron-icon.expanded {
  transform: rotate(90deg);
}

.loading-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid #e8e8e8;
  border-top-color: #024A14;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-left: auto;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.section__content {
  padding: 0 8px 12px;
  animation: slideDown 0.2s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.section__loading,
.section__empty {
  padding: 12px 8px;
  font-size: 13px;
  color: #666;
  font-family: 'Jaldi', sans-serif;
}

/* Methods List */
.methods-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.method-category {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.category-name {
  font-size: 11px;
  font-weight: 600;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 8px 8px 4px;
  font-family: 'Jaldi', sans-serif;
}

.method-item {
  display: block;
  width: 100%;
  padding: 8px 12px;
  background: #f8f8f8;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  font-size: 12px;
  font-family: 'Monaco', 'Menlo', monospace;
  color: #333;
  cursor: pointer;
  text-align: left;
  transition: all 0.15s ease;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.method-item:hover {
  background: #f0f7f2;
  border-color: #024A14;
  color: #024A14;
}

/* Files List */
.files-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px 12px;
  background: transparent;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-family: 'Jaldi', sans-serif;
  color: #333;
  cursor: pointer;
  text-align: left;
  transition: all 0.15s ease;
}

.file-item:hover {
  background: #f5f5f5;
}

.file-item.active {
  background: #f0f7f2;
  color: #024A14;
  font-weight: 500;
}

.file-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  color: #666;
}

.file-item.active .file-icon {
  color: #024A14;
}

.file-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Scrollbar */
.app-sidebar__sections::-webkit-scrollbar {
  width: 6px;
}

.app-sidebar__sections::-webkit-scrollbar-track {
  background: transparent;
}

.app-sidebar__sections::-webkit-scrollbar-thumb {
  background: #d0d0d0;
  border-radius: 3px;
}

.app-sidebar__sections::-webkit-scrollbar-thumb:hover {
  background: #b0b0b0;
}
</style>
