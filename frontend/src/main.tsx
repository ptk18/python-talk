import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Login from "./pages/Login.tsx"; // adjust path if needed
// import Home from "./pages/Home";
import HomeReal from "./pages/HomeReal";
import Signup from "./pages/Signup";
import Profile from "./pages/Profile";
import Setting from "./pages/Setting";
import Workspace from "./pages/Workspace";
import "./index.css";

import { AuthProvider } from "./context/AuthContext";
import { ThemeProvider } from "./theme/ThemeProvider";
import { TTSProvider } from "./context/TTSContext";
import { CodeProvider } from "./context/CodeContext";
import { FileProvider } from "./context/FileContext";
import { voiceService } from "./services/voiceService";

// Initialize voiceService globally at app startup
// This ensures the voice engine preference is loaded before any page renders
voiceService.getEngine(); // Triggers singleton initialization

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <AuthProvider>
      <ThemeProvider>
        <TTSProvider>
          <CodeProvider>
            <FileProvider>
              <BrowserRouter>
                <Routes>
                  <Route path="/" element={<Login />} />
                  <Route path="/login" element={<Login />} />
                  <Route path="/signup" element={<Signup />} />
                  <Route path="/homeReal" element={<HomeReal />} />
                  <Route path="/workspace" element={<Workspace />} />
                  <Route path="/profile" element={<Profile />} />
                  <Route path="/setting" element={<Setting />} />
                </Routes>
              </BrowserRouter>
            </FileProvider>
          </CodeProvider>
        </TTSProvider>
      </ThemeProvider>
    </AuthProvider>
  </React.StrictMode>
);