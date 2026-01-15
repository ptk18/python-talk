<template>
  <div :class="['app-wrapper', { 'lang-th': language === 'th' }]">
    <router-view />
  </div>
</template>

<script>
import { computed, watch } from 'vue'
import { useLanguage } from '@py-talk/shared'

export default {
  name: 'App',
  setup() {
    const { language } = useLanguage()
    
    // Update body class when language changes
    watch(language, (newLang) => {
      if (newLang === 'th') {
        document.body.classList.add('lang-th')
      } else {
        document.body.classList.remove('lang-th')
      }
    }, { immediate: true })
    
    return {
      language
    }
  }
}
</script>

