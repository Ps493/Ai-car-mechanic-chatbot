"use client";
import { useRef } from "react";

const ACCEPT = {
  image: "image/*",
  audio: "audio/*",
  video: "video/*",
};

export default function MediaUploader({ onUpload, disabled }) {
  const inputRefs = { image: useRef(), audio: useRef(), video: useRef() };

  const trigger = (type) => inputRefs[type].current?.click();

  const handleChange = (type) => (e) => {
    const file = e.target.files?.[0];
    if (file) onUpload(file, type);
    e.target.value = "";
  };

  const btnStyle = {
    background: "transparent",
    border: "1px solid var(--border)",
    color: "var(--text-muted)",
    borderRadius: 8,
    width: 34,
    height: 34,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: 15,
    opacity: disabled ? 0.4 : 1,
  };

  return (
    <div style={{ display: "flex", gap: 6 }}>
      {["image", "audio", "video"].map((type) => (
        <div key={type}>
          <input
            ref={inputRefs[type]}
            type="file"
            accept={ACCEPT[type]}
            style={{ display: "none" }}
            onChange={handleChange(type)}
            disabled={disabled}
          />
          <button
            type="button"
            title={`Attach ${type}`}
            style={btnStyle}
            disabled={disabled}
            onClick={() => trigger(type)}
          >
            {type === "image" ? "📷" : type === "audio" ? "🎤" : "🎥"}
          </button>
        </div>
      ))}
    </div>
  );
}
