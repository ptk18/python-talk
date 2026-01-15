import { ref, computed } from 'vue';

const user = ref(null);
const token = ref(null);

const savedUser = localStorage.getItem('auth_user');
const savedToken = localStorage.getItem('auth_token');

if (savedUser) {
  user.value = JSON.parse(savedUser);
}
if (savedToken) {
  token.value = savedToken;
}

// Cross-origin auth sync: Read auth from URL params (passed from main-app)
// This is needed because each port has its own localStorage
if (typeof window !== 'undefined') {
  const urlParams = new URLSearchParams(window.location.search);
  const urlUser = urlParams.get('auth_user');
  const urlToken = urlParams.get('auth_token');

  if (urlUser && !savedUser) {
    try {
      const userData = JSON.parse(urlUser);
      user.value = userData;
      localStorage.setItem('auth_user', urlUser);
      if (urlToken) {
        token.value = urlToken;
        localStorage.setItem('auth_token', urlToken);
      }
      // Clean URL to remove auth params
      window.history.replaceState({}, '', window.location.pathname);
    } catch (e) {
      console.error('Failed to parse auth from URL:', e);
    }
  }
}

export function useAuth() {
  const isAuthenticated = computed(() => !!user.value);

  const login = (userData, authToken) => {
    user.value = userData;
    token.value = authToken || null;

    localStorage.setItem('auth_user', JSON.stringify(userData));
    if (authToken) {
      localStorage.setItem('auth_token', authToken);
    }
  };

  const logout = () => {
    user.value = null;
    token.value = null;
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
  };

  return {
    user,
    token,
    isAuthenticated,
    login,
    logout,
  };
}
