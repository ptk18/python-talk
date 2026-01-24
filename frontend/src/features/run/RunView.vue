<template>
  <div class="app-container">
    <Sidebar />
    <main class="main-content">
      <header class="top-header">
        <h2 class="page-title">Code Space</h2>
        <button 
          class="function-panel-toggle" 
          @click="toggleFunctionPanel"
          :title="isFunctionPanelOpen ? 'Hide functions panel' : 'Show functions panel'"
        >
          <img :src="functionPanelIcon" alt="Functions" class="function-panel-icon" />
        </button>
      </header>
      
      <div class="content-area run-content">
        <!-- Left Column: Chat (matching Chat.vue exactly) -->
        <div class="chat-column">
          <div class="chat-content">
            <div class="chat-container">
              <div class="chat-messages" ref="messagesContainer">
                <div 
                  v-for="(message, index) in messages" 
                  :key="index"
                  :class="['message', message.type]"
                >
                  <div class="message-content">{{ message.text }}</div>
                  <div class="message-time">{{ message.time }}</div>
                </div>
                <div v-if="messages.length === 0" class="empty-state">
                  <p>Start a conversation by typing a message or using the microphone</p>
                </div>
              </div>
              
              <div class="chat-input-container">
                <div class="input-wrapper">
                  <input 
                    type="text" 
                    v-model="inputMessage"
                    @keyup.enter="sendMessage"
                    placeholder="Type your message..."
                    class="chat-input"
                    :disabled="isRecording"
                  />
                  <button 
                    class="mic-button"
                    :class="{ 'recording': isRecording }"
                    @click="toggleRecording"
                    :title="isRecording ? 'Stop recording' : 'Start voice recording'"
                  >
                    <svg v-if="!isRecording" width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M12 14C13.1 14 14 13.1 14 12V6C14 4.9 13.1 4 12 4C10.9 4 10 4.9 10 6V12C10 13.1 10.9 14 12 14ZM19 12C19 15.87 15.87 19 12 19V21H16V23H8V21H12V19C8.13 19 5 15.87 5 12H7C7 14.76 9.24 17 12 17C14.76 17 17 14.76 17 12H19Z" fill="currentColor"/>
                    </svg>
                    <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M12 14C11.45 14 11 13.55 11 13V7C11 6.45 11.45 6 12 6C12.55 6 13 6.45 13 7V13C13 13.55 12.55 14 12 14ZM10 19C10 19.55 10.45 20 11 20H13C13.55 20 14 19.55 14 19V18H10V19ZM16 10H20C20.55 10 21 10.45 21 11C21 11.55 20.55 12 20 12H16C15.45 12 15 11.55 15 11C15 10.45 15.45 10 16 10ZM4 10H8C8.55 10 9 10.45 9 11C9 11.55 8.55 12 8 12H4C3.45 12 3 11.55 3 11C3 10.45 3.45 10 4 10Z" fill="currentColor"/>
                    </svg>
                  </button>
                  <button 
                    class="send-button"
                    @click="sendMessage"
                    :disabled="!inputMessage.trim() && !isRecording"
                  >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M2.01 21L23 12L2.01 3L2 10L17 12L2 14L2.01 21Z" fill="currentColor"/>
                    </svg>
                  </button>
                </div>
                <div v-if="isRecording" class="recording-indicator">
                  <span class="recording-dot"></span>
                  Recording...
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Right Column: Code Input (top) and Output (bottom) -->
        <div class="code-output-column" :class="{ 'output-expanded': isOutputExpanded }">
          <!-- Code Input Section -->
          <div class="code-section" :class="{ 'hidden': isOutputExpanded }">
            <div class="code-header">
              <h3 class="section-title">Code Editor</h3>
              <button class="run-button" @click="runCode" :disabled="isRunning">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M8 5V19L19 12L8 5Z" fill="currentColor"/>
                </svg>
                <span>{{ isRunning ? 'Running...' : 'Run' }}</span>
              </button>
            </div>
            <div class="code-editor-wrapper">
              <div class="code-toolbar">
                <input 
                  type="file" 
                  ref="fileInput"
                  @change="handleFileUpload"
                  accept=".py"
                  style="display: none"
                  id="file-upload"
                />
                <label for="file-upload" class="toolbar-button" title="Upload Python file">
                  <img :src="uploadFileIcon" alt="Upload file" class="toolbar-icon" />
                </label>
                <button class="toolbar-button" @click="undoCode" title="Undo" :disabled="!canUndo">
                  <img :src="undoIcon" alt="Undo" class="toolbar-icon" />
                </button>
                <button class="toolbar-button" @click="redoCode" title="Redo" :disabled="!canRedo">
                  <img :src="redoIcon" alt="Redo" class="toolbar-icon" />
                </button>
              </div>
              <textarea
                v-model="code"
                class="code-input"
                placeholder="Enter your Python code here..."
                spellcheck="false"
              ></textarea>
            </div>
          </div>
          
          <!-- Output Section -->
          <div class="output-section" :class="{ 'expanded': isOutputExpanded }">
            <div class="output-header">
              <h3 class="section-title">Output</h3>
              <div class="output-actions">
                <!-- Mode Toggle Switch -->
                <div class="mode-toggle" @click="toggleOutputMode">
                  <div class="toggle-track" :class="{ 'text-mode': isTextMode, 'graphic-mode': !isTextMode }">
                    <div class="toggle-label-icon toggle-label-left" :class="{ 'active': isTextMode }">
                      <img :src="textModeIcon" alt="Text mode" class="toggle-label-icon-img" />
                    </div>
                    <div class="toggle-slider" :class="{ 'active': isTextMode }">
                      <img v-if="isTextMode" :src="textModeIcon" alt="Text mode" class="toggle-icon" />
                      <img v-else :src="graphicModeIcon" alt="Graphic mode" class="toggle-icon" />
                    </div>
                    <div class="toggle-label-icon toggle-label-right" :class="{ 'active': !isTextMode }">
                      <img :src="graphicModeIcon" alt="Graphic mode" class="toggle-label-icon-img" />
                    </div>
                  </div>
                </div>
                <button 
                  class="span-button" 
                  @click="toggleOutputSpan" 
                  :title="isOutputExpanded ? 'Collapse output' : 'Expand output to full column'"
                >
                  <img :src="spanIcon" alt="Span output" class="toolbar-icon" />
                </button>
                <button class="clear-button" @click="clearOutput" title="Clear output">
                  <img :src="clearIcon" alt="Clear output" class="toolbar-icon" />
                </button>
              </div>
            </div>
            <div class="output-content" ref="outputContainer" :class="{ 'text-mode': isTextMode, 'graphic-mode': !isTextMode }">
              <div v-if="output.length === 0" class="empty-output">
                <p>Output will appear here after running your code</p>
              </div>
              <!-- Text Mode Output -->
              <div v-else-if="isTextMode" class="output-lines">
                <div 
                  v-for="(line, index) in output" 
                  :key="index"
                  :class="['output-line', line.type]"
                >
                  <span class="output-prefix" v-if="line.type === 'input'">In:</span>
                  <span class="output-prefix" v-else-if="line.type === 'output'">Out:</span>
                  <span class="output-prefix" v-else-if="line.type === 'error'">Error:</span>
                  <pre class="output-text">{{ line.content }}</pre>
                </div>
              </div>
              <!-- Graphic Mode Output -->
              <div v-else class="output-graphic">
                <div 
                  v-for="(line, index) in output" 
                  :key="index"
                  :class="['graphic-line', line.type]"
                >
                  <div v-if="line.type === 'input'" class="graphic-input">
                    <div class="graphic-label">Input</div>
                    <div class="graphic-content">{{ line.content }}</div>
                  </div>
                  <div v-else-if="line.type === 'output'" class="graphic-output">
                    <div class="graphic-label">Output</div>
                    <div class="graphic-content">{{ line.content }}</div>
                  </div>
                  <div v-else-if="line.type === 'error'" class="graphic-error">
                    <div class="graphic-label">Error</div>
                    <div class="graphic-content">{{ line.content }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Overlay for function panel -->
      <div 
        v-if="isFunctionPanelOpen" 
        class="function-panel-overlay" 
        @click="toggleFunctionPanel"
      ></div>
      
      <!-- Right Functions Panel -->
      <div class="function-panel" :class="{ 'open': isFunctionPanelOpen }">
        <div class="function-panel-header">
          <h3 class="function-panel-title">Available Functions</h3>
          <button class="function-panel-close" @click="toggleFunctionPanel" title="Close panel">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </button>
        </div>
        <div class="function-panel-content">
          <div 
            v-for="func in availableFunctions" 
            :key="func.id"
            class="function-item"
            @click="selectFunction(func)"
          >
            <div class="function-item-name">{{ func.name }}</div>
            <div class="function-item-description">{{ func.description }}</div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import Sidebar from '@/shared/components/Sidebar.vue'
import uploadFileIcon from '@/assets/R-uploadfile.svg'
import undoIcon from '@/assets/R-undo.svg'
import redoIcon from '@/assets/R-redo.svg'
import spanIcon from '@/assets/R-span.svg'
import clearIcon from '@/assets/R-clear.svg'
import textModeIcon from '@/assets/R-textmode.svg'
import graphicModeIcon from '@/assets/R-graphicmode.svg'
import functionPanelIcon from '@/assets/R-functionpanel.svg'

export default {
  name: 'Run',
  components: {
    Sidebar
  },
  data() {
    return {
      uploadFileIcon: uploadFileIcon,
      undoIcon: undoIcon,
      redoIcon: redoIcon,
      spanIcon: spanIcon,
      clearIcon: clearIcon,
      textModeIcon: textModeIcon,
      graphicModeIcon: graphicModeIcon,
      functionPanelIcon: functionPanelIcon,
      isTextMode: true,
      isFunctionPanelOpen: false,
      availableFunctions: [
        { 
          id: 1, 
          name: 'Voice Recognition', 
          description: 'Convert speech to text using advanced AI models'
        },
        { 
          id: 2, 
          name: 'Code Execution', 
          description: 'Run Python code and see results in real-time'
        },
        { 
          id: 3, 
          name: 'Chat Assistant', 
          description: 'Interactive AI chat for coding assistance'
        },
        { 
          id: 4, 
          name: 'Function Extraction', 
          description: 'Extract and save functions from conversations'
        },
        { 
          id: 5, 
          name: 'Code Analysis', 
          description: 'Analyze code for errors and improvements'
        },
        { 
          id: 6, 
          name: 'History Management', 
          description: 'View and manage your chat and code history'
        }
      ],
      // Chat data
      inputMessage: '',
      messages: [],
      isRecording: false,
      recognition: null,
      chatId: null,
      // Code/Output data
      code: `# Welcome to PyTalk Code Runner
# Enter your Python code here and click Run

print("Hello, World!")
print("This is a Python code runner")

# Example: Simple calculation
result = 10 + 20
print(f"10 + 20 = {result}")`,
      output: [],
      isRunning: false,
      isOutputExpanded: false,
      // Undo/Redo history
      codeHistory: [],
      historyIndex: -1,
      isUndoRedo: false
    }
  },
  watch: {
    code(newVal, oldVal) {
      // Only save to history if change is not from undo/redo
      if (!this.isUndoRedo && oldVal !== undefined) {
        this.saveToHistory()
      }
      this.isUndoRedo = false
    }
  },
  computed: {
    canUndo() {
      return this.historyIndex > 0
    },
    canRedo() {
      return this.historyIndex < this.codeHistory.length - 1
    }
  },
  mounted() {
    // Initialize code history
    this.codeHistory = [this.code]
    this.historyIndex = 0
    // Initialize chat
    const chatId = this.$route.query.id
    if (chatId) {
      this.loadChat(chatId)
    } else {
      this.chatId = this.generateChatId()
    }
    
    // Initialize Web Speech API if available
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
      this.recognition = new SpeechRecognition()
      this.recognition.continuous = false
      this.recognition.interimResults = false
      this.recognition.lang = 'en-US'
      
      this.recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript
        this.inputMessage = transcript
        this.isRecording = false
      }
      
      this.recognition.onerror = () => {
        this.isRecording = false
      }
      
      this.recognition.onend = () => {
        this.isRecording = false
      }
    }
  },
  beforeUnmount() {
    if (this.messages.length > 0) {
      this.saveChat()
    }
  },
  methods: {
    // Chat methods
    generateChatId() {
      return 'chat_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
    },
    loadChat(chatId) {
      const stored = localStorage.getItem('chatHistory')
      if (stored) {
        const chatHistory = JSON.parse(stored)
        const chat = chatHistory.find(c => c.id === chatId)
        if (chat) {
          this.chatId = chat.id
          this.messages = chat.messages || []
          this.scrollChatToBottom()
        }
      }
    },
    saveChat() {
      if (this.messages.length === 0) {
        return
      }
      
      if (!this.chatId) {
        this.chatId = this.generateChatId()
      }
      
      try {
        const chat = {
          id: this.chatId,
          messages: [...this.messages],
          createdAt: this.messages[0]?.timestamp || new Date().toISOString(),
          updatedAt: new Date().toISOString()
        }
        
        let chatHistory = []
        const stored = localStorage.getItem('chatHistory')
        if (stored) {
          try {
            chatHistory = JSON.parse(stored)
            chatHistory = chatHistory.filter(c => c.id !== this.chatId)
          } catch (e) {
            console.error('Error parsing chat history:', e)
            chatHistory = []
          }
        }
        
        chatHistory.unshift(chat)
        
        if (chatHistory.length > 50) {
          chatHistory = chatHistory.slice(0, 50)
        }
        
        localStorage.setItem('chatHistory', JSON.stringify(chatHistory))
      } catch (error) {
        console.error('Error saving chat:', error)
      }
    },
    sendMessage() {
      if (this.inputMessage.trim()) {
        const now = new Date()
        const time = now.toLocaleTimeString('en-US', { 
          hour: '2-digit', 
          minute: '2-digit' 
        })
        
        this.messages.push({
          text: this.inputMessage,
          type: 'sent',
          time: time,
          timestamp: now.toISOString()
        })
        
        this.inputMessage = ''
        this.saveChat()
        this.scrollChatToBottom()
        
        // Simulate a response
        setTimeout(() => {
          const now = new Date()
          this.messages.push({
            text: 'Thank you for your message!',
            type: 'received',
            time: now.toLocaleTimeString('en-US', { 
              hour: '2-digit', 
              minute: '2-digit' 
            }),
            timestamp: now.toISOString()
          })
          this.saveChat()
          this.scrollChatToBottom()
        }, 1000)
      }
    },
    toggleRecording() {
      if (!this.recognition) {
        alert('Speech recognition is not supported in your browser')
        return
      }
      
      if (this.isRecording) {
        this.recognition.stop()
        this.isRecording = false
      } else {
        this.recognition.start()
        this.isRecording = true
      }
    },
    scrollChatToBottom() {
      this.$nextTick(() => {
        const container = this.$refs.messagesContainer
        if (container) {
          container.scrollTop = container.scrollHeight
        }
      })
    },
    // Code/Output methods
    async runCode() {
      if (!this.code.trim()) {
        this.addOutput('error', 'Please enter some code to run')
        return
      }

      this.isRunning = true
      this.addOutput('input', this.code)

      try {
        const result = await this.executeCode(this.code)
        this.addOutput('output', result)
      } catch (error) {
        this.addOutput('error', error.message || 'An error occurred while running the code')
      } finally {
        this.isRunning = false
        this.scrollOutputToBottom()
      }
    },
    async executeCode(code) {
      return new Promise((resolve, reject) => {
        setTimeout(() => {
          try {
            let output = ''
            
            const printMatches = code.match(/print\(['"](.*?)['"]\)/g) || []
            printMatches.forEach(match => {
              const content = match.match(/['"](.*?)['"]/)?.[1] || ''
              output += content + '\n'
            })

            const calcMatches = code.match(/(\w+)\s*=\s*(\d+)\s*([+\-*/])\s*(\d+)/g) || []
            calcMatches.forEach(match => {
              const parts = match.match(/(\w+)\s*=\s*(\d+)\s*([+\-*/])\s*(\d+)/)
              if (parts) {
                const [, varName, num1, op, num2] = parts
                let result
                switch(op) {
                  case '+': result = parseInt(num1) + parseInt(num2); break
                  case '-': result = parseInt(num1) - parseInt(num2); break
                  case '*': result = parseInt(num1) * parseInt(num2); break
                  case '/': result = parseInt(num1) / parseInt(num2); break
                }
                output += `${varName} = ${result}\n`
              }
            })

            const fStringMatches = code.match(/print\(f['"](.*?)['"]\)/g) || []
            fStringMatches.forEach(match => {
              const content = match.match(/['"](.*?)['"]/)?.[1] || ''
              const substituted = content.replace(/\{(\w+)\}/g, (matchStr, varName) => {
                const varMatch = code.match(new RegExp(`${varName}\\s*=\\s*(\\d+)`))
                return varMatch ? varMatch[1] : matchStr
              })
              output += substituted + '\n'
            })

            if (!output.trim()) {
              output = 'Code executed successfully (no output)'
            }

            resolve(output.trim())
          } catch (error) {
            reject(error)
          }
        }, 500)
      })
    },
    addOutput(type, content) {
      this.output.push({
        type: type,
        content: content,
        timestamp: new Date().toLocaleTimeString()
      })
    },
    clearOutput() {
      this.output = []
    },
    toggleOutputMode() {
      this.isTextMode = !this.isTextMode
    },
    toggleFunctionPanel() {
      this.isFunctionPanelOpen = !this.isFunctionPanelOpen
    },
    selectFunction(func) {
      console.log('Selected function:', func.name)
      // You can add logic here to handle function selection
      // For example, insert function code into the editor or navigate
    },
    toggleOutputSpan() {
      this.isOutputExpanded = !this.isOutputExpanded
      this.$nextTick(() => {
        this.scrollOutputToBottom()
      })
    },
    scrollOutputToBottom() {
      this.$nextTick(() => {
        const container = this.$refs.outputContainer
        if (container) {
          container.scrollTop = container.scrollHeight
        }
      })
    },
    async handleFileUpload(event) {
      const file = event.target.files[0]
      if (!file) return

      if (!file.name.endsWith('.py')) {
        alert('Please upload only Python (.py) files')
        event.target.value = ''
        return
      }

      try {
        const fileContent = await this.readFileContent(file)
        this.code = fileContent
        this.addOutput('output', `File "${file.name}" loaded successfully`)
      } catch (error) {
        this.addOutput('error', `Error reading file: ${error.message}`)
      }

      event.target.value = ''
    },
    readFileContent(file) {
      return new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = (e) => resolve(e.target.result)
        reader.onerror = (e) => reject(new Error('Failed to read file'))
        reader.readAsText(file)
      })
    },
    undoCode() {
      if (this.canUndo) {
        this.isUndoRedo = true
        this.historyIndex--
        this.code = this.codeHistory[this.historyIndex]
      }
    },
    redoCode() {
      if (this.canRedo) {
        this.isUndoRedo = true
        this.historyIndex++
        this.code = this.codeHistory[this.historyIndex]
      }
    },
    saveToHistory() {
      // Remove any history after current index (when user makes new change after undo)
      this.codeHistory = this.codeHistory.slice(0, this.historyIndex + 1)
      // Add new state
      this.codeHistory.push(this.code)
      this.historyIndex++
      // Limit history to 50 states
      if (this.codeHistory.length > 50) {
        this.codeHistory.shift()
        this.historyIndex--
      }
    }
  }
}
</script>

<style scoped>
.run-content {
  display: flex;
  gap: 16px;
  height: calc(100vh - 120px);
  padding: 20px;
}

/* Left Column: Chat - Matching Chat.vue exactly */
.chat-column {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.chat-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 0;
}

.chat-container {
  background: white;
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
  font-family: 'Jaldi', sans-serif;
  font-size: 16px;
}

.message {
  display: flex;
  flex-direction: column;
  max-width: 70%;
  animation: fadeIn 0.3s ease;
}

.message.sent {
  align-self: flex-end;
  align-items: flex-end;
}

.message.received {
  align-self: flex-start;
  align-items: flex-start;
}

.message-content {
  padding: 12px 16px;
  border-radius: 16px;
  font-family: 'Jaldi', sans-serif;
  font-size: 14px;
  word-wrap: break-word;
}

.message.sent .message-content {
  background: #1565C0;
  color: white;
  border-bottom-right-radius: 4px;
}

.message.received .message-content {
  background: #f0f0f0;
  color: #333;
  border-bottom-left-radius: 4px;
}

.message-time {
  font-size: 11px;
  color: #999;
  margin-top: 4px;
  font-family: 'Jaldi', sans-serif;
}

.chat-input-container {
  border-top: 1px solid #e8e8e8;
  padding: 16px 24px;
  background: #fafafa;
}

.input-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chat-input {
  flex: 1;
  padding: 12px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 24px;
  font-size: 14px;
  font-family: 'Jaldi', sans-serif;
  transition: all 0.2s ease;
  outline: none;
}

.chat-input:focus {
  border-color: #1565C0;
  box-shadow: 0 0 0 3px rgba(2, 74, 20, 0.1);
}

.chat-input:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

.mic-button,
.send-button {
  width: 44px;
  height: 44px;
  border: none;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  color: white;
}

.mic-button {
  background: #666;
}

.mic-button:hover {
  background: #555;
  transform: scale(1.05);
}

.mic-button.recording {
  background: #dc3545;
  animation: pulse 1.5s infinite;
}

.send-button {
  background: #1565C0;
}

.send-button:hover:not(:disabled) {
  background: #0D47A1;
  transform: scale(1.05);
}

.send-button:disabled {
  background: #ccc;
  cursor: not-allowed;
  opacity: 0.6;
}

.recording-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  color: #dc3545;
  font-size: 12px;
  font-family: 'Jaldi', sans-serif;
}

.recording-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #dc3545;
  animation: blink 1s infinite;
}

/* Right Column: Code Input and Output */
.code-output-column {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
  transition: all 0.3s ease;
}

.code-output-column.output-expanded {
  flex-direction: column;
}

.code-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  border: 1px solid #e8e8e8;
  min-height: 0;
  transition: all 0.3s ease;
}

.code-section.hidden {
  display: none;
}

.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid #e8e8e8;
  background: #fafafa;
}

.code-editor-wrapper {
  display: flex;
  flex: 1;
  overflow: hidden;
  min-height: 0;
}

.code-toolbar {
  width: 50px;
  background: #f5f5f5;
  border-right: 1px solid #e8e8e8;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 0;
  gap: 8px;
}

.toolbar-button {
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

.toolbar-button:hover:not(:disabled) {
  background: #e8e8e8;
  color: #1565C0;
}

.toolbar-button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.toolbar-icon {
  width: 18px;
  height: 18px;
  object-fit: contain;
  display: block;
  flex-shrink: 0;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
  font-family: 'Jaldi', sans-serif;
  margin: 0;
}

.run-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: #1565C0;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  font-family: 'Jaldi', sans-serif;
  cursor: pointer;
  transition: all 0.2s ease;
}

.run-button:hover:not(:disabled) {
  background: #0D47A1;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(2, 74, 20, 0.3);
}

.run-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.code-input {
  flex: 1;
  padding: 20px;
  border: none;
  outline: none;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.6;
  resize: none;
  background: #1e1e1e;
  color: #d4d4d4;
  tab-size: 2;
  overflow-y: auto;
}

.code-input::placeholder {
  color: #6a6a6a;
}

.output-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  border: 1px solid #e8e8e8;
  min-height: 0;
  transition: all 0.3s ease;
}

.output-section.expanded {
  flex: 1;
  height: 100%;
}

.output-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid #e8e8e8;
  background: #fafafa;
}

.output-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.mode-toggle {
  cursor: pointer;
  user-select: none;
}

.toggle-track {
  position: relative;
  width: 90px;
  height: 44px;
  background: #AC0A0A;
  border-radius: 22px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px;
  transition: background 0.3s ease;
}

.toggle-track.text-mode {
  background: #0B5B0A;
}

.toggle-slider {
  position: absolute;
  width: 40px;
  height: 36px;
  background: white;
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  left: 4px;
  z-index: 2;
}

.toggle-slider.active {
  transform: translateX(42px);
}

.toggle-icon {
  width: 16px;
  height: 16px;
  object-fit: contain;
}

.toggle-label-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
  pointer-events: none;
  flex: 1;
  opacity: 0.6;
  transition: opacity 0.3s ease;
}

