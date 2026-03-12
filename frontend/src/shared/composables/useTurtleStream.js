import { ref } from 'vue'

const STREAM_DEVICE_BASE_URL = import.meta.env.VITE_STREAM_DEVICE_BASE_URL || 'https://161.246.5.67:8001'
const STREAM_WS_BASE_URL = import.meta.env.VITE_STREAM_WS_BASE_URL || 'wss://161.246.5.67:5050'

export function useTurtleStream() {
  const streamSocket = ref(null)
  const streamFrame = ref(null)
  const isStreaming = ref(false)

  let reconnectTimer = null
  let manuallyClosed = false

  const connectStream = (channelId) => {
    if (!channelId) return

    // prevent duplicate connections
    if (streamSocket.value && streamSocket.value.readyState === WebSocket.OPEN) {
      console.log('[STREAM] already connected')
      return
    }

    const wsUrl = `${STREAM_WS_BASE_URL}/subscribe/${channelId}`
    console.log('[STREAM] connecting to', wsUrl)

    manuallyClosed = false

    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      console.log('[STREAM] connected')
      isStreaming.value = true
      clearTimeout(reconnectTimer)
    }

    ws.onmessage = (event) => {
      streamFrame.value = `data:image/jpeg;base64,${event.data}`
    }

    ws.onerror = (err) => {
      console.warn('[STREAM] error', err)
    }

    ws.onclose = () => {
      console.warn('[STREAM] closed')
      isStreaming.value = false
      streamSocket.value = null

      // auto-reconnect unless manually closed
      if (!manuallyClosed) {
        reconnectTimer = setTimeout(() => {
          console.log('[STREAM] reconnecting...')
          connectStream(channelId)
        }, 2000)
      }
    }

    streamSocket.value = ws
  }

  const disconnectStream = () => {
    manuallyClosed = true
    clearTimeout(reconnectTimer)

    if (streamSocket.value) {
      console.log('[STREAM] manual close')
      streamSocket.value.close()
      streamSocket.value = null
    }
  }

  const startRemoteTurtleSession = async (appId, code) => {
    if (!appId) return

    const payload = {
      files: {
        'runner.py': code
      }
    }

    const res = await fetch(
      `${STREAM_DEVICE_BASE_URL}/runturtle/${appId}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      }
    )

    if (!res.ok) {
      throw new Error('Failed to start turtle session')
    }

    console.log('[TURTLE] Pi turtle started')
  }

  return {
    streamFrame,
    isStreaming,
    connectStream,
    disconnectStream,
    startRemoteTurtleSession
  }
}
