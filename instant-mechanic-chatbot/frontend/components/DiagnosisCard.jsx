const URGENCY_COLOR = {
  low: "var(--green)",
  medium: "var(--amber)",
  high: "var(--red)",
  urgent: "var(--red)",
};

export default function DiagnosisCard({ diagnosis, onBook, booked }) {
  if (!diagnosis) return null;
  const color = URGENCY_COLOR[diagnosis.urgency] || "var(--amber)";

  return (
    <div
      style={{
        background: "var(--panel-raised)",
        border: `1px solid ${color}`,
        borderRadius: 10,
        padding: 16,
        marginBottom: 14,
        maxWidth: "88%",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
        <span style={{ fontFamily: "var(--font-head)", fontWeight: 600, fontSize: 15 }}>
          Diagnostic Report
        </span>
        <span
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: 11,
            color,
            border: `1px solid ${color}`,
            borderRadius: 4,
            padding: "2px 8px",
          }}
        >
          {diagnosis.urgency?.toUpperCase()}
        </span>
      </div>
      <p style={{ fontSize: 14, lineHeight: 1.55, margin: "0 0 10px" }}>{diagnosis.summary}</p>
      {diagnosis.likely_causes?.length > 0 && (
        <ul style={{ margin: "0 0 10px", paddingLeft: 18, fontSize: 13.5, color: "var(--text-muted)" }}>
          {diagnosis.likely_causes.map((c, i) => (
            <li key={i}>{c}</li>
          ))}
        </ul>
      )}
      <div style={{ fontFamily: "var(--font-mono)", fontSize: 12.5, color: "var(--text-muted)", marginBottom: 12 }}>
        RECOMMENDED SERVICE: {diagnosis.recommended_service} · CONFIDENCE {Math.round((diagnosis.confidence || 0) * 100)}%
      </div>
      <button
        onClick={onBook}
        disabled={booked}
        style={{
          background: booked ? "var(--panel)" : "var(--amber)",
          color: booked ? "var(--text-muted)" : "#1A1300",
          border: "none",
          borderRadius: 8,
          padding: "9px 16px",
          fontWeight: 600,
          fontSize: 13.5,
        }}
      >
        {booked ? "Booking Confirmed ✓" : "Book Mechanic →"}
      </button>
    </div>
  );
}
