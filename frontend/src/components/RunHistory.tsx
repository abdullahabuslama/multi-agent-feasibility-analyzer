/** Past and running analyses. Refreshes every few seconds while one is running. */
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { listRuns, type RunSummary } from "../api/client";
import { formatDateTime, formatDuration } from "../run/format";
import { RUN_STATUS_STYLE } from "../run/statusStyle";
import { StatusBadge } from "./StatusBadge";

const REFRESH_MS = 5000;

export function RunHistory() {
  const [runs, setRuns] = useState<RunSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const anyRunning = runs?.some((run) => run.status === "running") ?? false;

  useEffect(() => {
    const load = () => listRuns().then(setRuns).catch((reason: Error) => setError(reason.message));
    void load();
    if (!anyRunning) return;
    const timer = window.setInterval(load, REFRESH_MS);
    return () => window.clearInterval(timer);
  }, [anyRunning]);

  if (error) return <p className="text-sm text-rose-700">Could not load the runs: {error}</p>;
  if (!runs) return <p className="text-sm text-slate-500">Loading…</p>;
  if (!runs.length) return <p className="text-sm text-slate-500">No analyses yet. Start one above.</p>;

  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <table className="w-full text-left text-sm">
        <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-800/50">
          <tr>
            <th className="px-4 py-2">Idea</th>
            <th className="px-4 py-2">Status</th>
            <th className="px-4 py-2">Started</th>
            <th className="px-4 py-2">Duration</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => (
            <tr key={run.id} className="border-t border-slate-100 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/40">
              <td className="max-w-md px-4 py-2">
                <Link to={`/runs/${run.id}`} className="line-clamp-2 font-medium hover:underline">
                  {run.idea.idea}
                </Link>
              </td>
              <td className="px-4 py-2">
                <StatusBadge style={RUN_STATUS_STYLE[run.status]} pulse={run.status === "running"} />
              </td>
              <td className="whitespace-nowrap px-4 py-2 text-slate-600 dark:text-slate-300">{formatDateTime(run.created_at)}</td>
              <td className="px-4 py-2 text-slate-600 dark:text-slate-300">
                {run.finished_at ? formatDuration(Date.parse(run.finished_at) - Date.parse(run.created_at)) : "…"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
