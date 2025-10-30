import { Link, useLocation } from "react-router-dom";
import "./Navbar.css";

interface NavbarProps {
    rightButton?: {
        text: string;
        to?: string;
        onClick?: () => void;
    };
}

export default function Navbar({ rightButton }: NavbarProps) {
    const location = useLocation();

    return (
        <header className="navbar">
            <Link to="/" className="navbar__logo">PyTalk</Link>
            <nav className="navbar__links">
                <Link to="/" className={location.pathname === "/" ? "is-active" : ""}>
                    Home
                </Link>
                <Link
                    to="/setting"
                    className={location.pathname === "/setting" ? "is-active" : ""}
                >
                    Setting
                </Link>
                <Link
                    to="/profile"
                    className={location.pathname === "/profile" ? "is-active" : ""}
                >
                    Profile
                </Link>
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
    );
}

