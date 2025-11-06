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
}

export default function Navbar({ rightButton }: NavbarProps) {
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
                    <button
                        className="navbar__tts-toggle"
                        onClick={toggleTTS}
                        title={ttsEnabled ? "Disable Voice" : "Enable Voice"}
                    >
                        {ttsEnabled ? "🔊" : "🔇"}
                    </button>
                </nav>
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
                            >
                                {rightButton.text}
                            </button>
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
                    <button
                        className="navbar__tts-toggle"
                        onClick={toggleTTS}
                        title={ttsEnabled ? "Disable Voice" : "Enable Voice"}
                    >
                        {ttsEnabled ? "🔊 Voice On" : "🔇 Voice Off"}
                    </button>
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

