import { type FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./styles/Signup.css";

import api from "../services/api";

export default function Signup() {
  const [form, setForm] = useState({
    username: "",
    password: "",
    confirm: "",
    gender: "male",
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  function handleChange<K extends keyof typeof form>(key: K, val: string) {
    setForm((s) => ({ ...s, [key]: val }));
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    
    // Simple client check (optional)
    if (form.password !== form.confirm) {
      setError("Passwords do not match.");
      return;
    }

    setIsLoading(true);
    setError("");

    try {
      // Call FastAPI /api/users endpoint
      const res = await api.post("/api/users/", {
        username: form.username,
        password: form.password,
        gender: form.gender,
      });

      console.log("Signup success:", res.data);

      // Optionally save user info or redirect
      navigate("/login");
    } catch (err: any) {
      console.error("Signup error:", err);
      setError(
        err.response?.data?.detail || "Signup failed. Please try again."
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="signup__viewport">
      <div className="signup__logo">PyTalk</div>

      <div className="signup__card" role="dialog" aria-labelledby="signup-title">
        <h1 id="signup-title" className="signup__title">Sign up</h1>

        <form className="signup__form" onSubmit={onSubmit}>
          <label className="signup__field">
            <input
              type="text"
              placeholder="USERNAME"
              value={form.username}
              onChange={(e) => handleChange("username", e.target.value)}
              required
            />
          </label>

          <label className="signup__field">
            <input
              type="password"
              placeholder="PASSWORD"
              value={form.password}
              onChange={(e) => handleChange("password", e.target.value)}
              required
            />
          </label>

          <label className="signup__field">
            <input
              type="password"
              placeholder="CONFIRM PASSWORD"
              value={form.confirm}
              onChange={(e) => handleChange("confirm", e.target.value)}
              required
            />
          </label>

          {error && (
            <div className="signup__error" style={{ color: 'red', marginBottom: '1rem', fontSize: '0.9rem' }}>
              {error}
            </div>
          )}

          <button type="submit" className="signup__button" disabled={isLoading}>
            {isLoading ? "SIGNING UP..." : "SIGN UP"}
          </button>
        </form>
      </div>
    </div>
  );
}
