<template>
  <div class="app-container">
    <Sidebar />
    <main class="main-content">
      <header class="top-header">
        <div class="section-header">
          <h2 class="page-title">Codespace</h2>
          <div class="control-buttons">
            <button class="control-button" @click="toggleLanguage" :title="`Switch to ${language === 'en' ? 'Thai' : 'English'}`">
              <img :src="langIcon" alt="Language" class="control-icon" />
            </button>
            <button class="control-button" @click="toggleTTS" :title="ttsEnabled ? 'Disable Voice' : 'Enable Voice'">
              <img :src="ttsEnabled ? soundIcon : nosoundIcon" alt="Sound" class="control-icon" />
            </button>
          </div>
        </div>
      </header>
    <div class="workspace">

    <div class="workspace__container">
      <main class="workspace__chat">
        <section class="workspace__chat-scroll">
          <div
            v-for="msg in messages"
            :key="msg.id"
            style="display: flex; flex-direction: column; margin-bottom: 12px;"
          >
            <div
              :class="['workspace__chat-row', msg.sender === 'user' ? 'workspace__chat-row--right' : 'workspace__chat-row--left']"
              :style="{ alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start' }"
            >
              <div v-if="msg.sender !== 'user'" class="workspace__avatar-container">
                <img :src="scorpioIcon" alt="Scorpio" class="workspace__avatar" />
                <div class="workspace__name workspace__name--left">Scorpio</div>
              </div>
              <span v-if="msg.sender === 'user'" class="workspace__time workspace__time--left">
                {{ formatTime(msg.timestamp) }}
              </span>
              <div class="workspace__bubble">
                <div v-if="msg.content.includes('```')" class="workspace__code">
                  <pre><code>{{ msg.content.replace(/```[\s\S]*?\n|```/g, '') }}</code></pre>
                </div>
                <template v-else>
                  {{ msg.content }}
                </template>
              </div>
              <div v-if="msg.sender === 'user'" class="workspace__avatar-container">
                <img :src="userIcon" alt="User" class="workspace__avatar" />
                <div class="workspace__name workspace__name--right">{{ user?.username || 'User' }}</div>
              </div>
              <span v-if="msg.sender !== 'user'" class="workspace__time">
                {{ formatTime(msg.timestamp) }}
              </span>
            </div>

          </div>
        </section>

        <footer class="workspace__chat-footer">
          <div class="workspace__chat-input-container">
            <div
              :class="['workspace__mic-inner', { 'workspace__mic-inner--recording': isRecording }]"
              @click="handleMicClick"
            >
              <svg
                class="workspace__mic"
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
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

            <form class="workspace__input-form" @submit.prevent="handleSend">
              <input
                type="text"
                class="workspace__input"
                :placeholder="t.workspace.typeYourMessage"
                v-model="message"
              />
              <button type="submit" class="workspace__send-btn" aria-label="Send message">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                  <path d="M2 21L23 12L2 3V10L17 12L2 14V21Z"/>
                </svg>
              </button>
            </form>
          </div>
        </footer>
      </main>

      <section class="workspace__code-panel">
        <div v-if="refreshNotification" class="workspace__refresh-notification">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2a10 10 0 1 0 10 10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <path d="m9 12 2 2 4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          {{ refreshNotification }}
        </div>

        <div class="workspace__editor-section" v-if="!isOutputExpanded">
          <div class="workspace__editor-header">
            <h3 class="workspace__editor-title">Code Editor</h3>
            <div style="display: flex; gap: 8px; align-items: center;">
              <button
                v-if="availableMethods"
                class="workspace__icon-btn"
                @click="toggleMethodsPanel"
                aria-label="Methods"
                title="Toggle methods panel"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M4 6h16M4 12h16M4 18h16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
              </button>
              <button
                class="workspace__icon-btn"
                @click="handleSave"
                :disabled="isSaving"
                aria-label="Save"
                title="Save changes (Ctrl+S)"
              >
                <svg v-if="isSaving" width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" opacity="0.3"/>
                  <path d="M12 2a10 10 0 0110 10" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                    <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite"/>
                  </path>
                </svg>
                <img v-else :src="saveIcon" alt="Save" class="workspace__icon-btn-icon" />
              </button>

              <button
                class="workspace__icon-btn workspace__run-btn"
                @click="handleRun"
                :disabled="isRunning"
                aria-label="Run runner.py"
                title="Run runner.py"
              >
                <svg v-if="isRunning" width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" opacity="0.3"/>
                  <path d="M12 2a10 10 0 0110 10" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                    <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite"/>
                  </path>
                </svg>
                <template v-else>
                  <img :src="runCodeIcon" alt="Run" class="workspace__icon-btn-icon" />
                  <span class="workspace__run-text">Run</span>
                </template>
              </button>
            </div>
          </div>
          <div class="workspace__editor-wrapper">
            <div class="workspace__editor-toolbar">
              <input
                type="file"
                ref="fileInputRef"
                @change="handleFileUpload"
                accept=".py"
                style="display: none"
              />
              <button
                class="workspace__toolbar-btn"
                @click="() => fileInputRef?.click()"
                aria-label="Upload File"
                title="Upload Python file"
              >
                <img :src="uploadFileIcon" alt="Upload File" class="workspace__toolbar-icon" />
              </button>
              <button
                class="workspace__toolbar-btn"
                @click="handleUndo"
                aria-label="Undo"
                title="Undo (Ctrl+Z)"
              >
                <img :src="undoIcon" alt="Undo" class="workspace__toolbar-icon" />
              </button>
              <button
                class="workspace__toolbar-btn"
                @click="handleRedo"
                aria-label="Redo"
                title="Redo (Ctrl+Y)"
              >
                <img :src="redoIcon" alt="Redo" class="workspace__toolbar-icon" />
              </button>
            </div>
            <div class="workspace__editor-content">
              <div class="workspace__editor-file-info">
                <span v-if="isRefreshing" class="workspace__refresh-indicator" title="Refreshing file content...">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 2a10 10 0 0110 10" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                      <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite"/>
                    </path>
                  </svg>
                </span>
                <span class="workspace__current-file">{{ currentFile }}</span>
              </div>
            <MonacoEditor
              ref="editorRef"
              :key="`${conversationId}-${currentFile}`"
              :code="currentCode"
              @update:code="handleEditorChange"
              language="python"
            />
            </div>
          </div>
        </div>

        <div class="workspace__output-section" :class="{ 'expanded': isOutputExpanded }">
          <div class="workspace__output-header">
            <div class="workspace__output-header-content">
            <h3>{{ t.workspace.output }}</h3>
            <div class="workspace__output-actions">
                <button
                  class="workspace__icon-btn"
                  :class="{ 'active': isOutputExpanded }"
                  @click="toggleOutputExpand"
                  aria-label="Expand output"
                  title="Expand output to full height"
                >
                  <img :src="spanIcon" alt="Span" class="workspace__icon-btn-icon" />
                </button>
              <button
                class="workspace__icon-btn"
                @click="output = ''"
                aria-label="Clear output"
                title="Clear output"
              >
                  <img :src="clearIcon" alt="Clear" class="workspace__icon-btn-icon" />
                </button>
              </div>
            </div>
            <!-- Mode Tabs -->
            <div class="workspace__mode-tabs">
              <button
                class="workspace__mode-tab"
                :class="{ 'active': isTextMode }"
                @click="setOutputMode('text')"
                title="Text Mode"
              >
                <img :src="textModeIcon" alt="Text Mode" class="workspace__mode-tab-icon" />
                <span>Text</span>
              </button>
              <button
                class="workspace__mode-tab"
                :class="{ 'active': !isTextMode }"
                @click="setOutputMode('graphic')"
                title="Graphic Mode"
              >
                <img :src="graphicModeIcon" alt="Graphic Mode" class="workspace__mode-tab-icon" />
                <span>Graphic</span>
              </button>
            </div>
          </div>
          <div class="workspace__output">
            <div
              v-if="!isTextMode"
              style="width: 100%; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; background-color: #1e1e1e; padding: 10px;"
            >
              <div style="margin-bottom: 10px; color: #d4d4d4; font-size: 14px;">
                {{ t.workspace.turtleGraphicsStream }}
              </div>
              <img
                id="turtle-video"
                style="width: 100%; height: calc(100% - 40px); object-fit: contain; border: 1px solid #444; border-radius: 4px; background-color: #000;"
                alt="Turtle graphics stream"
              />
            </div>
            <pre v-else>{{ output || t.workspace.outputWillAppear }}</pre>
          </div>
        </div>
      </section>
    </div>

    <!-- Loading Status Bar -->
    <div v-if="isTranscribing" class="workspace__status-bar workspace__status-bar--transcribing">
      <div class="workspace__status-content">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="workspace__status-spinner">
          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-dasharray="60" stroke-dashoffset="0">
            <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite"/>
          </circle>
        </svg>
        <span class="workspace__status-text">{{ language === 'th' ? 'กำลังแปลงเสียงของคุณ...' : 'Transcribing your voice...' }}</span>
        <div class="workspace__status-progress">
          <div class="workspace__status-progress-bar"></div>
        </div>
      </div>
    </div>

    <div v-if="isProcessingCommand" class="workspace__status-bar workspace__status-bar--processing">
      <div class="workspace__status-content">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="workspace__status-spinner">
          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-dasharray="60" stroke-dashoffset="0">
            <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite"/>
          </circle>
        </svg>
        <span class="workspace__status-text">{{ language === 'th' ? 'กำลังประมวลผลและจับคู่คำสั่ง...' : 'Processing and mapping command...' }}</span>
        <div class="workspace__status-progress">
          <div class="workspace__status-progress-bar"></div>
        </div>
      </div>
    </div>

    <!-- Success Dialog -->
    <Transition name="dialog-fade">
      <div v-if="showSuccessDialog" class="workspace__success-dialog-overlay" @click="showSuccessDialog = false">
        <div class="workspace__success-dialog">
          <div class="workspace__success-dialog-icon">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" fill="#001f3f"/>
              <path d="M8 12l2.5 2.5L16 9" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <p class="workspace__success-dialog-message">{{ successDialogMessage }}</p>
        </div>
      </div>
    </Transition>

    <!-- Overlay for methods panel -->
    <div
      v-if="isMethodsPanelOpen"
      class="workspace__methods-overlay"
      @click="toggleMethodsPanel"
    ></div>

    <!-- Right Methods Panel -->
    <div class="workspace__methods-panel" :class="{ 'open': isMethodsPanelOpen }">
      <div class="workspace__methods-panel-header">
        <h3 class="workspace__methods-panel-title">
          {{ availableMethods?.file_name || t.workspace.availableMethods }}
        </h3>
        <button class="workspace__methods-panel-close" @click="toggleMethodsPanel" title="Close panel">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </button>
      </div>
      <div class="workspace__methods-panel-content">
        <div
          v-for="(classInfo, className) in availableMethods?.classes"
          :key="className"
          class="workspace__methods-class"
        >
          <div
            v-for="method in classInfo.methods"
            :key="method.name"
            class="workspace__method-card"
            @click="insertMethod(method)"
          >
            <div class="workspace__method-card-name">{{ method.name }}</div>
            <div class="workspace__method-card-params">
              {{ method.required_parameters.join(', ') }}
            </div>
          </div>
        </div>
      </div>
    </div>
    </div>

    <!-- Function Panel Overlay -->
    <div
      v-if="isFunctionPanelOpen"
      class="function-panel-overlay"
      @click="toggleFunctionPanel"
    ></div>

    <!-- Right Functions Panel -->
    <div class="function-panel" :class="{ 'open': isFunctionPanelOpen }">
      <div class="function-panel-header">
        <h3 class="function-panel-title">{{ availableMethods?.file_name || t.workspace.availableMethods }}</h3>
        <button class="function-panel-close" @click="toggleFunctionPanel" title="Close panel">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </button>
      </div>
      <div class="function-panel-content">
        <div
          v-for="(classInfo, className) in availableMethods?.classes"
          :key="className"
          class="function-panel-class"
        >
          <h4 class="function-panel-class-title">{{ className }}</h4>
          <div
            v-for="method in classInfo.methods"
            :key="method.name"
            class="function-item"
            @click="insertMethod(method)"
          >
            <div class="function-item-name">{{ method.name }}</div>
            <div class="function-item-description">
              Parameters: {{ method.required_parameters.join(', ') }}
            </div>
            <div v-if="method.file_name" class="function-item-file">{{ method.file_name }}</div>
          </div>
        </div>
        <div v-if="!availableMethods || Object.keys(availableMethods?.classes || {}).length === 0" class="function-panel-empty">
          <p>No methods available</p>
        </div>
      </div>
    </div>
    </main>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import Sidebar from '../components/Sidebar.vue';
