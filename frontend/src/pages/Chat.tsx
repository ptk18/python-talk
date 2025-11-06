import { useState, useEffect, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import Navbar from "../components/Navbar";
import "./styles/Chat.css";
import Snake from "../assets/scorpio.svg";
import User from "../assets/user.svg";
import RunIcon from "../assets/run.svg";
import ChatIcon from "../assets/chat.svg";
import UploadIcon from "../assets/upload_file.svg";
import Voice from "../assets/voice.svg";
import VoiceWhite from "../assets/voice-white.svg";
import { useTheme } from "../theme/ThemeProvider";
import { messageAPI, conversationAPI, executeAPI } from "../services/api";
import type { Message, AvailableMethodsResponse } from "../services/api";

import { analyzeAPI, voiceAPI } from "../services/api";
// import type { analyzeAPI } from "../services/api";

import { useAuth } from "../context/AuthContext";
import { API_BASE_URL } from "../config/api.ts"

export default function Chat() {
    const { theme } = useTheme();
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const conversationId = searchParams.get("conversationId");
    const [isChatActive, setIsChatActive] = useState(false);
    const [message, setMessage] = useState("");
    const [messages, setMessages] = useState<Message[]>([]);
    const voiceIcon = theme === "dark" ? VoiceWhite : Voice;
    const audioContextRef = useRef<AudioContext | null>(null);
    const [isRecording, setIsRecording] = useState(false);

    const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
    const audioChunks = useRef<BlobPart[]>([]);
    const { user } = useAuth();

    const [executionInfo, setExecutionInfo] = useState<any>(null);
    const [availableMethods, setAvailableMethods] = useState<AvailableMethodsResponse | null>(null);


    useEffect(() => {
    console.log("API_BASE", API_BASE_URL)
    console.log("import.meta.env.VITE_API_BASE_URL", import.meta.env.VITE_API_BASE_URL)
        if (conversationId) {
            // Initialize session first, then fetch data
            initializeSession();
        }
    }, [conversationId]);

    const initializeSession = async () => {
        if (!conversationId) return;
        try {
            // Ensure session is initialized before fetching other data
            await executeAPI.ensureSessionInitialized(parseInt(conversationId));
            // Now fetch messages and methods
            await fetchMessages();
            await fetchAvailableMethods();
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

    const handleChatToggle = () => {
        setIsChatActive(!isChatActive);
    };

    const handleSend = async (e: React.FormEvent) => {
  e.preventDefault();
  if (!message.trim() || !conversationId) return;

  const msgText = message.trim();
  setMessage("");

  try {
    // Save user message
    await messageAPI.create(parseInt(conversationId), "user", msgText);
    await fetchMessages();

    setTimeout(() => {
      window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
    }, 100);

    // Analyze command
    const data = await analyzeAPI.analyzeCommand(Number(conversationId), msgText);
    const r = data.result || {};
    console.log("Analyze result:", data);

    // Create system reply summary - show executable(s)
    let summary;
    if (r.executable) {
      // Simple command
      summary = r.executable;
    } else if (r.executables && r.executables.length > 0) {
      // Complex command with multiple executables
      summary = r.executables.join('\n');
    } else if (r.code) {
      // Complex command with formatted code
      summary = r.code;
    } else {
      summary = "No executable command generated";
    }

    // Save system reply message
    await messageAPI.create(parseInt(conversationId), "system", summary);
    await fetchMessages();

    setTimeout(() => {
      window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
    }, 100);

    // Update execution info
    const executable = r.executable || (r.executables && r.executables.length > 0 ? r.executables.join('\n') : null);
    setExecutionInfo({
      executable: executable,
      file_name: data.file_name,
    });

    // Ask user to append command
    if (executable) {
      const confirmed = window.confirm(
        `Do you want to append the command(s) to the runner file?\n\n${executable}`
      );

      if (confirmed) {
        const appendData = await executeAPI.appendCommand(
          Number(conversationId),
          executable
        );
        console.log("Append result:", appendData);

        await messageAPI.create(
          parseInt(conversationId),
          "system",
          `Command(s) appended successfully.`
        );

        await fetchMessages();
        setTimeout(() => {
          window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
        }, 100);
      }
    }
  } catch (err: any) {
    console.error("Failed to send or analyze message:", err);
    alert("Error: " + err.message);
  }
};


const gotoRun = () => {
  if (!executionInfo) {
    navigate("/run", {
      state: {
        conversationId,
        executable: null,
        file_name: null, // safe default
      },
    });
    return; // prevent running the next navigate
  }

  navigate("/run", {
    state: {
      conversationId,
      executable: executionInfo.executable,
      file_name: executionInfo.file_name,
    },
  });
};

    const handleRun = () => {
    if (!executionInfo.executable || !executionInfo.file_name || !conversationId) {
      console.error("Missing required data for navigation");
      alert("No executable command found.");
      return;
    }

    navigate("/run", {
      state: {
        conversationId,
        executable: executionInfo.executable,
        file_name: executionInfo.file_name,
      },
    });
  };

  const playClickSound = () => {
        try {
            // Create audio context if it doesn't exist
            if (!audioContextRef.current) {
                audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
            }
            const audioContext = audioContextRef.current;

            // Create a simple beep sound (800Hz for 100ms)
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
    // --- Start Recording ---
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      audioChunks.current = [];

      recorder.ondataavailable = (e) => {
        audioChunks.current.push(e.data);
      };

      recorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks.current, { type: "audio/webm" });

        try {
          // Use your unified voiceAPI function
          const result = await voiceAPI.transcribe(audioBlob as File, "en");

          const text = result.text || `[Error: ${result.error || "Unknown"}]`;
          console.log("Transcribed text:", text);

          // Instead of appendMessage or sendTypedMessage,
          // just set the transcribed text into the chat input box
          setMessage(text);

          // Optionally open the chat input if it's closed
          if (!isChatActive) setIsChatActive(true);

          // The user can now see and edit the transcribed text
          // then press Send (handleSend) to process it as usual.
        } catch (err: any) {
          console.error("Voice transcription error:", err);
          alert("Error transcribing voice: " + err.message);
        }
      };

      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
      console.log("🎙️ Recording started...");
    } catch (err) {
      console.error("Microphone access denied:", err);
      alert("Microphone access denied or unavailable.");
    }
  } else {
    // --- Stop Recording ---
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
      mediaRecorder.stop();
      console.log("Recording stopped.");
    }
    setIsRecording(false);
  }
};




    return (
        <div className="chat__viewport">
            {/* Top bar */}
            <Navbar />

            {/* Chat panel with sidebar */}
            <div className="chat__container">
                {/* Left sidebar - Available Methods */}
                {availableMethods && (
                    <aside className="chat__sidebar">
                        <h3 className="chat__sidebar-title">
                            {availableMethods.file_name || "Available Methods"}
                        </h3>
                        <div className="chat__sidebar-content">
                            {Object.entries(availableMethods.classes).map(([className, classInfo]) => (
                                <div key={className} className="chat__methods-list">
                                    {classInfo.methods.map((method) => {
                                        const params = method.required_parameters.length > 0
                                            ? method.required_parameters.join(", ")
                                            : "";
                                        const signature = `${method.name}(${params})`;

                                        return (
                                            <div key={method.name} className="chat__method-item">
                                                <div className="chat__method-name">{signature}</div>
                                            </div>
                                        );
                                    })}
                                </div>
                            ))}
                        </div>
                    </aside>
                )}

                {/* Chat panel */}
                <main className="chat__panel">
                    {/* Scroll area with messages */}
                    <section className="chat__scroll">
                    {messages.map((msg) => {
                        const isUser = msg.sender === "user";
                        const time = new Date(msg.timestamp).toLocaleTimeString('en-US', {
                            hour: '2-digit',
                            minute: '2-digit',
                            hour12: false
                        });

                        return (
                            <div key={msg.id} className={`chat__row ${isUser ? 'chat__row--right' : 'chat__row--left'}`}>
                                {!isUser && (
                                    <div className="chat__avatar-container">
                                        <img src={Snake} alt="Scorpio" className="chat__avatar" />
                                        <div className="chat__name chat__name--left">Scorpio</div>
                                    </div>
                                )}
                                {isUser && <span className="chat__time chat__time--left">{time}</span>}
                                <div className="chat__bubble">
                                    {msg.content.includes('```') ? (
                                        <div className="chat__code">
                                            <button
                                                className="chat__copy-btn"
                                                aria-label="Copy code"
                                                onClick={() => navigator.clipboard.writeText(msg.content.replace(/```[\s\S]*?\n|```/g, ''))}
                                            >
                                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                                    <rect x="9" y="9" width="11" height="11" rx="2" stroke="currentColor" strokeWidth="2" />
                                                    <rect x="4" y="4" width="11" height="11" rx="2" stroke="currentColor" strokeWidth="2" opacity="0.6" />
                                                </svg>
                                            </button>
                                            <pre>
                                                <code>{msg.content.replace(/```[\s\S]*?\n|```/g, '')}</code>
                                            </pre>
                                        </div>
                                    ) : (
                                        msg.content
                                    )}
                                </div>
                                {isUser && (
                                    <div className="chat__avatar-container">
                                        <img src={User} alt="User" className="chat__avatar" />
                                        <div className="chat__name chat__name--right">{user?.username || "User"}</div>
                                    </div>
                                )}
                                {!isUser && <span className="chat__time">{time}</span>}
                            </div>
                        );
                    })}
                </section>
            </main>
            </div>

            {/* Footer actions */}
            <footer className="chat__footer">
                <div className="chat__actions">
                    <button className="btn btn--run" onClick={gotoRun}>
      Confirm
    </button>

                    <button
                        className={`btn ${isChatActive ? "btn--active" : ""}`}
                        onClick={handleChatToggle}
                    >
                        Chat <img src={ChatIcon} alt="" />
                    </button>
                    <button className="btn btn--upload">
                        Upload File <img src={UploadIcon} alt="" />
                    </button>
                </div>
            </footer>

            {/* Chat input container (shown when chat is active) */}
            {isChatActive && (
                <div className="chat__input-container">
                    <img
                        src={voiceIcon}
                        alt="Start voice input"
                        className="chat__mic chat__mic--small"
                    />
                    <form className="chat__input-form" onSubmit={handleSend}>
                        <input
                            type="text"
                            className="chat__input"
                            placeholder="Type your message..."
                            value={message}
                            onChange={(e) => setMessage(e.target.value)}
                            autoFocus
                        />
                        <button
                            type="submit"
                            className="chat__send-btn"
                        >
                            Send
                        </button>
                    </form>
                </div>
            )}

            {/* Floating voice button (shown when chat is inactive) */}
            {!isChatActive && (
                <div className={`chat__mic-wrapper ${isRecording ? "chat__mic-wrapper--recording" : ""}`}>
                    <img
                        src={voiceIcon}
                        alt="Start voice input"
                        className="chat__mic"
                        onClick={handleMicClick}
                    />
                    {isRecording && <div className="chat__mic-pulse"></div>}
                </div>
            )}
        </div>
    );
}
