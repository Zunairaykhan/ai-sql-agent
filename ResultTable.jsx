import React from "react";

export default function ResultTable({ columns, rows, rowCount }) {
  if (!columns || columns.length === 0 || !rows || rows.length === 0) {
    return null;
  }

  return (
    <div className="mt-3">
      <div className="scrollbar-thin max-h-80 overflow-auto rounded-lg border border-slate-200 dark:border-slate-700">
        <table className="min-w-full divide-y divide-slate-200 text-left text-xs dark:divide-slate-700">
          <thead className="sticky top-0 bg-slate-100 dark:bg-slate-800">
            <tr>
              {columns.map((col) => (
                <th
                  key={col}
                  className="whitespace-nowrap px-3 py-2 font-semibold text-slate-600 dark:text-slate-300"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {rows.map((row, idx) => (
              <tr key={idx} className="bg-white transition hover:bg-slate-50 dark:bg-slate-900 dark:hover:bg-slate-800/60">
                {columns.map((col) => (
                  <td key={col} className="whitespace-nowrap px-3 py-2 text-slate-700 dark:text-slate-300">
                    {formatCell(row[col])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-1 text-[11px] text-slate-400 dark:text-slate-500">
        Showing {rows.length} of {rowCount} row{rowCount === 1 ? "" : "s"}
      </p>
    </div>
  );
}

function formatCell(value) {
  if (value === null || value === undefined) {
    return <span className="italic text-slate-400 dark:text-slate-600">null</span>;
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return String(value);
}
