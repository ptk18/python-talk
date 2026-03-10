import { ref } from 'vue'
import { executeAPI, voiceService } from '@py-talk/shared'
import { ENDPOINTS } from '@/config/endpoints'

export function useCodeExecution() {
  const output = ref('')
  const isRunning = ref(false)

  const handleRun = async (conversationId, isTextMode) => {
    try {
      const runnerResponse = await executeAPI.getRunnerCode(parseInt(conversationId))
      const runnerCode = runnerResponse.code

      if (!runnerCode.trim()) {
        output.value = 'Error: runner.py is empty. Please add some commands.\n'
        voiceService.speak('Runner file is empty. Please add some commands')
        return
      }
    } catch (err) {
      output.value = 'Error: runner.py not found. Please initialize the session first.\n'
      voiceService.speak('Runner file not found. Please initialize the session first')
      return
    }

    if (isTextMode) {
      await handleRunNormalCode(conversationId)
    } else {
      await handleRunTurtle(conversationId)
    }
  }

  const handleRunNormalCode = async (conversationId) => {
    isRunning.value = true
    output.value = 'Running code...\n\n'

    try {
      const res = await executeAPI.rerunCommand(parseInt(conversationId))
      output.value = res.output || 'No output returned from execute_command.\n'
      voiceService.speak('Output ready!')
    } catch (err) {
      console.error('Failed to execute command:', err)
      output.value = 'Error executing command.\n'
      voiceService.speak('Please try again')
    } finally {
      isRunning.value = false
    }
  }

  const handleRunTurtle = async (conversationId) => {
    isRunning.value = true
    output.value = 'Running turtle graphics...\n\n'

    const hostname = window.location.hostname
    const rawWsBase = ENDPOINTS.TURTLE.WS_BASE
    const wsBase = rawWsBase
      .replace('localhost', hostname)
      .replace('127.0.0.1', hostname)

    try {
      const channelName = encodeURIComponent(String(conversationId))
      const ws = new WebSocket(`${wsBase}/subscribe/${channelName}`)

      await new Promise((resolve, reject) => {
        ws.onopen = () => resolve()
        ws.onerror = (err) => {
          console.error('Turtle WebSocket error:', err)
          reject(err)
        }
      })

      ws.onmessage = (event) => {
        const image = event.data
        const videoEl = document.getElementById('turtle-video')
        if (videoEl) {
          videoEl.src = `data:image/jpeg;base64,${image}`
        }
      }

      ws.onclose = () => {
        console.log('Turtle WebSocket closed')
      }

      const res = await fetch(
        `${ENDPOINTS.API.BASE_URL}/api/run_turtle/${conversationId}`,
        {
          method: 'GET',
          headers: {
            'Accept': 'application/json'
          }
        }
      )

      if (!res.ok) {
        const errorText = await res.text()
        throw new Error(`Backend returned ${res.status}: ${errorText}`)
      }

      const data = await res.json()
      console.log('Incremental turtle response:', data)

      output.value = 'Incremental turtle command sent.\n'
      voiceService.speak('Turtle graphics running!')
    } catch (err) {
      console.error('Failed to execute turtle graphics:', err)
      output.value = 'Error executing turtle graphics.\n'
      voiceService.speak('Please try again')
    } finally {
      isRunning.value = false
    }
  }

  const clearOutput = () => {
    output.value = ''
  }

  return {
    output,
    isRunning,
    handleRun,
    clearOutput
  }
}
