import React from "react";
import SqlBlock from "./SqlBlock.jsx";
import ResultTable from "./ResultTable.jsx";
import LoadingSpinner from "./LoadingSpinner.jsx";

export default function MessageBubble({ message }) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="flex animate-fade-in justify-end px-2">
        <div className="max-w-[85%] rounded-2xl rounded-tr-sm bg-brand-600 px-4 py-2.5 text-sm text-white shadow-sm sm:max-w-[70%]">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className="flex animate-fade-in justify-start px-2">
      <div className="max-w-[90%] rounded-2xl rounded-tl-sm border border-slate-200 bg-white px-4 py-3 text-sm text-slate-800 shadow-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 sm:max-w-[80%]">
        {message.loading ? (
          <LoadingSpinner />
        ) : message.error ? (
          <ErrorBlock error={message.error} sql={message.sql} />
        ) : (
          <div>
            <p className="whitespace-pre-wrap leading-relaxed">{message.explanation}</p>
            <SqlBlock sql={message.sql} />
            <ResultTable columns={message.columns} rows={message.rows} rowCount={message.row_count} />
          </div>
        )}
      </div>
    </div>
  );
}

function ErrorBlock({ error, sql }) {
  return (
    <div>
      <div className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-red-700 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-300">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" className="mt-0.5 h-4 w-4 shrink-0">
          <path
            d="M12 9v4m0 4h.01M10.29 3.86l-8.18 14.18A1.5 1.5 0 003.32 20h17.36a1.5 1.5 0 001.21-2.36L13.71 3.86a1.5 1.5 0 00-2.42 0z"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        <span className="text-sm">{error}</span>
      </div>
      <SqlBlock sql={sql} />
    </div>
  );
}
