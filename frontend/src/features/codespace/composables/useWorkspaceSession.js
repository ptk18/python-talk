import { ref } from 'vue'
import { messageAPI, conversationAPI, executeAPI, analyzeAPI } from '@py-talk/shared'

export function useWorkspaceSession() {
  const messages = ref([])
  const availableMethods = ref(null)
  const appName = ref('Codespace')
  const appIcon = ref(null)
  const appType = ref('codespace')

  const initializeSession = async (conversationId) => {
    if (!conversationId) return
    try {
      await executeAPI.ensureSessionInitialized(parseInt(conversationId))
      await fetchMessages(conversationId)
      await fetchAvailableMethods(conversationId)
      await fetchAppDetails(conversationId)

      analyzeAPI.prewarmPipeline(parseInt(conversationId))
        .catch(err => console.warn('Pipeline pre-warm failed:', err))
    } catch (err) {
      console.error('Failed to initialize session:', err)
    }
  }

  const fetchMessages = async (conversationId) => {
    if (!conversationId) return
    try {
      const msgs = await messageAPI.getByConversation(parseInt(conversationId))
      messages.value = msgs.map(msg => {
        const existing = messages.value.find(m => m.id === msg.id)
        return existing
          ? { ...msg, interpretedCommand: existing.interpretedCommand, paraphrases: existing.paraphrases }
          : msg
      })
    } catch (err) {
      console.error('Failed to fetch messages:', err)
    }
  }

  const fetchAvailableMethods = async (conversationId) => {
    if (!conversationId) return
    try {
      const methods = await conversationAPI.getAvailableMethods(parseInt(conversationId))
      availableMethods.value = methods
    } catch (err) {
      console.error('Failed to fetch available methods:', err)
    }
  }

  const fetchAppDetails = async (conversationId) => {
    if (!conversationId) {
      appName.value = 'Codespace'
      appIcon.value = null
      appType.value = 'codespace'
      return
    }
    try {
      const appDetails = await conversationAPI.getSingleConversation(parseInt(conversationId))
      if (appDetails) {
        appName.value = appDetails.title || 'Codespace'
        appIcon.value = appDetails.app_image || null
        appType.value = appDetails.app_type || 'codespace'
      }
    } catch (err) {
      console.error('Failed to fetch app details:', err)
      appName.value = 'Codespace'
      appType.value = 'codespace'
    }
  }

  const updateMessages = (newMessages) => {
    messages.value = newMessages
  }

  return {
    messages,
    availableMethods,
    appName,
    appIcon,
    appType,
    initializeSession,
    fetchMessages,
    fetchAvailableMethods,
    fetchAppDetails,
    updateMessages
  }
}
