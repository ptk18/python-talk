<template>
  <div class="app-container">
    <Sidebar />
    <div class="turtle-playground">
      <div class="turtle-playground__container">
        <!-- Left Column: Code Editor + Available Methods -->
        <div class="turtle-playground__left-column">
          <!-- Code Editor Section -->
          <section class="turtle-playground__code-panel">
            <div class="turtle-playground__code-header">
              <h3>{{ language === 'th' ? 'โค้ดเอดิเตอร์' : 'Code Editor' }}</h3>
              <span class="turtle-playground__code-hint">{{ language === 'th' ? 'คำสั่งเสียงจะถูกเพิ่มที่นี่อัตโนมัติ' : 'Voice commands will be appended here automatically' }}</span>
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

          <!-- Available Methods Section -->
          <section class="turtle-playground__methods-panel">
            <div class="turtle-playground__methods-header">
              <h3>{{ language === 'th' ? 'เมธอดที่ใช้ได้' : 'Available Methods' }}</h3>
              <span v-if="activeModules.length > 0" class="turtle-playground__module-badge">{{ activeModules[0] }}</span>
            </div>
            <div class="turtle-playground__methods-scroll">
              <div v-if="availableMethods.length === 0" class="turtle-playground__methods-empty">
                {{ language === 'th' ? 'พิมพ์ import statement เพื่อดูเมธอดที่มี' : 'Type an import statement to see available methods' }}
              </div>
              <div v-else>
                <div
                  v-for="(category, catIndex) in methodCategories"
                  :key="catIndex"
                  class="turtle-playground__method-category"
                >
                  <div class="turtle-playground__category-header" @click="toggleCategory(category.name)">
                    <span class="turtle-playground__category-name">{{ category.name }}</span>
                    <span class="turtle-playground__category-count">{{ category.methods.length }} methods</span>
                    <svg
                      :class="['turtle-playground__category-chevron', { 'expanded': expandedCategories.includes(category.name) }]"
                      width="16" height="16" viewBox="0 0 24 24" fill="none"
                    >
                      <path d="M6 9l6 6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                  </div>
                  <div v-if="expandedCategories.includes(category.name)" class="turtle-playground__method-chips">
                    <button
                      v-for="method in category.methods"
                      :key="method.name"
                      class="turtle-playground__method-chip"
                      @click="insertMethod(method)"
                      :title="method.docstring || method.name"
                    >
                      {{ method.name }}({{ method.params.join(', ') }})
                    </button>
                  </div>
                </div>
              </div>
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
                <button
                  class="turtle-playground__btn turtle-playground__btn--secondary"
                  @click="handleClear"
                >
                  {{ t.turtlePlayground.clearCanvas }}
                </button>
                <button
                  class="turtle-playground__btn turtle-playground__btn--secondary"
                  @click="handleReset"
                >
                  {{ t.turtlePlayground.resetTurtle }}
                </button>
              </div>
            </div>
            <div class="turtle-playground__canvas-wrapper" ref="canvasWrapper">
              <canvas
                ref="turtleCanvas"
                width="600"
                height="450"
                class="turtle-playground__canvas"
              ></canvas>
              <div
                ref="turtleIndicator"
                class="turtle-playground__indicator"
              ></div>
            </div>
          </section>

          <!-- Command Input Section -->
          <section class="turtle-playground__command-panel">
            <div class="turtle-playground__command-header">
              <h3>{{ language === 'th' ? 'คำสั่ง' : 'Command Input' }}</h3>
            </div>
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
                  :placeholder="language === 'th' ? 'เช่น forward(100) หรือ t.left(90)' : 'e.g., forward(100) or t.left(90)'"
                  v-model="commandText"
                  @keydown.enter.prevent="handleRunCommand"
                />
                <button
                  class="turtle-playground__run-btn"
                  @click="handleRunCommand"
                  :disabled="isProcessing"
                >
                  {{ language === 'th' ? 'รัน' : 'Run' }}
                </button>
              </div>
              <div class="turtle-playground__command-output">
                <pre v-if="commandOutput">{{ commandOutput }}</pre>
                <span v-else class="turtle-playground__output-placeholder">{{ language === 'th' ? 'ผลลัพธ์จะแสดงที่นี่...' : 'Command output will appear here...' }}</span>
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
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue';
import Sidebar from '../components/Sidebar.vue';
import MonacoEditor from '../components/MonacoEditor.vue';
import { useLanguage } from '../composables/useLanguage';
import { useTranslations } from '../utils/translations';
import { voiceService } from '../services/voiceService';
import { turtleAPI, translateAPI } from '../services/api';
import { Turtle } from '../lib/turtle';
import { parseTurtleCommand } from '../lib/turtleCommandParser';

