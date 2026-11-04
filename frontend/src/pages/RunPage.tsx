/**
 * The live view of one run: the workflow graph (or timeline, or report) in
 * the middle, the selected agent's details on the right, the live log below.
 */
import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { AgentPanel } from "../components/AgentPanel";
import { EventLog } from "../components/EventLog";
import { ReportView } from "../components/ReportView";
import { StatusBadge } from "../components/StatusBadge";
import { Timeline } from "../components/Timeline";
import { WorkflowGraph } from "../components/WorkflowGraph";
import { deriveRunView, type RunView } from "../run/deriveRunView";
import { formatDuration } from "../run/format";
import { RUN_STATUS_STYLE } from "../run/statusStyle";
import { useNow } from "../run/useNow";
import { useRunEvents } from "../run/useRunEvents";
import { useWorkflow } from "../run/useWorkflow";

const VIEWS = ["Graph", "Timeline", "Report"] as const;
type ViewName = (typeof VIEWS)[number];

export function RunPage() {
  const { runId = "" } = useParams();
  const { workflow, error: workflowError } = useWorkflow();
  const { run, events, error: runError } = useRunEvents(runId);
  const [selected, setSelected] = useState<string | null>(null);
  const [viewName, setViewName] = useState<ViewName>("Graph");

  const view = useMemo(
    () => (workflow && run ? deriveRunView(workflow, events, run.status) : null),
    [workflow, run, events],
  );
  const now = useNow(view?.phase === "running");

  const error = workflowError ?? runError;
  if (error) return <p className="p-6 text-rose-700">Could not load this run: {error}</p>;
  if (!view || !workflow || !run) return <p className="p-6 text-slate-500">Loading…</p>;

  return (
    <div className="flex h-[calc(100vh-3rem)] flex-col">
      <RunHeader idea={run.idea.idea} view={view} now={now} />
      <div className="flex min-h-0 flex-1">
        <section className="flex min-w-0 flex-1 flex-col">
          <nav className="flex gap-1 border-b border-slate-200 px-4 py-2 dark:border-slate-800" role="tablist">
            {VIEWS.map((name) => (
              <button
                key={name}
                role="tab"
                aria-selected={viewName === name}
                onClick={() => setViewName(name)}
                className={`rounded px-3 py-1 text-sm ${viewName === name ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900" : "hover:bg-slate-100 dark:hover:bg-slate-800"}`}
              >
                {name}
                {name === "Report" && view.report && <span className="ml-1 text-emerald-500">●</span>}
              </button>
            ))}
          </nav>
          <div className="min-h-0 flex-1">
            {viewName === "Graph" && (
              <WorkflowGraph view={view} reviewAgent={workflow.review_agent} selected={selected} now={now} onSelect={setSelected} />
            )}
            {viewName === "Timeline" && <Timeline view={view} now={now} selected={selected} onSelect={setSelected} />}
            {viewName === "Report" && <ReportView report={view.report} />}
          </div>
        </section>
        <aside className="w-96 shrink-0 border-l border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
          <AgentPanel
            key={selected ?? "none"}
            agent={selected ? view.agents[selected] : null}
            entryAgent={workflow.entry}
            plan={view.plan}
            now={now}
          />
        </aside>
      </div>
      <EventLog events={events} agents={view.order} />
    </div>
  );
}

function RunHeader({ idea, view, now }: { idea: string; view: RunView; now: number }) {
  const elapsed = view.startedAt === null ? 0 : (view.finishedAt ?? now) - view.startedAt;
  return (
    <header className="flex items-center gap-4 border-b border-slate-200 bg-white px-4 py-3 dark:border-slate-800 dark:bg-slate-900">
      <Link to="/" className="text-sm text-slate-500 hover:text-slate-900 dark:hover:text-slate-100">
        ◀ Analyses
      </Link>
      <h1 className="min-w-0 flex-1 truncate font-medium" title={idea}>
        {idea}
      </h1>
      <StatusBadge style={RUN_STATUS_STYLE[view.phase]} pulse={view.phase === "running"} />
      <span className="text-sm tabular-nums text-slate-600 dark:text-slate-300" title="Elapsed time">
        ⏱ {formatDuration(elapsed)}
      </span>
      <span className="text-sm text-slate-600 dark:text-slate-300" title="Times the reviewer sent work back">
        Revisions {view.revisions} / {view.maxRevisions}
      </span>
      {view.error && <span className="max-w-xs truncate text-sm text-rose-700" title={view.error}>{view.error}</span>}
    </header>
  );
}
