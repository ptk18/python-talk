import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "../components/Navbar.tsx";
import UploadIcon from "../assets/upload_file.svg";
import "./styles/HomeReal.css";
import { conversationAPI } from "../services/api.ts";
import type { Conversation } from "../services/api.ts";
import { useAuth } from "../context/AuthContext.tsx";

import { API_BASE_URL } from "../config/api.ts"
import { speak, getGreeting } from "../utils/tts.ts";

export default function HomeReal() {
    const navigate = useNavigate();
    const { user } = useAuth();
    const [title, setTitle] = useState("");
    const [q, setQ] = useState("");
    const [conversations, setConversations] = useState<Conversation[]>([]);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const hasGreeted = useRef(false);

    useEffect(() => {
        console.log("API_BASE", API_BASE_URL);
        console.log("import.meta.env.VITE_API_BASE_URL", import.meta.env.VITE_API_BASE_URL);
        console.log("Current user:", user);

        if (user) {
            fetchConversations();
        } else {
            console.warn("No user found, skipping fetch.");
        }
    }, [user]);

    // Greet user on first interaction (required by browsers)
    useEffect(() => {
        const greetOnInteraction = () => {
            if (!hasGreeted.current && user) {
                hasGreeted.current = true;
                const greeting = getGreeting();
                speak(greeting);
                // Remove listeners after first greeting
                document.removeEventListener('click', greetOnInteraction);
                document.removeEventListener('keydown', greetOnInteraction);
            }
        };

        document.addEventListener('click', greetOnInteraction);
        document.addEventListener('keydown', greetOnInteraction);

        return () => {
            document.removeEventListener('click', greetOnInteraction);
            document.removeEventListener('keydown', greetOnInteraction);
        };
    }, [user]);

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
            speak("Please enter a title and select a Python file");
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
            speak("Conversation created successfully");
            fetchConversations();
        } catch (err) {
            console.error("Failed to create conversation:", err);
            speak("Failed to create conversation");
            alert("Failed to create conversation.");
        }
    };

    const handleConversationClick = (convId: number) => {
        navigate(`/workspace?conversationId=${convId}`);
    };

    const handleDeleteConversation = async (convId: number) => {
        if (!window.confirm("Are you sure you want to delete this conversation?")) {
            speak("Deletion cancelled");
            return;
        }
        try {
            await conversationAPI.delete(convId);
            speak("Conversation deleted successfully");
            fetchConversations();
        } catch (err) {
            console.error("Failed to delete conversation:", err);
            speak("Failed to delete conversation");
            alert("Failed to delete conversation.");
        }
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
                    {selectedFile ? selectedFile.name : "Upload File"} <img src={UploadIcon} alt="" />
                </button>
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
                        >
                            <div className="homeReal__row-content" onClick={() => handleConversationClick(conv.id)}>
                                <strong>{conv.title}</strong><br />
                                <small>File: {conv.file_name || 'N/A'}</small>
                            </div>
                            <div className="homeReal__row-actions">
                                <button
                                    className="homeReal__icon-btn"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        handleConversationClick(conv.id);
                                    }}
                                    title="Open File"
                                    aria-label="Open File"
                                >
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                        <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9l-7-7z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                        <path d="M13 2v7h7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                        <path d="M10 13l-3 3 3 3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                        <path d="M17 16H7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                    </svg>
                                </button>
                                <button
                                    className="homeReal__icon-btn homeReal__icon-btn--delete"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        handleDeleteConversation(conv.id);
                                    }}
                                    title="Delete Conversation"
                                    aria-label="Delete Conversation"
                                >
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                        <path d="M3 6h18" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                                        <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                                        <path d="M10 11v6" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                                        <path d="M14 11v6" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                                    </svg>
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </main>
        </div>
    );
}
