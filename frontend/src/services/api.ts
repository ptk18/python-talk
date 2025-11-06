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
  // GET /conversations/:userId
  async getByUser(userId: number): Promise<Conversation[]> {
    const res = await fetch(`${API_BASE_URL}/conversations/${userId}`);
    if (!res.ok) {
      throw new Error(`Failed to fetch conversations: ${res.statusText}`);
    }
    return await res.json();
  },

  // POST /conversations/:userId
  create: async (userId: number, data: any) => {
    const res = await fetch(`${API_BASE_URL}/conversations/${userId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to create conversation");
    return res.json();
  },

  // GET /conversations/:conversationId/available_methods
  async getAvailableMethods(conversationId: number): Promise<AvailableMethodsResponse> {
    return apiCall(`/conversations/${conversationId}/available_methods`);
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
}

// Message API functions
export const messageAPI = {
  create: async (conversationId: number, sender: string, content: string): Promise<Message> => {
    const params = new URLSearchParams({
      sender,
      content,
    });

    return apiCall(`/messages/${conversationId}?${params}`, {
      method: 'POST',
    });
  },

  getByConversation: async (conversationId: number): Promise<Message[]> => {
    return apiCall(`/messages/${conversationId}`);
  },
};

// Voice API functions
export interface VoiceTranscriptionResponse {
  text: string;           // Translated English text
  alternatives: string[];  // Paraphrased versions
  original: string;        // Original (possibly non-English) text
  error?: string;          // Optional error field
}

export const voiceAPI = {
  /**
   * Send an audio file to the backend Whisper API for transcription and paraphrasing.
   * 
   * @param audioFile The uploaded audio file (webm, wav, etc.)
   * @param language  The spoken language code (e.g., 'en', 'th', 'es')
   */
  transcribe: async (
    audioFile: File,
    language: string
  ): Promise<VoiceTranscriptionResponse> => {
    const formData = new FormData();
    formData.append("file", audioFile);
    formData.append("language", language);

    const response = await fetch(`${API_BASE_URL}/voice/transcribe`, {
      method: "POST",
      body: formData, // No content-type header; browser handles it
    });

    if (!response.ok) {
      const err = await response.text();
      throw new Error(`Voice transcription failed: ${err}`);
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
}

// Analyze Command API functions
export const analyzeAPI = {
  analyzeCommand: async (conversation_id: number, command: string): Promise<AnalyzeCommandResponse> => {
    return apiCall(`/analyze_command`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        conversation_id,
        command,
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
    return apiCall(`/execute_command`, {
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
    return apiCall(`/append_command`, {
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
    return apiCall(`/get_runner_code?${params}`, {
      method: "GET",
    });
  },

  // Check if session exists and initialize if needed
  ensureSessionInitialized: async (conversation_id: number): Promise<boolean> => {
    try {
      // Try to get runner code - if it exists, session is initialized
      const params = new URLSearchParams({ conversation_id: conversation_id.toString() });
      await apiCall(`/get_runner_code?${params}`, { method: "GET" });
      await apiCall(`/get_runner_code?${params}`, { method: "GET" });
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
    return apiCall(`/users/${userId}`, {
      method: 'GET',
    });
  },

  updateProfile: async (userId: number, data: UserProfileUpdate): Promise<UserProfile> => {
    return apiCall(`/users/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },
};
