<template>
  <div class="app-container">
    <TopToolbar />
    <Sidebar />
    <AppSidebar
      :app-id="conversationId"
      :app-name="appName"
      :app-icon="appIcon"
      :app-type="appType"
      :current-file="currentFile"
      @insert-method="handleInsertMethod"
      @select-file="handleSelectFile"
    />
    <main class="main-content">
      <div class="workspace">
        <div class="workspace__container">
          <ChatPanel
            :messages="messages"
            :user-name="user?.username || 'User'"
            :is-recording="isRecording"
            :placeholder="t.workspace.typeYourMessage"
            v-model="message"
            @send="handleSend"
            @mic-click="handleMicClick"
          />

          <section class="workspace__code-panel">
            <CodeEditorPanel
              v-if="!isOutputExpanded"
              ref="editorRef"
              :code="currentCode"
              :current-file="currentFile"
              :editor-key="`${conversationId}-${currentFile}`"
              :is-saving="isSaving"
              :is-running="isRunning"
              :is-refreshing="isRefreshing"
              :refresh-notification="refreshNotification"
              @save="handleSave"
              @undo="handleUndo"
              @redo="handleRedo"
              @run="handleRun"
              @change="handleEditorChange"
            />

            <OutputPanel
              :output="output"
              :is-text-mode="isTextMode"
              :is-expanded="isOutputExpanded"
              :title="t.workspace.output"
              :placeholder="t.workspace.outputWillAppear"
              :graphic-label="t.workspace.turtleGraphicsStream"
              @clear="clearOutput"
              @set-mode="setOutputMode"
              @toggle-expand="toggleOutputExpand"
            />
          </section>
        </div>

        <StatusBar
          :is-transcribing="isTranscribing"
          :is-processing="isProcessingCommand"
          :language="language"
        />

        <SuccessDialog
          :visible="showSuccessDialog"
          :message="successDialogMessage"
          @close="hideSuccessDialog"
        />
      </div>
    </main>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import TopToolbar from '@/shared/components/TopToolbar.vue'
import Sidebar from '@/shared/components/Sidebar.vue'
import AppSidebar from '@/shared/components/AppSidebar.vue'
import { conversationAPI, fileAPI, analyzeAPI, useAuth, useLanguage, useTTS, voiceService } from '@py-talk/shared'
import { useCode } from './composables/useCode'
import { useFile } from './composables/useFile'
import { useOutputMode } from './composables/useOutputMode'
import { useVoiceRecording } from './composables/useVoiceRecording'
import { useWorkspaceSession } from './composables/useWorkspaceSession'
import { useCodeExecution } from './composables/useCodeExecution'
import { useCommandProcessor } from './composables/useCommandProcessor'
import { useTranslations } from '@/utils/translations'
import { getGreeting } from '@/shared/utils/formatters'
import { RUNNER_POLL_INTERVAL, USER_EDIT_DEBOUNCE, USER_EDIT_TIMEOUT, REFRESH_INDICATOR_DURATION, REFRESH_NOTIFICATION_DURATION } from './config/constants'
import ChatPanel from './components/ChatPanel.vue'
import CodeEditorPanel from './components/CodeEditorPanel.vue'
import OutputPanel from './components/OutputPanel.vue'
import StatusBar from './components/StatusBar.vue'
import SuccessDialog from './components/SuccessDialog.vue'

