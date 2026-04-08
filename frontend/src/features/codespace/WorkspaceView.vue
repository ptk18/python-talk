<!-- frontend/src/features/codespace/WorkspaceView.vue -->
<template>
  <UnifiedLayout
    :app-id="conversationId"
    :app-name="appName"
    :app-icon="appIcon"
    :app-type="appType"
    :current-file="currentFile"
    @insert-method="handleInsertMethod"
    @select-file="handleSelectFile"
  >
    <!-- Editor Column -->
    <template #editor>
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
        :show-file-info="true"
        @save="handleSave"
        @undo="handleUndo"

        @run="handleRun"
        @change="handleEditorChange"
      />
    </template>

    <!-- Debug Panel -->
    <template #debug>
      <ParserDebugPanel :data="parserDebug" />
    </template>

    <!-- Output Column -->
    <template #output>
      <EnhancedOutputPanel
        :output="output"
        :stream-frame="streamFrame"
        :command-history="displayHistory"
        :active-tab="activeTab"
        :terminal-placeholder="t.workspace.outputWillAppear"
        :graphic-label="t.workspace.turtleGraphicsStream"
        @set-tab="activeTab = $event"
      />
    </template>

    <!-- Command Input -->
    <template #command>
      <CommandInput
        v-model="commandText"
        :placeholder="t.workspace.typeYourMessage"
        :is-recording="isRecording"
        :is-processing="isProcessingCommand"
        @submit="handleSend"
        @mic-click="handleMicClick"
      />
    </template>

    <!-- Overlays -->
    <template #overlays>
      <StatusBar
        :is-transcribing="isTranscribing"
        :is-processing="isProcessingCommand"
        :language="language"
      />

    </template>
  </UnifiedLayout>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import UnifiedLayout from '@/shared/components/UnifiedLayout.vue'
import CodeEditorPanel from './components/CodeEditorPanel.vue'
import EnhancedOutputPanel from '@/shared/components/EnhancedOutputPanel.vue'
import CommandInput from '@/shared/components/CommandInput.vue'
import StatusBar from './components/StatusBar.vue'
import SuccessDialog from './components/SuccessDialog.vue'
import ParserDebugPanel from '@/shared/components/ParserDebugPanel.vue'
import { conversationAPI, fileAPI, analyzeAPI, useAuth, useLanguage, useTTS, voiceService } from '@py-talk/shared'
import { useCode } from './composables/useCode'
import { useFile } from './composables/useFile'
import { useCodeExecution } from './composables/useCodeExecution'
import { useVoiceRecording } from './composables/useVoiceRecording'
import { useWorkspaceSession } from './composables/useWorkspaceSession'
import { useUnifiedCommand } from '@/shared/composables/useUnifiedCommand'
import { useTurtleStream } from '@/shared/composables/useTurtleStream'
import { useTranslations } from '@/utils/translations'
import { getGreeting } from '@/shared/utils/formatters'
import { RUNNER_POLL_INTERVAL, USER_EDIT_DEBOUNCE, USER_EDIT_TIMEOUT, REFRESH_INDICATOR_DURATION, REFRESH_NOTIFICATION_DURATION } from './config/constants'
import { SUCCESS_DIALOG_DURATION } from './config/constants'
import { nextTick } from 'vue'