.toggle-label-icon.active {
  opacity: 1;
}

.toggle-label-left {
  padding-right: 8px;
}

.toggle-label-right {
  padding-left: 8px;
}

.toggle-label-icon-img {
  width: 20px;
  height: 20px;
  object-fit: contain;
  filter: brightness(0) invert(1);
}

.span-button {
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
}

.span-button:hover {
  background: #f0f0f0;
  color: #1565C0;
}

.clear-button {
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
}

.clear-button:hover {
  background: #f0f0f0;
  color: #dc3545;
}

.output-content {
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

.empty-output {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #6a6a6a;
  font-family: 'Jaldi', sans-serif;
}

.output-lines {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.output-line {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.output-prefix {
  color: #858585;
  font-weight: 600;
  min-width: 50px;
  flex-shrink: 0;
}

.output-line.input .output-prefix {
  color: #569cd6;
}

.output-line.output .output-prefix {
  color: #4ec9b0;
}

.output-line.error .output-prefix {
  color: #f48771;
}

.output-text {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  flex: 1;
}

.output-line.error .output-text {
  color: #f48771;
}

/* Graphic Mode Styles */
.output-content.graphic-mode {
  background: #e1e1e1;
  color: #1a1a1a;
}

.output-graphic {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.graphic-line {
  display: flex;
  flex-direction: column;
}

.graphic-input,
.graphic-output,
.graphic-error {
  background: white;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-left: 4px solid;
}

.graphic-input {
  border-left-color: #569cd6;
}

.graphic-output {
  border-left-color: #4ec9b0;
}

.graphic-error {
  border-left-color: #f48771;
  background: #fff5f5;
}

.graphic-label {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
  font-family: 'Jaldi', sans-serif;
}

.graphic-input .graphic-label {
  color: #569cd6;
}

.graphic-output .graphic-label {
  color: #4ec9b0;
}

.graphic-error .graphic-label {
  color: #f48771;
}

.graphic-content {
  font-family: 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
  color: #1a1a1a;
}

.top-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e8e8e8;
  background: white;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: #1a1a1a;
  font-family: 'Jaldi', sans-serif;
  margin: 0;
}

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
  border-color: #1565C0;
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
  color: #1565C0;
  font-family: 'Courier New', monospace;
  font-weight: 500;
  background: #f0f7f2;
  padding: 4px 8px;
  border-radius: 4px;
  display: inline-block;
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

@media (max-width: 768px) {
  .function-panel {
    width: 100%;
    right: -100%;
  }
  
  .function-panel.open {
    right: 0;
  }
  
  .top-header {
    padding: 16px;
  }
  
  .page-title {
    font-size: 22px;
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

@keyframes blink {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.3;
  }
}

.chat-messages::-webkit-scrollbar {
  width: 8px;
}

.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: #c0c0c0;
  border-radius: 4px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: #a0a0a0;
}

.output-content::-webkit-scrollbar,
.code-input::-webkit-scrollbar {
  width: 8px;
}

.output-content::-webkit-scrollbar-track {
  background: #2d2d2d;
}

.output-content::-webkit-scrollbar-thumb {
  background: #555;
  border-radius: 4px;
}

.output-content::-webkit-scrollbar-thumb:hover {
  background: #666;
}

.code-input::-webkit-scrollbar-track {
  background: #2d2d2d;
}

.code-input::-webkit-scrollbar-thumb {
  background: #555;
  border-radius: 4px;
}

.code-input::-webkit-scrollbar-thumb:hover {
  background: #666;
}

@media (max-width: 768px) {
  .run-content {
    flex-direction: column;
    height: calc(100vh - 100px);
  }

  .chat-column,
  .code-output-column {
    flex: 1;
    min-height: 300px;
  }

  .chat-content {
    height: 100%;
  }

  .code-header,
  .output-header {
    padding: 12px 16px;
  }

  .code-input,
  .output-content,
  .chat-messages {
    padding: 16px;
    font-size: 13px;
  }

  .page-title {
    font-size: 22px;
  }
}
</style>
