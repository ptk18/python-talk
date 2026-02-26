<template>
  <div class="app-container">
    <TopToolbar />
    <Sidebar />
    <AppSidebar
      :app-id="appId"
      :app-name="appName || t.turtlePlayground.pageTitle"
      :app-icon="appIcon"
      app-type="turtle"
      @insert-method="handleInsertMethod"
    />
    <main class="main-content">
      <div class="content-area">
    <div class="turtle-playground">
      <div class="turtle-playground__container">
        <!-- Left Column: Code Editor -->
        <div class="turtle-playground__left-column">
          <!-- Code Editor Section -->
          <section class="turtle-playground__code-panel turtle-playground__code-panel--full">
            <div class="turtle-playground__code-header">
              <div class="turtle-playground__code-title">
                <h3>{{ language === 'th' ? 'โค้ดเอดิเตอร์' : 'Code Editor' }}</h3>
                <span class="turtle-playground__code-hint">{{ language === 'th' ? 'คำสั่งเสียงจะถูกเพิ่มที่นี่อัตโนมัติ' : 'Voice commands will be appended here automatically' }}</span>
              </div>
              <div class="turtle-playground__code-actions">
                <button class="turtle-playground__icon-btn" @click="handleUndo" :title="language === 'th' ? 'ย้อนกลับ' : 'Undo'">
                  <img :src="undoIcon" alt="Undo" class="turtle-playground__icon-img" />
                </button>
                <button class="turtle-playground__icon-btn" @click="handleRedo" :title="language === 'th' ? 'ทำซ้ำ' : 'Redo'">
                  <img :src="redoIcon" alt="Redo" class="turtle-playground__icon-img" />
                </button>
              </div>
            </div>
            <div class="turtle-playground__code-editor">
              <MonacoEditor
                ref="monacoEditor"
                :code="codeContent"
                language="python"
                @update:code="handleCodeUpdate"
              />
            </div>
          </section>
        </div>

        <!-- Right Column: Canvas + Command Input -->
        <div class="turtle-playground__right-column">
          <!-- Canvas Section -->
          <section class="turtle-playground__canvas-panel">
            <div class="turtle-playground__canvas-header">
              <h3>{{ t.turtlePlayground.canvas }}</h3>
              <div class="turtle-playground__canvas-controls">
                <button class="turtle-playground__canvas-btn" @click="handleClear" :title="t.turtlePlayground.clearCanvas">
                  <img :src="clearIcon" alt="Clear" class="turtle-playground__canvas-icon" />
                </button>
                <button class="turtle-playground__canvas-btn" @click="handleReset" :title="t.turtlePlayground.resetTurtle">
                  <img :src="resetIcon" alt="Reset" class="turtle-playground__canvas-icon" />
                </button>
              </div>
            </div>
            <div class="turtle-playground__canvas-wrapper" ref="canvasWrapper">
              <!-- <canvas
                ref="turtleCanvas"
                width="600"
                height="450"
                class="turtle-playground__canvas"
              ></canvas>
              <div
                ref="turtleIndicator"
                class="turtle-playground__indicator"
              ></div> -->
              <!-- STREAM VIEWER -->
              <div class="turtle-playground__stream-wrapper">
                <img
                  v-if="streamFrame"
                  :src="streamFrame"
                  class="turtle-playground__stream"
                />
                <div v-else class="turtle-playground__stream-placeholder">
                  Waiting for turtle stream…
                </div>
              </div>
            </div>
          </section>

          <!-- Command Input Section (Simplified) -->
          <section class="turtle-playground__command-panel">
            <div class="turtle-playground__command-input-area">
              <div class="turtle-playground__input-row">
                <div
                  :class="['turtle-playground__mic', { 'turtle-playground__mic--recording': isRecording }]"
                  @click="handleMicClick"
                >
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
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
                <input
                  type="text"
                  class="turtle-playground__command-input"
                  :placeholder="language === 'th' ? 'เช่น forward(100) หรือ พูดคำสั่ง...' : 'e.g., forward(100) or speak a command...'"
                  v-model="commandText"
                  @keydown.enter.prevent="handleRunCommand"
                />
                <button
                  class="turtle-playground__run-btn"
                  @click="handleRunCommand"
                  :disabled="isProcessing"
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                    <path d="M5 3l14 9-14 9V3z" fill="currentColor"/>
                  </svg>
                </button>
              </div>
            </div>
          </section>
        </div>
      </div>

      <!-- Status Bars (Workspace style - top card) -->
      <div v-if="isTranscribing" class="turtle-playground__status-bar turtle-playground__status-bar--transcribing">
        <div class="turtle-playground__status-content">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="turtle-playground__status-spinner">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-dasharray="60" stroke-dashoffset="0">
              <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite"/>
            </circle>
          </svg>
          <span class="turtle-playground__status-text">{{ language === 'th' ? 'กำลังแปลงเสียงของคุณ...' : 'Transcribing your voice...' }}</span>
          <div class="turtle-playground__status-progress">
            <div class="turtle-playground__status-progress-bar"></div>
          </div>
        </div>
      </div>

      <div v-if="isProcessing" class="turtle-playground__status-bar turtle-playground__status-bar--processing">
        <div class="turtle-playground__status-content">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="turtle-playground__status-spinner">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-dasharray="60" stroke-dashoffset="0">
              <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite"/>
            </circle>
          </svg>
          <span class="turtle-playground__status-text">{{ language === 'th' ? 'กำลังประมวลผลและจับคู่คำสั่ง...' : 'Processing and mapping command...' }}</span>
          <div class="turtle-playground__status-progress">
            <div class="turtle-playground__status-progress-bar"></div>
          </div>
        </div>
      </div>

      <!-- Alert Box -->
      <transition name="alert-slide">
        <div v-if="showAlert" :class="['turtle-playground__alert', `turtle-playground__alert--${alertType}`]">
          <span class="turtle-playground__alert-text">{{ alertMessage }}</span>
          <button class="turtle-playground__alert-close" @click="showAlert = false">&times;</button>
        </div>
      </transition>
    </div>
      </div>
    </main>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue';
