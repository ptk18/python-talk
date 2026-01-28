import { API_BASE_URL } from '../config.js';

// Token management
const TOKEN_KEY = 'auth_token';
const USER_KEY = 'auth_user';

export const getAuthToken = () => localStorage.getItem(TOKEN_KEY);
export const setAuthToken = (token) => localStorage.setItem(TOKEN_KEY, token);
export const removeAuthToken = () => localStorage.removeItem(TOKEN_KEY);

export const getAuthUser = () => {
  const user = localStorage.getItem(USER_KEY);
  return user ? JSON.parse(user) : null;
};
export const setAuthUser = (user) => localStorage.setItem(USER_KEY, JSON.stringify(user));
export const removeAuthUser = () => localStorage.removeItem(USER_KEY);

export const logout = () => {
  removeAuthToken();
  removeAuthUser();
};

const apiCall = async (endpoint, options = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;
  const token = getAuthToken();

  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
      ...options.headers,
    },
    ...options,
  };

  const response = await fetch(url, config);

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`HTTP ${response.status}: ${errorText}`);
  }

  return response.json();
};

export const authAPI = {
  login: async (credentials) => {
    const formData = new FormData();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);

    const response = await apiCall('/api/v1/auth/login', {
      method: 'POST',
      headers: {},
      body: formData,
    });

    // Store token and user after successful login
    if (response.access_token) {
      setAuthToken(response.access_token);
      setAuthUser(response.user);
    }
    return response;
  },

  signup: async (userData) => {
    const response = await apiCall('/api/v1/auth/signup', {
      method: 'POST',
      body: JSON.stringify(userData),
    });

    // Store token and user after successful signup
    if (response.access_token) {
      setAuthToken(response.access_token);
      setAuthUser(response.user);
    }
    return response;
  },

  logout: () => {
    logout();
  },
};

export const conversationAPI = {
  async getByUser(userId) {
    const token = getAuthToken();
    const res = await fetch(`${API_BASE_URL}/api/conversations/${userId}`, {
      headers: token ? { 'Authorization': `Bearer ${token}` } : {},
    });
    if (!res.ok) {
      throw new Error(`Failed to fetch conversations: ${res.statusText}`);
    }
    return await res.json();
  },

  create: async (userId, data) => {
    const token = getAuthToken();
    const res = await fetch(`${API_BASE_URL}/api/conversations/${userId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to create conversation');
    return res.json();
  },

  async getAvailableMethods(conversationId) {
    return apiCall(`/api/conversations/${conversationId}/available_methods`);
  },

  async delete(conversationId) {
    return apiCall(`/api/conversations/${conversationId}`, {
      method: 'DELETE',
    });
  },

  async update(conversationId, data) {
    return apiCall(`/api/conversations/${conversationId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  async getSingleConversation(conversationId) {
    return apiCall(`/api/conversations/${conversationId}/single`);
  },
};

export const messageAPI = {
  create: async (conversationId, sender, content) => {
    const params = new URLSearchParams({
      sender,
      content,
    });

    return apiCall(`/api/messages/${conversationId}?${params}`, {
      method: 'POST',
    });
  },

  getByConversation: async (conversationId) => {
    return apiCall(`/api/messages/${conversationId}`);
  },
};

export const voiceAPI = {
  transcribe: async (audioFile, language = 'en') => {
    const formData = new FormData();
    formData.append("file", audioFile);
    formData.append("language", language);

    const token = getAuthToken();
    const response = await fetch(`${API_BASE_URL}/api/voice/transcribe`, {
      method: "POST",
      headers: token ? { 'Authorization': `Bearer ${token}` } : {},
      body: formData,
    });

    if (!response.ok) {
      const err = await response.text();
      throw new Error(`Voice transcription failed: ${err}`);
    }

    return response.json();
  },
};

export const googleSpeechAPI = {
  checkStatus: async () => {
    return apiCall('/api/google-speech/status');
  },

  textToSpeech: async (text, rate = 1.0) => {
    const params = new URLSearchParams({
      text,
      rate: rate.toString()
    });
    const token = getAuthToken();

    const response = await fetch(`${API_BASE_URL}/api/google-speech/text-to-speech?${params}`, {
      method: 'POST',
      headers: token ? { 'Authorization': `Bearer ${token}` } : {},
    });

    if (!response.ok) {
      const err = await response.text();
      throw new Error(`Google TTS failed: ${err}`);
    }

    return response.blob();
  },

  speechToText: async (audioFile, language = 'en') => {
    const formData = new FormData();
    formData.append('file', audioFile);
    formData.append('language', language);

    const token = getAuthToken();
    const response = await fetch(`${API_BASE_URL}/api/google-speech/speech-to-text`, {
      method: 'POST',
      headers: token ? { 'Authorization': `Bearer ${token}` } : {},
      body: formData,
    });

    if (!response.ok) {
      const err = await response.text();
      throw new Error(`Google STT failed: ${err}`);
    }

    return response.json();
  },
};

export const analyzeAPI = {
  analyzeCommand: async (conversation_id, command) => {
    return apiCall(`/api/analyze_command`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        conversation_id,
        command,
        language: 'en',
      }),
    });
  },

  prewarmPipeline: async (conversation_id) => {
    return apiCall(`/api/prewarm_pipeline`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        conversation_id,
        command: '',
        language: 'en',
      }),
    });
  },

  invalidatePipelineCache: async (conversation_id) => {
    return apiCall(`/api/invalidate_pipeline_cache`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        conversation_id,
        command: '',
        language: 'en',
      }),
    });
  },
};

