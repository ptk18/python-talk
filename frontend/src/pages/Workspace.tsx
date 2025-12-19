import { useState, useEffect, useRef, useCallback } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import Navbar from "../components/Navbar";
import MonacoEditor from "../components/MonacoEditor";
import type { MonacoEditorRef } from "../components/MonacoEditor";
import FilePanel from "../components/FilePanel";
import "./styles/Workspace.css";
import Snake from "../assets/scorpio.svg";
import User from "../assets/user.svg";
import ChatIcon from "../assets/chat.svg";
import Voice from "../assets/voice.svg";
import VoiceWhite from "../assets/voice-white.svg";
import { useTheme } from "../theme/ThemeProvider";
import { messageAPI, conversationAPI, executeAPI, analyzeAPI, voiceAPI, fileAPI, paraphraseAPI } from "../services/api";
import type { Message, AvailableMethodsResponse } from "../services/api";
import { useAuth } from "../context/AuthContext";
import { useCode } from "../context/CodeContext";
import { useFiles } from "../context/FileContext";
import { voiceService } from "../services/voiceService";

export default function Workspace() {
    const { theme } = useTheme();
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const conversationId = searchParams.get("conversationId");
    const { user } = useAuth();
    const { code, setCode, syncCodeFromBackend, setConversationId } = useCode();
    const { 
        currentFile, 
        currentCode, 
        setCurrentCode,
        loadFiles, 
        loadFile, 
        saveFile 
    } = useFiles();

    const [isChatActive, setIsChatActive] = useState(false);
    const [message, setMessage] = useState("");
    const [messages, setMessages] = useState<Message[]>([]);
    const [availableMethods, setAvailableMethods] = useState<AvailableMethodsResponse | null>(null);
    const [output, setOutput] = useState("");
    const [isRunning, setIsRunning] = useState(false);
    const [isTurtleCode, setIsTurtleCode] = useState<boolean | null>(null);
    const [showTurtlePrompt, setShowTurtlePrompt] = useState(false);

    const voiceIcon = theme === "dark" ? VoiceWhite : Voice;
    const audioContextRef = useRef<AudioContext | null>(null);
    const [isRecording, setIsRecording] = useState(false);
    const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
    const audioChunks = useRef<BlobPart[]>([]);
    const editorRef = useRef<MonacoEditorRef>(null);
    const [isSaving, setIsSaving] = useState(false);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [refreshNotification, setRefreshNotification] = useState<string | null>(null);
    const [lastUserEdit, setLastUserEdit] = useState<number>(0);
    const [isUserEditing, setIsUserEditing] = useState(false);
    const editingTimeoutRef = useRef<number | null>(null);
    const [expandedParaphrases, setExpandedParaphrases] = useState<Set<number>>(new Set());
    const [loadingParaphrases, setLoadingParaphrases] = useState<Set<number>>(new Set());

    useEffect(() => {
        if (conversationId) {
            setConversationId(parseInt(conversationId));
            initializeSession();
        }
    }, [conversationId, setConversationId]);

    useEffect(() => {
        if (conversationId) {
            loadFiles(parseInt(conversationId));
        }
    }, [conversationId, loadFiles]);

    // Reset editing state when current file changes
    useEffect(() => {
        setIsUserEditing(false);
        if (editingTimeoutRef.current) {
            clearTimeout(editingTimeoutRef.current);
        }
    }, [currentFile]);

    // Auto-refresh runner.py when code context changes and it's the current file
    useEffect(() => {
        const refreshRunnerFile = async () => {
            if (conversationId && currentFile === 'runner.py' && code !== currentCode) {
                try {
                    // Only refresh if user hasn't edited recently
                    const timeSinceLastEdit = Date.now() - lastUserEdit;
                    if (timeSinceLastEdit > 10000) {
                        await loadFile(parseInt(conversationId), 'runner.py');
                    }
                } catch (error) {
                    console.error('Failed to auto-refresh runner.py:', error);
                }
            }
        };
        
        refreshRunnerFile();
    }, [code, currentFile, conversationId, loadFile, lastUserEdit]);

    // Poll for changes in runner.py every 10 seconds if it's the current file
    useEffect(() => {
        if (!conversationId || currentFile !== 'runner.py') return;

        const pollForChanges = async () => {
            try {
                // Don't poll if user has edited recently (within last 15 seconds)
                const timeSinceLastEdit = Date.now() - lastUserEdit;
                if (timeSinceLastEdit < 15000) {
                    return;
                }
                
                const response = await fileAPI.getFile(parseInt(conversationId), 'runner.py');
                // Only update if content actually changed and user isn't actively editing
                if (response.code !== currentCode && !isUserEditing) {
                    setIsRefreshing(true);
                    setCurrentCode(response.code);
                    // Also update the code context to keep it in sync
                    setCode(response.code);
                    
                    // Show notification
                    setRefreshNotification('File updated with new commands');
                    
                    // Hide refresh indicator and notification after delays
                    setTimeout(() => setIsRefreshing(false), 1000);
                    setTimeout(() => setRefreshNotification(null), 3000);
                }
            } catch (error) {
                console.error('Failed to poll for runner.py changes:', error);
            }
        };

        const intervalId = setInterval(pollForChanges, 10000); // Poll every 10 seconds (less frequent)

        return () => clearInterval(intervalId);
    }, [conversationId, currentFile, currentCode, setCurrentCode, setCode, lastUserEdit, isUserEditing]);

    // Cleanup editing timeout on unmount
    useEffect(() => {
        return () => {
            if (editingTimeoutRef.current) {
                clearTimeout(editingTimeoutRef.current);
            }
        };
    }, []);

    const initializeSession = async () => {
        if (!conversationId) return;
        try {
            await executeAPI.ensureSessionInitialized(parseInt(conversationId));
            await fetchMessages();
            await fetchAvailableMethods();
            await syncCodeFromBackend();

            // Pre-warm NLP pipeline in background for faster first command
            analyzeAPI.prewarmPipeline(parseInt(conversationId))
                .then(() => console.log('NLP pipeline pre-warmed'))
                .catch(err => console.warn('Pipeline pre-warm failed:', err));
        } catch (err) {
            console.error("Failed to initialize session:", err);
        }
    };

    const fetchMessages = async () => {
        if (!conversationId) return;
        try {
            const msgs = await messageAPI.getByConversation(parseInt(conversationId));
            // Preserve interpretedCommand and paraphrases from existing messages
            setMessages(prevMessages => {
                return msgs.map(msg => {
                    const existing = prevMessages.find(m => m.id === msg.id);
                    return existing
                        ? { ...msg, interpretedCommand: existing.interpretedCommand, paraphrases: existing.paraphrases }
                        : msg;
                });
            });
        } catch (err) {
            console.error("Failed to fetch messages:", err);
        }
    };

    const fetchAvailableMethods = async () => {
        if (!conversationId) return;
        try {
            const methods = await conversationAPI.getAvailableMethods(parseInt(conversationId));
            setAvailableMethods(methods);
        } catch (err) {
            console.error("Failed to fetch available methods:", err);
        }
    };

    const handleSend = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!message.trim() || !conversationId) return;

        const msgText = message.trim();
        setMessage("");

        try {
            const userMsg = await messageAPI.create(parseInt(conversationId), "user", msgText);

            const data = await analyzeAPI.analyzeCommand(Number(conversationId), msgText);
            const r = data.result || {};

            let summary;
            if (r.executable) {
                summary = r.executable;
            } else if (r.executables && r.executables.length > 0) {
                summary = r.executables.join('\n');
            } else if (r.code) {
                summary = r.code;
            } else {
                summary = "No executable command generated";
            }

            await messageAPI.create(parseInt(conversationId), "system", summary);

            // Fetch messages and add interpretedCommand to the user message
            const msgs = await messageAPI.getByConversation(parseInt(conversationId));
            const updatedMsgs = msgs.map(msg =>
                msg.id === userMsg.id
                    ? { ...msg, interpretedCommand: summary }
                    : msg
            );
            setMessages(updatedMsgs);

            const executable = r.executable || (r.executables && r.executables.length > 0 ? r.executables.join('\n') : null);

            if (executable) {
                const confirmed = window.confirm(
                    `Do you want to append the command(s) to the runner file?\n\n${executable}`
                );

                if (confirmed) {
                    await executeAPI.appendCommand(Number(conversationId), executable);
                    await syncCodeFromBackend();
                    
                    // If currently viewing runner.py, refresh it to show the new commands
                    if (currentFile === 'runner.py') {
                        setIsRefreshing(true);
                        await loadFile(parseInt(conversationId), 'runner.py');
                        setTimeout(() => setIsRefreshing(false), 1000);
                    }
                    
                    await messageAPI.create(parseInt(conversationId), "system", `Command(s) appended successfully.`);
                    voiceService.speak("Command appended successfully");
                    await fetchMessages();
                }
            } else {
                voiceService.speak("I couldn't process that command. Could you please try again?");
            }
        } catch (err: any) {
            console.error("Failed to send or analyze message:", err);
            voiceService.speak("I encountered an error. Please try again");
            alert("Error: " + err.message);
        }
    };

    const handleSave = useCallback(async () => {
        if (!conversationId) {
            console.error("No conversation ID");
            return;
        }

        setIsSaving(true);
        try {
            // Save the current file being edited
            await saveFile(parseInt(conversationId), currentFile, currentCode);
            
            // Also update the code context if we're editing runner.py
            if (currentFile === 'runner.py') {
                setCode(currentCode);
            }

            // Reset the last edit time and editing state to allow polling to resume
            setLastUserEdit(0);
            setIsUserEditing(false);
            if (editingTimeoutRef.current) {
                clearTimeout(editingTimeoutRef.current);
            }

            voiceService.speak("Code saved successfully");
            console.log("Code saved successfully");
        } catch (err) {
            console.error("Failed to save code:", err);
            voiceService.speak("Failed to save code");
        } finally {
            setIsSaving(false);
        }
    }, [conversationId, saveFile, currentFile, currentCode, setCode]);

    // Keyboard shortcut for saving (Ctrl+S / Cmd+S)
    useEffect(() => {
        const handleKeyDown = (event: KeyboardEvent) => {
            if ((event.ctrlKey || event.metaKey) && event.key === 's') {
                event.preventDefault();
                handleSave();
            }
        };

        document.addEventListener('keydown', handleKeyDown);
        return () => document.removeEventListener('keydown', handleKeyDown);
    }, [handleSave]);

    const handleUndo = () => {
        editorRef.current?.undo();
    };

    const handleRedo = () => {
        editorRef.current?.redo();
    };

    const handleRun = async () => {
        // Always run runner.py, regardless of which file is currently open in the editor
        try {
            // First, ensure runner.py exists and get its content
            const runnerResponse = await executeAPI.getRunnerCode(parseInt(conversationId!));
            const runnerCode = runnerResponse.code;
            
            if (!runnerCode.trim()) {
                setOutput("Error: runner.py is empty. Please add some commands.\n");
                voiceService.speak("Runner file is empty. Please add some commands");
                return;
            }
        } catch (err) {
            setOutput("Error: runner.py not found. Please initialize the session first.\n");
            voiceService.speak("Runner file not found. Please initialize the session first");
            return;
        }

        if (isTurtleCode === null) {
            setShowTurtlePrompt(true);
            voiceService.speak("Is this turtle code?");
            return;
        }

        if (isTurtleCode) {
            await handleRunTurtle();
        } else {
            await handleRunNormalCode();
        }
    };

    const handleRunNormalCode = async () => {
        setIsRunning(true);
        setOutput("Running code...\n\n");

        try {
            const res = await executeAPI.rerunCommand(parseInt(conversationId!));
            setOutput(res.output || "No output returned from execute_command.\n");
            voiceService.speak("Your output is ready, Sir");
        } catch (err) {
            console.error("Failed to execute command:", err);
            setOutput("Error executing command.\n");
            voiceService.speak("Please try again");
        } finally {
            setIsRunning(false);
        }
    };

    const handleRunTurtle = async () => {
        setIsRunning(true);
        setOutput("Running turtle graphics...\n\n");

        const hostname = window.location.hostname;
        const apiBase = `http://192.168.4.228:8001`;
        const rawWsBase = `ws://192.168.4.228:5050`;
        const wsBase = rawWsBase
            .replace("localhost", hostname)
            .replace("127.0.0.1", hostname);

        try {
            // Setup WebSocket FIRST - before triggering turtle execution
            const channelName = encodeURIComponent(String(conversationId));
            const ws = new WebSocket(`${wsBase}/subscribe/${channelName}`);

            console.log("Connecting WebSocket subscriber before starting turtle execution...");

            // Wait for WebSocket to connect
            await new Promise<void>((resolve, reject) => {
                ws.onopen = () => {
                    console.log("Turtle WebSocket connected - ready to receive frames");
                    resolve();
                };
                ws.onerror = (err) => {
                    console.error("Turtle WebSocket error:", err);
                    reject(err);
                };
            });

            // Now setup message handler
            ws.onmessage = (event) => {
                console.log("Received turtle frame:", event.data?.substring(0, 50));
                const image = event.data;
                const videoEl = document.getElementById("turtle-video") as HTMLImageElement | null;
                if (videoEl) {
                    videoEl.src = `data:image/jpeg;base64,${image}`;
                    console.log("Updated turtle video element");
                } else {
                    console.error("turtle-video element not found");
                }
            };

            ws.onclose = () => {
                console.log("Turtle WebSocket closed");
            };

            // NOW fetch session files and trigger turtle execution
            const getRes = await fetch(
                `${import.meta.env.VITE_API_BASE_URL || ""}/api/get_session_files?conversation_id=${conversationId}`,
                { headers: { Accept: "application/json" } }
            );

            if (!getRes.ok) {
                const text = await getRes.text();
                throw new Error(`Failed to fetch session files: ${text}`);
            }

            const { files } = await getRes.json();
            console.log("Session files fetched:", Object.keys(files));

            const payload = {
                files: files,
            };

            const res = await fetch(`${apiBase}/run_turtle/${conversationId}`, {
                method: "POST",
                headers: {
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(payload),
            });

            if (!res.ok) {
                const errorText = await res.text();
                throw new Error(`Backend returned ${res.status}: ${errorText}`);
            }

            const data = await res.json();
            console.log("Turtle execute response:", data);

            setOutput("Turtle graphics execution triggered on streaming device.\n");
            voiceService.speak("Your turtle graphics are running, Sir");
        } catch (err) {
            console.error("Failed to execute turtle graphics:", err);
            setOutput("Error executing turtle graphics.\n");
            voiceService.speak("Please try again");
        } finally {
            setIsRunning(false);
        }
    };

    const playClickSound = () => {
        try {
            if (!audioContextRef.current) {
                audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
            }
            const audioContext = audioContextRef.current;
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();

            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            oscillator.frequency.value = 800;
            oscillator.type = 'sine';
            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.1);
        } catch (error) {
            console.log("Audio playback not available:", error);
        }
    };


    const handleToggleParaphrases = async (msg: Message) => {
        if (!msg.id) return;

        // If already expanded, just collapse
        if (expandedParaphrases.has(msg.id)) {
            setExpandedParaphrases(prev => {
                const next = new Set(prev);
                next.delete(msg.id);
                return next;
            });
            return;
        }

        // If paraphrases are already loaded, just expand
        if (msg.paraphrases && msg.paraphrases.length > 0) {
            setExpandedParaphrases(prev => new Set(prev).add(msg.id));
            return;
        }

        // Otherwise, fetch paraphrases
        setLoadingParaphrases(prev => new Set(prev).add(msg.id));
        try {
            const response = await paraphraseAPI.getParaphrases(msg.content, 10);

            // Update the message with paraphrases
            setMessages(prevMessages =>
                prevMessages.map(m =>
                    m.id === msg.id
                        ? { ...m, paraphrases: response.variants }
                        : m
                )
            );

            // Expand the section
            setExpandedParaphrases(prev => new Set(prev).add(msg.id));
        } catch (error) {
            console.error("Failed to fetch paraphrases:", error);
            voiceService.speak("Failed to generate suggestions");
        } finally {
            setLoadingParaphrases(prev => {
                const next = new Set(prev);
                next.delete(msg.id);
                return next;
            });
        }
    };

    const handleMicClick = async () => {
        playClickSound();

        if (!isRecording) {
            try {
                voiceService.speak("Listening");
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                const recorder = new MediaRecorder(stream);
                audioChunks.current = [];

                recorder.ondataavailable = (e) => {
                    audioChunks.current.push(e.data);
                };

                recorder.onstop = async () => {
                    const audioBlob = new Blob(audioChunks.current, { type: "audio/webm" });

                    // Convert Blob to proper File object with metadata
                    const audioFile = new File(
                        [audioBlob],
                        `recording_${Date.now()}.webm`,
                        { type: "audio/webm" }
                    );

                    try {
                        const result = await voiceService.transcribe(audioFile);
                        const text = result.text || `[Error: ${result.error || "Unknown"}]`;

                        if (text.includes("[Error")) {
                            voiceService.speak("I couldn't understand that. Please try again");
                        } else {
                            console.log(`Transcribed text: ${text}`);
                            voiceService.speak("Voice command received");
                        }

                        setMessage(text);
                        if (!isChatActive) setIsChatActive(true);
                    } catch (err: any) {
                        console.error("Voice transcription error:", err);
                        voiceService.speak("Voice transcription error");
                        alert("Error transcribing voice: " + err.message);
                    }
                };

                recorder.start();
                setMediaRecorder(recorder);
                setIsRecording(true);
            } catch (err) {
                console.error("Microphone access denied:", err);
                voiceService.speak("Microphone access denied");
                alert("Microphone access denied or unavailable.");
            }
        } else {
            if (mediaRecorder && mediaRecorder.state !== "inactive") {
                mediaRecorder.stop();
            }
            setIsRecording(false);
        }
    };



    return (
        <div className="workspace">
            <Navbar />

            {/* Turtle Code Prompt Modal */}
            {showTurtlePrompt && (
                <div className="workspace__modal-overlay">
                    <div className="workspace__modal">
                        <h3>Is this Turtle Code?</h3>
                        <p>Does this code use Python turtle graphics?</p>
                        <div className="workspace__modal-buttons">
                            <button
                                onClick={() => {
                                    setIsTurtleCode(true);
                                    setShowTurtlePrompt(false);
                                    handleRunTurtle();
                                }}
                                className="workspace__modal-btn workspace__modal-btn--yes"
                            >
                                Yes, Turtle Code
                            </button>
                            <button
                                onClick={() => {
                                    setIsTurtleCode(false);
                                    setShowTurtlePrompt(false);
                                    handleRunNormalCode();
                                }}
                                className="workspace__modal-btn workspace__modal-btn--no"
                            >
                                No, Normal Code
                            </button>
                        </div>
                    </div>
                </div>
            )}

            <div className="workspace__container">
                {/* Left sidebar - Available Methods */}
                {availableMethods && (
                    <aside className="workspace__sidebar">
                        <h3 className="workspace__sidebar-title">
                            {availableMethods.file_name || "Available Methods"}
                        </h3>
                        <div className="workspace__sidebar-content">
                            {Object.entries(availableMethods.classes).map(([className, classInfo]) => (
                                <div key={className} className="workspace__methods-list">
                                    {classInfo.methods.map((method) => {
                                        const params = method.required_parameters.length > 0
                                            ? method.required_parameters.join(", ")
                                            : "";
                                        const signature = `${method.name}(${params})`;

                                        return (
                                            <div key={method.name} className="workspace__method-item">
                                                <div className="workspace__method-name">{signature}</div>
                                            </div>
                                        );
                                    })}
                                </div>
                            ))}
                        </div>
                    </aside>
                )}

                {/* Middle - Chat Panel */}
                <main className="workspace__chat">
                    <section className="workspace__chat-scroll">
                        {messages.map((msg) => {
                            const isUser = msg.sender === "user";
                            const time = new Date(msg.timestamp).toLocaleTimeString('en-US', {
                                hour: '2-digit',
                                minute: '2-digit',
                                hour12: false
                            });
                            const isExpanded = expandedParaphrases.has(msg.id);
                            const isLoadingParaphrase = loadingParaphrases.has(msg.id);

                            return (
                                <div key={msg.id} style={{ display: 'flex', flexDirection: 'column', marginBottom: '12px' }}>
                                    <div className={`workspace__chat-row ${isUser ? 'workspace__chat-row--right' : 'workspace__chat-row--left'}`} style={{ alignSelf: isUser ? 'flex-end' : 'flex-start' }}>
                                        {!isUser && (
                                            <div className="workspace__avatar-container">
                                                <img src={Snake} alt="Scorpio" className="workspace__avatar" />
                                                <div className="workspace__name workspace__name--left">Scorpio</div>
                                            </div>
                                        )}
                                        {isUser && <span className="workspace__time workspace__time--left">{time}</span>}
                                        <div className="workspace__bubble">
                                            {msg.content.includes('```') ? (
                                                <div className="workspace__code">
                                                    <pre><code>{msg.content.replace(/```[\s\S]*?\n|```/g, '')}</code></pre>
                                                </div>
                                            ) : (
                                                msg.content
                                            )}
                                        </div>
                                        {isUser && (
                                            <div className="workspace__avatar-container">
                                                <img src={User} alt="User" className="workspace__avatar" />
                                                <div className="workspace__name workspace__name--right">{user?.username || "User"}</div>
                                            </div>
                                        )}
                                        {!isUser && <span className="workspace__time">{time}</span>}
                                    </div>

                                    {/* Paraphrase suggestions for user messages */}
                                    {isUser && msg.interpretedCommand && (
                                        <div className="workspace__command-card" style={{ alignSelf: 'flex-end', marginRight: '60px', marginTop: '4px', width: 'max-content', maxWidth: '400px' }}>
                                            <button
                                                className="workspace__paraphrase-toggle"
                                                onClick={() => handleToggleParaphrases(msg)}
                                                disabled={isLoadingParaphrase}
                                            >
                                                {isLoadingParaphrase ? (
                                                    <span>Generating suggestions...</span>
                                                ) : isExpanded ? (
                                                    <span>▼ Hide </span>
                                                ) : (
                                                    <span>▶ Other ways to say it</span>
                                                )}
                                            </button>

                                            {isExpanded && msg.paraphrases && msg.paraphrases.length > 0 && (
                                                <div className="workspace__paraphrases-list">
                                                    {msg.paraphrases.map((paraphrase, idx) => (
                                                        <div
                                                            key={idx}
                                                            className="workspace__paraphrase-item"
                                                            onClick={() => setMessage(paraphrase)}
                                                        >
                                                            • {paraphrase}
                                                        </div>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </section>

                    {/* Chat Input */}
                    <footer className="workspace__chat-footer">
                        <div className="workspace__chat-input-container">
                            <div
                                className={`workspace__mic-inner ${isRecording ? "workspace__mic-inner--recording" : ""}`}
                                onClick={handleMicClick}
                            >
                                <svg
                                    className="workspace__mic"
                                    viewBox="0 0 24 24"
                                    fill="none"
                                    xmlns="http://www.w3.org/2000/svg"
                                >
                                    <path
                                        d="M12 14C13.66 14 15 12.66 15 11V5C15 3.34 13.66 2 12 2C10.34 2 9 3.34 9 5V11C9 12.66 10.34 14 12 14Z"
                                        fill="currentColor"
                                    />
                                    <path
                                        d="M17 11C17 13.76 14.76 16 12 16C9.24 16 7 13.76 7 11H5C5 14.53 7.61 17.43 11 17.92V21H13V17.92C16.39 17.43 19 14.53 19 11H17Z"
                                        fill="currentColor"
                                    />
                                </svg>
                                {isRecording && <div className="workspace__mic-pulse"></div>}
                            </div>

                            <form className="workspace__input-form" onSubmit={handleSend}>
                                <input
                                    type="text"
                                    className="workspace__input"
                                    placeholder="Type your message..."
                                    value={message}
                                    onChange={(e) => setMessage(e.target.value)}
                                />
                                <button type="submit" className="workspace__send-btn" aria-label="Send message">
                                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                                        <path d="M2 21L23 12L2 3V10L17 12L2 14V21Z"/>
                                    </svg>
                                </button>
                            </form>
                        </div>
                    </footer>
                </main>

                {/* Right - Code & Output Panel */}
                <section className="workspace__code-panel">
                    {/* Refresh notification */}
                    {refreshNotification && (
                        <div className="workspace__refresh-notification">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M12 2a10 10 0 1 0 10 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                                <path d="m9 12 2 2 4-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                            </svg>
                            {refreshNotification}
                        </div>
                    )}
                    
                    <div className="workspace__editor-section">
                        <div className="workspace__editor-header">
                            <div className="workspace__editor-title">
                                <FilePanel conversationId={parseInt(conversationId || '0')} />
                                <h3>💻 {currentFile}</h3>
                                {isRefreshing && (
                                    <div className="workspace__refresh-indicator" title="Refreshing file content...">
                                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                            <path d="M12 2a10 10 0 0110 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                                                <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite"/>
                                            </path>
                                        </svg>
                                    </div>
                                )}
                            </div>
                            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                                {/* Undo button */}
                                <button
                                    className="workspace__icon-btn"
                                    onClick={handleUndo}
                                    aria-label="Undo"
                                    title="Undo (Ctrl+Z)"
                                >
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                        <path d="M3 7v6h6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                        <path d="M21 17a9 9 0 00-9-9 9 9 0 00-9 9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                    </svg>
                                </button>

                                {/* Redo button */}
                                <button
                                    className="workspace__icon-btn"
                                    onClick={handleRedo}
                                    aria-label="Redo"
                                    title="Redo (Ctrl+Y)"
                                >
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                        <path d="M21 7v6h-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                        <path d="M3 17a9 9 0 019-9 9 9 0 019 9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                    </svg>
                                </button>

                                {/* Save button */}
                                <button
                                    className="workspace__icon-btn workspace__icon-btn--primary"
                                    onClick={handleSave}
                                    disabled={isSaving}
                                    aria-label="Save"
                                    title="Save changes (Ctrl+S)"
                                >
                                    {isSaving ? (
                                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                            <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" opacity="0.3"/>
                                            <path d="M12 2a10 10 0 0110 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                                                <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite"/>
                                            </path>
                                        </svg>
                                    ) : (
                                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                            <path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                            <path d="M17 21v-8H7v8M7 3v5h8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                        </svg>
                                    )}
                                </button>

                                {/* Run button - Always runs runner.py */}
                                <button
                                    className="workspace__icon-btn workspace__icon-btn--success"
                                    onClick={handleRun}
                                    disabled={isRunning}
                                    aria-label="Run runner.py"
                                    title="Run runner.py"
                                >
                                    {isRunning ? (
                                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                            <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" opacity="0.3"/>
                                            <path d="M12 2a10 10 0 0110 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                                                <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite"/>
                                            </path>
                                        </svg>
                                    ) : (
                                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                            <path d="M5 3l14 9-14 9V3z" fill="currentColor"/>
                                        </svg>
                                    )}
                                </button>
                            </div>
                        </div>
                        <div className="workspace__editor-wrapper">
                            <MonacoEditor
                                ref={editorRef}
                                code={currentCode}
                                onChange={(value) => {
                                    setCurrentCode(value || "");
                                    setLastUserEdit(Date.now());
                                    setIsUserEditing(true);
                                    
                                    // Clear existing timeout and set a new one
                                    if (editingTimeoutRef.current) {
                                        clearTimeout(editingTimeoutRef.current);
                                    }
                                    
                                    // Mark as not editing after 3 seconds of inactivity
                                    editingTimeoutRef.current = setTimeout(() => {
                                        setIsUserEditing(false);
                                    }, 3000);
                                }}
                                language="python"
                            />
                        </div>
                    </div>

                    <div className="workspace__output-section">
                        <div className="workspace__output-header">
                            <h3>📊 Output</h3>
                            <button
                                className="workspace__icon-btn"
                                onClick={() => setOutput("")}
                                aria-label="Clear output"
                                title="Clear output"
                            >
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                </svg>
                            </button>
                        </div>
                        <div className="workspace__output">
                            {isTurtleCode ? (
                                <div style={{
                                    width: '100%',
                                    height: '100%',
                                    display: 'flex',
                                    flexDirection: 'column',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    backgroundColor: '#1e1e1e',
                                    padding: '10px'
                                }}>
                                    <div style={{ marginBottom: '10px', color: '#d4d4d4', fontSize: '14px' }}>
                                        🐢 Turtle Graphics Stream
                                    </div>
                                    <img
                                        id="turtle-video"
                                        style={{
                                            width: '100%',
                                            height: 'calc(100% - 40px)',
                                            objectFit: 'contain',
                                            border: '1px solid #444',
                                            borderRadius: '4px',
                                            backgroundColor: '#000'
                                        }}
                                        alt="Turtle graphics stream"
                                    />
                                </div>
                            ) : (
                                <pre>{output || "Output will appear here..."}</pre>
                            )}
                        </div>
                    </div>
                </section>
            </div>
        </div>
    );
}
