<template>
  <div class="app-container">
    <Sidebar />
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
                placeholder="Type your message..."
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

        <div class="workspace__editor-section">
          <div class="workspace__editor-header">
            <div class="workspace__editor-title">
              <FilePanel :conversationId="parseInt(conversationId || '0')" />
              <h3>{{ currentFile }}</h3>
              <div v-if="isRefreshing" class="workspace__refresh-indicator" title="Refreshing file content...">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 2a10 10 0 0110 10" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                    <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite"/>
                  </path>
                </svg>
              </div>
            </div>
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
                @click="handleUndo"
                aria-label="Undo"
                title="Undo (Ctrl+Z)"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M3 7v6h6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M21 17a9 9 0 00-9-9 9 9 0 00-9 9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>

              <button
                class="workspace__icon-btn"
                @click="handleRedo"
                aria-label="Redo"
                title="Redo (Ctrl+Y)"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M21 7v6h-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M3 17a9 9 0 019-9 9 9 0 019 9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>

              <button
                class="workspace__icon-btn workspace__icon-btn--primary"
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
                <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M17 21v-8H7v8M7 3v5h8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>

              <button
                class="workspace__icon-btn workspace__icon-btn--success"
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
                <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M5 3l14 9-14 9V3z" fill="currentColor"/>
                </svg>
              </button>
            </div>
          </div>
          <div class="workspace__editor-wrapper">
            <MonacoEditor
              ref="editorRef"
              :key="`${conversationId}-${currentFile}`"
              :code="currentCode"
              @update:code="handleEditorChange"
              language="python"
            />
          </div>
        </div>

        <div class="workspace__output-section">
          <div class="workspace__output-header">
            <h3>Output</h3>
            <div class="workspace__output-actions">
              <!-- Mode Toggle Switch -->
              <div class="workspace__mode-toggle" @click="toggleOutputMode">
                <div class="workspace__toggle-track" :class="{ 'text-mode': isTextMode, 'graphic-mode': !isTextMode }">
                  <div class="workspace__toggle-label-icon workspace__toggle-label-left" :class="{ 'active': isTextMode }">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M3 5h18v2H3V5zm0 6h18v2H3v-2zm0 6h18v2H3v-2z" fill="currentColor"/>
                    </svg>
                  </div>
                  <div class="workspace__toggle-slider" :class="{ 'active': isTextMode }">
                    <svg v-if="isTextMode" width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M3 5h18v2H3V5zm0 6h18v2H3v-2zm0 6h18v2H3v-2z" fill="currentColor"/>
                    </svg>
                    <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M3 3h8v8H3V3zm10 0h8v8h-8V3zM3 13h8v8H3v-8zm10 0h8v8h-8v-8z" fill="currentColor"/>
                    </svg>
                  </div>
                  <div class="workspace__toggle-label-icon workspace__toggle-label-right" :class="{ 'active': !isTextMode }">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M3 3h8v8H3V3zm10 0h8v8h-8V3zM3 13h8v8H3v-8zm10 0h8v8h-8v-8z" fill="currentColor"/>
                    </svg>
                  </div>
                </div>
              </div>
              <button
                class="workspace__icon-btn"
                @click="output = ''"
                aria-label="Clear output"
                title="Clear output"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
              </button>
            </div>
          </div>
          <div class="workspace__output">
            <div
              v-if="!isTextMode"
              style="width: 100%; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; background-color: #1e1e1e; padding: 10px;"
            >
              <div style="margin-bottom: 10px; color: #d4d4d4; font-size: 14px;">
                Turtle Graphics Stream
              </div>
              <img
                id="turtle-video"
                style="width: 100%; height: calc(100% - 40px); object-fit: contain; border: 1px solid #444; border-radius: 4px; background-color: #000;"
                alt="Turtle graphics stream"
              />
            </div>
            <pre v-else>{{ output || 'Output will appear here...' }}</pre>
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
        <span class="workspace__status-text">Transcribing your voice...</span>
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
        <span class="workspace__status-text">Processing and mapping command...</span>
        <div class="workspace__status-progress">
          <div class="workspace__status-progress-bar"></div>
        </div>
      </div>
    </div>

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
          {{ availableMethods?.file_name || 'Available Methods' }}
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
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import Sidebar from '../components/Sidebar.vue';
import MonacoEditor from '../components/MonacoEditor.vue';
import FilePanel from '../components/FilePanel.vue';
import { messageAPI, conversationAPI, executeAPI, analyzeAPI, paraphraseAPI, fileAPI, translateAPI } from '../services/api';
import { useAuth } from '../composables/useAuth';
import { useCode } from '../composables/useCode';
import { useFile } from '../composables/useFile';
import { useLanguage } from '../composables/useLanguage';
import { voiceService } from '../services/voiceService';
import scorpioIcon from '../assets/scorpio.svg';
import userIcon from '../assets/user.svg';

