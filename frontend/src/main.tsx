import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Login from "./pages/Login.tsx"; // adjust path if needed
// import Home from "./pages/Home";
import HomeReal from "./pages/HomeReal";
import Signup from "./pages/Signup";
import Chat from "./pages/Chat";
import Profile from "./pages/Profile";
import Setting from "./pages/Setting";
import Run from "./pages/Run";
import "./index.css";

import { AuthProvider } from "./context/AuthContext";
import { ThemeProvider } from "./theme/ThemeProvider";
import { TTSProvider } from "./context/TTSContext";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <AuthProvider>
      <ThemeProvider>
        <TTSProvider>
          <BrowserRouter basename="/pytalk">
            <Routes>
              <Route path="/" element={<Login />} />
              <Route path="/login" element={<Login />} />
              <Route path="/signup" element={<Signup />} />
              <Route path="/homeReal" element={<HomeReal />} />
              <Route path="/chat" element={<Chat />} />
              <Route path="/profile" element={<Profile />} />
              <Route path="/setting" element={<Setting />} />
              <Route path="/run" element={<Run />} />
            </Routes>
          </BrowserRouter>
        </TTSProvider>
      </ThemeProvider>
    </AuthProvider>
  </React.StrictMode>
);