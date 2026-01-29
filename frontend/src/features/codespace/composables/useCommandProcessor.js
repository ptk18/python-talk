import { ref } from 'vue'
import { messageAPI, analyzeAPI, translateAPI, executeAPI, voiceService } from '@py-talk/shared'
import { SUCCESS_DIALOG_DURATION } from '../config/constants'

export function useCommandProcessor() {
  const isProcessingCommand = ref(false)
  const showSuccessDialog = ref(false)
  const successDialogMessage = ref('')

  const processCommand = async (
    conversationId,
    msgText,
    language,
    { onMessagesUpdate, onCodeSync, onFileRefresh }
  ) => {
    if (!msgText.trim() || !conversationId) return

    try {
      isProcessingCommand.value = true

      const startTime = performance.now()
      let translationTime = 0
      let commandProcessingTime = 0

      console.log('')
      console.log('='.repeat(60))
      console.log('COMMAND PROCESSING PIPELINE')
      console.log('='.repeat(60))
      console.log('Current Language Mode:', language === 'en' ? 'English' : 'Thai')
      console.log('Transcribed Text:', msgText)
      console.log('-'.repeat(60))

      let commandForAnalysis = msgText
      let translatedText = null

      if (language === 'th') {
        try {
          console.log('TRANSLATION STEP')
          console.log('Calling Google Cloud Translate API...')

          const translateStartTime = performance.now()
          const translateResult = await translateAPI.translateToEnglish(msgText)
          const translateEndTime = performance.now()
          translationTime = (translateEndTime - translateStartTime) / 1000

          commandForAnalysis = translateResult.translated_text
          translatedText = translateResult.translated_text

          console.log('Translation Result:', translatedText)
          console.log('Time to Translate:', translationTime.toFixed(3), 'seconds')
          console.log('-'.repeat(60))
          voiceService.speak('Command translated')
        } catch (translateErr) {
          console.error('Translation failed:', translateErr)
          voiceService.speak('Translation failed, please try again')
          alert('Translation failed: ' + translateErr.message)
          return
        }
      } else {
        console.log('Translation: Not required (English mode)')
        console.log('-'.repeat(60))
      }

      await messageAPI.create(parseInt(conversationId), 'user', msgText)

      console.log('COMMAND ANALYSIS STEP')
      console.log('Text for Analysis:', commandForAnalysis)

      const analyzeStartTime = performance.now()
      const data = await analyzeAPI.analyzeCommand(Number(conversationId), commandForAnalysis)
      const analyzeEndTime = performance.now()
      commandProcessingTime = (analyzeEndTime - analyzeStartTime) / 1000

      const allResults = data.results && data.results.length > 0 ? data.results : [data.result].filter(r => r)

      // Categorize results by status
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

      // Build summary lines for system message
      const summaryLines = []
      for (const r of matched) {
        summaryLines.push(r.executable)
      }
      for (const r of suggestions) {
        summaryLines.push(`Did you mean ${r.method}(${Object.entries(r.parameters || {}).map(([k, v]) => `${k}=${v}`).join(', ')})?`)
      }
      for (const r of noMatches) {
        const cmd = r.original_command || 'unknown'
        summaryLines.push(`Could not understand: "${cmd}"`)
      }

      const summary = summaryLines.length > 0 ? summaryLines.join('\n') : 'No matching commands found'

      console.log('Processed Command(s):', summary)
      console.log('Time to Process:', commandProcessingTime.toFixed(3), 'seconds')
      console.log('='.repeat(60))
      console.log('')

      await messageAPI.create(parseInt(conversationId), 'system', summary)

      const msgs = await messageAPI.getByConversation(parseInt(conversationId))
      if (onMessagesUpdate) {
        onMessagesUpdate(msgs)
      }

      // TTS feedback based on result categories
      if (matched.length > 0 && suggestions.length === 0 && noMatches.length === 0) {
        // All matched — proceed to confirmation
      } else if (suggestions.length > 0) {
        const sugNames = suggestions.map(s => s.method).join(', ')
        voiceService.speak(`Did you mean ${sugNames}?`)
      }
      if (noMatches.length > 0 && matched.length === 0 && suggestions.length === 0) {
        voiceService.speak("I couldn't understand that command. Please try again with a different phrase.")
      }

      // Only offer to append matched commands
      const allExecutables = matched.map(r => r.executable)
      const executable = allExecutables.length > 0 ? allExecutables.join('\n') : null

      if (executable) {
        const commandCount = allExecutables.length
        const pluralText = commandCount > 1 ? `${commandCount} commands` : 'command'

        let confirmMsg = `Do you want to append the ${pluralText} to the runner file?\n\n${executable}`
        if (suggestions.length > 0) {
          confirmMsg += `\n\n(${suggestions.length} suggestion(s) skipped — low confidence)`
        }
        if (noMatches.length > 0) {
          confirmMsg += `\n\n(${noMatches.length} command(s) not recognized)`
        }

        const confirmed = window.confirm(confirmMsg)

        if (confirmed) {
          await executeAPI.appendCommand(Number(conversationId), executable)

          if (onCodeSync) {
            await onCodeSync()
          }

          if (onFileRefresh) {
            await onFileRefresh()
          }

          const successMessage = commandCount > 1
            ? `${commandCount} commands appended successfully.`
            : 'Command appended successfully.'

          successDialogMessage.value = successMessage
          showSuccessDialog.value = true

          setTimeout(() => {
            showSuccessDialog.value = false
          }, SUCCESS_DIALOG_DURATION)

          const speechMessage = commandCount > 1
            ? `${commandCount} commands appended successfully`
            : 'Command appended successfully'
          voiceService.speak(speechMessage)
        }
      } else if (suggestions.length > 0) {
        // Only suggestions, no strong matches — already spoke TTS above
      } else {
        voiceService.speak("I couldn't understand that command. Please try again with a different phrase.")
      }
    } catch (err) {
      console.error('Failed to send or analyze message:', err)
      voiceService.speak('I encountered an error. Please try again')
      alert('Error: ' + err.message)
    } finally {
      isProcessingCommand.value = false
    }
  }

  const hideSuccessDialog = () => {
    showSuccessDialog.value = false
  }

  return {
    isProcessingCommand,
    showSuccessDialog,
    successDialogMessage,
    processCommand,
    hideSuccessDialog
  }
}
