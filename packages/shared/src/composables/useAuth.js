import { ref, computed } from 'vue';

const user = ref(null);
const token = ref(null);

const savedUser = localStorage.getItem('auth_user');
const savedToken = localStorage.getItem('auth_token');

if (savedUser) {
  try {
    user.value = JSON.parse(savedUser);
  } catch (e) {
    console.warn('[useAuth] Failed to parse saved user');
  }
}
if (savedToken) {
  token.value = savedToken;
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

  // Sync auth from URL params (for cross-app navigation)
  const syncFromUrl = () => {
    const params = new URLSearchParams(window.location.search);
    const urlToken = params.get('token');
    const urlUser = params.get('user');

    if (urlToken) {
      token.value = urlToken;
      localStorage.setItem('auth_token', urlToken);
    }
    if (urlUser) {
      try {
        const userData = JSON.parse(decodeURIComponent(urlUser));
        user.value = userData;
        localStorage.setItem('auth_user', JSON.stringify(userData));
      } catch (e) {
        console.warn('[useAuth] Failed to parse user from URL');
      }
    }

    // Clean URL params after syncing
    if (urlToken || urlUser) {
      const url = new URL(window.location.href);
      url.searchParams.delete('token');
      url.searchParams.delete('user');
      window.history.replaceState({}, '', url.toString());
    }
  };

  // Generate URL with auth params for cross-app navigation
  const getUrlWithAuth = (baseUrl) => {
    const url = new URL(baseUrl, window.location.origin);
    if (token.value) {
      url.searchParams.set('token', token.value);
    }
    if (user.value) {
      url.searchParams.set('user', encodeURIComponent(JSON.stringify(user.value)));
    }
    return url.toString();
  };

  return {
    user,
    token,
    isAuthenticated,
    login,
    logout,
    syncFromUrl,
    getUrlWithAuth,
  };
}
