/** Starts a new analysis and opens its live view. */
import { type FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import { startRun } from "../api/client";

// The API checks the real limits (BusinessIdea in src/orchestrator/state.py)
// and its message is shown below. This is only a hint while typing.
const SUGGESTED_MIN_LENGTH = 10;

export function NewRunForm() {
  const navigate = useNavigate();
  const [idea, setIdea] = useState("");
  const [context, setContext] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSending(true);
    setError(null);
    try {
      const runId = await startRun({ idea, context: context.trim() || null });
      navigate(`/runs/${runId}`);
    } catch (reason) {
      setError((reason as Error).message);
      setSending(false);
    }
  }

  return (
    <form onSubmit={submit} className="space-y-4 rounded-lg border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <h2 className="text-lg font-semibold">New analysis</h2>
      <label className="block space-y-1">
        <span className="text-sm font-medium">Business idea</span>
        <textarea
          value={idea}
          onChange={(change) => setIdea(change.target.value)}
          rows={3}
          required
          placeholder="Offer buy now, pay later at checkout for orders above EGP 3,000."
          className="w-full rounded border border-slate-300 bg-transparent p-2 text-sm dark:border-slate-700"
        />
        {idea.length > 0 && idea.trim().length < SUGGESTED_MIN_LENGTH && (
          <span className="text-xs text-amber-700">Describe the idea in at least {SUGGESTED_MIN_LENGTH} characters.</span>
        )}
      </label>
      <label className="block space-y-1">
        <span className="text-sm font-medium">
          Extra context <span className="font-normal text-slate-500">(optional: budget, timeline, constraints)</span>
        </span>
        <textarea
          value={context}
          onChange={(change) => setContext(change.target.value)}
          rows={2}
          placeholder="Pilot in Cairo and Giza, budget around EGP 1.5 million."
          className="w-full rounded border border-slate-300 bg-transparent p-2 text-sm dark:border-slate-700"
        />
      </label>
      {error && <p className="whitespace-pre-line rounded bg-rose-50 p-2 text-sm text-rose-800 dark:bg-rose-950 dark:text-rose-200">{error}</p>}
      <button
        type="submit"
        disabled={sending}
        className="rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50 dark:bg-slate-100 dark:text-slate-900"
      >
        {sending ? "Starting…" : "Start analysis"}
      </button>
    </form>
  );
}
