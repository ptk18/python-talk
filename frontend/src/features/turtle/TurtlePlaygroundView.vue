<!-- frontend/src/features/turtle/TurtlePlaygroundView.vue -->
<template>
  <UnifiedLayout
    :app-id="appId"
    :app-name="appName || t.turtlePlayground.pageTitle"
    :app-icon="appIcon"
    app-type="turtle"
    @insert-method="handleInsertMethod"
  >
    <template #editor>
      <CodeEditorPanel
        ref="editorRef"
        :code="codeContent"
        :show-file-info="false"
        @save="handleSave"
        @undo="handleUndo"

        @run="handleRunCode"
        @change="handleCodeUpdate"
      />
    </template>

    <template #debug>
      <ParserDebugPanel :data="parserDebug" />
    </template>

    <template #output>
      <EnhancedOutputPanel
        :output="textOutput"
        :stream-frame="streamFrame"
        :command-history="displayHistory"
        :active-tab="activeTab"
        graphic-label="Turtle Graphics Stream"
        :graphic-placeholder="'Waiting for turtle stream...'"
        @set-tab="activeTab = $event"
        @clear-history="messageAPI.deleteByConversation(appId).then(() => messages = [])"
      />
    </template>

    <template #command>
      <CommandInput
        v-model="commandText"
        :placeholder="language === 'th'
          ? 'เช่น t1.forward(100) หรือ พูดคำสั่ง...'
          : 'e.g., t1.forward(100) or speak a command...'"
        :is-recording="isRecording"
        :is-processing="isProcessingCommand"
        @submit="handleRunCommand"
        @mic-click="handleMicClick"
      />
    </template>

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
import { useLanguage, useTTS, voiceService, executeAPI, messageAPI, conversationAPI, analyzeAPI } from '@py-talk/shared'
import { useTranslations } from '@/utils/translations'
import { useUnifiedCommand } from '@/shared/composables/useUnifiedCommand'

