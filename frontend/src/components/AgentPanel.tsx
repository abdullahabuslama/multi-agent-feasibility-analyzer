/**
 * Details of the selected agent: what it is doing (Activity), what the
 * supervisor asked of it (Brief), and what it produced (Output).
 */
import { useState } from "react";

import type { RunEvent, TaskPlan } from "../api/client";
import type { AgentStatus, AgentView } from "../run/deriveRunView";
import { describeEvent, EVENT_ICON } from "../run/describeEvent";
import { agentTitle, formatClock, formatDuration } from "../run/format";
import { STATUS_STYLE } from "../run/statusStyle";
import { Empty, OutputView, PlanCard, Section } from "./OutputView";
import { StatusBadge } from "./StatusBadge";

const TABS = ["Activity", "Brief", "Output"] as const;
type Tab = (typeof TABS)[number];

interface Props {
  agent: AgentView | null;
  entryAgent: string;
  plan: TaskPlan | null;
  now: number;
}

export function AgentPanel({ agent, entryAgent, plan, now }: Props) {
  const [tab, setTab] = useState<Tab>("Activity");
  if (!agent) return <StatusLegend />;

  return (
    <div className="flex h-full flex-col">
      <header className="space-y-2 border-b border-slate-200 p-4 dark:border-slate-800">
        <div className="flex items-center justify-between gap-2">
          <h2 className="text-lg font-semibold">{agentTitle(agent.name)}</h2>
          <StatusBadge style={STATUS_STYLE[agent.status]} pulse={agent.status === "running"} />
        </div>
        <p className="text-sm text-slate-600 dark:text-slate-300">{agent.role}</p>
        {agent.activity && <p className="text-sm font-medium text-sky-700 dark:text-sky-300">{agent.activity}</p>}
        {agent.error && <p className="rounded bg-rose-50 p-2 text-sm text-rose-800 dark:bg-rose-950 dark:text-rose-200">{agent.error}</p>}
        <details className="text-xs text-slate-500">
          <summary className="cursor-pointer">Goal and tools</summary>
          <p className="mt-1">{agent.goal}</p>
          <p className="mt-1">Tools: {agent.tools.length ? agent.tools.join(", ") : "none"}</p>
        </details>
        <nav className="flex gap-1 pt-1" role="tablist">
          {TABS.map((name) => (
            <button
              key={name}
              role="tab"
              aria-selected={tab === name}
              onClick={() => setTab(name)}
              className={`rounded px-3 py-1 text-sm ${tab === name ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900" : "hover:bg-slate-100 dark:hover:bg-slate-800"}`}
            >
              {name}
              {name === "Activity" && agent.events.length > 0 && <span className="ml-1 text-xs opacity-70">{agent.events.length}</span>}
            </button>
          ))}
        </nav>
      </header>
      <div className="flex-1 overflow-y-auto p-4">
        {tab === "Activity" && <ActivityList events={agent.events} running={agent.status === "running"} now={now} />}
        {tab === "Brief" && <Brief agent={agent.name} entryAgent={entryAgent} plan={plan} />}
        {tab === "Output" && <OutputView output={agent.output} agent={agent.name} />}
      </div>
    </div>
  );
}

function ActivityList({ events, running, now }: { events: RunEvent[]; running: boolean; now: number }) {
  if (!events.length) return <Empty>No activity yet.</Empty>;
  return (
    <ol className="space-y-3">
      {events.map((event, index) => {
        const next = events[index + 1];
        // A step lasts until this agent's next event; the last one lasts until now while running.
        const end = next ? Date.parse(next.at) : running ? now : null;
        return (
          <li key={event.seq} className="flex gap-3 text-sm">
            <span aria-hidden className="w-4 shrink-0 text-center text-slate-400">{EVENT_ICON[event.kind]}</span>
            <div className="min-w-0 flex-1">
              <p className="break-words">{describeEvent(event)}</p>
              <p className="text-xs text-slate-500">
                {formatClock(Date.parse(event.at))}
                {end !== null && ` · ${formatDuration(end - Date.parse(event.at))}`}
              </p>
              {event.kind === "tool_returned" && typeof event.detail?.preview === "string" && (
                <details className="mt-1">
                  <summary className="cursor-pointer text-xs text-slate-500">Show result</summary>
                  <pre className="mt-1 max-h-60 overflow-auto whitespace-pre-wrap rounded bg-slate-100 p-2 text-xs dark:bg-slate-800">
                    {event.detail.preview}
                  </pre>
                </details>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}

function Brief({ agent, entryAgent, plan }: { agent: string; entryAgent: string; plan: TaskPlan | null }) {
  if (!plan) return <Empty>The supervisor has not written the briefs yet.</Empty>;
  if (agent === entryAgent) return <PlanCard plan={plan} />;
  const brief = plan.briefs.find((item) => item.agent === agent);
  return brief ? <p className="text-sm leading-relaxed">{brief.instructions}</p> : <Empty>The supervisor wrote no brief for this agent.</Empty>;
}

const LEGEND_ORDER: AgentStatus[] = ["running", "waiting", "sent_back", "done", "failed", "stopped", "not_started"];
const LEGEND_TEXT: Record<AgentStatus, string> = {
  running: "Working now: calling the LLM or a tool.",
  waiting: "Waiting for earlier agents to finish.",
  sent_back: "The reviewer asked for changes; it will run again.",
  done: "Finished its work.",
  failed: "Stopped with an error.",
  stopped: "Was cut off because another agent failed.",
  not_started: "Did not run.",
};

function StatusLegend() {
  return (
    <div className="space-y-4 p-4">
      <p className="text-sm text-slate-600 dark:text-slate-300">Click an agent to see what it is doing and what it produced.</p>
      <Section title="Statuses">
        <ul className="space-y-2">
          {LEGEND_ORDER.map((status) => (
            <li key={status} className="flex items-start gap-2 text-sm">
              <StatusBadge style={STATUS_STYLE[status]} />
              <span className="text-slate-600 dark:text-slate-300">{LEGEND_TEXT[status]}</span>
            </li>
          ))}
        </ul>
      </Section>
    </div>
  );
}
