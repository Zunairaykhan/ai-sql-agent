import React from "react";

export default function LoadingSpinner() {
  return (
    <div className="flex items-center gap-1.5 px-1 py-2">
      <span className="h-2 w-2 animate-bounce-slow rounded-full bg-brand-500 [animation-delay:-0.3s]" />
      <span className="h-2 w-2 animate-bounce-slow rounded-full bg-brand-500 [animation-delay:-0.15s]" />
      <span className="h-2 w-2 animate-bounce-slow rounded-full bg-brand-500" />
      <span className="ml-2 text-xs text-slate-400 dark:text-slate-500">Thinking...</span>
    </div>
  );
}