export const executeAPI = {
  executeCommand: async (conversation_id, executable) => {
    return apiCall(`/api/execute_command`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        conversation_id,
        executable,
      }),
    });
  },

  rerunCommand: async (conversation_id) => {
    const params = new URLSearchParams({ conversation_id: conversation_id.toString() });
    return apiCall(`/api/rerun_command?${params}`, {
      method: "POST",
    });
  },

  appendCommand: async (conversation_id, executable) => {
    return apiCall(`/api/append_command`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        conversation_id,
        executable,
      }),
    });
  },

  getRunnerCode: async (conversation_id) => {
    const params = new URLSearchParams({ conversation_id: conversation_id.toString() });
    return apiCall(`/api/get_runner_code?${params}`, {
      method: "GET",
    });
  },

  ensureSessionInitialized: async (conversation_id) => {
    try {
      const params = new URLSearchParams({ conversation_id: conversation_id.toString() });
      await apiCall(`/api/get_runner_code?${params}`, { method: "GET" });
      await apiCall(`/api/get_runner_code?${params}`, { method: "GET" });
      return true;
    } catch (error) {
      if (error.message.includes("404")) {
        console.log(`Session ${conversation_id} not initialized, creating...`);
        try {
          await executeAPI.executeCommand(conversation_id, "first_time_created");
          console.log(`Session ${conversation_id} initialized successfully`);
          return true;
        } catch (initError) {
          console.error(`Failed to initialize session ${conversation_id}:`, initError);
          return false;
        }
      }
      console.error(`Error checking session ${conversation_id}:`, error);
      return false;
    }
  },
};

export const userAPI = {
  getProfile: async (userId) => {
    return apiCall(`/api/users/${userId}`, {
      method: 'GET',
    });
  },

  updateProfile: async (userId, data) => {
    return apiCall(`/api/users/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },
};

export const fileAPI = {
  listFiles: async (conversation_id) => {
    const params = new URLSearchParams({ conversation_id: conversation_id.toString() });
    return apiCall(`/api/list_files?${params}`, {
      method: "GET",
    });
  },

  getFile: async (conversation_id, filename) => {
    const params = new URLSearchParams({
      conversation_id: conversation_id.toString(),
      filename
    });
    return apiCall(`/api/get_file?${params}`, {
      method: "GET",
    });
  },

  saveFile: async (conversation_id, filename, code) => {
    return apiCall(`/api/save_file`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        conversation_id,
        filename,
        code,
      }),
    });
  },

  deleteFile: async (conversation_id, filename) => {
    return apiCall(`/api/delete_file`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        conversation_id,
        filename,
      }),
    });
  },
};

export const paraphraseAPI = {
  getParaphrases: async (text, maxVariants = 10) => {
    return apiCall(`/api/user_command_paraphrasing_suggestion`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        text,
        max_variants: maxVariants,
      }),
    });
  },
};

export const translateAPI = {
  translateToEnglish: async (text) => {
    return apiCall(`/api/translate/text`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        text,
        source_lang: "th",
        target_lang: "en",
      }),
    });
  },

  translate: async (text, sourceLang, targetLang) => {
    return apiCall(`/api/translate/text`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        text,
        source_lang: sourceLang,
        target_lang: targetLang,
      }),
    });
  },

  checkStatus: async () => {
    return apiCall(`/api/translate/status`);
  },
};

export const turtleAPI = {
  analyzeCommand: async (command, language = 'en') => {
    return apiCall(`/api/analyze_turtle_command`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        command,
        language,
      }),
    });
  },

  getMethods: async () => {
    return apiCall(`/api/turtle_methods`, {
      method: 'GET',
    });
  },

  prewarmPipeline: async () => {
    return apiCall(`/api/prewarm_turtle_pipeline`, {
      method: 'POST',
    });
  },
};

export const favoritesAPI = {
  async getByUser(userId) {
    return apiCall(`/api/favorites/${userId}`);
  },

  async toggle(userId, data) {
    return apiCall(`/api/favorites/${userId}/toggle`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
};
