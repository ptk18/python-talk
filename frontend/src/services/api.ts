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
export const voiceAPI = {
  transcribe: async (audioFile: File, language: string) => {
    const formData = new FormData();
    formData.append('file', audioFile);
    formData.append('language', language);

    return apiCall('/voice/transcribe', {
      method: 'POST',
      headers: {}, // Remove Content-Type for FormData
      body: formData,
    });
  },
};

// Code execution API (will implement endpoint later)
export const codeAPI = {
  execute: async (code: string) => {
    return apiCall('/api/v1/run', {
      method: 'POST',
      body: JSON.stringify({ code }),
    });
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
    return apiCall(`/api/get_runner_code?${params}`, {
      method: "GET",
    });
  },
};
