import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Send a natural language question to the backend chat endpoint.
 * @param {string} question
 * @param {string|null} sessionId
 * @returns {Promise<object>} chat response payload
 */
export async function sendChatMessage(question, sessionId) {
  try {
    const response = await client.post("/chat", {
      question,
      session_id: sessionId,
    });
    return response.data;
  } catch (error) {
    if (error.response) {
      const detail = error.response.data?.detail || error.response.data?.error;
      throw new Error(detail || `Server error (${error.response.status})`);
    } else if (error.request) {
      throw new Error("No response from server. Is the backend running?");
    } else {
      throw new Error(error.message || "Unexpected error while sending the request.");
    }
  }
}

/**
 * Clear the conversation memory for a given session on the backend.
 * @param {string} sessionId
 */
export async function clearSession(sessionId) {
  if (!sessionId) return;
  try {
    await client.delete(`/chat/${sessionId}`);
  } catch {
    // Non-fatal: local chat state is cleared regardless.
  }
}

/**
 * Fetch backend health status.
 */
export async function fetchHealth() {
  try {
    const response = await client.get("/health");
    return response.data;
  } catch {
    return { status: "unreachable", database_connected: false };
  }
}

export default client;