export default {
  name: 'Workspace',
  components: {
    Sidebar,
    MonacoEditor,
    FilePanel
  },
  setup() {
    const route = useRoute();
    const router = useRouter();
    const { user } = useAuth();
    const { code, setCode, syncCodeFromBackend, setConversationId } = useCode();
    const { language } = useLanguage();
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
        console.log('');
        console.log('═════════════════════════════════════════════════════════════');
        console.log('📝 COMMAND PROCESSING PIPELINE');
        console.log('═════════════════════════════════════════════════════════════');
        console.log('Current Language:', language.value === 'en' ? 'English' : 'Thai');
        console.log('STT Model Used:', language.value === 'en' ? 'Whisper English (distil-whisper/distil-large-v3)' : 'Whisper Thai (nectec/Pathumma-whisper-th-large-v3)');
        console.log('Original Input:', msgText);
        console.log('─────────────────────────────────────────────────────────────');

        // Step 1: Translate Thai to English if needed
        let commandForAnalysis = msgText;
        let translatedText = null;

        if (language.value === 'th') {
          try {
            console.log('🔄 TRANSLATION STEP');
            console.log('Calling Google Cloud Translate API...');
            console.log('Source Language: Thai');
            console.log('Target Language: English');

            const translateResult = await translateAPI.translateToEnglish(msgText);
            commandForAnalysis = translateResult.translated_text;
            translatedText = translateResult.translated_text;

            console.log('✅ Translation Result:', translatedText);
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
          console.log('─────────────────────────────────────────────────────────────');
        }

        // Step 2: Save original message (Thai or English)
        const userMsg = await messageAPI.create(parseInt(conversationId.value), 'user', msgText);

        // Step 3: Analyze using English command
        console.log('🔍 COMMAND ANALYSIS STEP');
        console.log('Text for Analysis:', commandForAnalysis);
        const data = await analyzeAPI.analyzeCommand(Number(conversationId.value), commandForAnalysis);

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
        console.log('─────────────────────────────────────────────────────────────');
        console.log('📊 SUMMARY');
        console.log('Transcribed Text:', msgText);
        console.log('Translated Text:', translatedText || 'null');
        console.log('Final Processed Command(s):', summary);
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
            await messageAPI.create(parseInt(conversationId.value), 'system', successMessage);
            const speechMessage = commandCount > 1
              ? `${commandCount} commands appended successfully`
              : 'Command appended successfully';
            voiceService.speak(speechMessage);
            await fetchMessages();
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
      isTextMode.value = !isTextMode.value;
      // Save preference to localStorage
      localStorage.setItem('outputMode', isTextMode.value ? 'text' : 'graphic');
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

              const result = await voiceService.transcribe(audioFile, language.value);
              const text = result.text || `[Error: ${result.error || 'Unknown'}]`;

              if (text.includes('[Error')) {
                console.log('❌ Transcription failed:', text);
                voiceService.speak("I couldn't understand that. Please try again");
              } else {
                console.log('✅ Transcribed Text:', text);
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
      isMethodsPanelOpen,
      formatTime,
      handleSend,
      handleSave,
      handleUndo,
      handleRedo,
      handleRun,
      toggleOutputMode,
      handleToggleParaphrases,
      handleMicClick,
      handleEditorChange,
      toggleMethodsPanel,
      insertMethod,
    };
  }
};
</script>

<style src="../pages/styles/Workspace.css" scoped></style>
