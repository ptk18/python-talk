import { type FormEvent, useState } from "react";
import "./styles/Signup.css";

export default function Signup() {
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    confirm: "",
  });

  function handleChange<K extends keyof typeof form>(key: K, val: string) {
    setForm((s) => ({ ...s, [key]: val }));
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    // Simple client check (optional)
    if (form.password !== form.confirm) {
      alert("Passwords do not match.");
      return;
    }
    // TODO: call your API here
    console.log("signup:", form);
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
              type="email"
              placeholder="EMAIL ADDRESS"
              value={form.email}
              onChange={(e) => handleChange("email", e.target.value)}
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

          <button type="submit" className="signup__button">SIGN UP</button>
        </form>
      </div>
    </div>
  );
}
