const BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000/api";

async function handle(res) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error || `Request failed (${res.status})`);
  }
  return res.json();
}

export const api = {
  sendChat: (conversationId, message) =>
    fetch(`${BASE}/chat/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ conversation_id: conversationId, message }),
    }).then(handle),

  uploadMedia: (conversationId, file, mediaType) => {
    const form = new FormData();
    form.append("conversation_id", conversationId);
    form.append("file", file);
    form.append("media_type", mediaType);
    return fetch(`${BASE}/upload/`, { method: "POST", body: form }).then(handle);
  },

  requestDiagnosis: (conversationId) =>
    fetch(`${BASE}/diagnosis/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ conversation_id: conversationId }),
    }).then(handle),

  createBooking: (payload) =>
    fetch(`${BASE}/booking/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then(handle),

  getBooking: (id) => fetch(`${BASE}/booking/${id}/`).then(handle),
};
