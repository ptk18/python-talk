import { ref, onMounted } from 'vue';
import { settingsSync } from '../services/settingsSync.js';

const language = ref('en');

// Initialize from localStorage
const savedLanguage = localStorage.getItem('language');
if (savedLanguage) {
  language.value = savedLanguage;
}

export function useLanguage() {
  const setLanguage = (lang) => {
    language.value = lang;
    settingsSync.set('language', lang);
  };

  // Listen for changes from other tabs/apps
  onMounted(() => {
    settingsSync.onSettingChange('language', (newLang) => {
      if (newLang && newLang !== language.value) {
        language.value = newLang;
      }
    });

    // Sync from URL on mount (for cross-origin navigation)
    settingsSync.syncFromUrl();
    const urlLang = localStorage.getItem('language');
    if (urlLang) {
      language.value = urlLang;
    }
  });

  return {
    language,
    setLanguage,
  };
}