import MonacoEditor from '../components/MonacoEditor.vue';
import { messageAPI, conversationAPI, executeAPI, analyzeAPI, paraphraseAPI, fileAPI, translateAPI, useAuth, useLanguage, useTTS, voiceService } from '@py-talk/shared';
import { useCode } from '../composables/useCode';
import { useFile } from '../composables/useFile';
import { useTranslations } from '../utils/translations';
import scorpioIcon from '../assets/scorpio.svg';
import langIcon from '../assets/lang-icon.svg';
import soundIcon from '../assets/sound-icon.svg';
import nosoundIcon from '../assets/nosound-icon.svg';
import userIcon from '../assets/user.svg';
import undoIcon from '../assets/R-undo.svg';
import redoIcon from '../assets/R-redo.svg';
import uploadFileIcon from '../assets/R-uploadfile.svg';
import functionPanelIcon from '../assets/R-functionpanel.svg';
import textModeIcon from '../assets/R-textmode.svg';
import graphicModeIcon from '../assets/R-graphicmode.svg';
import clearIcon from '../assets/R-clear.svg';
import spanIcon from '../assets/R-span.svg';
import saveIcon from '../assets/R-save.svg';
import runCodeIcon from '../assets/R-runcode.svg';

export default {
  name: 'Workspace',
  components: {
    Sidebar,
    MonacoEditor
  },
  setup() {
    const route = useRoute();
    const router = useRouter();
    const { user } = useAuth();
    const { code, setCode, syncCodeFromBackend, setConversationId } = useCode();
    const { language, setLanguage } = useLanguage();
    const { ttsEnabled, setTTSEnabled } = useTTS();
    const t = computed(() => useTranslations(language.value));
    const {
      currentFile,
      currentCode,
      files,
      setCurrentCode,
      loadFiles,
      loadFile,
      saveFile
    } = useFile();

    const conversationId = computed(() => route.query.conversationId);
    const message = ref('');
    const messages = ref([]);
    const availableMethods = ref(null);
    const output = ref('');
    const isRunning = ref(false);
    const isTextMode = ref(true);
    const isOutputExpanded = ref(false);
    const isRecording = ref(false);
    const isTranscribing = ref(false);
    const isProcessingCommand = ref(false);
    const mediaRecorder = ref(null);
    const audioChunks = ref([]);
    const editorRef = ref(null);
    const isSaving = ref(false);
    const isRefreshing = ref(false);
    const refreshNotification = ref(null);
    const lastUserEdit = ref(0);
    const isUserEditing = ref(false);
    const editingTimeoutRef = ref(null);
    const expandedParaphrases = ref(new Set());
    const loadingParaphrases = ref(new Set());
    const audioContextRef = ref(null);
    const hasGreeted = ref(false);
    const isMethodsPanelOpen = ref(false);
    const isFunctionPanelOpen = ref(false);
    const fileInputRef = ref(null);
    const showSuccessDialog = ref(false);
    const successDialogMessage = ref('');

    let pollIntervalId = null;

    const formatTime = (timestamp) => {
      return new Date(timestamp).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
      });
    };

    const initializeSession = async () => {
      if (!conversationId.value) return;
      try {
        await executeAPI.ensureSessionInitialized(parseInt(conversationId.value));
        await fetchMessages();
        await fetchAvailableMethods();
        await syncCodeFromBackend();

        analyzeAPI.prewarmPipeline(parseInt(conversationId.value))
          .catch(err => console.warn('Pipeline pre-warm failed:', err));
      } catch (err) {
        console.error('Failed to initialize session:', err);
      }
    };

    const fetchMessages = async () => {
      if (!conversationId.value) return;
      try {
        const msgs = await messageAPI.getByConversation(parseInt(conversationId.value));
        messages.value = msgs.map(msg => {
          const existing = messages.value.find(m => m.id === msg.id);
          return existing
            ? { ...msg, interpretedCommand: existing.interpretedCommand, paraphrases: existing.paraphrases }
            : msg;
        });
      } catch (err) {
        console.error('Failed to fetch messages:', err);
      }
    };

    const fetchAvailableMethods = async () => {
      if (!conversationId.value) return;
      try {
        const methods = await conversationAPI.getAvailableMethods(parseInt(conversationId.value));
        availableMethods.value = methods;
      } catch (err) {
        console.error('Failed to fetch available methods:', err);
      }
    };

    const handleSend = async (e) => {
      if (!message.value.trim() || !conversationId.value) return;

      const msgText = message.value.trim();
      message.value = '';

      try {
        isProcessingCommand.value = true;

        // Timing variables
        const startTime = performance.now();
        let translateStartTime, translateEndTime, analyzeStartTime, analyzeEndTime;
        let translationTime = 0;
        let commandProcessingTime = 0;

        // Safari-compatible logging
        const logGroup = () => {
          console.log('');
          console.log('═════════════════════════════════════════════════════════════');
          console.log('📝 COMMAND PROCESSING PIPELINE');
          console.log('═════════════════════════════════════════════════════════════');
          console.log('Current Language Mode:', language.value === 'en' ? 'English' : 'Thai');
          console.log('TTS Model Chosen:', language.value === 'en' ? 'Whisper English (distil-whisper/distil-large-v3)' : 'Whisper Thai (nectec/Pathumma-whisper-th-large-v3)');
          console.log('Transcribed Text:', msgText);
          console.log('─────────────────────────────────────────────────────────────');
        };
        logGroup();

        // Step 1: Translate Thai to English if needed
        let commandForAnalysis = msgText;
        let translatedText = null;

        if (language.value === 'th') {
          try {
            console.log('🔄 TRANSLATION STEP');
            console.log('Calling Google Cloud Translate API...');
            console.log('Source Language: Thai');
            console.log('Target Language: English');

            translateStartTime = performance.now();
            const translateResult = await translateAPI.translateToEnglish(msgText);
            translateEndTime = performance.now();
            translationTime = (translateEndTime - translateStartTime) / 1000; // Convert to seconds

            commandForAnalysis = translateResult.translated_text;
            translatedText = translateResult.translated_text;

            console.log('✅ Translation Result:', translatedText);
            console.log('Time to Translate Transcribed Text:', translationTime.toFixed(3), 'seconds');
            console.log('─────────────────────────────────────────────────────────────');
            voiceService.speak("Command translated");
          } catch (translateErr) {
            console.error("❌ Translation failed:", translateErr);
            voiceService.speak("Translation failed, please try again");
            alert("Translation failed: " + translateErr.message);
            return; // Stop if translation fails
          }
        } else {
          console.log('Translation: Not required (English mode)');
          console.log('Translated Text: null');
          console.log('Time to Translate Transcribed Text: 0 seconds (not applicable)');
          console.log('─────────────────────────────────────────────────────────────');
        }

        // Step 2: Save original message (Thai or English)
        const userMsg = await messageAPI.create(parseInt(conversationId.value), 'user', msgText);

        // Step 3: Analyze using English command
        console.log('🔍 COMMAND ANALYSIS STEP');
        console.log('Text for Analysis:', commandForAnalysis);

        analyzeStartTime = performance.now();
        const data = await analyzeAPI.analyzeCommand(Number(conversationId.value), commandForAnalysis);
        analyzeEndTime = performance.now();
        commandProcessingTime = (analyzeEndTime - analyzeStartTime) / 1000; // Convert to seconds

        const allResults = data.results && data.results.length > 0 ? data.results : [data.result].filter(r => r);

        let summary;
        let allExecutables = [];

        if (allResults.length > 0) {
          allResults.forEach(r => {
            if (r.executable) {
              allExecutables.push(r.executable);
            }
          });

          if (allExecutables.length > 0) {
            summary = allExecutables.join('\n');
          } else {
            summary = 'No executable command generated';
          }
        } else {
          summary = 'No matching commands found';
        }

        console.log('✅ Processed Command(s):', summary);
        console.log('Time to Process Commands:', commandProcessingTime.toFixed(3), 'seconds');
        console.log('─────────────────────────────────────────────────────────────');
        console.log('📊 SUMMARY');
        console.log('Current Language Mode:', language.value === 'en' ? 'English' : 'Thai');
        console.log('TTS Model Chosen:', language.value === 'en' ? 'Whisper English (distil-whisper/distil-large-v3)' : 'Whisper Thai (nectec/Pathumma-whisper-th-large-v3)');
        console.log('Transcribed Text:', msgText);
        console.log('Translated Text:', translatedText || 'null');
        console.log('Time to Translate Transcribed Text:', translationTime > 0 ? translationTime.toFixed(3) + ' seconds' : '0 seconds (not applicable)');
        console.log('Processed Commands:', summary);
        console.log('Time to Process Commands:', commandProcessingTime.toFixed(3), 'seconds');
        console.log('═════════════════════════════════════════════════════════════');
        console.log('');

        await messageAPI.create(parseInt(conversationId.value), 'system', summary);

        const msgs = await messageAPI.getByConversation(parseInt(conversationId.value));
        messages.value = msgs.map(msg =>
          msg.id === userMsg.id
            ? { ...msg, interpretedCommand: summary }
            : msg
        );

        const executable = allExecutables.length > 0 ? allExecutables.join('\n') : null;

        if (executable) {
          const commandCount = allExecutables.length;
          const pluralText = commandCount > 1 ? `${commandCount} commands` : 'command';
          const confirmed = window.confirm(
            `Do you want to append the ${pluralText} to the runner file?\n\n${executable}`
          );

          if (confirmed) {
            await executeAPI.appendCommand(Number(conversationId.value), executable);
            await syncCodeFromBackend();

            if (currentFile.value === 'runner.py') {
              isRefreshing.value = true;
              await loadFile(parseInt(conversationId.value), 'runner.py');
              setTimeout(() => isRefreshing.value = false, 1000);
            }

            const successMessage = commandCount > 1
              ? `${commandCount} commands appended successfully.`
              : `Command appended successfully.`;

            // Show success dialog instead of chat message
            successDialogMessage.value = successMessage;
            showSuccessDialog.value = true;

            // Auto-dismiss after 3 seconds
            setTimeout(() => {
              showSuccessDialog.value = false;
            }, 3000);

            const speechMessage = commandCount > 1
              ? `${commandCount} commands appended successfully`
              : 'Command appended successfully';
            voiceService.speak(speechMessage);
          }
        } else {
          voiceService.speak("I couldn't process that command. Could you please try again?");
        }
      } catch (err) {
        console.error('Failed to send or analyze message:', err);
        voiceService.speak('I encountered an error. Please try again');
        alert('Error: ' + err.message);
      } finally {
        isProcessingCommand.value = false;
      }
    };

    const handleFileUpload = async (event) => {
      const file = event.target.files?.[0];
      if (!file || !conversationId.value) return;

      if (!file.name.endsWith('.py')) {
        alert('Please upload only Python (.py) files');
        event.target.value = '';
        return;
      }

      try {
        const fileContent = await file.text();
        await saveFile(parseInt(conversationId.value), file.name, fileContent);
        await loadFiles(parseInt(conversationId.value));
        await loadFile(parseInt(conversationId.value), file.name);
        voiceService.speak('File uploaded successfully');
        refreshNotification.value = 'File uploaded successfully';
        setTimeout(() => {
          refreshNotification.value = null;
        }, 3000);
      } catch (err) {
        console.error('Failed to upload file:', err);
        voiceService.speak('Failed to upload file');
        alert('Failed to upload file: ' + err.message);
      }

      event.target.value = '';
    };

    const handleSave = async () => {
      if (!conversationId.value) {
        console.error('No conversation ID');
        return;
      }

      isSaving.value = true;
      try {
        await saveFile(parseInt(conversationId.value), currentFile.value, currentCode.value);

        if (currentFile.value === 'runner.py') {
          setCode(currentCode.value);
        }

        if (currentFile.value !== 'runner.py') {
          try {
            await analyzeAPI.invalidatePipelineCache(parseInt(conversationId.value));
          } catch (err) {
            console.warn('Failed to invalidate pipeline cache:', err);
          }

          await fetchAvailableMethods();

          analyzeAPI.prewarmPipeline(parseInt(conversationId.value))
            .catch(err => console.warn('Pipeline re-prewarm failed:', err));

          voiceService.speak('Code saved and methods updated');
        } else {
          voiceService.speak('Code saved successfully');
        }

        lastUserEdit.value = 0;
        isUserEditing.value = false;
        if (editingTimeoutRef.value) {
          clearTimeout(editingTimeoutRef.value);
        }
      } catch (err) {
        console.error('Failed to save code:', err);
        voiceService.speak('Failed to save code');
      } finally {
        isSaving.value = false;
      }
    };

    const handleUndo = () => {
      editorRef.value?.undo();
    };

    const handleRedo = () => {
      editorRef.value?.redo();
    };

    const handleRun = async () => {
      try {
        const runnerResponse = await executeAPI.getRunnerCode(parseInt(conversationId.value));
        const runnerCode = runnerResponse.code;

        if (!runnerCode.trim()) {
          output.value = 'Error: runner.py is empty. Please add some commands.\n';
          voiceService.speak('Runner file is empty. Please add some commands');
          return;
        }
      } catch (err) {
        output.value = 'Error: runner.py not found. Please initialize the session first.\n';
        voiceService.speak('Runner file not found. Please initialize the session first');
        return;
      }

      if (isTextMode.value) {
        await handleRunNormalCode();
      } else {
        await handleRunTurtle();
      }
    };

    const handleRunNormalCode = async () => {
      isRunning.value = true;
      output.value = 'Running code...\n\n';

      try {
        const res = await executeAPI.rerunCommand(parseInt(conversationId.value));
        output.value = res.output || 'No output returned from execute_command.\n';
        voiceService.speak('Your output is ready, Sir');
      } catch (err) {
        console.error('Failed to execute command:', err);
        output.value = 'Error executing command.\n';
        voiceService.speak('Please try again');
      } finally {
        isRunning.value = false;
      }
    };

    const handleRunTurtle = async () => {
      isRunning.value = true;
      output.value = 'Running turtle graphics...\n\n';

      const hostname = window.location.hostname;
      const apiBase = `http://192.168.4.228:8001`;
      const rawWsBase = `ws://192.168.4.228:5050`;
      const wsBase = rawWsBase
        .replace('localhost', hostname)
        .replace('127.0.0.1', hostname);

      try {
        const channelName = encodeURIComponent(String(conversationId.value));
        const ws = new WebSocket(`${wsBase}/subscribe/${channelName}`);

        await new Promise((resolve, reject) => {
          ws.onopen = () => {
            resolve();
          };
          ws.onerror = (err) => {
            console.error('Turtle WebSocket error:', err);
            reject(err);
          };
        });

        ws.onmessage = (event) => {
          const image = event.data;
          const videoEl = document.getElementById('turtle-video');
          if (videoEl) {
            videoEl.src = `data:image/jpeg;base64,${image}`;
          }
        };

        ws.onclose = () => {
          console.log('Turtle WebSocket closed');
        };

        const getRes = await fetch(
          `${import.meta.env.VITE_API_BASE_URL || ''}/api/get_session_files?conversation_id=${conversationId.value}`,
          { headers: { Accept: 'application/json' } }
        );

        if (!getRes.ok) {
          const text = await getRes.text();
          throw new Error(`Failed to fetch session files: ${text}`);
        }

        const { files } = await getRes.json();

        const payload = {
          files: files,
        };

        const res = await fetch(`${apiBase}/run_turtle/${conversationId.value}`, {
          method: 'POST',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(payload),
        });

        if (!res.ok) {
          const errorText = await res.text();
          throw new Error(`Backend returned ${res.status}: ${errorText}`);
        }

        output.value = 'Turtle graphics execution triggered on streaming device.\n';
        voiceService.speak('Your turtle graphics are running, Sir');
      } catch (err) {
        console.error('Failed to execute turtle graphics:', err);
        output.value = 'Error executing turtle graphics.\n';
        voiceService.speak('Please try again');
      } finally {
        isRunning.value = false;
      }
    };

    const toggleOutputMode = () => {
      // This function is kept for compatibility but tabs handle the switching directly
      isTextMode.value = !isTextMode.value;
      localStorage.setItem('outputMode', isTextMode.value ? 'text' : 'graphic');
    };

    const setOutputMode = (mode) => {
      isTextMode.value = mode === 'text';
      localStorage.setItem('outputMode', mode);
    };

    const toggleOutputExpand = () => {
      isOutputExpanded.value = !isOutputExpanded.value;
      localStorage.setItem('outputExpanded', isOutputExpanded.value);
    };

    const playClickSound = () => {
      try {
        if (!audioContextRef.value) {
          audioContextRef.value = new (window.AudioContext || window.webkitAudioContext)();
        }
        const audioContext = audioContextRef.value;
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();

        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        oscillator.frequency.value = 800;
        oscillator.type = 'sine';
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.1);
      } catch (error) {
        console.log('Audio playback not available:', error);
      }
    };

    const handleToggleParaphrases = async (msg) => {
      if (!msg.id) return;

      if (expandedParaphrases.value.has(msg.id)) {
        const newSet = new Set(expandedParaphrases.value);
        newSet.delete(msg.id);
        expandedParaphrases.value = newSet;
        return;
      }

      if (msg.paraphrases && msg.paraphrases.length > 0) {
        const newSet = new Set(expandedParaphrases.value);
        newSet.add(msg.id);
        expandedParaphrases.value = newSet;
        return;
      }

      const newLoadingSet = new Set(loadingParaphrases.value);
      newLoadingSet.add(msg.id);
      loadingParaphrases.value = newLoadingSet;

      try {
        const response = await paraphraseAPI.getParaphrases(msg.content, 10);

        messages.value = messages.value.map(m =>
          m.id === msg.id
            ? { ...m, paraphrases: response.variants }
            : m
        );

        const newExpandedSet = new Set(expandedParaphrases.value);
        newExpandedSet.add(msg.id);
        expandedParaphrases.value = newExpandedSet;
      } catch (error) {
        console.error('Failed to fetch paraphrases:', error);
        voiceService.speak('Failed to generate suggestions');
      } finally {
        const newLoadingSet = new Set(loadingParaphrases.value);
        newLoadingSet.delete(msg.id);
        loadingParaphrases.value = newLoadingSet;
      }
    };

    const handleMicClick = async () => {
      playClickSound();
      // Enable audio context on mic click
      voiceService.enableAudioContext();

      if (!isRecording.value) {
        try {
          voiceService.speak('Listening');
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          const recorder = new MediaRecorder(stream);
          audioChunks.value = [];

          recorder.ondataavailable = (e) => {
            audioChunks.value.push(e.data);
          };

          recorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks.value, { type: 'audio/webm' });

            const audioFile = new File(
              [audioBlob],
              `recording_${Date.now()}.webm`,
              { type: 'audio/webm' }
            );

            try {
              isTranscribing.value = true;
              console.log('🎤 VOICE TRANSCRIPTION START');
              console.log('Language:', language.value === 'en' ? 'English' : 'Thai');
              console.log('STT Model:', language.value === 'en'
                ? 'Whisper English (distil-whisper/distil-large-v3)'
                : 'Whisper Thai (nectec/Pathumma-whisper-th-large-v3)');

              const transcribeStartTime = performance.now();
              const result = await voiceService.transcribe(audioFile, language.value);
              const transcribeEndTime = performance.now();
              const transcriptionTime = (transcribeEndTime - transcribeStartTime) / 1000; // Convert to seconds

              const text = result.text || `[Error: ${result.error || 'Unknown'}]`;

              if (text.includes('[Error')) {
                console.log('❌ Transcription failed:', text);
                console.log('Time to Transcribe TTS:', transcriptionTime.toFixed(3), 'seconds');
                voiceService.speak("I couldn't understand that. Please try again");
              } else {
                console.log('✅ Transcribed Text:', text);
                console.log('Time to Transcribe TTS:', transcriptionTime.toFixed(3), 'seconds');
                voiceService.speak('Voice command received');
              }

              message.value = text;
            } catch (err) {
              console.error('Voice transcription error:', err);
              voiceService.speak('Voice transcription error');
              alert('Error transcribing voice: ' + err.message);
            } finally {
              isTranscribing.value = false;
            }
          };

          recorder.start();
          mediaRecorder.value = recorder;
          isRecording.value = true;
        } catch (err) {
          console.error('Microphone access denied:', err);
          voiceService.speak('Microphone access denied');
          alert('Microphone access denied or unavailable.');
        }
      } else {
        if (mediaRecorder.value && mediaRecorder.value.state !== 'inactive') {
          mediaRecorder.value.stop();
        }
        isRecording.value = false;
      }
    };

    const handleEditorChange = (value) => {
      setCurrentCode(value || '');
      lastUserEdit.value = Date.now();
      isUserEditing.value = true;

      if (editingTimeoutRef.value) {
        clearTimeout(editingTimeoutRef.value);
      }

      editingTimeoutRef.value = setTimeout(() => {
        isUserEditing.value = false;
      }, 3000);
    };

    const toggleMethodsPanel = () => {
      isMethodsPanelOpen.value = !isMethodsPanelOpen.value;
    };

    const toggleFunctionPanel = () => {
      isFunctionPanelOpen.value = !isFunctionPanelOpen.value;
    };

    const toggleLanguage = () => {
      setLanguage(language.value === 'en' ? 'th' : 'en');
    };

    const toggleTTS = () => {
      setTTSEnabled(!ttsEnabled.value);
    };

    const insertMethod = (method) => {
      const methodCall = `${method.name}(${method.required_parameters.join(', ')})`;
      const currentPosition = editorRef.value?.getPosition();

      if (editorRef.value && currentPosition) {
        editorRef.value.insertText(methodCall, currentPosition);
      } else {
        setCurrentCode(currentCode.value + '\n' + methodCall);
      }

      toggleMethodsPanel();
    };

    const handleKeyDown = (event) => {
      if ((event.ctrlKey || event.metaKey) && event.key === 's') {
        event.preventDefault();
        handleSave();
      }
    };

    const getGreeting = () => {
      const hour = new Date().getHours();
      if (hour >= 5 && hour < 12) return 'Good Morning, Sir';
      if (hour >= 12 && hour < 17) return 'Good Afternoon, Sir';
      if (hour >= 17 && hour < 21) return 'Good Evening, Sir';
      return 'Welcome, Sir';
    };

    watch(() => route.query.conversationId, async (newId, oldId) => {
      if (newId && newId !== oldId) {
        setConversationId(parseInt(newId));

        // Clear current file state
        setCurrentCode('');

        // Reload files and select the uploaded file
        await loadFiles(parseInt(newId));
        if (files.value.length > 0) {
          const uploadedFile = files.value.find(f => f !== 'runner.py') || files.value[0];
          await loadFile(parseInt(newId), uploadedFile);
        }

        await initializeSession();
      }
    });

    watch(currentFile, () => {
      isUserEditing.value = false;
      if (editingTimeoutRef.value) {
        clearTimeout(editingTimeoutRef.value);
      }
    });

    // Log language mode changes
    watch(language, (newLang) => {
      console.log('═══════════════════════════════════════════');
      console.log('🌐 LANGUAGE MODE CHANGED');
      console.log('═══════════════════════════════════════════');
      console.log('Current Language:', newLang === 'en' ? 'English' : 'Thai');
      console.log('STT Model:', newLang === 'en' ? 'Whisper English (distil-whisper/distil-large-v3)' : 'Whisper Thai (nectec/Pathumma-whisper-th-large-v3)');
      console.log('Translation Required:', newLang === 'th' ? 'Yes (Thai → English)' : 'No');
      console.log('═══════════════════════════════════════════');
    });

    watch([code, currentFile, conversationId], async () => {
      const refreshRunnerFile = async () => {
        if (conversationId.value && currentFile.value === 'runner.py' && code.value !== currentCode.value) {
          try {
            const timeSinceLastEdit = Date.now() - lastUserEdit.value;
            if (timeSinceLastEdit > 10000) {
              await loadFile(parseInt(conversationId.value), 'runner.py');
            }
          } catch (error) {
            console.error('Failed to auto-refresh runner.py:', error);
          }
        }
      };

      await refreshRunnerFile();
    });

    onMounted(async () => {
      // If no conversationId provided, try to load the most recent conversation
      if (!conversationId.value && user.value?.id) {
        try {
          const conversations = await conversationAPI.getByUser(user.value.id);
          if (conversations && conversations.length > 0) {
            // Sort by created_at descending and get the most recent
            const sorted = conversations.sort((a, b) =>
              new Date(b.created_at) - new Date(a.created_at)
            );
            // Redirect to the most recent conversation
            router.replace({ query: { conversationId: sorted[0].id } });
            return; // The watch on conversationId will handle initialization
          }
        } catch (error) {
          console.error('Failed to load recent conversation:', error);
        }
      }

      if (conversationId.value) {
        setConversationId(parseInt(conversationId.value));
        await loadFiles(parseInt(conversationId.value));

        // Load the first uploaded file (not runner.py) if available
        if (files.value.length > 0) {
          const uploadedFile = files.value.find(f => f !== 'runner.py') || files.value[0];
          await loadFile(parseInt(conversationId.value), uploadedFile);
        }

        await initializeSession();
      }

      // Load saved output mode preference
      const savedMode = localStorage.getItem('outputMode');
      if (savedMode) {
        isTextMode.value = savedMode === 'text';
      }

      // Load saved output expand preference
      const savedExpand = localStorage.getItem('outputExpanded');
      if (savedExpand) {
        isOutputExpanded.value = savedExpand === 'true';
      }

      const greetOnInteraction = () => {
        if (!hasGreeted.value && conversationId.value) {
          hasGreeted.value = true;
          // Enable audio context first
          voiceService.enableAudioContext();
          const greeting = getGreeting();
          voiceService.speak(greeting);
          document.removeEventListener('click', greetOnInteraction);
          document.removeEventListener('keydown', greetOnInteraction);
        }
      };

      if (conversationId.value) {
        document.addEventListener('click', greetOnInteraction);
        document.addEventListener('keydown', greetOnInteraction);
      }

      document.addEventListener('keydown', handleKeyDown);

      if (conversationId.value && currentFile.value === 'runner.py') {
        pollIntervalId = setInterval(async () => {
          try {
            const timeSinceLastEdit = Date.now() - lastUserEdit.value;
            if (timeSinceLastEdit < 15000) {
              return;
            }

            const response = await fileAPI.getFile(parseInt(conversationId.value), 'runner.py');
            if (response.code !== currentCode.value && !isUserEditing.value) {
              isRefreshing.value = true;
              setCurrentCode(response.code);
              setCode(response.code);

              refreshNotification.value = 'File updated with new commands';

              setTimeout(() => isRefreshing.value = false, 1000);
              setTimeout(() => refreshNotification.value = null, 3000);
            }
          } catch (error) {
            console.error('Failed to poll for runner.py changes:', error);
          }
        }, 10000);
      }
    });

    onUnmounted(() => {
      if (editingTimeoutRef.value) {
        clearTimeout(editingTimeoutRef.value);
      }
      if (pollIntervalId) {
        clearInterval(pollIntervalId);
      }
      document.removeEventListener('keydown', handleKeyDown);
    });

    return {
      conversationId,
      message,
      messages,
      availableMethods,
      output,
      isRunning,
      isTextMode,
      isRecording,
      isTranscribing,
      isProcessingCommand,
      editorRef,
      fileInputRef,
      isSaving,
      isRefreshing,
      refreshNotification,
      expandedParaphrases,
      loadingParaphrases,
      user,
      currentFile,
      currentCode,
      scorpioIcon,
      userIcon,
      undoIcon,
      redoIcon,
      uploadFileIcon,
      functionPanelIcon,
      textModeIcon,
      graphicModeIcon,
      clearIcon,
      spanIcon,
      saveIcon,
      runCodeIcon,
      langIcon,
      soundIcon,
      nosoundIcon,
      isMethodsPanelOpen,
      isFunctionPanelOpen,
      isOutputExpanded,
      showSuccessDialog,
      successDialogMessage,
      language,
      ttsEnabled,
      t,
      formatTime,
      toggleLanguage,
      toggleTTS,
      handleSend,
      handleFileUpload,
      handleSave,
      handleUndo,
      handleRedo,
      handleRun,
      toggleOutputMode,
      setOutputMode,
      toggleOutputExpand,
      handleToggleParaphrases,
      handleMicClick,
      handleEditorChange,
      toggleMethodsPanel,
      toggleFunctionPanel,
      insertMethod,
    };
  }
};
</script>

