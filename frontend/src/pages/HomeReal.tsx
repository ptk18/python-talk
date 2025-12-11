import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "../components/Navbar";
import UploadIcon from "../assets/upload_file.svg";
import "./styles/HomeReal.css";
import { conversationAPI } from "../services/api";
import type { Conversation } from "../services/api";
import { useAuth } from "../context/AuthContext";

import { API_BASE_URL } from "../config/api.ts"
import { speak, getGreeting } from "../utils/tts";

export default function HomeReal() {
    const navigate = useNavigate();
    const { user } = useAuth();
    const [title, setTitle] = useState("");
    const [q, setQ] = useState("");
    const [conversations, setConversations] = useState<Conversation[]>([]);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [hasGreeted, setHasGreeted] = useState(false);

    useEffect(() => {
        console.log("API_BASE", API_BASE_URL)

    console.log("import.meta.env.VITE_API_BASE_URL", import.meta.env.VITE_API_BASE_URL)
  console.log("Current user:", user);
  if (user) {
    fetchConversations();
  } else {
    console.warn("No user found, skipping fetch.");
  }
}, [user]);

    useEffect(() => {
        if (!hasGreeted) {
            const greeting = getGreeting();
            speak(greeting);
            setHasGreeted(true);
        }
    }, [hasGreeted]);

    const fetchConversations = async () => {
        if (!user) return;
        try {
            const convs = await conversationAPI.getByUser(user.id);
            console.log("Fetched conversations:", convs);
            setConversations(convs);
        } catch (err) {
            console.error("Failed to fetch conversations:", err);
            alert("Failed to fetch conversations.");
        }
    };

    const handleFileSelect = () => {
        fileInputRef.current?.click();
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            setSelectedFile(file);
        }
    };

    const handleCreate = async () => {
        if (!title.trim() || !selectedFile || !user) {
            alert("Please enter a title and select a Python file.");
            return;
        }

        try {
            const code = await selectedFile.text();
            await conversationAPI.create(user.id, {
                title,
                user_id: user.id,
                file_name: selectedFile.name,
                code,
            });
            setTitle("");
            setSelectedFile(null);
            if (fileInputRef.current) {
                fileInputRef.current.value = "";
            }
            fetchConversations();
        } catch (err) {
            console.error("Failed to create conversation:", err);
            alert("Failed to create conversation.");
        }
    };

    const handleConversationClick = (convId: number) => {
        navigate(`/workspace?conversationId=${convId}`);
    };

    const filteredConversations = conversations.filter(conv =>
        conv.title.toLowerCase().includes(q.toLowerCase()) ||
        conv.file_name?.toLowerCase().includes(q.toLowerCase())
    );

    return (
        <div className="homeReal__viewport">
            {/* Top bar */}
            <Navbar />

            {/* Title + actions */}
            <div className="homeReal__headerRow">
                <div className="homeReal__titleWrapper">
                    <span className="homeReal__titleLabel">Title: </span>
                    <input
                        className="homeReal__titleInput"
                        placeholder=""
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                    />
                </div>
                <input
                    ref={fileInputRef}
                    type="file"
                    accept=".py"
                    style={{ display: "none" }}
                    onChange={handleFileChange}
                />
                <button className="homeReal__btn" onClick={handleFileSelect}>
                    Upload File <img src={UploadIcon} alt="" />
                </button>
                {selectedFile && <span style={{ fontSize: "12px", marginLeft: "8px" }}>{selectedFile.name}</span>}
                <button className="homeReal__btn homeReal__btn--create" onClick={handleCreate}>Create</button>
            </div>

            {/* Big white panel with search + rows */}
            <main className="homeReal__panel">
                <div className="homeReal__searchWrap">
                    <input
                        className="homeReal__search"
                        placeholder="Search..."
                        value={q}
                        onChange={(e) => setQ(e.target.value)}
                    />
                    <button className="homeReal__searchIcon" type="button" aria-label="Search">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="2" />
                            <path d="m20 20-4-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                        </svg>
                    </button>
                </div>

                <div className="homeReal__list">
                    {filteredConversations.map((conv) => (
                        <div
                            key={conv.id}
                            className="homeReal__row"
                            style={{ cursor: "pointer", padding: "12px", display: "flex", justifyContent: "space-between", alignItems: "center" }}
                        >
                            <div onClick={() => handleConversationClick(conv.id)}>
                                <strong>{conv.title}</strong><br />
                                <small>File: {conv.file_name || 'N/A'}</small>
                            </div>
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    handleConversationClick(conv.id, true);
                                }}
                                style={{
                                    padding: "6px 12px",
                                    background: "#007bff",
                                    color: "white",
                                    border: "none",
                                    borderRadius: "4px",
                                    cursor: "pointer",
                                    fontSize: "12px"
                                }}
                            >
                                Open Workspace
                            </button>
                        </div>
                    ))}
                </div>
            </main>
        </div>
    );
}
