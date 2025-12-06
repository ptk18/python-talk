import React, { createContext, useContext, useState, useCallback } from 'react';
import { executeAPI } from '../services/api';

interface CodeContextType {
  code: string;
  setCode: (code: string) => void;
  appendCode: (snippet: string) => void;
  resetCode: () => void;
  conversationId: number | null;
  setConversationId: (id: number) => void;
  syncCodeFromBackend: () => Promise<void>;
  lastAppendedLineRange: { start: number; end: number } | null;
  setLastAppendedLineRange: (range: { start: number; end: number } | null) => void;
  isLoading: boolean;
}

const CodeContext = createContext<CodeContextType | undefined>(undefined);

export const useCode = () => {
  const context = useContext(CodeContext);
  if (!context) {
    throw new Error('useCode must be used within CodeProvider');
  }
  return context;
};

interface CodeProviderProps {
  children: React.ReactNode;
}

export const CodeProvider: React.FC<CodeProviderProps> = ({ children }) => {
  const [code, setCode] = useState('');
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [lastAppendedLineRange, setLastAppendedLineRange] = useState<{ start: number; end: number } | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const syncCodeFromBackend = useCallback(async () => {
    if (!conversationId) {
      console.warn('Cannot sync code: no conversationId set');
      return;
    }

    setIsLoading(true);
    try {
      const { code: latestCode } = await executeAPI.getRunnerCode(conversationId);
      setCode(latestCode);
    } catch (err) {
      console.error('Failed to sync code from backend:', err);
    } finally {
      setIsLoading(false);
    }
  }, [conversationId]);

  const appendCode = useCallback((snippet: string) => {
    setCode(prevCode => {
      const linesBefore = prevCode.split('\n').length;
      const newCode = prevCode + '\n' + snippet;
      const linesAfter = newCode.split('\n').length;

      setLastAppendedLineRange({ start: linesBefore, end: linesAfter });

      // Clear highlight after 3 seconds
      setTimeout(() => {
        setLastAppendedLineRange(null);
      }, 3000);

      return newCode;
    });
  }, []);

  const resetCode = useCallback(() => {
    setCode('');
    setLastAppendedLineRange(null);
  }, []);

  const value: CodeContextType = {
    code,
    setCode,
    appendCode,
    resetCode,
    conversationId,
    setConversationId,
    syncCodeFromBackend,
    lastAppendedLineRange,
    setLastAppendedLineRange,
    isLoading,
  };

  return (
    <CodeContext.Provider value={value}>
      {children}
    </CodeContext.Provider>
  );
};
