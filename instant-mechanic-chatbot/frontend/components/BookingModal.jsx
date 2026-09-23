"use client";
import { useState } from "react";

export default function BookingModal({ onClose, onSubmit, submitting, error }) {
  const [form, setForm] = useState({
    customer_name: "",
    phone_number: "",
    preferred_date: "",
    preferred_time_slot: "",
    address: "",
    notes: "",
  });

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const inputStyle = {
    width: "100%",
    background: "var(--panel)",
    border: "1px solid var(--border)",
    borderRadius: 8,
    color: "var(--text)",
    padding: "9px 11px",
    fontSize: 13.5,
    marginBottom: 12,
    fontFamily: "var(--font-body)",
  };
  const label = { fontSize: 12, color: "var(--text-muted)", display: "block", marginBottom: 5 };

  return (
    <div
      style={{
        position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)",
        display: "flex", alignItems: "center", justifyContent: "center", zIndex: 50, padding: 16,
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: "var(--panel)", border: "1px solid var(--border)", borderRadius: 12,
          padding: 24, width: 420, maxWidth: "100%",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <h2 style={{ fontFamily: "var(--font-head)", fontSize: 18, margin: "0 0 16px" }}>Book a Mechanic</h2>

        <label style={label}>Full name</label>
        <input style={inputStyle} value={form.customer_name} onChange={update("customer_name")} placeholder="Rahul Sharma" />

        <label style={label}>Phone number</label>
        <input style={inputStyle} value={form.phone_number} onChange={update("phone_number")} placeholder="98765 43210" />

        <label style={label}>Preferred date</label>
        <input style={inputStyle} type="date" value={form.preferred_date} onChange={update("preferred_date")} />

        <label style={label}>Preferred time slot (optional)</label>
        <input style={inputStyle} value={form.preferred_time_slot} onChange={update("preferred_time_slot")} placeholder="Morning / 10–12 PM" />

        <label style={label}>Address (optional)</label>
        <input style={inputStyle} value={form.address} onChange={update("address")} placeholder="Where should the mechanic come?" />

        {error && <div style={{ color: "var(--red)", fontSize: 13, marginBottom: 10 }}>{error}</div>}

        <div style={{ display: "flex", gap: 10, marginTop: 6 }}>
          <button
            onClick={onClose}
            style={{ flex: 1, background: "transparent", border: "1px solid var(--border)", color: "var(--text-muted)", borderRadius: 8, padding: "10px 0" }}
          >
            Cancel
          </button>
          <button
            onClick={() => onSubmit(form)}
            disabled={submitting || !form.customer_name || !form.phone_number || !form.preferred_date}
            style={{ flex: 1.4, background: "var(--amber)", color: "#1A1300", border: "none", borderRadius: 8, padding: "10px 0", fontWeight: 600 }}
          >
            {submitting ? "Booking…" : "Confirm Booking"}
          </button>
        </div>
      </div>
    </div>
  );
}