export default {
  name: 'TurtlePlayground',
  components: { Sidebar, MonacoEditor },
  setup() {
    const { language } = useLanguage();
    const t = computed(() => useTranslations(language.value));

    // Refs
    const turtleCanvas = ref(null);
    const turtleIndicator = ref(null);
    const canvasWrapper = ref(null);
    const monacoEditor = ref(null);
    const commandText = ref('');
    const commandOutput = ref('');
    const codeContent = ref(`import turtle

t = turtle.Turtle()
`);
    const isRecording = ref(false);
    const isTranscribing = ref(false);
    const isProcessing = ref(false);
    const mediaRecorder = ref(null);
    const audioChunks = ref([]);

    const availableMethods = ref([]);
    const methodCategories = ref([]);
    const activeModules = ref(['turtle']);
    const expandedCategories = ref([]);
    let turtle = null;

    const fetchTurtleMethods = async () => {
      try {
        const response = await turtleAPI.getMethods();
        if (response.success) {
          availableMethods.value = response.methods;

          const categories = {};
          response.methods.forEach(method => {
            const cat = method.category || 'other';
            if (!categories[cat]) categories[cat] = [];
            categories[cat].push(method);
          });

          methodCategories.value = Object.entries(categories).map(([name, methods]) => ({
            name, methods
          }));

          if (methodCategories.value.length > 0) {
            expandedCategories.value = [methodCategories.value[0].name];
          }
        }
      } catch (err) {
        console.error('[TurtlePlayground] Failed to fetch methods:', err);
      }
    };

    const handleCodeUpdate = (newCode) => {
      codeContent.value = newCode;
    };

    const toggleCategory = (categoryName) => {
      const index = expandedCategories.value.indexOf(categoryName);
      if (index === -1) {
        expandedCategories.value.push(categoryName);
      } else {
        expandedCategories.value.splice(index, 1);
      }
    };

    const insertMethod = (method) => {
      commandText.value = `${method.name}(${method.params.join(', ')})`;
    };

    const appendToCodeEditor = (command, comment = null) => {
      const newLine = comment ? `\n# ${comment}\n${command}` : `\n${command}`;
      codeContent.value += newLine;
    };

    onMounted(async () => {
      await nextTick();
      if (turtleCanvas.value) {
        turtle = new Turtle(turtleCanvas.value, turtleIndicator.value);
        try {
          await turtleAPI.prewarmPipeline();
        } catch (err) {
          console.warn('[TurtlePlayground] Failed to pre-warm pipeline:', err);
        }
        await fetchTurtleMethods();
      }
    });

    const executeDirectCommand = (cmd) => {
      if (!turtle) return { success: false, error: 'Turtle not initialized' };
      return parseTurtleCommand(cmd, turtle);
    };

    const processNaturalLanguageCommand = async (cmd, originalText = null) => {
      isProcessing.value = true;

      try {
        let commandForAnalysis = cmd;

        if (language.value === 'th') {
          const translateResult = await translateAPI.translateToEnglish(cmd);
          commandForAnalysis = translateResult.translated_text;
        }

        const result = await turtleAPI.analyzeCommand(commandForAnalysis, 'en');

        if (result.success && (result.executable || result.executables)) {
          const commands = result.executables || [result.executable];
          const outputs = [];
          const codeLines = [];
          let allSuccess = true;

          for (const executable of commands) {
            const execResult = executeDirectCommand(executable);
            if (execResult.success) {
              outputs.push(`${executable} -> ${execResult.result}`);
              codeLines.push(`t.${executable}`);
            } else {
              outputs.push(`${executable} -> Error: ${execResult.error}`);
              allSuccess = false;
            }
          }

          commandOutput.value = outputs.join('\n');
          appendToCodeEditor(codeLines.join('\n'), originalText || cmd);

          if (allSuccess) {
            voiceService.speak(t.value.turtlePlayground.commandExecuted);
            return { success: true, executables: commands };
          } else {
            voiceService.speak(t.value.turtlePlayground.invalidCommand);
            return { success: false, error: 'Some commands failed' };
          }
        } else {
          commandOutput.value = result.error || t.value.turtlePlayground.invalidCommand;
          voiceService.speak(t.value.turtlePlayground.invalidCommand);
          return { success: false, error: result.error };
        }
      } catch (err) {
        console.error('[TurtlePlayground] Command error:', err);
        commandOutput.value = 'Error: ' + err.message;
        voiceService.speak(t.value.turtlePlayground.invalidCommand);
        return { success: false, error: err.message };
      } finally {
        isProcessing.value = false;
      }
    };

    const handleRunCommand = async () => {
      if (!commandText.value.trim() || isProcessing.value) return;

      const cmd = commandText.value.trim();
      const directResult = executeDirectCommand(cmd);

      if (directResult.success) {
        commandOutput.value = directResult.result;
        appendToCodeEditor(`t.${cmd}`);
        voiceService.speak(t.value.turtlePlayground.commandExecuted);
      } else {
        await processNaturalLanguageCommand(cmd, cmd);
      }
    };

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
                commandOutput.value = 'Transcription failed. Please try again.';
                voiceService.speak(t.value.turtlePlayground.invalidCommand);
                isTranscribing.value = false;
              }
            } catch (err) {
              commandOutput.value = 'Error: ' + err.message;
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

    const handleClear = () => {
      if (turtle) {
        turtle.clear();
        commandOutput.value = 'Canvas cleared';
        appendToCodeEditor('t.clear()');
        voiceService.speak('Canvas cleared');
      }
    };

    const handleReset = () => {
      if (turtle) {
        turtle.reset();
        commandOutput.value = 'Turtle reset';
        appendToCodeEditor('t.reset()');
        voiceService.speak('Turtle reset');
      }
    };

    return {
      t,
      language,
      turtleCanvas,
      turtleIndicator,
      canvasWrapper,
      monacoEditor,
      commandText,
      commandOutput,
      codeContent,
      isRecording,
      isTranscribing,
      isProcessing,
      availableMethods,
      methodCategories,
      activeModules,
      expandedCategories,
      handleCodeUpdate,
      toggleCategory,
      insertMethod,
      handleRunCommand,
      handleMicClick,
      handleClear,
      handleReset,
    };
  }
};
</script>

<style>
@import '../pages/styles/TurtlePlayground.css';
</style>