<style scoped>
/* Main Layout */
.main-content {
  margin-left: 260px;
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fafafa;
  height: 100vh;
  max-height: 100vh;
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

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: #1a1a1a;
  font-family: 'Jaldi', sans-serif;
  margin: 0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
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

.workspace {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
  height: calc(100vh - 80px); /* Subtract header height */
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

/* Chat Section - Left Column */
.workspace__chat {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  border: 1px solid #e8e8e8;
  min-width: 0;
  min-height: 0;
  max-height: 100%;
}

.workspace__chat-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 0;
}

.workspace__chat-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  max-width: 70%;
  animation: fadeIn 0.3s ease;
}

.workspace__chat-row--left {
  align-self: flex-start;
}

.workspace__chat-row--right {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.workspace__avatar-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.workspace__avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
}

.workspace__name {
  font-size: 11px;
  color: #999;
  font-family: 'Jaldi', sans-serif;
}

.workspace__name--left {
  text-align: center;
}

.workspace__name--right {
  text-align: center;
}

.workspace__bubble {
  padding: 12px 16px;
  border-radius: 16px;
  font-family: 'Jaldi', sans-serif;
  font-size: 14px;
  word-wrap: break-word;
  white-space: pre-line;
  background: #f0f0f0;
  color: #333;
  border-bottom-left-radius: 4px;
}

