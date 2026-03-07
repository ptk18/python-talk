<template>
  <UnifiedLayout
    :app-id="appId"
    :app-name="appName || t.turtlePlayground.pageTitle"
    :app-icon="appIcon"
    app-type="turtle"
    @insert-method="handleInsertMethod"
  >
    <!-- Editor Column -->
    <template #editor>
      <CodeEditorPanel
        ref="editorRef"
        :code="codeContent"
        :show-file-info="false"
        @save="handleSave"
        @undo="handleUndo"
        @redo="handleRedo"
        @run="handleRunCode"
        @change="handleCodeUpdate"
      />
    </template>

    <!-- Debug Panel -->
    <template #debug>
      <ParserDebugPanel :data="parserDebug" />
    </template>

    <!-- Output Column -->
    <template #output>
      <EnhancedOutputPanel
        :output="textOutput"
        :stream-frame="streamFrame"
        :command-history="commandHistory"
        :active-tab="activeTab"
        graphic-label="Turtle Graphics Stream"
        :graphic-placeholder="'Waiting for turtle stream...'"
        @set-tab="activeTab = $event"
      />
    </template>

    <!-- Command Input -->
    <template #command>
      <CommandInput
        v-model="commandText"
        :placeholder="language === 'th' ? 'เช่น forward(100) หรือ พูดคำสั่ง...' : 'e.g., forward(100) or speak a command...'"
        :is-recording="isRecording"
        :is-processing="isProcessingCommand"
        @submit="handleRunCommand"
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

      <transition name="alert-slide">
        <div v-if="showAlert" :class="['turtle-alert', `turtle-alert--${alertType}`]">
          <span class="turtle-alert__text">{{ alertMessage }}</span>
          <button class="turtle-alert__close" @click="showAlert = false">&times;</button>
        </div>
      </transition>
    </template>
  </UnifiedLayout>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import UnifiedLayout from '@/shared/components/UnifiedLayout.vue'
import CodeEditorPanel from '@/features/codespace/components/CodeEditorPanel.vue'
import EnhancedOutputPanel from '@/shared/components/EnhancedOutputPanel.vue'
import CommandInput from '@/shared/components/CommandInput.vue'
import StatusBar from '@/features/codespace/components/StatusBar.vue'
import ParserDebugPanel from '@/shared/components/ParserDebugPanel.vue'
import { useLanguage, useTTS, voiceService, executeAPI } from '@py-talk/shared'
import { useTranslations } from '@/utils/translations'
import { useTurtleStream } from '@/shared/composables/useTurtleStream'
import { useUnifiedCommand } from '@/shared/composables/useUnifiedCommand'

