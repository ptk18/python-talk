import { ref } from 'vue';

const language = ref('en');

const savedLanguage = localStorage.getItem('language');
if (savedLanguage) {
  language.value = savedLanguage;
}

export function useLanguage() {
  const setLanguage = (lang) => {
    language.value = lang;
    localStorage.setItem('language', lang);
  };

  return {
    language,
    setLanguage,
  };
}
