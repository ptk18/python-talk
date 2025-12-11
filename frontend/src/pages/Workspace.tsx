import { useState, useEffect, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import Navbar from "../components/Navbar";
import MonacoEditor from "../components/MonacoEditor";
import type { MonacoEditorRef } from "../components/MonacoEditor";
import "./styles/Workspace.css";
import Snake from "../assets/scorpio.svg";
import User from "../assets/user.svg";
import ChatIcon from "../assets/chat.svg";
import Voice from "../assets/voice.svg";
import VoiceWhite from "../assets/voice-white.svg";
import { useTheme } from "../theme/ThemeProvider";
import { messageAPI, conversationAPI, executeAPI, analyzeAPI, voiceAPI } from "../services/api";
import type { Message, AvailableMethodsResponse } from "../services/api";
import { useAuth } from "../context/AuthContext";
import { useCode } from "../context/CodeContext";
import { speak } from "../utils/tts";

export default function Workspace() {
    const { theme } = useTheme();
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const conversationId = searchParams.get("conversationId");
    const { user } = useAuth();
    const { code, setCode, syncCodeFromBackend, setConversationId } = useCode();

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

    useEffect(() => {
        if (conversationId) {
            setConversationId(parseInt(conversationId));
            initializeSession();
        }
    }, [conversationId, setConversationId]);

    const initializeSession = async () => {
        if (!conversationId) return;
        try {
            await executeAPI.ensureSessionInitialized(parseInt(conversationId));
            await fetchMessages();
            await fetchAvailableMethods();
            await syncCodeFromBackend();
        } catch (err) {
            console.error("Failed to initialize session:", err);
        }
    };

    const fetchMessages = async () => {
        if (!conversationId) return;
        try {
            const msgs = await messageAPI.getByConversation(parseInt(conversationId));
            setMessages(msgs);
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
            await messageAPI.create(parseInt(conversationId), "user", msgText);
            await fetchMessages();

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
            await fetchMessages();

            const executable = r.executable || (r.executables && r.executables.length > 0 ? r.executables.join('\n') : null);

            if (executable) {
                speak("Your command has been successfully processed");

                const confirmed = window.confirm(
                    `Do you want to append the command(s) to the runner file?\n\n${executable}`
                );

                if (confirmed) {
                    speak("Appending to file");
                    await executeAPI.appendCommand(Number(conversationId), executable);
                    await syncCodeFromBackend();
                    await messageAPI.create(parseInt(conversationId), "system", `Command(s) appended successfully.`);
                    speak("Command appended successfully");
                    await fetchMessages();
                }
            } else {
                speak("I couldn't process that command. Could you please try again?");
            }
        } catch (err: any) {
            console.error("Failed to send or analyze message:", err);
            speak("I encountered an error. Please try again");
            alert("Error: " + err.message);
        }
    };

    const handleSave = async () => {
        if (!conversationId) {
            console.error("No conversation ID");
            return;
        }

        setIsSaving(true);
        try {
            const API_BASE = import.meta.env.VITE_API_BASE_URL || "";
            const res = await fetch(`${API_BASE}/api/save_runner_code`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                body: JSON.stringify({
                    conversation_id: conversationId,
                    code: code
                })
            });

            if (!res.ok) {
                throw new Error(`Failed to save: ${res.status}`);
            }

            speak("Code saved successfully");
            console.log("Code saved successfully");
        } catch (err) {
            console.error("Failed to save code:", err);
            speak("Failed to save code");
        } finally {
            setIsSaving(false);
        }
    };

    const handleUndo = () => {
        editorRef.current?.undo();
    };

    const handleRedo = () => {
        editorRef.current?.redo();
    };

    const handleRun = async () => {
        if (!code.trim()) {
            setOutput("Error: Code editor is empty. Please enter some Python code.\n");
            speak("Code editor is empty. Please enter some Python code");
            return;
        }

        if (isTurtleCode === null) {
            setShowTurtlePrompt(true);
            speak("Is this turtle code?");
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
            speak("Your output is ready, Sir");
        } catch (err) {
            console.error("Failed to execute command:", err);
            setOutput("Error executing command.\n");
            speak("Please try again");
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
            speak("Your turtle graphics are running, Sir");
        } catch (err) {
            console.error("Failed to execute turtle graphics:", err);
            setOutput("Error executing turtle graphics.\n");
            speak("Please try again");
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


    const handleMicClick = async () => {
        playClickSound();

        if (!isRecording) {
            try {
                speak("Listening");
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                const recorder = new MediaRecorder(stream);
                audioChunks.current = [];

                recorder.ondataavailable = (e) => {
                    audioChunks.current.push(e.data);
                };

                recorder.onstop = async () => {
                    const audioBlob = new Blob(audioChunks.current, { type: "audio/webm" });

                    try {
                        speak("Processing your voice");
                        const result = await voiceAPI.transcribe(audioBlob as File, "en");
                        const text = result.text || `[Error: ${result.error || "Unknown"}]`;

                        if (text.includes("[Error")) {
                            speak("I couldn't understand that. Please try again");
                        } else {
                            speak("Voice command received");
                        }

                        setMessage(text);
                        if (!isChatActive) setIsChatActive(true);
                    } catch (err: any) {
                        console.error("Voice transcription error:", err);
                        speak("Voice transcription error");
                        alert("Error transcribing voice: " + err.message);
                    }
                };

                recorder.start();
                setMediaRecorder(recorder);
                setIsRecording(true);
            } catch (err) {
                console.error("Microphone access denied:", err);
                speak("Microphone access denied");
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

                            return (
                                <div key={msg.id} className={`workspace__chat-row ${isUser ? 'workspace__chat-row--right' : 'workspace__chat-row--left'}`}>
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
                            );
                        })}
                    </section>

                    {/* Chat Input */}
                    <footer className="workspace__chat-footer">
                        <div className="workspace__chat-input-container">
                            <div className="workspace__mic-wrapper">
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
                            </div>

                            <form className="workspace__input-form" onSubmit={handleSend}>
                                <input
                                    type="text"
                                    className="workspace__input"
                                    placeholder="Type your message..."
                                    value={message}
                                    onChange={(e) => setMessage(e.target.value)}
                                />
                                <button type="submit" className="workspace__send-btn">
                                    Send
                                </button>
                            </form>
                        </div>
                    </footer>
                </main>

                {/* Right - Code & Output Panel */}
                <section className="workspace__code-panel">
                    <div className="workspace__editor-section">
                        <div className="workspace__editor-header">
                            <h3>💻 Code Editor</h3>
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

                                {/* Run button */}
                                <button
                                    className="workspace__icon-btn workspace__icon-btn--success"
                                    onClick={handleRun}
                                    disabled={isRunning}
                                    aria-label="Run code"
                                    title="Run code"
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
                                code={code}
                                onChange={(value) => setCode(value || "")}
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
