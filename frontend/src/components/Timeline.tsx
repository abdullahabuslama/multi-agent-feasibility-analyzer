/**
 * One row per agent along a time axis, like a Gantt chart. Solid bars are
 * running time, striped bars are time spent waiting for earlier agents, and
 * dots are tool calls. It shows at a glance who waited for whom, and how long.
 */
import type { RunView } from "../run/deriveRunView";
import { agentTitle, formatClock, formatDuration } from "../run/format";
import { STATUS_STYLE } from "../run/statusStyle";

/** Tick spacing options in seconds; the first one giving at most 8 ticks is used. */
const TICK_STEPS = [5, 10, 15, 30, 60, 120, 300, 600, 1800];

interface Props {
  view: RunView;
  now: number;
  selected: string | null;
  onSelect: (agent: string) => void;
}

export function Timeline({ view, now, selected, onSelect }: Props) {
  if (view.startedAt === null) return <p className="p-6 text-sm text-slate-500">The run has not started yet.</p>;
  const start = view.startedAt;
  const span = Math.max((view.finishedAt ?? now) - start, 1000);
  const percent = (time: number) => `${((time - start) / span) * 100}%`;
  const width = (from: number, to: number) => `${(Math.max(to - from, 0) / span) * 100}%`;
  const step = TICK_STEPS.find((seconds) => span / 1000 / seconds <= 8) ?? TICK_STEPS.at(-1)!;
  const ticks = Array.from({ length: Math.floor(span / 1000 / step) + 1 }, (_, index) => index * step * 1000);

  return (
    <div className="h-full overflow-auto p-6">
      <div className="ml-32 flex justify-between border-b border-slate-200 pb-1 text-[11px] text-slate-500 dark:border-slate-700">
        <span>{formatClock(start)}</span>
        <span>{formatDuration(span)}</span>
      </div>
      <div className="relative">
        <div className="pointer-events-none absolute inset-y-0 left-32 right-0">
          {ticks.map((offset) => (
            <div key={offset} className="absolute inset-y-0 border-l border-dashed border-slate-200 dark:border-slate-800" style={{ left: percent(start + offset) }}>
              <span className="absolute left-1 top-0 whitespace-nowrap text-[10px] text-slate-400">+{formatDuration(offset)}</span>
            </div>
          ))}
        </div>
        {view.order.map((name) => {
          const agent = view.agents[name];
          return (
            <button
              key={name}
              type="button"
              onClick={() => onSelect(name)}
              className={`flex w-full items-center py-2 text-left ${selected === name ? "bg-slate-100 dark:bg-slate-800/60" : ""}`}
            >
              <span className="w-32 shrink-0 truncate pr-3 text-sm font-medium">
                <span aria-hidden className="mr-1">{STATUS_STYLE[agent.status].icon}</span>
                {agentTitle(name)}
              </span>
              <span className="relative h-6 flex-1 rounded bg-slate-100 dark:bg-slate-800/40">
                {agent.spans.map((bar) => (
                  <span
                    key={`${bar.kind}-${bar.start}`}
                    className={`absolute inset-y-0.5 rounded ${bar.kind === "waiting" ? "bar-waiting" : STATUS_STYLE[agent.status === "failed" || agent.status === "stopped" ? agent.status : "running"].bar}`}
                    style={{ left: percent(bar.start), width: width(bar.start, bar.end ?? now) }}
                    title={`${bar.kind === "waiting" ? "Waiting" : "Running"}: ${formatDuration((bar.end ?? now) - bar.start)}`}
                  />
                ))}
                {agent.events
                  .filter((event) => event.kind === "tool_called")
                  .map((event) => (
                    <span
                      key={event.seq}
                      className="absolute top-1/2 h-2 w-2 -translate-x-1/2 -translate-y-1/2 rounded-full bg-white ring-2 ring-slate-700"
                      style={{ left: percent(Date.parse(event.at)) }}
                      title={`Tool call at ${formatClock(Date.parse(event.at))}`}
                    />
                  ))}
              </span>
            </button>
          );
        })}
      </div>
      <div className="ml-32 mt-4 flex gap-4 text-xs text-slate-500">
        <Legend className={STATUS_STYLE.running.bar} label="Running" />
        <Legend className="bar-waiting" label="Waiting for earlier agents" />
        <span className="flex items-center gap-1">
          <span className="h-2 w-2 rounded-full bg-white ring-2 ring-slate-700" /> Tool call
        </span>
      </div>
    </div>
  );
}

function Legend({ className, label }: { className: string; label: string }) {
  return (
    <span className="flex items-center gap-1">
      <span className={`h-3 w-6 rounded ${className}`} /> {label}
    </span>
  );
}