.workspace__chat-row--right .workspace__bubble {
  background: #001f3f;
  color: white;
  border-bottom-left-radius: 16px;
  border-bottom-right-radius: 4px;
}

.workspace__code {
  background: #1e1e1e;
  border-radius: 8px;
  padding: 12px;
  margin-top: 8px;
}

.workspace__code pre {
  margin: 0;
  color: #d4d4d4;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
}

.workspace__time {
  font-size: 11px;
  color: #999;
  margin-top: 4px;
  font-family: 'Jaldi', sans-serif;
}

.workspace__time--left {
  align-self: flex-end;
}

/* Chat Footer */
.workspace__chat-footer {
  border-top: 1px solid #e8e8e8;
  padding: 16px 24px;
  background: #fafafa;
}

.workspace__chat-input-container {
  display: flex;
  align-items: center;
  gap: 12px;
}

.workspace__mic-inner {
  width: 44px;
  height: 44px;
  border: none;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  background: #666;
  color: white;
  flex-shrink: 0;
}

.workspace__mic-inner:hover {
  background: #555;
  transform: scale(1.05);
}

.workspace__mic-inner--recording {
  background: #dc3545;
  animation: pulse 1.5s infinite;
}

.workspace__mic {
  width: 20px;
  height: 20px;
}

