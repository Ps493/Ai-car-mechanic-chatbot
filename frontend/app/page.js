"use client";
import { useState, useRef, useEffect } from "react";
import { api } from "../lib/api";
import MessageBubble from "../components/MessageBubble";
import MediaUploader from "../components/MediaUploader";
import DiagnosisCard from "../components/DiagnosisCard";
import BookingModal from "../components/BookingModal";

const WELCOME = {
  sender: "bot",
  message_type: "text",
  text: "Welcome to Instant Mechanic. I'm your virtual senior technician — describe the issue you're having with your vehicle and I'll walk you through diagnosing it.",
};

export default function Page() {
  const [conversationId, setConversationId] = useState(null);
  const [messages, setMessages] = useState([WELCOME]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [readyForDiagnosis, setReadyForDiagnosis] = useState(false);
  const [diagnosis, setDiagnosis] = useState(null);
  const [diagnosing, setDiagnosing] = useState(false);
  const [showBooking, setShowBooking] = useState(false);
  const [bookingSubmitting, setBookingSubmitting] = useState(false);
  const [bookingError, setBookingError] = useState("");
  const [booking, setBooking] = useState(null);

  const scrollRef = useRef(null);
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, diagnosis]);

  const pushMessage = (msg) => setMessages((prev) => [...prev, msg]);

  const send = async (text) => {
    if (!text.trim() || sending) return;
    pushMessage({ sender: "user", message_type: "text", text });
    setInput("");
    setSending(true);
    try {
      const res = await api.sendChat(conversationId, text);
      setConversationId(res.conversation_id);
      setReadyForDiagnosis(res.ready_for_diagnosis);
      pushMessage({ sender: "bot", message_type: "text", text: res.reply });
    } catch (err) {
      pushMessage({ sender: "bot", message_type: "text", text: `Something went wrong: ${err.message}` });
    } finally {
      setSending(false);
    }
  };

  const handleUpload = async (file, mediaType) => {
    if (!conversationId) {
      pushMessage({ sender: "bot", message_type: "text", text: "Please describe your issue first so I have a case open for this upload." });
      return;
    }
    pushMessage({ sender: "user", message_type: mediaType, text: file.name });
    setSending(true);
    try {
      const res = await api.uploadMedia(conversationId, file, mediaType);
      pushMessage({ sender: "bot", message_type: "text", text: res.reply });
    } catch (err) {
      pushMessage({ sender: "bot", message_type: "text", text: `Upload failed: ${err.message}` });
    } finally {
      setSending(false);
    }
  };

  const runDiagnosis = async () => {
    if (!conversationId || diagnosing) return;
    setDiagnosing(true);
    try {
      const res = await api.requestDiagnosis(conversationId);
      setDiagnosis(res.diagnosis);
      pushMessage({ sender: "bot", message_type: "text", text: res.reply });
      setReadyForDiagnosis(false);
    } catch (err) {
      pushMessage({ sender: "bot", message_type: "text", text: `Diagnosis failed: ${err.message}` });
    } finally {
      setDiagnosing(false);
    }
  };

  const submitBooking = async (form) => {
    setBookingSubmitting(true);
    setBookingError("");
    try {
      const res = await api.createBooking({ conversation_id: conversationId, diagnosis: diagnosis?.id, ...form });
      setBooking(res);
      setShowBooking(false);
      pushMessage({ sender: "bot", message_type: "text", text: `Booking confirmed — ID #${res.id}. A mechanic will reach out at ${form.phone_number}.` });
    } catch (err) {
      setBookingError(err.message);
    } finally {
      setBookingSubmitting(false);
    }
  };

  return (
    <div style={{ minHeight: "100dvh", display: "flex", flexDirection: "column" }}>
      <header
        style={{
          borderBottom: "1px solid var(--border)", padding: "16px 20px",
          display: "flex", alignItems: "center", gap: 10,
        }}
      >
        <div style={{ width: 10, height: 10, borderRadius: "50%", background: "var(--amber)" }} />
        <div>
          <div style={{ fontFamily: "var(--font-head)", fontWeight: 700, fontSize: 17 }}>Instant Mechanic</div>
          <div style={{ fontSize: 11.5, color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
            AI TROUBLESHOOTING · {conversationId ? `CASE #${conversationId.slice(0, 8).toUpperCase()}` : "NEW CASE"}
          </div>
        </div>
      </header>

      <main
        ref={scrollRef}
        className="scrollbar"
        style={{ flex: 1, overflowY: "auto", padding: "20px", maxWidth: 720, width: "100%", margin: "0 auto" }}
      >
        {messages.map((m, i) => (
          <MessageBubble key={i} message={m} />
        ))}
        {diagnosis && <DiagnosisCard diagnosis={diagnosis} onBook={() => setShowBooking(true)} booked={!!booking} />}
        {sending && (
          <div style={{ color: "var(--text-muted)", fontSize: 13, fontFamily: "var(--font-mono)" }}>typing…</div>
        )}
      </main>

      <footer style={{ borderTop: "1px solid var(--border)", padding: 16 }}>
        <div style={{ maxWidth: 720, margin: "0 auto" }}>
          {readyForDiagnosis && !diagnosis && (
            <button
              onClick={runDiagnosis}
              disabled={diagnosing}
              style={{
                width: "100%", marginBottom: 10, background: "var(--green)", color: "#08150D",
                border: "none", borderRadius: 8, padding: "10px 0", fontWeight: 600, fontSize: 13.5,
              }}
            >
              {diagnosing ? "Analyzing…" : "Get Diagnosis →"}
            </button>
          )}
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <MediaUploader onUpload={handleUpload} disabled={sending} />
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && send(input)}
              placeholder="Describe the problem with your vehicle…"
              disabled={sending}
              style={{
                flex: 1, background: "var(--panel)", border: "1px solid var(--border)",
                borderRadius: 10, color: "var(--text)", padding: "10px 14px", fontSize: 14,
              }}
            />
            <button
              onClick={() => send(input)}
              disabled={sending || !input.trim()}
              style={{
                background: "var(--amber)", color: "#1A1300", border: "none",
                borderRadius: 10, padding: "10px 18px", fontWeight: 600, fontSize: 13.5,
              }}
            >
              Send
            </button>
          </div>
        </div>
      </footer>

      {showBooking && (
        <BookingModal
          onClose={() => setShowBooking(false)}
          onSubmit={submitBooking}
          submitting={bookingSubmitting}
          error={bookingError}
        />
      )}
    </div>
  );
}
