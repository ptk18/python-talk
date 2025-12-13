import React, { useState, useRef, useEffect } from 'react';
import { useFiles } from '../context/FileContext';
import './FilePanel.css';

interface FilePanelProps {
  conversationId: number;
}

const FilePanel: React.FC<FilePanelProps> = ({ conversationId }) => {
  const {
    files,
    currentFile,
    isFilePanelOpen,
    setFilePanelOpen,
    loadFile,
    deleteFile,
    createNewFile,
  } = useFiles();

  const [isCreatingFile, setIsCreatingFile] = useState(false);
  const [newFileName, setNewFileName] = useState('');
  const panelRef = useRef<HTMLDivElement>(null);

  const handleFileClick = async (filename: string) => {
    if (filename !== currentFile) {
      await loadFile(conversationId, filename);
    }
    setFilePanelOpen(false);
  };

  const handleCreateFile = async () => {
    if (newFileName.trim() && !files.includes(newFileName.trim())) {
      let filename = newFileName.trim();
      if (!filename.endsWith('.py')) {
        filename += '.py';
      }
      
      try {
        await createNewFile(conversationId, filename);
        setNewFileName('');
        setIsCreatingFile(false);
      } catch (error) {
        alert('Failed to create file');
      }
    }
  };

  const handleDeleteFile = async (filename: string, event: React.MouseEvent) => {
    event.stopPropagation();
    
    if (filename === 'runner.py') {
      alert('Cannot delete runner.py');
      return;
    }

    if (window.confirm(`Delete ${filename}?`)) {
      try {
        await deleteFile(conversationId, filename);
      } catch (error) {
        alert('Failed to delete file');
      }
    }
  };

  const togglePanel = () => {
    setFilePanelOpen(!isFilePanelOpen);
  };

  // Handle clicking outside the panel to close it
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (isFilePanelOpen && panelRef.current && !panelRef.current.contains(event.target as Node)) {
        setFilePanelOpen(false);
      }
    };

    if (isFilePanelOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isFilePanelOpen, setFilePanelOpen]);

  return (
    <div className="file-panel" ref={panelRef}>
      {/* File Icon Button */}
      <button
        className="file-panel__toggle-btn"
        onClick={togglePanel}
        aria-label="Toggle file panel"
        title="Files"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M3 3h7l2 2h9v14H3V3z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </button>

      {/* File Panel */}
      {isFilePanelOpen && (
        <div className="file-panel__overlay">
          <div className="file-panel__content">
            <div className="file-panel__header">
              <h3>Files</h3>
              <div className="file-panel__actions">
                <button
                  className="file-panel__action-btn"
                  onClick={() => setIsCreatingFile(true)}
                  title="New File"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 5v14M5 12h14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </button>
                <button
                  className="file-panel__action-btn"
                  onClick={() => setFilePanelOpen(false)}
                  title="Close"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </button>
              </div>
            </div>

            {/* New File Input */}
            {isCreatingFile && (
              <div className="file-panel__new-file">
                <input
                  type="text"
                  value={newFileName}
                  onChange={(e) => setNewFileName(e.target.value)}
                  placeholder="filename.py"
                  className="file-panel__new-file-input"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      handleCreateFile();
                    } else if (e.key === 'Escape') {
                      setIsCreatingFile(false);
                      setNewFileName('');
                    }
                  }}
                  autoFocus
                />
                <div className="file-panel__new-file-actions">
                  <button
                    className="file-panel__new-file-btn file-panel__new-file-btn--create"
                    onClick={handleCreateFile}
                  >
                    Create
                  </button>
                  <button
                    className="file-panel__new-file-btn file-panel__new-file-btn--cancel"
                    onClick={() => {
                      setIsCreatingFile(false);
                      setNewFileName('');
                    }}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}

            {/* File List */}
            <div className="file-panel__files">
              {files.length === 0 ? (
                <div className="file-panel__empty">No files</div>
              ) : (
                files.map((filename) => (
                  <div
                    key={filename}
                    className={`file-panel__file ${
                      filename === currentFile ? 'file-panel__file--active' : ''
                    }`}
                    onClick={() => handleFileClick(filename)}
                  >
                    <div className="file-panel__file-icon">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                    </div>
                    <span className="file-panel__file-name">{filename}</span>
                    {filename !== 'runner.py' && (
                      <button
                        className="file-panel__file-delete"
                        onClick={(e) => handleDeleteFile(filename, e)}
                        title="Delete file"
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      </button>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FilePanel;