export default {
  name: 'Workspace',
  components: {
    UnifiedLayout,
    CodeEditorPanel,
    EnhancedOutputPanel,
    CommandInput,
    StatusBar,
    SuccessDialog,
    ParserDebugPanel
  },
  setup() {
    const route = useRoute()
    const router = useRouter()
    const { user } = useAuth()
    const { language } = useLanguage()
    const { ttsEnabled } = useTTS()
    const t = computed(() => useTranslations(language.value))

    const conversationId = computed(() => route.query.conversationId)
    const commandText = ref('')
    const editorRef = ref(null)
    const isSaving = ref(false)
    const isRefreshing = ref(false)
    const refreshNotification = ref(null)
    const lastUserEdit = ref(0)
    const isUserEditing = ref(false)
    const editingTimeoutRef = ref(null)
    const hasGreeted = ref(false)
    let pollIntervalId = null

    // Output state
    const activeTab = ref('history')
    const isOutputExpanded = ref(false)

    // Success dialog
    const showSuccessDialog = ref(false)
    const successDialogMessage = ref('')

    // Composables
    const { code, setCode, syncCodeFromBackend, setConversationId } = useCode()
    const { currentFile, currentCode, files, setCurrentCode, loadFiles, loadFile, saveFile, clearFileState } = useFile()
    const { isRecording, isTranscribing, handleMicClick: micClick } = useVoiceRecording(language)
    const { messages, appName, appIcon, appType, initializeSession, fetchMessages, fetchAvailableMethods, updateMessages } = useWorkspaceSession()
    const { output, isRunning, handleRun: runCode, clearOutput } = useCodeExecution()
    const { commandHistory, isProcessingCommand, parserDebug, processCommand, clearHistory } = useUnifiedCommand()
    const { streamFrame, connectStream, disconnectStream } = useTurtleStream()

    const displayHistory = computed(() =>
      (messages.value || []).map(msg => ({
        id: msg.id,
        text: msg.content || '',
        translatedText: '',
        timestamp: msg.timestamp,
        status: msg.sender === 'system' ? 'success' : 'info',
        sender: msg.sender,
        executables: [],
        error: null
      }))
    )

    const handleMicClick = () => {
      micClick((transcribedText) => {
        commandText.value = transcribedText
        // Auto-send after transcription
        if (transcribedText && !transcribedText.includes('[Error')) {
          handleSend(transcribedText)
        }
      })
    }

    const handleSend = async (msgText) => {
      const text = msgText || commandText.value.trim()
      if (!text || !conversationId.value) return
      commandText.value = ''

      const res = await processCommand(
        conversationId.value,
        text,
        language.value,
        {
          mode: 'codespace',
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

      if (res?.success) {
        const commandCount = res.executables.length
        successDialogMessage.value = commandCount > 1
          ? `${commandCount} commands executed successfully.`
          : 'Command executed successfully.'
        showSuccessDialog.value = true
        setTimeout(() => { showSuccessDialog.value = false }, SUCCESS_DIALOG_DURATION)
      }
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

          voiceService.speak('All set!')
        } else {
          voiceService.speak('Saved!')
        }

        lastUserEdit.value = 0
        isUserEditing.value = false
        if (editingTimeoutRef.value) {
          clearTimeout(editingTimeoutRef.value)
        }
      } catch (err) {
        console.error('Failed to save code:', err)
        voiceService.speak('Save failed.')
      } finally {
        isSaving.value = false
      }
    }

    const handleUndo = async () => {
      if (!conversationId.value) return

      try {
        const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

        if (currentFile.value === 'runner.py') {
          const undoRes = await fetch(`${baseUrl}/api/undo_last`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              conversation_id: Number(conversationId.value)
            })
          })

          const undoData = await undoRes.json()

          if (!undoRes.ok || !undoData?.success) {
            throw new Error(undoData?.message || 'Undo failed')
          }

          await loadFile(parseInt(conversationId.value), 'runner.py')
          await syncCodeFromBackend()
          voiceService.speak('Undo')
          return
        }

        if (!editorRef.value || !currentFile.value) return

        const beforeCode = currentCode.value

        editorRef.value?.undo?.()
        await nextTick()

        const afterCode = editorRef.value?.getValue
          ? editorRef.value.getValue()
          : currentCode.value

        if (afterCode === beforeCode) return

        setCurrentCode(afterCode)
        await saveFile(parseInt(conversationId.value), currentFile.value, afterCode)

        voiceService.speak('Undo')
      } catch (err) {
        console.error('Undo failed:', err)
        voiceService.speak('Undo failed')
      }
    }

    const handleRun = async () => {
      await runCode(conversationId.value, appType.value !== 'turtle')
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

    const handleClearOutput = () => {
      clearOutput()
      clearHistory()
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
      disconnectStream()
    })

    return {
      conversationId,
      commandText,
      output,
      isRunning,
      isRecording,
      isTranscribing,
      isProcessingCommand,
      editorRef,
      isSaving,
      isRefreshing,
      refreshNotification,
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
      activeTab,
      streamFrame,
      commandHistory,
      parserDebug,
      displayHistory,
      handleSend,
      handleSave,
      handleUndo,
      handleRun,
      handleMicClick,
      handleEditorChange,
      handleInsertMethod,
      handleSelectFile,
      handleClearOutput
    }
  }
}
</script>

<style scoped>
/* No additional styles needed — UnifiedLayout handles the layout */
</style>
