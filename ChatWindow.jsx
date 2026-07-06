import React, { useEffect, useRef } from "react";
import MessageBubble from "./MessageBubble.jsx";

export default function ChatWindow({ messages }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center px-6 text-center">
        <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-500 to-brand-700 text-white shadow-lg">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" className="h-7 w-7">
            <path d="M4 6a2 2 0 012-2h12a2 2 0 012 2v2H4V6zm0 5h16v2H4v-2zm0 5h16v2H4v-2z" fill="currentColor" />
          </svg>
        </div>
        <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100">
          Ask anything about your database
        </h2>
        <p className="mt-1.5 max-w-sm text-sm text-slate-500 dark:text-slate-400">
          I automatically read your PostgreSQL schema and turn your questions into safe,
          read-only SQL queries.
        </p>
      </div>
    );
  }

  return (
    <div className="scrollbar-thin flex-1 space-y-4 overflow-y-auto px-2 py-4 sm:px-4">
      <div className="mx-auto flex max-w-4xl flex-col gap-4">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
