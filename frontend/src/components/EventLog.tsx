/** Every event of the run, newest at the bottom, filterable by agent. It can be collapsed. */
import { useEffect, useRef, useState } from "react";

import type { RunEvent } from "../api/client";
import { describeEvent, EVENT_ICON } from "../run/describeEvent";
import { agentTitle, formatClock } from "../run/format";

const ALL = "";

export function EventLog({ events, agents }: { events: RunEvent[]; agents: string[] }) {
  const [open, setOpen] = useState(true);
  const [agentFilter, setAgentFilter] = useState(ALL);
  const bottom = useRef<HTMLLIElement>(null);
  const shown = agentFilter === ALL ? events : events.filter((event) => event.agent === agentFilter);

  useEffect(() => {
    if (open) bottom.current?.scrollIntoView({ block: "nearest" });
  }, [open, shown.length]);

  return (
    <section className="border-t border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
      <header className="flex items-center gap-3 px-4 py-2 text-sm">
        <button type="button" onClick={() => setOpen(!open)} className="font-medium" aria-expanded={open}>
          {open ? "▾" : "▸"} Live log <span className="text-slate-500">({events.length})</span>
        </button>
        {open && (
          <select
            value={agentFilter}
            onChange={(change) => setAgentFilter(change.target.value)}
            className="rounded border border-slate-300 bg-transparent px-2 py-0.5 text-xs dark:border-slate-700"
            aria-label="Filter by agent"
          >
            <option value={ALL}>All agents</option>
            {agents.map((name) => (
              <option key={name} value={name}>
                {agentTitle(name)}
              </option>
            ))}
          </select>
        )}
      </header>
      {open && (
        <ol className="h-40 overflow-y-auto px-4 pb-2 font-mono text-xs">
          {shown.map((event) => (
            <li key={event.seq} className="flex gap-3 py-0.5">
              <span className="text-slate-400">{formatClock(Date.parse(event.at))}</span>
              <span className="w-24 shrink-0 truncate font-semibold">{event.agent ? agentTitle(event.agent) : "run"}</span>
              <span aria-hidden className="text-slate-400">{EVENT_ICON[event.kind]}</span>
              <span className="truncate" title={describeEvent(event)}>
                {describeEvent(event)}
              </span>
            </li>
          ))}
          <li ref={bottom} />
        </ol>
      )}
    </section>
  );
}
