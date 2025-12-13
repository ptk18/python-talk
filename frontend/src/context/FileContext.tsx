import React, { createContext, useContext, useState, useCallback } from 'react';
import { fileAPI } from '../services/api';

interface FileContextType {
  files: string[];
  currentFile: string;
  currentCode: string;
  isFilePanelOpen: boolean;
  
  setFiles: (files: string[]) => void;
  setCurrentFile: (filename: string) => void;
  setCurrentCode: (code: string) => void;
  setFilePanelOpen: (open: boolean) => void;
  
  loadFiles: (conversationId: number) => Promise<void>;
  loadFile: (conversationId: number, filename: string) => Promise<void>;
  saveFile: (conversationId: number, filename: string, code: string) => Promise<void>;
  deleteFile: (conversationId: number, filename: string) => Promise<void>;
  createNewFile: (conversationId: number, filename: string) => Promise<void>;
}

const FileContext = createContext<FileContextType | undefined>(undefined);

export const useFiles = (): FileContextType => {
  const context = useContext(FileContext);
  if (!context) {
    throw new Error('useFiles must be used within a FileProvider');
  }
  return context;
};

interface FileProviderProps {
  children: React.ReactNode;
}

export const FileProvider: React.FC<FileProviderProps> = ({ children }) => {
  const [files, setFiles] = useState<string[]>([]);
  const [currentFile, setCurrentFile] = useState<string>('runner.py');
  const [currentCode, setCurrentCode] = useState<string>('');
  const [isFilePanelOpen, setFilePanelOpen] = useState<boolean>(false);

  const loadFiles = useCallback(async (conversationId: number) => {
    try {
      const response = await fileAPI.listFiles(conversationId);
      setFiles(response.files);
      
      // If runner.py exists, load it by default
      if (response.files.includes('runner.py')) {
        await loadFile(conversationId, 'runner.py');
      } else if (response.files.length > 0) {
        // Load the first file if runner.py doesn't exist
        await loadFile(conversationId, response.files[0]);
      }
    } catch (error) {
      console.error('Failed to load files:', error);
      setFiles([]);
    }
  }, []);

  const loadFile = useCallback(async (conversationId: number, filename: string) => {
    try {
      const response = await fileAPI.getFile(conversationId, filename);
      // Only update if actually different to prevent unnecessary re-renders
      if (filename !== currentFile) {
        setCurrentFile(filename);
      }
      if (response.code !== currentCode) {
        setCurrentCode(response.code);
      }
    } catch (error) {
      console.error(`Failed to load file ${filename}:`, error);
      // If file doesn't exist, create it as empty
      if (filename !== currentFile) {
        setCurrentFile(filename);
      }
      if (currentCode !== '') {
        setCurrentCode('');
      }
    }
  }, [currentFile, currentCode]);

  const saveFile = useCallback(async (conversationId: number, filename: string, code: string) => {
    try {
      await fileAPI.saveFile(conversationId, filename, code);
      // Update current code if we're saving the current file
      if (filename === currentFile) {
        setCurrentCode(code);
      }
      // Reload files to ensure our list is up to date
      await loadFiles(conversationId);
    } catch (error) {
      console.error(`Failed to save file ${filename}:`, error);
      throw error;
    }
  }, [currentFile, loadFiles]);

  const deleteFile = useCallback(async (conversationId: number, filename: string) => {
    try {
      await fileAPI.deleteFile(conversationId, filename);
      
      // Update files list
      const updatedFiles = files.filter(f => f !== filename);
      setFiles(updatedFiles);
      
      // If we deleted the current file, switch to runner.py or first available file
      if (filename === currentFile) {
        if (updatedFiles.includes('runner.py')) {
          await loadFile(conversationId, 'runner.py');
        } else if (updatedFiles.length > 0) {
          await loadFile(conversationId, updatedFiles[0]);
        } else {
          setCurrentFile('runner.py');
          setCurrentCode('');
        }
      }
    } catch (error) {
      console.error(`Failed to delete file ${filename}:`, error);
      throw error;
    }
  }, [files, currentFile, loadFile]);

  const createNewFile = useCallback(async (conversationId: number, filename: string) => {
    try {
      await fileAPI.saveFile(conversationId, filename, '');
      await loadFiles(conversationId);
      await loadFile(conversationId, filename);
    } catch (error) {
      console.error(`Failed to create file ${filename}:`, error);
      throw error;
    }
  }, [loadFiles, loadFile]);

  const value: FileContextType = {
    files,
    currentFile,
    currentCode,
    isFilePanelOpen,
    
    setFiles,
    setCurrentFile,
    setCurrentCode,
    setFilePanelOpen,
    
    loadFiles,
    loadFile,
    saveFile,
    deleteFile,
    createNewFile,
  };

  return (
    <FileContext.Provider value={value}>
      {children}
    </FileContext.Provider>
  );
};
