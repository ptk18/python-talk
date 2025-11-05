import { type FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./styles/Login.css";

export default function Login() {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const navigate = useNavigate();

    function onSubmit(e: FormEvent) {
        e.preventDefault();
        // TODO: replace with your auth call
        console.log({ username, password });
        navigate("/homeReal");
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
                        // required
                        />
                    </label>

                    <label className="login__field">
                        <input
                            type="password"
                            placeholder="PASSWORD"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            aria-label="Password"
                        // required
                        />
                    </label>

                    <p className="login__meta">
                        Don’t have an account?{" "}
                        <a className="login__link" href="/signup">Sign up</a>
                    </p>

                    <button type="submit" className="login__button">LOG IN</button>
                </form>
            </div>
        </div>
    );
}
