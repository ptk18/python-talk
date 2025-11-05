import { useState } from "react";
import Navbar from "../components/Navbar";
import UploadIcon from "../assets/upload_file.svg";
import "./styles/HomeReal.css";

export default function HomeReal() {
  const [title, setTitle] = useState("");
  const [q, setQ] = useState("");

  // mock rows to render faint separators like in the design
  const rows = Array.from({ length: 6 });

  return (
    <div className="homeReal__viewport">
      {/* Top bar */}
      <Navbar rightButton={{ text: "Chat", to: "/chat" }} />

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
          <div className="homeReal__titleActions">
            <button className="homeReal__btn homeReal__btn--mobile">
              Upload File <img src={UploadIcon} alt="" />
            </button>
            <button className="homeReal__btn homeReal__btn--create homeReal__btn--mobile">Create</button>
          </div>
        </div>
        <button className="homeReal__btn homeReal__btn--desktop">
          Upload File <img src={UploadIcon} alt="" />
        </button>
        <button className="homeReal__btn homeReal__btn--create homeReal__btn--desktop">Create</button>
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
          {rows.map((_, i) => (
            <div key={i} className="homeReal__row" />
          ))}
        </div>
      </main>
    </div>
  );
}
