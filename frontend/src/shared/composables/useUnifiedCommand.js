// useUnifiedCommand.js
import { ref } from 'vue'
import { analyzeAPI, translateAPI, voiceService, messageAPI, executeAPI } from '@py-talk/shared'

export function useUnifiedCommand() {
  const commandHistory = ref([])
  const isProcessingCommand = ref(false)
  const parserDebug = ref(null)

  let historyIdCounter = 0

  const addHistoryEntry = (entry) => {
    commandHistory.value.push({
      id: ++historyIdCounter,
      timestamp: new Date(),
      ...entry
    })
  }

  /**
   * Process a command (natural language or direct method call).
   *
   * @param {number|string} conversationId
   * @param {string} text - The raw input text
   * @param {string} language - 'en' or 'th'
   * @param {object} options
   * @param {'turtle'|'codespace'} options.mode
   * @param {function} [options.onCodeSync] - Called after code is synced (workspace)
   * @param {function} [options.onFileRefresh] - Called after file needs refresh (workspace)
   * @param {function} [options.onMessagesUpdate] - Called with updated messages (workspace)
   * @returns {{ success: boolean, executables?: string[], error?: string }}
   */
  const processCommand = async (conversationId, text, language, options = {}) => {
    if (!text.trim() || !conversationId) return { success: false, error: 'Empty command' }

    const { mode = 'codespace', onCodeSync, onFileRefresh, onMessagesUpdate } = options

    isProcessingCommand.value = true

    try {
      let commandForAnalysis = text
      let translatedText = null

      // 1) Translate Thai -> English if needed
      if (language === 'th') {
        try {
          const translateResult = await translateAPI.translateToEnglish(text)
          commandForAnalysis = translateResult?.translated_text || text
          translatedText = commandForAnalysis
          // Silent - no TTS for translation
        } catch (translateErr) {
          console.error('Translation failed:', translateErr)
          voiceService.speak('Translation failed, please try again')
          addHistoryEntry({ text, status: 'error', error: 'Translation failed' })
          return { success: false, error: 'Translation failed' }
        }
      }

      // 2) In workspace mode, save user message to chat history
      if (mode === 'codespace' || mode === 'turtle') {
        console.log('[MSG] saving user:', conversationId, text)
        const savedUser = await messageAPI.create(parseInt(conversationId), 'user', text)
        console.log('[MSG] saved user result:', savedUser)

        const currentMsgs = await messageAPI.getByConversation(parseInt(conversationId))
        console.log('[MSG] fetched after user save:', currentMsgs)

        if (onMessagesUpdate) onMessagesUpdate(currentMsgs)
      }

      // 3) Analyze the command
      const apiRes = await analyzeAPI.analyzeCommand(Number(conversationId), commandForAnalysis)

      const allResults = Array.isArray(apiRes?.results)
        ? apiRes.results
        : (apiRes?.result ? [apiRes.result] : [])

      // Capture raw API response for debug panel
      parserDebug.value = apiRes

      // Categorize results
      const matched = []
      const suggestions = []
      const noMatches = []

      for (const r of allResults) {
        if (r.status === 'matched' && r.executable) {
          matched.push(r)
        } else if (r.status === 'suggestion') {
          suggestions.push(r)
        } else {
          noMatches.push(r)
        }
      }

      const executables = matched.map(r => r.executable)

      // 4) Build summary for workspace message history
      if (mode === 'codespace' || mode === 'turtle') {
        const summaryLines = []
        for (const r of matched) summaryLines.push(r.executable)
        for (const r of suggestions) {
          summaryLines.push(`Did you mean ${r.method}(${Object.entries(r.parameters || {}).map(([k, v]) => `${k}=${v}`).join(', ')})?`)
        }
        for (const r of noMatches) {
          if (r.suggestion_message) summaryLines.push(r.suggestion_message)
          else summaryLines.push(`Could not understand: "${r.original_command || 'unknown'}"`)
        }

        const summary = summaryLines.length > 0 ? summaryLines.join('\n') : 'No matching commands found'
        console.log('[MSG] saving system:', conversationId, summary)

        const savedSystem = await messageAPI.create(parseInt(conversationId), 'system', summary)
        console.log('[MSG] saved system result:', savedSystem)

        const msgs = await messageAPI.getByConversation(parseInt(conversationId))
        console.log('[MSG] fetched after system save:', msgs)

        if (onMessagesUpdate) onMessagesUpdate(msgs)
      }

      // 5) Handle results
      if (executables.length > 0) {
        addHistoryEntry({
          text,
          translatedText,
          executables,
          status: 'success'
        })

        if (mode === 'codespace') {
          // Sync code and refresh files
          if (onCodeSync) await onCodeSync()
          if (onFileRefresh) await onFileRefresh()

          // Auto-execute
          try {
            const execResult = await executeAPI.rerunCommand(Number(conversationId))
            console.log('[Output]', execResult.output || 'No output')
          } catch (execErr) {
            console.error('[Execute Error]', execErr)
          }

          voiceService.speak(
            executables.length > 1
              ? `${executables.length} commands executed successfully`
              : 'Command executed successfully'
          )
        } else {
          // Turtle mode: voice feedback handled by the caller
          voiceService.speak('Command executed')
        }

        return { success: true, executables }
      }

      // No executables found
      const first = allResults[0]
      const errorMsg = first?.suggestion_message || first?.error || apiRes?.error || 'No matching commands found'

      addHistoryEntry({
        text,
        translatedText,
        status: suggestions.length > 0 ? 'suggestion' : 'error',
        error: errorMsg,
        executables: []
      })

      // TTS feedback — use fixed translatable strings, not raw API messages
      if (suggestions.length > 0) {
        const sugNames = suggestions.map(s => s.method).join(', ')
        voiceService.speak(`Did you mean ${sugNames}?`)
      } else {
        voiceService.speak("I couldn't understand that command. Please try again with a different phrase.")
      }

      return { success: false, error: errorMsg }
    } catch (err) {
      console.error('[UnifiedCommand] error:', err)
      const errorMsg = err?.message || 'Unknown error'
      addHistoryEntry({ text, status: 'error', error: errorMsg })
      voiceService.speak('Invalid command')
      return { success: false, error: errorMsg }
    } finally {
      isProcessingCommand.value = false
    }
  }

  const clearHistory = () => {
    commandHistory.value = []
  }

  return {
    commandHistory,
    isProcessingCommand,
    parserDebug,
    processCommand,
    clearHistory
  }
}
