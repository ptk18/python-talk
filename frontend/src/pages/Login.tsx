import React, { type FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./styles/Login.css";

import api from "../services/api";
// import { API_BASE_URL } from "../config/api";
import { useAuth } from "../context/AuthContext";

export default function Login() {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState("");
    const navigate = useNavigate();

    const { login } = useAuth();

    async function onSubmit(e: FormEvent) {
        e.preventDefault();
        setIsLoading(true);
        setError("");

        try {
            const res = await api.post("/api/users/login", {
                username,
                password,
            });

            console.log("Login success:", res.data);

            // const userId = res.data.id;

            // const userRes = await api.get(`${API_BASE_URL}/users/${userId}`);
            // const userData = userRes.data;

            // Optionally store user info in localStorage or context
            // localStorage.setItem("user", JSON.stringify(userData));
            login(res.data);

            navigate("/homeReal");
        } catch (err: any) {
            console.error("Login error:", err);
            setError(
                err.response?.data?.detail ||
                "Login failed. Please check your credentials."
            );
        } finally {
            setIsLoading(false);
        }
    }

    return (
        <div className="login__viewport">
            {/* Logo (top-left) */}
            <div className="login__logo">PyTalk</div>

            {/* Center Card */}
            <div className="login__card" role="dialog" aria-labelledby="login-title">
                <h1 id="login-title" className="login__title">Log in</h1>

                <form className="login__form" onSubmit={onSubmit}>
                    <label className="login__field">
                        <input
                            type="text"
                            placeholder="USERNAME"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            aria-label="Username"
                            required
                        />
                    </label>

                    <label className="login__field">
                        <input
                            type="password"
                            placeholder="PASSWORD"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            aria-label="Password"
                            required
                        />
                    </label>

                    {error && (
                        <div className="login__error" style={{ color: 'red', marginBottom: '1rem', fontSize: '0.9rem' }}>
                            {error}
                        </div>
                    )}

                    <p className="login__meta">
                        Don't have an account?{" "}
                        <a className="login__link" href="/signup">Sign up</a>
                    </p>

                    <button type="submit" className="login__button" disabled={isLoading}>
                        {isLoading ? "LOGGING IN..." : "LOG IN"}
                    </button>
                </form>
            </div>
        </div>
    );
}