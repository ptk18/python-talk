import { ref } from 'vue'
import { voiceService } from '@py-talk/shared'
import { useAudioContext } from '@/shared/composables/useAudioContext'

export function useVoiceRecording(language) {
  const isRecording = ref(false)
  const isTranscribing = ref(false)
  const mediaRecorder = ref(null)
  const audioChunks = ref([])

  const { playClickSound } = useAudioContext()

  const handleMicClick = async (onTranscriptionComplete) => {
    playClickSound()
    voiceService.enableAudioContext()

    if (!isRecording.value) {
      try {
        voiceService.speak('Listening')
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
        const recorder = new MediaRecorder(stream)
        audioChunks.value = []

        recorder.ondataavailable = (e) => {
          audioChunks.value.push(e.data)
        }

        recorder.onstop = async () => {
          const audioBlob = new Blob(audioChunks.value, { type: 'audio/webm' })
          const audioFile = new File(
            [audioBlob],
            `recording_${Date.now()}.webm`,
            { type: 'audio/webm' }
          )

          try {
            isTranscribing.value = true
            const langValue = typeof language === 'function' ? language() : language.value || language

            console.log('Voice transcription starting...')
            console.log('Language:', langValue === 'en' ? 'English' : 'Thai')

            const transcribeStartTime = performance.now()
            const result = await voiceService.transcribe(audioFile, langValue)
            const transcribeEndTime = performance.now()
            const transcriptionTime = (transcribeEndTime - transcribeStartTime) / 1000

            const text = result.text || `[Error: ${result.error || 'Unknown'}]`

            if (text.includes('[Error')) {
              console.log('Transcription failed:', text)
              console.log('Time:', transcriptionTime.toFixed(3), 'seconds')
              voiceService.speak("I couldn't understand that. Please try again")
            } else {
              console.log('Transcribed:', text)
              console.log('Time:', transcriptionTime.toFixed(3), 'seconds')
              voiceService.speak('Voice command received')
            }

            if (onTranscriptionComplete) {
              onTranscriptionComplete(text)
            }
          } catch (err) {
            console.error('Voice transcription error:', err)
            voiceService.speak('Voice transcription error')
            alert('Error transcribing voice: ' + err.message)
          } finally {
            isTranscribing.value = false
          }
        }

        recorder.start()
        mediaRecorder.value = recorder
        isRecording.value = true
      } catch (err) {
        console.error('Microphone access denied:', err)
        voiceService.speak('Microphone access denied')
        alert('Microphone access denied or unavailable.')
      }
    } else {
      if (mediaRecorder.value && mediaRecorder.value.state !== 'inactive') {
        mediaRecorder.value.stop()
      }
      isRecording.value = false
    }
  }

  return {
    isRecording,
    isTranscribing,
    handleMicClick
  }
}
