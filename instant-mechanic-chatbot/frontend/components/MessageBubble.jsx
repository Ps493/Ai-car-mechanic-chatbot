export default function MessageBubble({ message }) {
  const isBot = message.sender === "bot";
  return (
    <div style={{ display: "flex", justifyContent: isBot ? "flex-start" : "flex-end", marginBottom: 14 }}>
      <div
        style={{
          maxWidth: "78%",
          background: isBot ? "var(--panel-raised)" : "var(--amber)",
          color: isBot ? "var(--text)" : "#1A1300",
          border: isBot ? "1px solid var(--border)" : "none",
          borderRadius: isBot ? "4px 14px 14px 14px" : "14px 4px 14px 14px",
          padding: "10px 14px",
          fontSize: 14.5,
          lineHeight: 1.5,
          whiteSpace: "pre-wrap",
        }}
      >
        {!isBot && message.message_type && message.message_type !== "text" && (
          <div style={{ fontSize: 11, opacity: 0.7, marginBottom: 4, fontFamily: "var(--font-mono)" }}>
            {message.message_type.toUpperCase()} ATTACHMENT
          </div>
        )}
        {message.text}
      </div>
    </div>
  );
}
