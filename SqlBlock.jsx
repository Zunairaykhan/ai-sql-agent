import React, { useState } from "react";

export default function SqlBlock({ sql }) {
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  if (!sql) return null;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(sql);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  };

  return (
    <div className="mt-2 overflow-hidden rounded-lg border border-slate-200 dark:border-slate-700">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between bg-slate-50 px-3 py-2 text-left text-xs font-medium text-slate-600 transition hover:bg-slate-100 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
      >
        <span className="flex items-center gap-1.5">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" className="h-3.5 w-3.5">
            <path d="M8 9l-4 3 4 3m8-6l4 3-4 3M14 4l-4 16" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          {open ? "Hide SQL query" : "Show SQL query"}
        </span>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          className={`h-3.5 w-3.5 transition-transform ${open ? "rotate-180" : ""}`}
        >
          <path d="M6 9l6 6 6-6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>

      {open && (
        <div className="relative bg-slate-900 dark:bg-slate-950">
          <button
            onClick={handleCopy}
            className="absolute right-2 top-2 rounded-md bg-slate-700/70 px-2 py-1 text-[10px] font-medium text-slate-100 transition hover:bg-slate-600"
          >
            {copied ? "Copied!" : "Copy"}
          </button>
          <pre className="scrollbar-thin overflow-x-auto p-3 pr-16 text-xs leading-relaxed text-emerald-300">
            <code>{sql}</code>
          </pre>
        </div>
      )}
    </div>
  );
}