.workspace__input-form {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
}

.workspace__input {
  flex: 1;
  padding: 12px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 24px;
  font-size: 14px;
  font-family: 'Jaldi', sans-serif;
  transition: all 0.2s ease;
  outline: none;
}

.workspace__input:focus {
  border-color: #001f3f;
  box-shadow: 0 0 0 3px rgba(2, 74, 20, 0.1);
}

.workspace__send-btn {
  width: 44px;
  height: 44px;
  border: none;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  background: #001f3f;
  color: white;
  flex-shrink: 0;
}

.workspace__send-btn:hover:not(:disabled) {
  background: #001a33;
  transform: scale(1.05);
}

.workspace__send-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
  opacity: 0.6;
}

/* Code Panel - Right Column */
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

.workspace__refresh-notification {
  background: #001f3f;
  color: white;
  padding: 12px 16px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-family: 'Jaldi', sans-serif;
  animation: fadeIn 0.3s ease;
}

/* Editor Section */
.workspace__editor-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  border: 1px solid #e8e8e8;
  min-height: 0;
  max-height: 60%;
}

.workspace__editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid #e8e8e8;
  background: #fafafa;
  flex-shrink: 0;
}

.workspace__editor-title {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
  font-family: 'Jaldi', sans-serif;
  margin: 0;
}

