import React from "react";

export default function Header({ darkMode, onToggleDarkMode, onClearChat, dbStatus }) {
  return (
    <header className="sticky top-0 z-10 flex items-center justify-between border-b border-slate-200 bg-white/80 px-4 py-3 backdrop-blur-md dark:border-slate-700 dark:bg-slate-900/80 sm:px-6">
      <div className="flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 text-white shadow-md">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" className="h-5 w-5">
            <path
              d="M4 6a2 2 0 012-2h12a2 2 0 012 2v2H4V6zm0 5h16v2H4v-2zm0 5h16v2H4v-2z"
              fill="currentColor"
            />
          </svg>
        </div>
        <div>
          <h1 className="text-sm font-semibold text-slate-900 dark:text-white sm:text-base">
            AI SQL Agent
          </h1>
          <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
            <span
              className={`h-1.5 w-1.5 rounded-full ${
                dbStatus === "ok" ? "bg-emerald-500" : dbStatus === "degraded" ? "bg-amber-500" : "bg-red-500"
              }`}
            />
            <span>{dbStatus === "ok" ? "Database connected" : dbStatus === "degraded" ? "Checking database..." : "Database unreachable"}</span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={onClearChat}
          className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 transition hover:bg-slate-100 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
          title="Clear chat"
        >
          Clear chat
        </button>
        <button
          onClick={onToggleDarkMode}
          className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 text-slate-600 transition hover:bg-slate-100 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
          title="Toggle dark mode"
        >
          {darkMode ? (
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" className="h-4 w-4">
              <path
                d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.36 6.36l-.7-.7M6.34 6.34l-.7-.7m12.02 0l-.7.7M6.34 17.66l-.7.7M12 7a5 5 0 100 10 5 5 0 000-10z"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
              />
            </svg>
          ) : (
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" className="h-4 w-4">
              <path
                d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinejoin="round"
              />
            </svg>
          )}
        </button>
      </div>
    </header>
  );
}
