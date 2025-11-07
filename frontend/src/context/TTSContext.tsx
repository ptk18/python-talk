import { createContext, useContext, useState, type ReactNode, useEffect } from "react";
import { setTTSEnabled } from "../utils/tts";

interface TTSContextType {
  ttsEnabled: boolean;
  toggleTTS: () => void;
}

const TTSContext = createContext<TTSContextType | undefined>(undefined);

export function TTSProvider({ children }: { children: ReactNode }) {
  const [ttsEnabled, setTtsEnabled] = useState(true);

  const toggleTTS = () => {
    setTtsEnabled(prev => {
      const newValue = !prev;
      setTTSEnabled(newValue);
      return newValue;
    });
  };

  // Initialize TTS state on mount
  useEffect(() => {
    setTTSEnabled(ttsEnabled);
  }, []);

  return (
    <TTSContext.Provider value={{ ttsEnabled, toggleTTS }}>
      {children}
    </TTSContext.Provider>
  );
}

export function useTTS() {
  const context = useContext(TTSContext);
  if (!context) {
    throw new Error("useTTS must be used within TTSProvider");
  }
  return context;
}