.workspace__refresh-indicator {
  animation: spin 1s linear infinite;
}

.workspace__icon-btn {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  background: transparent;
  color: #666;
  padding: 0;
}

.workspace__run-btn {
  width: auto;
  padding: 6px 12px;
  gap: 6px;
  border: 1px solid #001f3f;
  color: #001f3f;
}

.workspace__run-btn:hover:not(:disabled) {
  background: #001a33;
  color: white;
  border-color: #001a33;
}

.workspace__run-btn:hover:not(:disabled) .workspace__icon-btn-icon {
  filter: brightness(0) invert(1);
}

.workspace__run-btn:hover:not(:disabled) .workspace__run-text {
  color: white;
}

.workspace__icon-btn:hover:not(:disabled) {
  background: #001f3f;
  color: #001f3f;
}

.workspace__icon-btn--primary {
  background: #001f3f;
  color: white;
}

.workspace__icon-btn--primary:hover:not(:disabled) {
  background: #001a33;
}

.workspace__icon-btn--success {
  background: #28a745;
  color: white;
}

.workspace__icon-btn--success:hover:not(:disabled) {
  background: #218838;
}

.workspace__icon-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.workspace__icon-btn-icon {
  width: 20px;
  height: 20px;
  object-fit: contain;
}

.workspace__run-text {
  font-size: 14px;
  font-family: 'Jaldi', sans-serif;
  font-weight: 500;
  color: inherit;
}

