import { useState, useEffect, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import Navbar from "../components/Navbar";
import MonacoEditor from "../components/MonacoEditor";
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
        // Implement turtle graphics execution similar to Run.tsx
        // For now, just a placeholder
        setOutput("Turtle graphics execution not yet implemented in workspace.\n");
        setIsRunning(false);
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
                                <div className={`workspace__mic-inner ${isRecording ? "workspace__mic-inner--recording" : ""}`}>
                                    <img
                                        src={voiceIcon}
                                        alt="Start voice input"
                                        className="workspace__mic"
                                        onClick={handleMicClick}
                                    />
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
                            <button
                                className="workspace__run-btn"
                                onClick={handleRun}
                                disabled={isRunning}
                            >
                                {isRunning ? "Running..." : "Run Code"}
                            </button>
                        </div>
                        <div className="workspace__editor-wrapper">
                            <MonacoEditor
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
                                className="workspace__clear-btn"
                                onClick={() => setOutput("")}
                            >
                                Clear
                            </button>
                        </div>
                        <div className="workspace__output">
                            <pre>{output || "Output will appear here..."}</pre>
                        </div>
                    </div>
                </section>
            </div>
        </div>
    );
}