export default {
  name: 'TurtlePlayground',
  components: {
    UnifiedLayout,
    CodeEditorPanel,
    EnhancedOutputPanel,
    CommandInput,
    StatusBar,
    ParserDebugPanel
  },
  setup() {
    const route = useRoute()
    const { language } = useLanguage()
    const { ttsEnabled } = useTTS()
    const t = computed(() => useTranslations(language.value))

    // App state
    const appId = computed(() => route.params.appId)
    const appName = ref('')
    const appIcon = ref(null)

    // Editor state
    const editorRef = ref(null)
    const codeContent = ref('import turtle\n\n')
    const commandText = ref('')

    // Output state
    const activeTab = ref('history')
    const isOutputExpanded = ref(false)
    const textOutput = ref('')

    // Voice state
    const isRecording = ref(false)
    const isTranscribing = ref(false)
    const mediaRecorder = ref(null)
    const audioChunks = ref([])

    // Alert state
    const alertMessage = ref('')
    const alertType = ref('success')
    const showAlert = ref(false)
    let alertTimeout = null

    // Auto-save state
    let saveTimeout = null

    // Composables
    const { streamFrame, connectStream, disconnectStream, startRemoteTurtleSession } = useTurtleStream()
    const { commandHistory, isProcessingCommand, parserDebug, processCommand, clearHistory } = useUnifiedCommand()

    const showAlertBox = (message, type = 'success', duration = 3500) => {
      if (alertTimeout) clearTimeout(alertTimeout)
      alertMessage.value = message
      alertType.value = type
      showAlert.value = true
      alertTimeout = setTimeout(() => { showAlert.value = false }, duration)
    }

    // --- Save logic ---
    const saveAppData = async (code) => {
      if (!appId.value) return
      try {
        const response = await fetch(
          `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/save_runner_code`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              conversation_id: Number(appId.value),
              code: code
            }),
          }
        )
        if (!response.ok) {
          console.warn('[TurtlePlayground] save_runner_code failed')
        }
      } catch (err) {
        console.warn('[TurtlePlayground] Failed to auto-save runner:', err)
      }
    }

    const handleCodeUpdate = (newCode) => {
      codeContent.value = newCode
      if (saveTimeout) clearTimeout(saveTimeout)
      saveTimeout = setTimeout(() => {
        saveAppData(newCode)
      }, 2000)
    }

    const handleSave = () => {
      saveAppData(codeContent.value)
      voiceService.speak('Saved!')
    }

    const handleInsertMethod = (methodCall) => {
      commandText.value = methodCall
    }

    // --- Editor actions ---
    const handleUndo = async () => {
      if (!appId.value) return
      try {
        const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
        const undoRes = await fetch(`${baseUrl}/api/undo_last`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ conversation_id: Number(appId.value) }),
        })
        const undoData = await undoRes.json()

        if (!undoRes.ok || !undoData?.success) {
          const msg = undoData?.message || 'Nothing to undo'
          showAlertBox(msg, 'info')
          voiceService.speak('Nothing to undo')
          return
        }

        const codeRes = await fetch(`${baseUrl}/api/get_runner_code?conversation_id=${Number(appId.value)}`)
        if (!codeRes.ok) throw new Error('Failed to load runner after undo')
        const codeData = await codeRes.json()
        codeContent.value = codeData?.code || ''

        await startRemoteTurtleSession(appId.value, codeContent.value)
        showAlertBox('Undo success', 'success')
        voiceService.speak('Undo')
      } catch (e) {
        showAlertBox(e?.message || 'Undo failed', 'error')
        voiceService.speak('Undo failed')
      }
    }

    const handleRedo = () => {
      editorRef.value?.redo()
    }

    const handleRunCode = async () => {
      if (!appId.value) return
      await saveAppData(codeContent.value)
      await startRemoteTurtleSession(appId.value, codeContent.value)
      showAlertBox('Code executed', 'success')
      voiceService.speak('Running turtle code')
    }

    const appendToCodeEditor = (command, comment = null) => {
      const newLine = comment ? `\n# ${comment}\n${command}` : `\n${command}`
      codeContent.value += newLine
      if (saveTimeout) clearTimeout(saveTimeout)
      saveTimeout = setTimeout(() => {
        saveAppData(codeContent.value)
      }, 2000)
    }

    // --- Command handling ---
    const isMethodCallSyntax = (s) => /^[a-zA-Z_]\w*\s*\(.*\)\s*$/.test(s)

    const handleRunCommand = async (cmdText) => {
      const cmd = cmdText || commandText.value.trim()
      if (!cmd || isProcessingCommand.value) return

      // Direct method call syntax
      if (isMethodCallSyntax(cmd)) {
        const s = cmd.trim()
        const isAssignment = /^[a-zA-Z_]\w*\s*=/.test(s)
        const isAlreadyTargeted = /^[a-zA-Z_]\w*\./.test(s)

        if (isAssignment || isAlreadyTargeted) {
          appendToCodeEditor(s)
          commandText.value = ''
          await startRemoteTurtleSession(appId.value, codeContent.value)
          return
        }

        showAlertBox("Please create/select a turtle first (e.g., 'create turtle call t1') or type a targeted call like t1.forward(100).", 'error')
        return
      }

      // Natural language command
      const res = await processCommand(appId.value, cmd, language.value, { mode: 'turtle' })

      if (res?.success) {
        const codeLines = res.executables.map(x => String(x).trim())
        appendToCodeEditor(codeLines.join('\n'), cmd)
        showAlertBox(codeLines.join(' | '), 'success')

        commandText.value = ''
        await startRemoteTurtleSession(appId.value, codeContent.value)
      } else {
        showAlertBox(res?.error || 'Command failed', 'error')
      }
    }

    // --- Voice handling ---
    const handleMicClick = async () => {
      voiceService.enableAudioContext()

      if (!isRecording.value) {
        try {
          voiceService.speak('Listening')
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
          const recorder = new MediaRecorder(stream)
          audioChunks.value = []

          recorder.ondataavailable = (e) => audioChunks.value.push(e.data)

          recorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks.value, { type: 'audio/webm' })
            const audioFile = new File([audioBlob], `recording_${Date.now()}.webm`, { type: 'audio/webm' })
            stream.getTracks().forEach(track => track.stop())

            isTranscribing.value = true
            try {
              const result = await voiceService.transcribe(audioFile, language.value)
              const transcribedText = result.text || ''

              if (transcribedText && !transcribedText.includes('[Error')) {
                commandText.value = transcribedText
                isTranscribing.value = false
                await handleRunCommand(transcribedText)
              } else {
                showAlertBox(
                  language.value === 'th'
                    ? 'แปลงเสียงไม่สำเร็จ กรุณาลองอีกครั้ง'
                    : 'Transcription failed. Please try again.',
                  'error'
                )
                voiceService.speak('Transcription failed. Please try again.')
                isTranscribing.value = false
              }
            } catch (err) {
              showAlertBox(err.message, 'error')
              voiceService.speak('Transcription error. Please try again.')
              isTranscribing.value = false
            }
          }

          recorder.start()
          mediaRecorder.value = recorder
          isRecording.value = true
        } catch (err) {
          voiceService.speak('Microphone access denied')
        }
      } else {
        if (mediaRecorder.value && mediaRecorder.value.state !== 'inactive') {
          mediaRecorder.value.stop()
        }
        isRecording.value = false
      }
    }

    // --- Clear / Reset ---
    const handleClear = async () => {
      if (!appId.value) return
      try {
        const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
        const res = await fetch(
          `${baseUrl}/api/reset_runner?conversation_id=${Number(appId.value)}`,
          { method: 'POST' }
        )
        if (!res.ok) throw new Error('Failed to reset runner')

        const codeRes = await fetch(`${baseUrl}/api/get_runner_code?conversation_id=${Number(appId.value)}`)
        const codeData = await codeRes.json()
        codeContent.value = codeData?.code || 'import turtle\n\n'

        await startRemoteTurtleSession(appId.value, codeContent.value)
        textOutput.value = ''
        clearHistory()

        const msg = t.value.turtlePlayground.canvasCleared || 'Canvas cleared'
        showAlertBox(msg, 'success')
        voiceService.speak('Canvas cleared')
      } catch (err) {
        showAlertBox('Failed to clear canvas', 'error')
      }
    }

    // --- Load app data ---
    const loadAppData = async () => {
      if (!appId.value) return
      try {
        const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/conversations/${appId.value}/single`)
        if (response.ok) {
          const data = await response.json()
          appName.value = data.title || ''
          appIcon.value = data.app_image || null

          try {
            const runner = await executeAPI.getRunnerCode(appId.value)
            codeContent.value = runner.code
          } catch (e) {
            console.warn('[TurtlePlayground] runner not found, initializing session...')
            try {
              await executeAPI.ensureSessionInitialized(appId.value)
              const runner = await executeAPI.getRunnerCode(appId.value)
              codeContent.value = runner.code
            } catch (e2) {
              console.warn('[TurtlePlayground] Still no runner after init, using default')
            }
          }
        }
      } catch (err) {
        console.warn('[TurtlePlayground] Failed to load app data:', err)
      }
    }

    // --- Lifecycle ---
    onMounted(async () => {
      if (!appId.value) {
        console.error('appId missing')
        return
      }

      await loadAppData()
      connectStream(appId.value)
      await startRemoteTurtleSession(appId.value, codeContent.value)
    })

    onUnmounted(() => {
      disconnectStream()
      if (saveTimeout) clearTimeout(saveTimeout)
      if (alertTimeout) clearTimeout(alertTimeout)
    })

    return {
      t,
      language,
      ttsEnabled,
      appId,
      appName,
      appIcon,
      editorRef,
      codeContent,
      commandText,
      activeTab,
      isOutputExpanded,
      textOutput,
      streamFrame,
      commandHistory,
      parserDebug,
      isRecording,
      isTranscribing,
      isProcessingCommand,
      showAlert,
      alertMessage,
      alertType,
      handleCodeUpdate,
      handleSave,
      handleInsertMethod,
      handleUndo,
      handleRedo,
      handleRunCode,
      handleRunCommand,
      handleMicClick,
      handleClear
    }
  }
}
</script>

<style scoped>
/* Alert Box */
.turtle-alert {
  position: fixed;
  top: 80px;
  right: 20px;
  z-index: 1600;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-radius: 8px;
  font-family: var(--font-family, 'Jaldi', sans-serif);
  font-size: 14px;
  font-weight: 500;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  max-width: 400px;
}

.turtle-alert--success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.turtle-alert--error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.turtle-alert--info {
  background: #d1ecf1;
  color: #0c5460;
  border: 1px solid #bee5eb;
}

.turtle-alert__text {
  flex: 1;
  line-height: 1.4;
}

.turtle-alert__close {
  background: transparent;
  border: none;
  padding: 4px 8px;
  cursor: pointer;
  opacity: 0.6;
  font-size: 18px;
  line-height: 1;
  color: inherit;
  transition: opacity 0.2s;
}

.turtle-alert__close:hover {
  opacity: 1;
}

/* Alert animation */
.alert-slide-enter-active {
  animation: alertSlideIn 0.3s ease-out;
}

.alert-slide-leave-active {
  animation: alertSlideOut 0.3s ease-in;
}

@keyframes alertSlideIn {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

@keyframes alertSlideOut {
  from { transform: translateX(0); opacity: 1; }
  to { transform: translateX(100%); opacity: 0; }
}
</style>