.workspace__output-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.workspace__icon-btn.active {
  background: #001f3f;
  color: white;
}

.workspace__icon-btn.active .workspace__icon-btn-icon {
  filter: brightness(0) invert(1);
}

.workspace__editor-wrapper {
  flex: 1;
  overflow: hidden;
  min-height: 0;
  max-height: 100%;
  display: flex;
}

.workspace__editor-toolbar {
  width: 50px;
  background: #f5f5f5;
  border-right: 1px solid #e8e8e8;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 0;
  gap: 8px;
  flex-shrink: 0;
}

.workspace__toolbar-btn {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  background: transparent;
  color: #666;
  padding: 0;
}

.workspace__toolbar-btn:hover:not(:disabled) {
  background: #e8e8e8;
  color: #001f3f;
}

.workspace__toolbar-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.workspace__toolbar-icon {
  width: 20px;
  height: 20px;
  object-fit: contain;
}

.workspace__editor-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
  max-height: 100%;
}

.workspace__editor-file-info {
  padding: 8px 16px;
  background: #f9f9f9;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-family: 'Courier New', monospace;
  color: #666;
  flex-shrink: 0;
}

.workspace__current-file {
  font-weight: 500;
  color: #1a1a1a;
}

.workspace__editor-content :deep(.monaco-editor-container) {
  flex: 1;
  min-height: 0;
}

/* Output Section */
.workspace__output-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  border: 1px solid #e8e8e8;
  min-height: 0;
  max-height: 40%;
  transition: flex 0.3s ease;
}

.workspace__output-section.expanded {
  flex: 1 1 100%;
  min-height: 100%;
}

.workspace__output-header {
  display: flex;
  flex-direction: column;
  background: #fafafa;
  border-bottom: 1px solid #e8e8e8;
}

.workspace__output-header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
}

.workspace__output-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
  font-family: 'Jaldi', sans-serif;
  margin: 0;
}

/* Mode Tabs - Folder Tab Style */
.workspace__mode-tabs {
  display: flex;
  gap: 0;
  background: #262525;
  padding: 4px 4px 0 4px;
  border-top: 1px solid #e8e8e8;
}

.workspace__mode-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 1px solid rgb(180, 176, 176);
  background: transparent;
  border-radius: 6px 6px 0 0;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: 'Jaldi', sans-serif;
  font-size: 14px;
  font-weight: 500;
  color: #ffffff;
  position: relative;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
}

.workspace__mode-tab:hover {
  background: rgba(255, 255, 255, 0.5);
  color: #333;
}

.workspace__mode-tab.active {
  background: white;
  border-bottom: 2px solid white;
  font-weight: 600;
  z-index: 1;
  margin-bottom: -2px;
}

/* Text Mode Tab - Dark blue color */
.workspace__mode-tab:first-child.active {
  background: #1565c0;
  color: #ffffff;
  border-bottom-color: #1565c0;
}

.workspace__mode-tab:first-child:hover {
  background: rgba(21, 101, 192, 0.8);
  color: #ffffff;
}

/* Graphic Mode Tab - Dark green color */
.workspace__mode-tab:last-child.active {
  background: #2e7d32;
  color: #ffffff;
  border-bottom-color: #2e7d32;
}

.workspace__mode-tab:last-child:hover {
  background: rgba(46, 125, 50, 0.8);
  color: #ffffff;
}

.workspace__mode-tab-icon {
  width: 16px;
  height: 16px;
  object-fit: contain;
}

.workspace__output {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background: #1e1e1e;
  color: #d4d4d4;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.6;
  min-height: 0;
}

.workspace__output pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}

