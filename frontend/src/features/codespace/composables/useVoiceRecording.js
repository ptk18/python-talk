import { ref } from 'vue'
import { voiceService } from '@py-talk/shared'
import { useAudioContext } from '@/shared/composables/useAudioContext'

export function useVoiceRecording(language) {
  const isRecording = ref(false)
  const isTranscribing = ref(false)
  const mediaRecorder = ref(null)
  const audioChunks = ref([])
  const activeStream = ref(null)

  const { playClickSound } = useAudioContext()

  const stopStream = () => {
    if (activeStream.value) {
      activeStream.value.getTracks().forEach(track => track.stop())
      activeStream.value = null
    }
  }

  const handleMicClick = async (onTranscriptionComplete) => {
    playClickSound()
    voiceService.enableAudioContext()

    if (!isRecording.value) {
      try {
        voiceService.speak('Listening')
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
          }
        })
        activeStream.value = stream

        // Use browser-appropriate MIME type (Safari uses mp4, Chrome uses webm)
        const mimeType = voiceService.getPreferredAudioType()
        const recorder = new MediaRecorder(stream, { mimeType })
        audioChunks.value = []

        recorder.ondataavailable = (e) => {
          audioChunks.value.push(e.data)
        }

        recorder.onstop = async () => {
          // Release microphone immediately
          stopStream()

          const extMap = {
            'audio/webm': 'webm',
            'audio/webm;codecs=opus': 'webm',
            'audio/mp4': 'mp4',
            'audio/wav': 'wav',
          }
          const ext = extMap[mimeType] || 'webm'

          const audioBlob = new Blob(audioChunks.value, { type: mimeType })
          const audioFile = new File(
            [audioBlob],
            `recording_${Date.now()}.${ext}`,
            { type: mimeType }
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

            const text = result.error
              ? `[Error: ${result.error}]`
              : (result.text || '[Error: No text returned]')

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
        stopStream()
        voiceService.speak('Microphone access denied')
        alert('Microphone access denied or unavailable.')
      }
    } else {
      if (mediaRecorder.value && mediaRecorder.value.state !== 'inactive') {
        mediaRecorder.value.stop()
      }
      // Safety net: ensure stream is released even if onstop doesn't fire
      stopStream()
      isRecording.value = false
    }
  }

  return {
    isRecording,
    isTranscribing,
    handleMicClick
  }
}
