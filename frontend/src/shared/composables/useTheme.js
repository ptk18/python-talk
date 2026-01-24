import { ref, watch } from 'vue';

const theme = ref('light');

const savedTheme = localStorage.getItem('theme');
if (savedTheme) {
  theme.value = savedTheme;
}

export function useTheme() {
  const setTheme = (newTheme) => {
    theme.value = newTheme;
    localStorage.setItem('theme', newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
  };

  watch(theme, (newTheme) => {
    document.documentElement.setAttribute('data-theme', newTheme);
  }, { immediate: true });

  return {
    theme,
    setTheme,
  };
}