const PI_API_BASE_URL = import.meta.env.VITE_STREAM_DEVICE_BASE_URL || 'https://161.246.5.67:8001'
const STREAM_WS_BASE_URL = import.meta.env.VITE_STREAM_WS_BASE_URL || 'wss://161.246.5.67:443'

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
    const messages = ref([])
    const availableMethods = ref(null)
    const appName = ref('Turtle Playground')
    const appIcon = ref(null)

    const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms))

    const route = useRoute()
    const { language } = useLanguage()
    const { ttsEnabled } = useTTS()
    const t = computed(() => useTranslations(language.value))
    const {
      commandHistory,
      isProcessingCommand,
      parserDebug,
      processCommand,
      clearHistory
    } = useUnifiedCommand()

    const fetchMessages = async (conversationId) => {
      if (!conversationId) return
      try {
        const msgs = await messageAPI.getByConversation(parseInt(conversationId))
        messages.value = msgs
        console.log('messages', messages.value)
        console.log('displayHistory', displayHistory.value)
      } catch (err) {
        console.error('Failed to fetch messages:', err)
      }
    }

    const fetchAvailableMethods = async (conversationId) => {
      if (!conversationId) return
      try {
        const methods = await conversationAPI.getAvailableMethods(parseInt(conversationId))
        availableMethods.value = methods
      } catch (err) {
        console.error('Failed to fetch available methods:', err)
      }
    }

    const fetchAppDetails = async (conversationId) => {
      if (!conversationId) return
      try {
        const appDetails = await conversationAPI.getSingleConversation(parseInt(conversationId))
        if (appDetails) {
          appName.value = appDetails.title || 'Turtle Playground'
          appIcon.value = appDetails.app_image || null
        }
      } catch (err) {
        console.error('Failed to fetch app details:', err)
      }
    }

    const initializeSession = async (conversationId) => {
      if (!conversationId) return
      try {
        await executeAPI.ensureSessionInitialized(parseInt(conversationId))
        await fetchMessages(conversationId)
        await fetchAvailableMethods(conversationId)
        await fetchAppDetails(conversationId)

        // Prewarm pipeline + domain caches to avoid cold-start on first voice command
        analyzeAPI.prewarmPipeline(parseInt(conversationId))
          .catch(err => console.warn('Pipeline pre-warm failed:', err))
      } catch (err) {
        console.error('Failed to initialize session:', err)
      }
    }

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

    const fullRestartAndReplay = async () => {
      try {
        await killPiTurtleSession(appId.value)
      } catch (err) {
        console.warn('[Turtle] kill before replay failed:', err)
      }

      await startPiTurtleSession(appId.value)

      const lines = extractExecutableLines(codeContent.value)
      for (const line of lines) {
        await sendPiTurtleCommand(appId.value, line)
        await sleep(80)
      }
    }

    const streamSocket = ref(null)
    const streamFrame = ref(null)
    const isStreaming = ref(false)

    let reconnectTimer = null
    let manuallyClosed = false
    let currentChannelId = null

    const connectStream = (channelId) => {
      if (!channelId) return

      currentChannelId = channelId

      if (
        streamSocket.value &&
        (
          streamSocket.value.readyState === WebSocket.OPEN ||
          streamSocket.value.readyState === WebSocket.CONNECTING
        )
      ) {
        console.log('[STREAM] already connected/connecting')
        return
      }

      const wsUrl = `wss://161.246.5.67:443/subscribe/${channelId}`
      console.log('[STREAM] connecting to', wsUrl)

      manuallyClosed = false
      const ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        console.log('[STREAM] connected')
        isStreaming.value = true
        if (reconnectTimer) {
          clearTimeout(reconnectTimer)
          reconnectTimer = null
        }
      }

      ws.onmessage = (event) => {
        streamFrame.value = `data:image/jpeg;base64,${event.data}`
      }

      ws.onerror = (err) => {
        console.warn('[STREAM] error', err)
      }

      ws.onclose = () => {
        console.warn('[STREAM] closed')
        isStreaming.value = false
        streamSocket.value = null

        if (!manuallyClosed && currentChannelId) {
          reconnectTimer = setTimeout(() => {
            console.log('[STREAM] reconnecting...')
            connectStream(currentChannelId)
          }, 2000)
        }
      }

      streamSocket.value = ws
    }

    const disconnectStream = () => {
      manuallyClosed = true

      if (reconnectTimer) {
        clearTimeout(reconnectTimer)
        reconnectTimer = null
      }

      if (streamSocket.value) {
        console.log('[STREAM] manual close')
        streamSocket.value.close()
        streamSocket.value = null
      }

      isStreaming.value = false
    }

    const startPiTurtleSession = async (appId) => {
      if (!appId) return null

      const res = await fetch(`${PI_API_BASE_URL}/start_turtle/${appId}`, {
        method: 'POST'
      })

      if (!res.ok) {
        const errText = await res.text()
        throw new Error(`Failed to start Pi turtle session: ${errText}`)
      }

      return await res.json()
    }

    const sendPiTurtleCommand = async (appId, command) => {
      if (!appId || !command) return null

      const url = new URL(`${PI_API_BASE_URL}/turtle_command/${appId}`)
      url.searchParams.set('command', command)

      const res = await fetch(url.toString(), {
        method: 'POST'
      })

      if (!res.ok) {
        const errText = await res.text()
        throw new Error(`Failed to send turtle command: ${errText}`)
      }

      return await res.json()
    }

    const refreshPiTurtleSession = async (appId) => {
      if (!appId) return null

      const res = await fetch(`${PI_API_BASE_URL}/start_turtle/${appId}`, {
        method: 'POST'
      })

      if (!res.ok) {
        const errText = await res.text()
        throw new Error(`Failed to refresh turtle session: ${errText}`)
      }

      return await res.json()
    }

    const killPiTurtleSession = async (appId) => {
      if (!appId) return null

      const res = await fetch(`${PI_API_BASE_URL}/kill/${appId}`, {
        method: 'POST'
      })

      if (res.status === 404) {
        return { status: 'not_running' }
      }

      if (!res.ok) {
        const errText = await res.text()
        throw new Error(`Failed to kill turtle session: ${errText}`)
      }

      return await res.json()
    }

    const appId = computed(() => route.params.appId)

    const editorRef = ref(null)
    const codeContent = ref('import turtle\n\n')
    const commandText = ref('')

    const activeTab = ref('graphic')
    const textOutput = ref('')

    const isRecording = ref(false)
    const isTranscribing = ref(false)
    const mediaRecorder = ref(null)
    const audioChunks = ref([])

    const alertMessage = ref('')
    const alertType = ref('success')
    const showAlert = ref(false)
    let alertTimeout = null

    let saveTimeout = null

    const showAlertBox = (message, type = 'success', duration = 3500) => {
      if (alertTimeout) clearTimeout(alertTimeout)
      alertMessage.value = message
      alertType.value = type
      showAlert.value = true
      alertTimeout = setTimeout(() => {
        showAlert.value = false
      }, duration)
    }

    const saveAppData = async (code) => {
      if (!appId.value) return

      const response = await fetch(
        `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/save_runner_code`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            conversation_id: Number(appId.value),
            code
          })
        }
      )

      if (!response.ok) {
        throw new Error('save_runner_code failed')
      }
    }

    const handleCodeUpdate = (newCode) => {
      codeContent.value = newCode

      if (saveTimeout) clearTimeout(saveTimeout)
      saveTimeout = setTimeout(async () => {
        try {
          await saveAppData(newCode)
        } catch (err) {
          console.warn('[TurtlePlayground] Failed to auto-save runner:', err)
        }
      }, 2000)
    }

    const handleSave = async () => {
      try {
        await saveAppData(codeContent.value)
        voiceService.speak('Saved!')
      } catch (err) {
        showAlertBox('Save failed', 'error')
      }
    }

    const handleInsertMethod = (methodCall) => {
      commandText.value = methodCall
    }

    const extractExecutableLines = (code) => {
      if (!code) return []

      return code
        .split('\n')
        .map(line => line.trim())
        .filter(line => {
          if (!line) return false
          if (line.startsWith('#')) return false
          if (line.startsWith('import ')) return false
          if (line.startsWith('from ')) return false
          if (line.includes('time.sleep(')) return false
          if (line.includes('done(')) return false
          if (line.includes('mainloop(')) return false
          if (line.includes('exitonclick(')) return false
          return true
        })
    }

    const getLatestExecutableLine = (code) => {
      const lines = extractExecutableLines(code)
      return lines.length ? lines[lines.length - 1] : null
    }

    const replayWholeRunnerToPi = async () => {
      const lines = extractExecutableLines(codeContent.value)

      for (const line of lines) {
        await sendPiTurtleCommand(appId.value, line, true)
        await sleep(180)
      }
    }

    const handleUndo = async () => {
      if (!appId.value) return

      try {
        const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
        const undoRes = await fetch(`${baseUrl}/api/undo_last`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ conversation_id: Number(appId.value) })
        })

        const undoData = await undoRes.json()

        if (!undoRes.ok || !undoData?.success) {
          const msg = undoData?.message || 'Nothing to undo'
          showAlertBox(msg, 'info')
          voiceService.speak('Nothing to undo')
          return
        }

        const codeRes = await fetch(
          `${baseUrl}/api/get_runner_code?conversation_id=${Number(appId.value)}`
        )

        if (!codeRes.ok) {
          throw new Error('Failed to load runner after undo')
        }

        const codeData = await codeRes.json()
        codeContent.value = codeData?.code || 'import turtle\n\n'

        await saveAppData(codeContent.value)
        await fullRestartAndReplay()
        await fetchMessages(appId.value)

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

    const isValueReturningTurtleCall = (line) => {
      const s = String(line || '').trim()
      const valueMethods = [
        'heading',
        'position',
        'pos',
        'xcor',
        'ycor',
        'isdown',
        'isvisible',
        'distance',
        'towards'
      ]

      const m1 = s.match(/^[A-Za-z_]\w*\.(\w+)\s*\(/)
      if (m1 && valueMethods.includes(m1[1])) return true

      const m2 = s.match(/^(\w+)\s*\(/)
      if (m2 && valueMethods.includes(m2[1])) return true

      return false
    }

    const normalizeTurtleLineForEditor = (line) => {
      const s = String(line || '').trim()
      if (!s) return s
      if (s.startsWith('print(')) return s
      if (isValueReturningTurtleCall(s)) return `print(${s})`
      return s
    }

    const handleRunCode = async () => {
      if (!appId.value) return

      try {
        await saveAppData(codeContent.value)
        await fullRestartAndReplay()
        await fetchMessages(appId.value)

        showAlertBox('Code executed', 'success')
        voiceService.speak('Running turtle code')
      } catch (err) {
        showAlertBox(err?.message || 'Run failed', 'error')
      }
    }

    const appendToCodeEditor = (command, comment = null) => {
      const newLine = comment ? `\n# ${comment}\n${command}` : `\n${command}`
      codeContent.value += newLine

      if (saveTimeout) clearTimeout(saveTimeout)
      saveTimeout = setTimeout(async () => {
        try {
          await saveAppData(codeContent.value)
        } catch (err) {
          console.warn('[TurtlePlayground] Failed to auto-save runner:', err)
        }
      }, 2000)
    }

    const detectDirectPythonCommand = (s) => {
      const text = s.trim()
      return {
        isAssignment: /^[a-zA-Z_]\w*\s*=/.test(text),
        isTargetedCall: /^[a-zA-Z_]\w*\./.test(text),
        isBareCall: /^[a-zA-Z_]\w*\s*\(.*\)\s*$/.test(text)
      }
    }

    const handleRunCommand = async () => {
      if (!commandText.value.trim() || isProcessingCommand.value) return

      const cmd = commandText.value.trim()
      commandText.value = ''
      const { isAssignment, isTargetedCall, isBareCall } = detectDirectPythonCommand(cmd)

      try {
        if (isAssignment || isTargetedCall) {
          const normalizedCmd = normalizeTurtleLineForEditor(cmd)
          appendToCodeEditor(normalizedCmd)
          commandText.value = ''

          await saveAppData(codeContent.value)

          const startData = await startPiTurtleSession(appId.value)
          if (startData?.status === 'started') {
            await replayWholeRunnerToPi()
          } else {
            await sendPiTurtleCommand(appId.value, normalizedCmd)
          }

          return
        }

        if (isBareCall) {
          showAlertBox(
            'Please use a targeted call like t1.forward(100), or create/select a turtle first.',
            'error'
          )
          return
        }

        const res = await processCommand(appId.value, cmd, language.value, {
          mode: 'turtle',
          onMessagesUpdate: (msgs) => { messages.value = msgs }
        })

        if (res?.success) {
          const codeLines = Array.isArray(res.executables)
            ? res.executables.map(x => String(x).trim()).filter(Boolean)
            : []

          if (!codeLines.length) {
            showAlertBox(res?.message || res?.suggestion_message || 'No executable code generated', 'info')
            return
          }

          const normalizedLines = codeLines.map(normalizeTurtleLineForEditor)
          appendToCodeEditor(normalizedLines.join('\n'), cmd)
          showAlertBox(codeLines.join(' | '), 'success')
          commandText.value = ''

          await saveAppData(codeContent.value)

          const startData = await startPiTurtleSession(appId.value)
          if (startData?.status === 'started') {
            await replayWholeRunnerToPi()
          } else {
            for (const line of normalizedLines) {
              await sendPiTurtleCommand(appId.value, line)
            }
          }
        } else {
          showAlertBox(res?.error || res?.suggestion_message || 'Command failed', 'error')
        }
      } catch (err) {
        showAlertBox(err?.message || 'Command failed', 'error')
      } finally {
        await fetchMessages(appId.value)
      }
    }

    const handleMicClick = async () => {
      voiceService.enableAudioContext()

      if (!isRecording.value) {
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
          const recorder = new MediaRecorder(stream)
          audioChunks.value = []

          recorder.ondataavailable = (e) => {
            audioChunks.value.push(e.data)
          }

          recorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks.value, { type: 'audio/webm' })
            const audioFile = new File([audioBlob], `recording_${Date.now()}.webm`, {
              type: 'audio/webm'
            })

            stream.getTracks().forEach(track => track.stop())

            isTranscribing.value = true
            try {
              const result = await voiceService.transcribe(audioFile, language.value)
              const transcribedText = result.text || ''

              if (transcribedText && !transcribedText.includes('[Error')) {
                commandText.value = transcribedText
                isTranscribing.value = false
                await handleRunCommand()
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
              showAlertBox(err.message || 'Transcription error', 'error')
              voiceService.speak('Transcription error. Please try again.')
              isTranscribing.value = false
            }
          }

          recorder.start()
          mediaRecorder.value = recorder
          isRecording.value = true
        } catch (err) {
          showAlertBox('Microphone access denied', 'error')
          voiceService.speak('Microphone access denied')
        }
      } else {
        if (mediaRecorder.value && mediaRecorder.value.state !== 'inactive') {
          mediaRecorder.value.stop()
        }
        isRecording.value = false
      }
    }

    const handleClear = async () => {
      if (!appId.value) return

      try {
        const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
        const res = await fetch(
          `${baseUrl}/api/reset_runner?conversation_id=${Number(appId.value)}`,
          { method: 'POST' }
        )

        if (!res.ok) {
          throw new Error('Failed to reset runner')
        }

        const codeRes = await fetch(
          `${baseUrl}/api/get_runner_code?conversation_id=${Number(appId.value)}`
        )
        const codeData = await codeRes.json()
        codeContent.value = codeData?.code || 'import turtle\n\n'

        await saveAppData(codeContent.value)
        await fullRestartAndReplay()
        await fetchMessages(appId.value)

        textOutput.value = ''
        clearHistory()

        const msg = t.value.turtlePlayground.canvasCleared || 'Canvas cleared'
        showAlertBox(msg, 'success')
        voiceService.speak('Canvas cleared')
      } catch (err) {
        showAlertBox(err?.message || 'Failed to clear canvas', 'error')
      }
    }

    const loadAppData = async () => {
      if (!appId.value) return

      try {
        const response = await fetch(
          `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/conversations/${appId.value}/single`
        )

        if (!response.ok) return

        const data = await response.json()
        appName.value = data.title || ''
        appIcon.value = data.app_image || null

        try {
          const runner = await executeAPI.getRunnerCode(appId.value)
          codeContent.value = runner.code || 'import turtle\n\n'
        } catch (e) {
          console.warn('[TurtlePlayground] runner not found, initializing session...')
          try {
            await executeAPI.ensureSessionInitialized(appId.value)
            const runner = await executeAPI.getRunnerCode(appId.value)
            codeContent.value = runner.code || 'import turtle\n\n'
          } catch (e2) {
            console.warn('[TurtlePlayground] Still no runner after init, using default')
            codeContent.value = 'import turtle\n\n'
          }
        }
      } catch (err) {
        console.warn('[TurtlePlayground] Failed to load app data:', err)
      }
    }

    onMounted(async () => {
      if (!appId.value) {
        console.error('appId missing')
        return
      }

      await initializeSession(appId.value)
      await loadAppData()
      connectStream(appId.value)

      try {
        await fullRestartAndReplay()
      } catch (err) {
        showAlertBox(err?.message || 'Failed to start turtle session', 'error')
      }
    })

    onUnmounted(async () => {
      try {
        await killPiTurtleSession(appId.value)
      } catch (err) {
        console.warn('[Turtle] kill on leave failed:', err)
      }

      disconnectStream()

      if (saveTimeout) {
        clearTimeout(saveTimeout)
        saveTimeout = null
      }

      if (alertTimeout) {
        clearTimeout(alertTimeout)
        alertTimeout = null
      }

      if (reconnectTimer) {
        clearTimeout(reconnectTimer)
        reconnectTimer = null
      }
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
      textOutput,
      streamFrame,
      isStreaming,
      commandHistory,
      parserDebug,
      isRecording,
      isTranscribing,
      isProcessingCommand,
      showAlert,
      alertMessage,
      alertType,
      messages,
      availableMethods,
      displayHistory,
      fetchMessages,
      initializeSession,
      handleCodeUpdate,
      handleSave,
      handleInsertMethod,
      handleUndo,
      handleRedo,
      handleRunCode,
      handleRunCommand,
      handleMicClick,
      handleClear,
      clearHistory,
      messageAPI
    }
  }
}
</script>