import { useRoute } from 'vue-router';
import TopToolbar from '@/shared/components/TopToolbar.vue';
import Sidebar from '@/shared/components/Sidebar.vue';
import AppSidebar from '@/shared/components/AppSidebar.vue';
import MonacoEditor from '@/shared/components/MonacoEditor.vue';
import { useLanguage, useTTS, voiceService, translateAPI, conversationAPI, analyzeAPI, executeAPI } from '@py-talk/shared';
import { useTranslations } from '@/utils/translations';
import { getGreeting } from '@/shared/utils/formatters';
// import { Turtle } from './lib/turtle';
import { parseTurtleCommand } from './lib/turtleCommandParser';
import undoIcon from '@/assets/R-undo.svg';
import redoIcon from '@/assets/R-redo.svg';
import clearIcon from '@/assets/T-clear.svg';
import resetIcon from '@/assets/T-reset.svg';

export default {
  name: 'TurtlePlayground',
  components: { TopToolbar, Sidebar, AppSidebar, MonacoEditor },
  setup() {

    const STREAM_DEVICE_BASE_URL="https://161.246.5.67:8001"
    const STREAM_WS_BASE_URL="wss://161.246.5.67:5050"

    const streamSocket = ref(null);
    const streamFrame = ref(null);
    const isStreaming = ref(false);

    let reconnectTimer = null;
    let manuallyClosed = false;

    const streamOutput = ref("");
    let ws = null;

    const route = useRoute();
    const { language } = useLanguage();
    const { ttsEnabled } = useTTS();
    const t = computed(() => useTranslations(language.value));

    // App-specific state
    const appId = computed(() => route.params.appId);
    const appName = ref('');
    const appIcon = ref(null);

    // Refs
    const turtleCanvas = ref(null);
    const turtleIndicator = ref(null);
    const canvasWrapper = ref(null);
    const monacoEditor = ref(null);
    const commandText = ref('');
    const codeContent = ref(`import turtle

t = turtle.Turtle()
`);
    const isRecording = ref(false);
    const isTranscribing = ref(false);
    const isProcessing = ref(false);
    const hasGreeted = ref(false);
    const mediaRecorder = ref(null);
    const audioChunks = ref([]);

    // Alert box state
    const alertMessage = ref('');
    const alertType = ref('success');
    const showAlert = ref(false);
    let alertTimeout = null;
    
    // Auto-save state
    let saveTimeout = null;

    const connectStream = (cid) => {
      if (!cid) return;

      // prevent duplicate connections
      if (streamSocket.value && streamSocket.value.readyState === WebSocket.OPEN) {
        console.log("[STREAM] already connected");
        return;
      }

      const wsUrl = `${STREAM_WS_BASE_URL}/subscribe/${cid}`;
      console.log("[STREAM] connecting to", wsUrl);

      manuallyClosed = false;

      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log("[STREAM] connected");
        isStreaming.value = true;
        clearTimeout(reconnectTimer);
      };

      ws.onmessage = (event) => {
        streamFrame.value = `data:image/jpeg;base64,${event.data}`;
      };

      ws.onerror = (err) => {
        console.warn("[STREAM] error", err);
      };

      ws.onclose = () => {
        console.warn("[STREAM] closed");
        isStreaming.value = false;
        streamSocket.value = null;

        // 🔁 auto-reconnect unless page is leaving
        if (!manuallyClosed) {
          reconnectTimer = setTimeout(() => {
            console.log("[STREAM] reconnecting...");
            connectStream(cid);
          }, 2000);
        }
      };

      streamSocket.value = ws;
    };


    const disconnectStream = () => {
      manuallyClosed = true;
      clearTimeout(reconnectTimer);

      if (streamSocket.value) {
        console.log("[STREAM] manual close");
        streamSocket.value.close();
        streamSocket.value = null;
      }
    };

    const startRemoteTurtleSession = async () => {
      if (!appId.value) return;

      const payload = {
        files: {
          "runner.py": codeContent.value
        }
      };

      const res = await fetch(
        `${STREAM_DEVICE_BASE_URL}/runturtle/${appId.value}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        }
      );

      if (!res.ok) {
        showAlertBox("Failed to start turtle session", "error");
        return;
      }

      console.log("[TURTLE] Pi turtle started");
    };

    // const runRemoteTurtle = async () => {
    //   if (!appId.value) return;

    //   // disconnectStream();
    //   streamFrame.value = null;

    //   // connect viewer FIRST
    //   connectStream(appId.value);

    //   // send code to Pi
    //   const payload = {
    //     files: {
    //       "runner.py": codeContent.value
    //     }
    //   };

    //   const res = await fetch(
    //     `${STREAM_DEVICE_BASE_URL}/runturtle/${appId.value}`,
    //     {
    //       method: "POST",
    //       headers: { "Content-Type": "application/json" },
    //       body: JSON.stringify(payload)
    //     }
    //   );

    //   if (!res.ok) {
    //     showAlertBox("Failed to start turtle stream", "error");
    //   }
    // };


    const showAlertBox = (message, type = 'success', duration = 3500) => {
      if (alertTimeout) clearTimeout(alertTimeout);
      alertMessage.value = message;
      alertType.value = type;
      showAlert.value = true;
      alertTimeout = setTimeout(() => { showAlert.value = false; }, duration);
    };

    // --- AUTO SAVE LOGIC START ---
    const saveAppData = async (code) => {
      if (!appId.value) return;

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
        );

        if (!response.ok) {
          console.warn('[TurtlePlayground] save_runner_code failed');
        }
      } catch (err) {
        console.warn('[TurtlePlayground] Failed to auto-save runner:', err);
      }
    };
    // --- AUTO SAVE LOGIC END ---

    const handleCodeUpdate = (newCode) => {
      codeContent.value = newCode;
      
      // Debounce save: wait 2 seconds after typing stops before saving
      if (saveTimeout) clearTimeout(saveTimeout);
      saveTimeout = setTimeout(() => {
        saveAppData(newCode);
      }, 2000);
    };

    // Handle method insertion from AppSidebar
    const handleInsertMethod = (methodCall) => {
      commandText.value = methodCall;
    };

    // Editor toolbar handlers
    const handleUndo = () => { monacoEditor.value?.undo(); };
    const handleRedo = () => { monacoEditor.value?.redo(); };

    const appendToCodeEditor = (command, comment = null) => {
      const newLine = comment ? `\n# ${comment}\n${command}` : `\n${command}`;
      codeContent.value += newLine;
      
      // Also trigger save when code is appended via commands
      if (saveTimeout) clearTimeout(saveTimeout);
      saveTimeout = setTimeout(() => {
        saveAppData(codeContent.value);
      }, 2000);
    };

    // Load app data if appId is provided
    const loadAppData = async () => {
      if (appId.value) {
        try {
          const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/conversations/${appId.value}/single`);
          if (response.ok) {
            const data = await response.json();
            appName.value = data.title || '';
            appIcon.value = data.app_image || null;
            // Load saved code if available
            // Load runner.py into editor (NOT conversation.code)
            try {
              const runner = await executeAPI.getRunnerCode(appId.value);
              codeContent.value = runner.code;
            } catch (e) {
              // runner.py not created yet -> keep default template
              console.warn('[TurtlePlayground] runner not found yet');
            }
          }
        } catch (err) {
          console.warn('[TurtlePlayground] Failed to load app data:', err);
        }
      }
    };

  onMounted(async () => {
    console.log("[MOUNT] appId =", appId.value);
    console.log("[MOUNT] route params =", route.params);

    if (!appId.value) {
      console.error("❌ appId missing");
      return;
    }

    // 1️⃣ load saved code + metadata
    await loadAppData();

    // 2️⃣ connect stream FIRST (viewer)
    connectStream(appId.value);

    // 3️⃣ start turtle session on Pi
    await startRemoteTurtleSession();

    console.log("[MOUNT] turtle session + stream initialized");
  });

    const processNaturalLanguageCommand = async (cmd, originalText = null) => {
      isProcessing.value = true;

      try {
        let commandForAnalysis = cmd;

        // 1) Translate Thai -> English for analysis
        if (language.value === 'th') {
          const translateResult = await translateAPI.translateToEnglish(cmd);
          commandForAnalysis = translateResult?.translated_text || cmd;
        }

        // 2) Call unified parser endpoint (codespace)
        const apiRes = await analyzeAPI.analyzeCommand(appId.value, commandForAnalysis);

        // Backend returns: { success: true, result: {...}, results: [{...}, ...] }
        const items = Array.isArray(apiRes?.results)
          ? apiRes.results
          : (apiRes?.result ? [apiRes.result] : []);

        // Collect executable strings from matched items
        const commands = items
          .map((x) => x?.executable)
          .filter(Boolean);

        // 3) If we got executables, append to editor + let Pi run it
        if (commands.length > 0) {
          const codeLines = commands.map((x) => `t.${x}`);
          appendToCodeEditor(codeLines.join('\n'), originalText || cmd);

          showAlertBox(commands.join(' | '), 'success');
          voiceService.speak(t.value.turtlePlayground.commandExecuted);

          return { success: true, executables: commands };
        }

        // 4) No executable: show clarification / suggestion if available
        const first = items[0];
        const msg =
          first?.suggestion_message ||
          first?.error ||
          apiRes?.error ||
          t.value.turtlePlayground.invalidCommand;

        showAlertBox(msg, 'error');
        voiceService.speak(t.value.turtlePlayground.invalidCommand);
        return { success: false, error: msg };

      } catch (err) {
        console.error('[TurtlePlayground] Command error:', err);
        const msg = err?.message || 'Unknown error';
        showAlertBox(msg, 'error');
        voiceService.speak(t.value.turtlePlayground.invalidCommand);
        return { success: false, error: msg };
      } finally {
        isProcessing.value = false;
      }
    };

    // const handleRunCommand = async () => {
    //   if (!commandText.value.trim() || isProcessing.value) return;

    //   const cmd = commandText.value.trim();
    //   const directResult = executeDirectCommand(cmd);

    //   if (directResult.success) {
    //     showAlertBox(directResult.result, 'success');
    //     appendToCodeEditor(`t.${cmd}`);
    //     voiceService.speak(t.value.turtlePlayground.commandExecuted);
    //   } else {
    //     await processNaturalLanguageCommand(cmd, cmd);
    //   }
    // };

    // const handleRunCommand = async () => {
    //   if (!commandText.value.trim() || isProcessing.value) return;

    //   const cmd = commandText.value.trim();

    //   appendToCodeEditor(`t.${cmd}`);
    //   commandText.value = '';

    //   await runRemoteTurtle();
    // };

    const isMethodCallSyntax = (s) => /^[a-zA-Z_]\w*\s*\(.*\)\s*$/.test(s);

    const handleRunCommand = async () => {
      if (!commandText.value.trim() || isProcessing.value) return;

      const cmd = commandText.value.trim();

      // Case 1: user typed something like forward(100)
      if (isMethodCallSyntax(cmd)) {
        appendToCodeEditor(`t.${cmd}`);
        commandText.value = '';
        await startRemoteTurtleSession();
        return;
      }

      // Case 2: natural language -> use your backend parser to get executable(s)
      const res = await processNaturalLanguageCommand(cmd, cmd);

      // If parser produced executables, send updated code to Pi
      if (res?.success) {
        commandText.value = '';
        await startRemoteTurtleSession();
      }
    };

    onUnmounted(() => {
      disconnectStream();
    });

    const handleMicClick = async () => {
      voiceService.enableAudioContext();

      if (!isRecording.value) {
        try {
          voiceService.speak(t.value.turtlePlayground.listening);
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          const recorder = new MediaRecorder(stream);
          audioChunks.value = [];

          recorder.ondataavailable = (e) => audioChunks.value.push(e.data);

          recorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks.value, { type: 'audio/webm' });
            const audioFile = new File([audioBlob], `recording_${Date.now()}.webm`, { type: 'audio/webm' });
            stream.getTracks().forEach(track => track.stop());

            isTranscribing.value = true;
            try {
              const result = await voiceService.transcribe(audioFile, language.value);
              const transcribedText = result.text || '';

              if (transcribedText && !transcribedText.includes('[Error')) {
                commandText.value = transcribedText;
                isTranscribing.value = false;
                await processNaturalLanguageCommand(transcribedText, transcribedText);
              } else {
                showAlertBox(language.value === 'th' ? 'แปลงเสียงไม่สำเร็จ กรุณาลองอีกครั้ง' : 'Transcription failed. Please try again.', 'error');
                voiceService.speak(t.value.turtlePlayground.invalidCommand);
                isTranscribing.value = false;
              }
            } catch (err) {
              showAlertBox(err.message, 'error');
              voiceService.speak(t.value.turtlePlayground.invalidCommand);
              isTranscribing.value = false;
            }
          };

          recorder.start();
          mediaRecorder.value = recorder;
          isRecording.value = true;
        } catch (err) {
          voiceService.speak('Microphone access denied');
        }
      } else {
        if (mediaRecorder.value && mediaRecorder.value.state !== 'inactive') {
          mediaRecorder.value.stop();
        }
        isRecording.value = false;
      }
    };

    const handleClear = async () => {
      appendToCodeEditor('t.clear()');
      await startRemoteTurtleSession();
      const msg = t.value.turtlePlayground.canvasCleared || 'Canvas cleared';
      showAlertBox(msg, 'success');
      voiceService.speak(msg);
    };

    const handleReset = async () => {
      appendToCodeEditor('t.reset()');
      await startRemoteTurtleSession();
      const msg = t.value.turtlePlayground.turtleReset || 'Turtle reset';
      showAlertBox(msg, 'success');
      voiceService.speak(msg);
    };

    return {
      t,
      language,
      ttsEnabled,
      undoIcon,
      redoIcon,
      clearIcon,
      resetIcon,
      turtleCanvas,
      turtleIndicator,
      canvasWrapper,
      monacoEditor,
      commandText,
      codeContent,
      isRecording,
      isTranscribing,
      isProcessing,
      // App-specific
      appId,
      appName,
      appIcon,
      // Alert box
      alertMessage,
      alertType,
      showAlert,
      // Handlers
      handleCodeUpdate,
      handleInsertMethod,
      handleRunCommand,
      handleMicClick,
      handleClear,
      handleReset,
      handleUndo,
      handleRedo,
      streamFrame,
    };
  }
};
</script>

<style>
@import './styles/TurtlePlayground.css';

/* Header Styles */
.main-content {
  margin-left: var(--sidebar-total);
  margin-top: var(--toolbar-height);
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--color-bg);
  height: calc(100vh - var(--toolbar-height));
  overflow: hidden;
}

.top-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e8e8e8;
  background: white;
  flex-shrink: 0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: #1a1a1a;
  font-family: 'Jaldi', sans-serif;
  margin: 0;
}

.control-buttons {
  display: flex;
  gap: 8px;
  align-items: center;
}

.control-button {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: transparent;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  padding: 0;
}

.control-button:hover {
  background: transparent;
  transform: translateY(-1px);
  opacity: 0.7;
}

.control-icon {
  width: 20px;
  height: 20px;
  object-fit: contain;
}

.content-area {
  flex: 1;
  padding: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.content-area .turtle-playground {
  margin-left: 0;
  height: 100%;
  min-height: auto;
}

.content-area .turtle-playground__container {
  height: 100%;
}

.turtle-playground__icon-img {
  width: 18px;
  height: 18px;
  object-fit: contain;
}

.turtle-playground__canvas-icon {
  width: 18px;
  height: 18px;
  object-fit: contain;
}

/* Full height code panel when methods panel is removed */
.turtle-playground__code-panel--full {
  flex: 1;
  min-height: 0;
}

.turtle-playground__stream-wrapper {
  width: 100%;
  height: 450px;
  background: #000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.turtle-playground__stream {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.turtle-playground__stream-placeholder {
  color: #aaa;
  font-size: 14px;
}

</style>
