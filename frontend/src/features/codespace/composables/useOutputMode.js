import { ref, onMounted } from 'vue'

export function useOutputMode() {
  const isTextMode = ref(true)
  const isOutputExpanded = ref(false)

  const setOutputMode = (mode) => {
    isTextMode.value = mode === 'text'
    localStorage.setItem('outputMode', mode)
  }

  const toggleOutputExpand = () => {
    isOutputExpanded.value = !isOutputExpanded.value
    localStorage.setItem('outputExpanded', isOutputExpanded.value)
  }

  const loadSavedPreferences = () => {
    const savedMode = localStorage.getItem('outputMode')
    if (savedMode) {
      isTextMode.value = savedMode === 'text'
    }

    const savedExpand = localStorage.getItem('outputExpanded')
    if (savedExpand) {
      isOutputExpanded.value = savedExpand === 'true'
    }
  }

  onMounted(() => {
    loadSavedPreferences()
  })

  return {
    isTextMode,
    isOutputExpanded,
    setOutputMode,
    toggleOutputExpand
  }
}
