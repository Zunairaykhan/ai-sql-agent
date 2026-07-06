import React, { useEffect, useState, useCallback } from "react";
import Header from "./components/Header.jsx";
import ChatWindow from "./components/ChatWindow.jsx";
import ChatInput from "./components/ChatInput.jsx";
import { sendChatMessage, clearSession, fetchHealth } from "./services/api.js";

function generateId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export default function App() {
  const [messages, setMessages] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [darkMode, setDarkMode] = useState(() => {
    if (typeof window === "undefined") return true;
    const stored = window.localStorage.getItem("ai-sql-agent-dark-mode");
    return stored ? stored === "true" : true;
  });
  const [dbStatus, setDbStatus] = useState("degraded");

  useEffect(() => {
    document.documentElement.classList.toggle("dark", darkMode);
    window.localStorage.setItem("ai-sql-agent-dark-mode", String(darkMode));
  }, [darkMode]);

  useEffect(() => {
    let mounted = true;
    fetchHealth().then((health) => {
      if (mounted) setDbStatus(health.status);
    });
    const interval = setInterval(() => {
      fetchHealth().then((health) => {
        if (mounted) setDbStatus(health.status);
      });
    }, 30000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const handleSend = useCallback(
    async (question) => {
      const userMessage = { id: generateId(), role: "user", content: question };
      const loadingMessage = { id: generateId(), role: "assistant", loading: true };

      setMessages((prev) => [...prev, userMessage, loadingMessage]);
      setIsLoading(true);

      try {
        const data = await sendChatMessage(question, sessionId);
        if (!sessionId) setSessionId(data.session_id);

        setMessages((prev) =>
          prev.map((m) =>
            m.id === loadingMessage.id
              ? {
                  id: m.id,
                  role: "assistant",
                  loading: false,
                  success: data.success,
                  sql: data.sql,
                  columns: data.columns,
                  rows: data.rows,
                  row_count: data.row_count,
                  explanation: data.explanation,
                  error: data.success ? null : data.error || data.explanation,
                }
              : m
          )
        );
      } catch (err) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === loadingMessage.id
              ? { id: m.id, role: "assistant", loading: false, error: err.message || "Something went wrong." }
              : m
          )
        );
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId]
  );

  const handleClearChat = useCallback(() => {
    setMessages([]);
    clearSession(sessionId);
    setSessionId(null);
  }, [sessionId]);

  return (
    <div className="flex h-screen flex-col bg-slate-50 dark:bg-slate-900">
      <Header
        darkMode={darkMode}
        onToggleDarkMode={() => setDarkMode((d) => !d)}
        onClearChat={handleClearChat}
        dbStatus={dbStatus}
      />
      <main className="flex flex-1 flex-col overflow-hidden">
        <ChatWindow messages={messages} />
        <ChatInput onSend={handleSend} disabled={isLoading} />
      </main>
    </div>
  );
}
