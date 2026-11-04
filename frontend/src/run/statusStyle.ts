/**
 * How each status looks. Every badge, card border, and timeline bar reads
 * this map, so a new status is one new entry here, not an `if` in a view.
 * The icon carries the meaning too, so status is never shown by colour alone.
 */
import type { RunStatus } from "../api/client";
import type { AgentStatus, RunPhase } from "./deriveRunView";

export interface StatusStyle {
  label: string;
  icon: string;
  badge: string; // Tailwind classes for the pill
  border: string; // Tailwind classes for the card border
  bar: string; // Tailwind classes for the timeline bar
}

export const STATUS_STYLE: Record<AgentStatus, StatusStyle> = {
  not_started: {
    label: "Not started",
    icon: "○",
    badge: "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300",
    border: "border-slate-200 dark:border-slate-700",
    bar: "bg-slate-300",
  },
  waiting: {
    label: "Waiting",
    icon: "◷",
    badge: "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200",
    border: "border-amber-300 dark:border-amber-700",
    bar: "bar-waiting",
  },
  running: {
    label: "Running",
    icon: "●",
    badge: "bg-sky-100 text-sky-800 dark:bg-sky-900/40 dark:text-sky-200",
    border: "border-sky-400 ring-2 ring-sky-200 dark:ring-sky-900",
    bar: "bg-sky-500",
  },
  done: {
    label: "Done",
    icon: "✓",
    badge: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200",
    border: "border-emerald-300 dark:border-emerald-700",
    bar: "bg-emerald-500",
  },
  sent_back: {
    label: "Sent back",
    icon: "↩",
    badge: "bg-violet-100 text-violet-800 dark:bg-violet-900/40 dark:text-violet-200",
    border: "border-violet-400 dark:border-violet-600",
    bar: "bg-violet-500",
  },
  stopped: {
    label: "Stopped",
    icon: "■",
    badge: "bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-200",
    border: "border-slate-400 border-dashed dark:border-slate-500",
    bar: "bg-slate-400",
  },
  failed: {
    label: "Failed",
    icon: "✕",
    badge: "bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-200",
    border: "border-rose-400 dark:border-rose-600",
    bar: "bg-rose-500",
  },
};

/** The run's own status, styled like the matching agent status. */
export const RUN_STATUS_STYLE: Record<RunPhase | RunStatus, StatusStyle> = {
  running: STATUS_STYLE.running,
  done: STATUS_STYLE.done,
  failed: STATUS_STYLE.failed,
};
