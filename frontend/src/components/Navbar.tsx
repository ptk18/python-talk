import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import "./Navbar.css";
import { useTTS } from "../context/TTSContext";

interface NavbarProps {
    rightButton?: {
        text: string;
        to?: string;
        onClick?: () => void;
    };
    showTTSToggle?: boolean;
}

const SpeakerIcon = ({ muted }: { muted: boolean }) => (
    <svg
        width="22"
        height="22"
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        role="presentation"
        aria-hidden="true"
    >
        <path
            d="M11 5 6.2 9H3v6h3.2L11 19V5Z"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
        />
        {muted ? (
            <>
                <line
                    x1="18"
                    y1="8"
                    x2="22"
                    y2="12"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                />
                <line
                    x1="22"
                    y1="8"
                    x2="18"
                    y2="12"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                />
            </>
        ) : (
            <>
                <path
                    d="M15.5 9.5a2.5 2.5 0 0 1 0 5"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                />
                <path
                    d="M18.5 7a5 5 0 0 1 0 10"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                />
            </>
        )}
    </svg>
);

export default function Navbar({ rightButton, showTTSToggle = false }: NavbarProps) {
    const location = useLocation();
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const { ttsEnabled, toggleTTS } = useTTS();

    const toggleSidebar = () => {
        setIsSidebarOpen(!isSidebarOpen);
    };

    const closeSidebar = () => {
        setIsSidebarOpen(false);
    };

    return (
        <>
            <header className={`navbar ${isSidebarOpen ? "navbar--sidebar-open" : ""}`}>
                {/* Hamburger menu button for mobile */}
                <button
                    className="navbar__menu-btn"
                    onClick={toggleSidebar}
                    aria-label="Toggle menu"
                    type="button"
                >
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M3 12h18M3 6h18M3 18h18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                    </svg>
                </button>

                <Link to="/" className="navbar__logo">PyTalk</Link>
                <nav className="navbar__links">
                    <Link
                        to="/homeReal"
                        className={location.pathname === "/homeReal" ? "is-active" : ""}
                        onClick={closeSidebar}
                    >
                        Home
                    </Link>
                    <Link
                        to="/setting"
                        className={location.pathname === "/setting" ? "is-active" : ""}
                        onClick={closeSidebar}
                    >
                        Setting
                    </Link>
                    <Link
                        to="/profile"
                        className={location.pathname === "/profile" ? "is-active" : ""}
                        onClick={closeSidebar}
                    >
                        Profile
                    </Link>
                </nav>
                {(showTTSToggle || rightButton) && (
                    <div className="navbar__actions">
                        {showTTSToggle && (
                            <button
                                className={`navbar__tts-toggle ${ttsEnabled ? "is-active" : ""}`}
                                onClick={toggleTTS}
                                title={ttsEnabled ? "Disable Voice" : "Enable Voice"}
                                aria-label={ttsEnabled ? "Disable text to speech" : "Enable text to speech"}
                                aria-pressed={ttsEnabled}
                                type="button"
                            >
                                <SpeakerIcon muted={!ttsEnabled} />
                            </button>
                        )}
                        {rightButton && (
                            <div className="navbar__button">
                                {rightButton.to ? (
                                    <Link to={rightButton.to} className="navbar__button-link">
                                        {rightButton.text}
                                    </Link>
                                ) : (
                                    <button
                                        className="navbar__button-btn"
                                        onClick={rightButton.onClick}
                                        type="button"
                                    >
                                        {rightButton.text}
                                    </button>
                                )}
                            </div>
                        )}
                    </div>
                )}
            </header>

            {/* Sidebar overlay */}
            {isSidebarOpen && (
                <div className="navbar__overlay" onClick={closeSidebar}></div>
            )}

            {/* Slide-out sidebar */}
            <aside className={`navbar__sidebar ${isSidebarOpen ? "navbar__sidebar--open" : ""}`}>
                <div className="navbar__sidebar-header">
                    <Link to="/" className="navbar__sidebar-logo" onClick={closeSidebar}>PyTalk</Link>
                    {/* <button
                        className="navbar__sidebar-close"
                        onClick={closeSidebar}
                        aria-label="Close menu"
                    >
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                        </svg>
                    </button> */}
                </div>
                <nav className="navbar__sidebar-links">
                    <Link
                        to="/homeReal"
                        className={location.pathname === "/homeReal" ? "is-active" : ""}
                        onClick={closeSidebar}
                    >
                        Home
                    </Link>
                    <Link
                        to="/setting"
                        className={location.pathname === "/setting" ? "is-active" : ""}
                        onClick={closeSidebar}
                    >
                        Setting
                    </Link>
                    <Link
                        to="/profile"
                        className={location.pathname === "/profile" ? "is-active" : ""}
                        onClick={closeSidebar}
                    >
                        Profile
                    </Link>
                    {showTTSToggle && (
                        <button
                            className={`navbar__tts-toggle navbar__tts-toggle--sidebar ${ttsEnabled ? "is-active" : ""}`}
                            onClick={toggleTTS}
                            title={ttsEnabled ? "Disable Voice" : "Enable Voice"}
                            aria-label={ttsEnabled ? "Disable text to speech" : "Enable text to speech"}
                            aria-pressed={ttsEnabled}
                            type="button"
                        >
                            <SpeakerIcon muted={!ttsEnabled} />
                            <span>{ttsEnabled ? "Voice On" : "Voice Off"}</span>
                        </button>
                    )}
                </nav>
                {rightButton && (
                    <div className="navbar__sidebar-button">
                        {rightButton.to ? (
                            <Link to={rightButton.to} className="navbar__button-link" onClick={closeSidebar}>
                                {rightButton.text}
                            </Link>
                        ) : (
                            <button
                                className="navbar__button-btn"
                                onClick={() => {
                                    if (rightButton.onClick) rightButton.onClick();
                                    closeSidebar();
                                }}
                                type="button"
                            >
                                {rightButton.text}
                            </button>
                        )}
                    </div>
                )}
            </aside>
        </>
    );
}