/* Status Bars */
.workspace__status-bar {
  position: fixed;
  top: 80px;
  left: 260px;
  right: 0;
  background: white;
  border-bottom: 1px solid #e8e8e8;
  padding: 12px 24px;
  z-index: 1000;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.workspace__status-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.workspace__status-spinner {
  animation: spin 1s linear infinite;
}

.workspace__status-text {
  font-size: 14px;
  font-family: 'Jaldi', sans-serif;
  color: #1a1a1a;
}

.workspace__status-progress {
  flex: 1;
  height: 4px;
  background: #e8e8e8;
  border-radius: 2px;
  overflow: hidden;
}

.workspace__status-progress-bar {
  height: 100%;
  background: #001f3f;
  animation: progress 2s ease-in-out infinite;
}

/* Methods Panel */
.workspace__methods-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.3);
  z-index: 999;
  animation: fadeIn 0.2s ease;
}

.workspace__methods-panel {
  position: fixed;
  top: 0;
  right: -400px;
  width: 400px;
  height: 100vh;
  background: white;
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.1);
  transition: right 0.3s ease;
  z-index: 1000;
  display: flex;
  flex-direction: column;
}

.workspace__methods-panel.open {
  right: 0;
}

.workspace__methods-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e8e8e8;
  background: white;
}

.workspace__methods-panel-title {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
  font-family: 'Jaldi', sans-serif;
  margin: 0;
}

.workspace__methods-panel-close {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  background: transparent;
  color: #666;
}

.workspace__methods-panel-close:hover {
  background: #f0f0f0;
  color: #1a1a1a;
}

.workspace__methods-panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.workspace__methods-class {
  margin-bottom: 24px;
}

.workspace__method-card {
  background: #f9f9f9;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.workspace__method-card:hover {
  background: #f0f0f0;
  border-color: #001f3f;
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.workspace__method-card-name {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  font-family: 'Jaldi', sans-serif;
  margin-bottom: 8px;
}

.workspace__method-card-params {
  font-size: 14px;
  color: #666;
  font-family: 'Courier New', monospace;
}

/* Scrollbars */
.workspace__chat-scroll::-webkit-scrollbar,
.workspace__output::-webkit-scrollbar,
.workspace__methods-panel-content::-webkit-scrollbar {
  width: 8px;
}

.workspace__chat-scroll::-webkit-scrollbar-track,
.workspace__methods-panel-content::-webkit-scrollbar-track {
  background: transparent;
}

.workspace__chat-scroll::-webkit-scrollbar-thumb,
.workspace__methods-panel-content::-webkit-scrollbar-thumb {
  background: #c0c0c0;
  border-radius: 4px;
}

.workspace__chat-scroll::-webkit-scrollbar-thumb:hover,
.workspace__methods-panel-content::-webkit-scrollbar-thumb:hover {
  background: #a0a0a0;
}

.workspace__output::-webkit-scrollbar-track {
  background: #2d2d2d;
}

.workspace__output::-webkit-scrollbar-thumb {
  background: #555;
  border-radius: 4px;
}

.workspace__output::-webkit-scrollbar-thumb:hover {
  background: #666;
}

/* Animations */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes progress {
  0% {
    width: 0%;
  }
  50% {
    width: 70%;
  }
  100% {
    width: 100%;
  }
}

/* Function Panel Toggle Styles */
.function-panel-toggle {
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  background: transparent;
}

.function-panel-toggle:hover {
  background: #f0f0f0;
}

.function-panel-icon {
  width: 28px;
  height: 28px;
  object-fit: contain;
}

/* Function Panel Styles */
.function-panel {
  position: fixed;
  top: 0;
  right: -400px;
  width: 400px;
  height: 100vh;
  background: white;
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.1);
  transition: right 0.3s ease;
  z-index: 1000;
  display: flex;
  flex-direction: column;
}

.function-panel.open {
  right: 0;
}

.function-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e8e8e8;
  background: white;
}

.function-panel-title {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
  font-family: 'Jaldi', sans-serif;
  margin: 0;
}

.function-panel-close {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  background: transparent;
  color: #666;
}

.function-panel-close:hover {
  background: #f0f0f0;
  color: #1a1a1a;
}

.function-panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.function-panel-class {
  margin-bottom: 24px;
}

.function-panel-class-title {
  font-size: 16px;
  font-weight: 600;
  color: #001f3f;
  font-family: 'Jaldi', sans-serif;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid #001f3f;
}

.function-item {
  background: #f9f9f9;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.function-item:hover {
  background: #f0f0f0;
  border-color: #001f3f;
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.function-item-name {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  font-family: 'Jaldi', sans-serif;
  margin-bottom: 8px;
}

.function-item-description {
  font-size: 14px;
  color: #666;
  font-family: 'Jaldi', sans-serif;
  line-height: 1.5;
  margin-bottom: 8px;
}

.function-item-file {
  font-size: 12px;
  color: #001f3f;
  font-family: 'Courier New', monospace;
  font-weight: 500;
  background: #f0f7f2;
  padding: 4px 8px;
  border-radius: 4px;
  display: inline-block;
}

.function-panel-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: #999;
  font-family: 'Jaldi', sans-serif;
}

.function-panel-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.3);
  z-index: 999;
  animation: fadeIn 0.2s ease;
}

/* Responsive */
@media (max-width: 768px) {
  .main-content {
    margin-left: 0;
  }
  
  .workspace {
    margin-left: 0;
  }

  .workspace__container {
    flex-direction: column;
    padding: 16px;
    height: calc(100vh - 20px);
  }

  .workspace__chat,
  .workspace__code-panel {
    min-height: 300px;
  }

  .workspace__methods-panel {
    width: 100%;
    right: -100%;
  }

  .workspace__methods-panel.open {
    right: 0;
  }

  .workspace__status-bar {
    left: 0;
  }

  .function-panel {
    width: 100%;
    right: -100%;
  }
  
  .function-panel.open {
    right: 0;
  }
  
  .function-panel-toggle {
    width: 36px;
    height: 36px;
  }
  
  .function-panel-icon {
    width: 24px;
    height: 24px;
  }
}

/* Success Dialog */
.workspace__success-dialog-overlay {
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

.workspace__success-dialog {
  background: white;
  border-radius: 12px;
  padding: 24px 32px;
  text-align: center;
  box-shadow: 0 4px 20px rgba(0, 31, 63, 0.15);
  border-left: 4px solid #001f3f;
  display: flex;
  align-items: center;
  gap: 16px;
  cursor: default;
}

.workspace__success-dialog-icon {
  flex-shrink: 0;
}

.workspace__success-dialog-message {
  font-size: 16px;
  font-weight: 500;
  color: #1a1a1a;
  font-family: 'Jaldi', sans-serif;
  margin: 0;
}

/* Dialog Transition */
.dialog-fade-enter-active,
.dialog-fade-leave-active {
  transition: opacity 0.2s ease;
}

.dialog-fade-enter-from,
.dialog-fade-leave-to {
  opacity: 0;
}

.dialog-fade-enter-active .workspace__success-dialog,
.dialog-fade-leave-active .workspace__success-dialog {
  transition: transform 0.2s ease;
}

.dialog-fade-enter-from .workspace__success-dialog {
  transform: translateY(-10px);
}

.dialog-fade-leave-to .workspace__success-dialog {
  transform: translateY(-10px);
}
</style>
