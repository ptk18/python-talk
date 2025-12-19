import axios from "axios";
import { API_BASE_URL } from "../config/api";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export default api;

export interface Conversation {
  id: number;
  title: string;
  user_id: number;
  file_name?: string;
  code?: string;
  created_at?: string;
}

export interface MethodInfo {
  name: string;
  parameters: Record<string, string>;
  required_parameters: string[];
  return_type: string | null;
  docstring: string | null;
}

export interface ClassInfo {
  docstring: string | null;
  methods: MethodInfo[];
}

export interface AvailableMethodsResponse {
  success: boolean;
  file_name: string;
  classes: Record<string, ClassInfo>;
  total_classes: number;
}

export const conversationAPI = {
  // GET /api/conversations/:userId
  async getByUser(userId: number): Promise<Conversation[]> {
    const res = await fetch(`${API_BASE_URL}/api/conversations/${userId}`);
    if (!res.ok) {
      throw new Error(`Failed to fetch conversations: ${res.statusText}`);
    }
    return await res.json();
  },

  // POST /api/conversations/:userId
  create: async (userId: number, data: any) => {
    const res = await fetch(`${API_BASE_URL}/api/conversations/${userId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to create conversation");
    return res.json();
  },

  // GET /api/conversations/:conversationId/available_methods
  async getAvailableMethods(conversationId: number): Promise<AvailableMethodsResponse> {
    return apiCall(`/api/conversations/${conversationId}/available_methods`);
  },

  // DELETE /api/conversations/:conversationId
  async delete(conversationId: number): Promise<{ message: string }> {
    return apiCall(`/api/conversations/${conversationId}`, {
      method: "DELETE",
    });
  },
};

// Generic API call function
export const apiCall = async <T = any>(
  endpoint: string, 
  options: RequestInit = {}
): Promise<T> => {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const config: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
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

// Authentication types
export interface LoginRequest {
  username: string;
  password: string;
}

export interface SignupRequest {
  username: string;
  email?: string;
  password: string;
  gender: "male";
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

// Auth API functions
export const authAPI = {
  login: async (credentials: LoginRequest): Promise<AuthResponse> => {
    // FastAPI expects form data for OAuth2PasswordRequestForm
    const formData = new FormData();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);

    return apiCall('/api/v1/auth/login', {
      method: 'POST',
      headers: {}, // Remove Content-Type to let browser set it for FormData
      body: formData,
    });
  },

  signup: async (userData: SignupRequest): Promise<AuthResponse> => {
    return apiCall('/api/v1/auth/signup', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  },
};

// Conversation types
export interface ConversationCreateRequest {
  title: string;
  user_id: number;
  file_name?: string;
  code?: string;
}


// Message types
export interface Message {
  id: number;
  sender: string;
  content: string;
  timestamp: string;
  conversation_id: number;
  paraphrases?: string[]; // Optional field to store paraphrases
  interpretedCommand?: string; // Optional field to store the interpreted command
}

// Message API functions
export const messageAPI = {
  create: async (conversationId: number, sender: string, content: string): Promise<Message> => {
    const params = new URLSearchParams({
      sender,
      content,
    });

    return apiCall(`/api/messages/${conversationId}?${params}`, {
      method: 'POST',
    });
  },

  getByConversation: async (conversationId: number): Promise<Message[]> => {
    return apiCall(`/api/messages/${conversationId}`);
  },
};

// Voice API types - exported for use in voiceService
export interface VoiceTranscriptionResponse {
  text: string;           // Transcribed text in original language
  language: string;       // Detected language code (e.g., "en", "th", "en-US")
  alternatives: string[];  // Paraphrased versions in same language
  original: string;        // Original text (same as text now)
  confidence?: number;     // Confidence score (0-1)
  error?: string;          // Optional error field
}

export const voiceAPI = {
  /**
   * Send an audio file to the backend Whisper API for transcription and paraphrasing.
   *
   * @param audioFile The uploaded audio file (webm, wav, etc.)
   */
  transcribe: async (
    audioFile: File
  ): Promise<VoiceTranscriptionResponse> => {
    const formData = new FormData();
    formData.append("file", audioFile);

    const response = await fetch(`${API_BASE_URL}/api/voice/transcribe`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const err = await response.text();
      throw new Error(`Voice transcription failed: ${err}`);
    }

    return response.json();
  },
};

// Google Speech API functions
export interface GoogleSpeechStatusResponse {
  available: boolean;
  credentials_found: boolean;
  libraries_installed: boolean;
  message: string;
}

export const googleSpeechAPI = {
  /**
   * Check if Google Speech API is available
   */
  checkStatus: async (): Promise<GoogleSpeechStatusResponse> => {
    return apiCall('/api/google-speech/status');
  },

  /**
   * Convert text to speech using Google Cloud TTS
   */
  textToSpeech: async (text: string): Promise<Blob> => {
    const params = new URLSearchParams({ text });

    const response = await fetch(`${API_BASE_URL}/api/google-speech/text-to-speech?${params}`, {
      method: 'POST',
    });

    if (!response.ok) {
      const err = await response.text();
      throw new Error(`Google TTS failed: ${err}`);
    }

    return response.blob();
  },

  /**
   * Convert speech to text using Google Cloud STT
   */
  speechToText: async (
    audioFile: File
  ): Promise<VoiceTranscriptionResponse> => {
    const formData = new FormData();
    formData.append('file', audioFile);

    const response = await fetch(`${API_BASE_URL}/api/google-speech/speech-to-text`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const err = await response.text();
      throw new Error(`Google STT failed: ${err}`);
    }

    return response.json();
  },
};


// Analyze Command types
export interface AnalyzeCommandResponse {
  class_name: string;
  file_name: string;
  result: any; // can refine to string | object depending on what backend returns
}

export interface AnalyzeCommandRequest {
  conversation_id: number;
  command: string;
  language?: string;
}

// Analyze Command API functions
export const analyzeAPI = {
  analyzeCommand: async (conversation_id: number, command: string): Promise<AnalyzeCommandResponse> => {
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
};

// Execute Command types
export interface ExecuteCommandRequest {
  conversation_id: number;
  executable: string;
}

export interface ExecuteCommandResponse {
  output: string;
}

export interface AppendCommandResponse {
  message: string;
}

export interface GetRunnerCodeResponse {
  conversation_id: number;
  code: string;
}

// Execute Command API functions
export const executeAPI = {
  executeCommand: async (
    conversation_id: number,
    executable: string
  ): Promise<ExecuteCommandResponse> => {
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

  rerunCommand: async (conversation_id: number): Promise<ExecuteCommandResponse> => {
    const params = new URLSearchParams({ conversation_id: conversation_id.toString() });
    return apiCall(`/api/rerun_command?${params}`, {
      method: "POST",
    });
  },

  appendCommand: async (
    conversation_id: number,
    executable: string
  ): Promise<AppendCommandResponse> => {
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

  getRunnerCode: async (conversation_id: number): Promise<GetRunnerCodeResponse> => {
    const params = new URLSearchParams({ conversation_id: conversation_id.toString() });
    return apiCall(`/api/get_runner_code?${params}`, {
      method: "GET",
    });
  },

  // Check if session exists and initialize if needed
  ensureSessionInitialized: async (conversation_id: number): Promise<boolean> => {
    try {
      // Try to get runner code - if it exists, session is initialized
      const params = new URLSearchParams({ conversation_id: conversation_id.toString() });
      await apiCall(`/api/get_runner_code?${params}`, { method: "GET" });
      await apiCall(`/api/get_runner_code?${params}`, { method: "GET" });
      return true; // Session exists
    } catch (error: any) {
      // If 404, session doesn't exist - initialize it with a dummy command
      if (error.message.includes("404")) {
        console.log(`Session ${conversation_id} not initialized, creating...`);
        try {
          // Initialize with first_time_created to just create the runner without executing anything
          await executeAPI.executeCommand(conversation_id, "first_time_created");
          console.log(`Session ${conversation_id} initialized successfully`);
          return true;
        } catch (initError) {
          console.error(`Failed to initialize session ${conversation_id}:`, initError);
          return false;
        }
      }
      // Other errors
      console.error(`Error checking session ${conversation_id}:`, error);
      return false;
    }
  },
};

// User Profile types
export interface UserProfile {
  id: number;
  username: string;
  full_name?: string;
  email?: string;
  phone?: string;
  address?: string;
  gender: string;
  created_at: string;
  updated_at?: string;
}

export interface UserProfileUpdate {
  username?: string;
  full_name?: string;
  email?: string;
  phone?: string;
  address?: string;
  gender?: string;
}

// User Profile API functions
export const userAPI = {
  getProfile: async (userId: number): Promise<UserProfile> => {
    return apiCall(`/api/users/${userId}`, {
      method: 'GET',
    });
  },

  updateProfile: async (userId: number, data: UserProfileUpdate): Promise<UserProfile> => {
    return apiCall(`/api/users/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },
};

// File Management types
export interface FileInfo {
  filename: string;
  code: string;
}

export interface ListFilesResponse {
  conversation_id: number;
  files: string[];
}

export interface GetFileResponse {
  conversation_id: number;
  filename: string;
  code: string;
}

export interface SaveFileResponse {
  message: string;
  conversation_id: number;
}

// File Management API functions
export const fileAPI = {
  listFiles: async (conversation_id: number): Promise<ListFilesResponse> => {
    const params = new URLSearchParams({ conversation_id: conversation_id.toString() });
    return apiCall(`/api/list_files?${params}`, {
      method: "GET",
    });
  },

  getFile: async (conversation_id: number, filename: string): Promise<GetFileResponse> => {
    const params = new URLSearchParams({ 
      conversation_id: conversation_id.toString(),
      filename 
    });
    return apiCall(`/api/get_file?${params}`, {
      method: "GET",
    });
  },

  saveFile: async (
    conversation_id: number,
    filename: string,
    code: string
  ): Promise<SaveFileResponse> => {
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

  deleteFile: async (
    conversation_id: number,
    filename: string
  ): Promise<SaveFileResponse> => {
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

// Paraphrase API types
export interface ParaphraseRequest {
  text: string;
  max_variants: number;
}

export interface ParaphraseResponse {
  variants: string[];
}

// Paraphrase API functions
export const paraphraseAPI = {
  getParaphrases: async (text: string, maxVariants: number = 10): Promise<ParaphraseResponse> => {
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