export default {
  name: 'Workspace',
  components: {
    TopToolbar,
    Sidebar,
    AppSidebar,
    ChatPanel,
    CodeEditorPanel,
    OutputPanel,
    StatusBar,
    SuccessDialog
  },
  setup() {
    const route = useRoute()
    const router = useRouter()
    const { user } = useAuth()
    const { language } = useLanguage()
    const { ttsEnabled } = useTTS()
    const t = computed(() => useTranslations(language.value))

    const conversationId = computed(() => route.query.conversationId)
    const message = ref('')
    const editorRef = ref(null)
    const isSaving = ref(false)
    const isRefreshing = ref(false)
    const refreshNotification = ref(null)
    const lastUserEdit = ref(0)
    const isUserEditing = ref(false)
    const editingTimeoutRef = ref(null)
    const hasGreeted = ref(false)
    let pollIntervalId = null

    const { code, setCode, syncCodeFromBackend, setConversationId } = useCode()
    const { currentFile, currentCode, files, setCurrentCode, loadFiles, loadFile, saveFile, clearFileState } = useFile()
    const { isTextMode, isOutputExpanded, setOutputMode, toggleOutputExpand } = useOutputMode()
    const { isRecording, isTranscribing, handleMicClick: micClick } = useVoiceRecording(language)
    const { messages, availableMethods, appName, appIcon, appType, initializeSession, fetchMessages, fetchAvailableMethods, updateMessages } = useWorkspaceSession()
    const { output, isRunning, handleRun: runCode, clearOutput } = useCodeExecution()
    const { isProcessingCommand, showSuccessDialog, successDialogMessage, processCommand, hideSuccessDialog } = useCommandProcessor()

    const handleMicClick = () => {
      micClick((transcribedText) => {
        message.value = transcribedText
      })
    }

    const handleSend = async (msgText) => {
      if (!msgText || !conversationId.value) return
      message.value = ''

      await processCommand(
        conversationId.value,
        msgText,
        language.value,
        {
          onMessagesUpdate: updateMessages,
          onCodeSync: syncCodeFromBackend,
          onFileRefresh: async () => {
            if (currentFile.value === 'runner.py') {
              isRefreshing.value = true
              await loadFile(parseInt(conversationId.value), 'runner.py')
              setTimeout(() => isRefreshing.value = false, REFRESH_INDICATOR_DURATION)
            }
          }
        }
      )
    }

    const handleSave = async () => {
      if (!conversationId.value) return

      isSaving.value = true
      try {
        await saveFile(parseInt(conversationId.value), currentFile.value, currentCode.value)

        if (currentFile.value === 'runner.py') {
          setCode(currentCode.value)
        }

        if (currentFile.value !== 'runner.py') {
          try {
            await analyzeAPI.invalidatePipelineCache(parseInt(conversationId.value))
          } catch (err) {
            console.warn('Failed to invalidate pipeline cache:', err)
          }

          await fetchAvailableMethods(conversationId.value)

          analyzeAPI.prewarmPipeline(parseInt(conversationId.value))
            .catch(err => console.warn('Pipeline re-prewarm failed:', err))

          voiceService.speak('Code saved and methods updated')
        } else {
          voiceService.speak('Code saved successfully')
        }

        lastUserEdit.value = 0
        isUserEditing.value = false
        if (editingTimeoutRef.value) {
          clearTimeout(editingTimeoutRef.value)
        }
      } catch (err) {
        console.error('Failed to save code:', err)
        voiceService.speak('Failed to save code')
      } finally {
        isSaving.value = false
      }
    }

    const handleUndo = () => editorRef.value?.undo()
    const handleRedo = () => editorRef.value?.redo()

    const handleRun = async () => {
      await runCode(conversationId.value, isTextMode.value)
    }

    const handleInsertMethod = (methodCall) => {
      const currentPosition = editorRef.value?.getPosition()
      if (editorRef.value && currentPosition) {
        editorRef.value.insertText(methodCall, currentPosition)
      } else {
        setCurrentCode(currentCode.value + '\n' + methodCall)
      }
    }

    const handleSelectFile = async (filename) => {
      if (conversationId.value) {
        await loadFile(parseInt(conversationId.value), filename)
      }
    }

    const handleEditorChange = (value) => {
      setCurrentCode(value || '')
      lastUserEdit.value = Date.now()
      isUserEditing.value = true

      if (editingTimeoutRef.value) {
        clearTimeout(editingTimeoutRef.value)
      }

      editingTimeoutRef.value = setTimeout(() => {
        isUserEditing.value = false
      }, USER_EDIT_TIMEOUT)
    }

    const handleKeyDown = (event) => {
      if ((event.ctrlKey || event.metaKey) && event.key === 's') {
        event.preventDefault()
        handleSave()
      }
    }

    watch(() => route.query.conversationId, async (newId, oldId) => {
      if (newId && newId !== oldId) {
        setConversationId(parseInt(newId))
        clearFileState()
        await loadFiles(parseInt(newId))
        if (files.value.length > 0) {
          const uploadedFile = files.value.find(f => f !== 'runner.py') || files.value[0]
          await loadFile(parseInt(newId), uploadedFile)
        }
        await initializeSession(newId)
        await syncCodeFromBackend()
      }
    })

    watch(currentFile, () => {
      isUserEditing.value = false
      if (editingTimeoutRef.value) {
        clearTimeout(editingTimeoutRef.value)
      }
    })

    watch(language, (newLang) => {
      console.log('Language changed to:', newLang === 'en' ? 'English' : 'Thai')
    })

    watch([code, currentFile, conversationId], async () => {
      if (conversationId.value && currentFile.value === 'runner.py' && code.value !== currentCode.value) {
        const timeSinceLastEdit = Date.now() - lastUserEdit.value
        if (timeSinceLastEdit > RUNNER_POLL_INTERVAL) {
          try {
            await loadFile(parseInt(conversationId.value), 'runner.py')
          } catch (error) {
            console.error('Failed to auto-refresh runner.py:', error)
          }
        }
      }
    })

    onMounted(async () => {
      if (!conversationId.value && user.value?.id) {
        try {
          const conversations = await conversationAPI.getByUser(user.value.id)
          if (conversations && conversations.length > 0) {
            const sorted = conversations.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
            router.replace({ query: { conversationId: sorted[0].id } })
            return
          }
        } catch (error) {
          console.error('Failed to load recent conversation:', error)
        }
      }

      if (conversationId.value) {
        setConversationId(parseInt(conversationId.value))
        await loadFiles(parseInt(conversationId.value))

        if (files.value.length > 0) {
          const uploadedFile = files.value.find(f => f !== 'runner.py') || files.value[0]
          await loadFile(parseInt(conversationId.value), uploadedFile)
        }

        await initializeSession(conversationId.value)
        await syncCodeFromBackend()
      }

      const greetOnInteraction = () => {
        if (!hasGreeted.value && conversationId.value) {
          hasGreeted.value = true
          voiceService.enableAudioContext()
          voiceService.speak(getGreeting())
          document.removeEventListener('click', greetOnInteraction)
          document.removeEventListener('keydown', greetOnInteraction)
        }
      }

      if (conversationId.value) {
        document.addEventListener('click', greetOnInteraction)
        document.addEventListener('keydown', greetOnInteraction)
      }

      document.addEventListener('keydown', handleKeyDown)

      if (conversationId.value && currentFile.value === 'runner.py') {
        pollIntervalId = setInterval(async () => {
          try {
            const timeSinceLastEdit = Date.now() - lastUserEdit.value
            if (timeSinceLastEdit < USER_EDIT_DEBOUNCE) return

            const response = await fileAPI.getFile(parseInt(conversationId.value), 'runner.py')
            if (response.code !== currentCode.value && !isUserEditing.value) {
              isRefreshing.value = true
              setCurrentCode(response.code)
              setCode(response.code)

              refreshNotification.value = 'File updated with new commands'
              setTimeout(() => isRefreshing.value = false, REFRESH_INDICATOR_DURATION)
              setTimeout(() => refreshNotification.value = null, REFRESH_NOTIFICATION_DURATION)
            }
          } catch (error) {
            console.error('Failed to poll for runner.py changes:', error)
          }
        }, RUNNER_POLL_INTERVAL)
      }
    })

    onUnmounted(() => {
      if (editingTimeoutRef.value) {
        clearTimeout(editingTimeoutRef.value)
      }
      if (pollIntervalId) {
        clearInterval(pollIntervalId)
      }
      document.removeEventListener('keydown', handleKeyDown)
    })

    return {
      conversationId,
      message,
      messages,
      output,
      isRunning,
      isTextMode,
      isRecording,
      isTranscribing,
      isProcessingCommand,
      editorRef,
      isSaving,
      isRefreshing,
      refreshNotification,
      user,
      currentFile,
      currentCode,
      isOutputExpanded,
      showSuccessDialog,
      successDialogMessage,
      language,
      ttsEnabled,
      t,
      appName,
      appIcon,
      appType,
      handleSend,
      handleSave,
      handleUndo,
      handleRedo,
      handleRun,
      setOutputMode,
      toggleOutputExpand,
      handleMicClick,
      handleEditorChange,
      handleInsertMethod,
      handleSelectFile,
      clearOutput,
      hideSuccessDialog
    }
  }
}
</script>

<style scoped>
.main-content {
  margin-left: var(--sidebar-total);
  margin-top: var(--toolbar-height);
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--color-bg);
  height: calc(100vh - var(--toolbar-height));
  max-height: calc(100vh - var(--toolbar-height));
  overflow: hidden;
}

.workspace {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
  height: calc(100vh - 80px);
  max-height: calc(100vh - 80px);
}

.workspace__container {
  display: flex;
  gap: 16px;
  padding: 20px;
  height: 100%;
  max-height: 100%;
  overflow: hidden;
  box-sizing: border-box;
  background: transparent;
  flex: 1;
  min-height: 0;
}

.workspace__code-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
  min-height: 0;
  max-height: 100%;
  overflow: hidden;
}

@media (max-width: 768px) {
  .main-content {
    margin-left: 0;
  }

  .workspace__container {
    flex-direction: column;
    padding: 16px;
    height: calc(100vh - 20px);
  }
}
</style>
