/**
 * Turns the workflow shape and a run's events into what every view shows:
 * each agent's status, who it waits for, what it is doing, and its output.
 *
 * This is the only place that interprets events. The graph, the timeline,
 * the agent panel, and the header all read its result, so they cannot
 * disagree. It is a pure function: same input, same output.
 */
import type {
  AgentFinding,
  FinalReport,
  RunEvent,
  RunStatus,
  TaskPlan,
  ValidationResult,
  Workflow,
} from "../api/client";
import { toolLabel } from "./format";

/** `stopped`: it was still running when the run failed because of another agent. */
export type AgentStatus = "not_started" | "waiting" | "running" | "done" | "failed" | "sent_back" | "stopped";
export type RunPhase = "running" | "done" | "failed";

/** A stretch of time in the timeline. `end` is null while it is still going on. */
export interface Span {
  kind: "running" | "waiting";
  start: number;
  end: number | null;
}

/** What an agent posted when it finished: one of these keys is set. */
export interface AgentOutput {
  plan?: TaskPlan;
  findings?: Record<string, AgentFinding & Record<string, unknown>>;
  validation?: ValidationResult;
  report?: FinalReport;
}

export interface AgentView {
  name: string;
  role: string;
  goal: string;
  tools: string[];
  column: number;
  status: AgentStatus;
  waitingOn: string[];
  activity: string | null;
  runs: number;
  toolCalls: number;
  startedAt: number | null;
  finishedAt: number | null;
  events: RunEvent[];
  output: AgentOutput | null;
  error: string | null;
  spans: Span[];
}

export interface RunView {
  phase: RunPhase;
  startedAt: number | null;
  finishedAt: number | null;
  /** Column 0 is the entry agent; then one column per workflow stage. */
  columns: string[][];
  order: string[];
  agents: Record<string, AgentView>;
  plan: TaskPlan | null;
  validation: ValidationResult | null;
  report: FinalReport | null;
  revisions: number;
  maxRevisions: number;
  error: string | null;
}

/** Per-agent counters collected while reading the events in order. */
interface Track {
  lastStartSeq: number;
  lastFinishSeq: number;
  lastFailSeq: number;
  runs: number;
  toolCalls: number;
  startedAt: number | null;
  finishedAt: number | null;
  events: RunEvent[];
  output: AgentOutput | null;
  error: string | null;
  spans: Span[];
}

const BUSY: ReadonlySet<AgentStatus> = new Set(["running", "waiting", "sent_back"]);

export function deriveRunView(workflow: Workflow, events: RunEvent[], serverStatus: RunStatus): RunView {
  const columns = [[workflow.entry], ...workflow.stages];
  const order = columns.flat();
  const tracks = new Map(order.map((name) => [name, emptyTrack()]));

  let startedAt: number | null = null;
  let finishedAt: number | null = null;
  let endedAs: RunPhase | null = null;
  let error: string | null = null;
  let plan: TaskPlan | null = null;
  let report: FinalReport | null = null;
  let validation: { seq: number; value: ValidationResult } | null = null;
  let revisions = 0;
  let lastRevisionAt: number | null = null;

  for (const event of events) {
    const at = Date.parse(event.at);
    const track = event.agent ? tracks.get(event.agent) : undefined;
    track?.events.push(event);

    switch (event.kind) {
      case "run_started":
        startedAt = at;
        break;
      case "run_finished":
        finishedAt = at;
        endedAs = "done";
        break;
      case "run_failed":
        finishedAt = at;
        endedAs = "failed";
        error = text(event.detail?.error);
        break;
      case "agent_started": {
        if (!track) break;
        // The wait began when the run started, or when the reviewer sent work back after this agent's last finish.
        const waitStart = Math.max(startedAt ?? at, track.finishedAt ?? 0, lastRevisionAt ?? 0);
        if (at > waitStart) track.spans.push({ kind: "waiting", start: waitStart, end: at });
        track.spans.push({ kind: "running", start: at, end: null });
        track.lastStartSeq = event.seq;
        track.startedAt = at;
        track.runs += 1;
        break;
      }
      case "agent_finished": {
        if (!track) break;
        closeSpan(track, at);
        track.lastFinishSeq = event.seq;
        track.finishedAt = at;
        const output = (event.detail?.output ?? null) as AgentOutput | null;
        track.output = output;
        if (output?.plan) plan = output.plan;
        if (output?.report) report = output.report;
        if (output?.validation) {
          validation = { seq: event.seq, value: output.validation };
          if (output.validation.revision_requests?.length) {
            revisions += 1;
            lastRevisionAt = at;
          }
        }
        break;
      }
      case "agent_failed":
        if (!track) break;
        closeSpan(track, at);
        track.lastFailSeq = event.seq;
        track.error = text(event.detail?.error);
        break;
      case "tool_called":
        if (track) track.toolCalls += 1;
        break;
    }
  }

  // A run that stopped without a final event (for example a server restart) ends as the server says.
  const phase: RunPhase = endedAs ?? (serverStatus === "running" ? "running" : serverStatus);
  if (phase !== "running" && finishedAt === null && events.length) finishedAt = Date.parse(events.at(-1)!.at);

  const meta = new Map(workflow.agents.map((agent) => [agent.name, agent]));
  const agents: Record<string, AgentView> = {};
  columns.forEach((column, columnIndex) => {
    for (const name of column) {
      const track = tracks.get(name)!;
      const sentBack =
        validation !== null &&
        (validation.value.revision_requests ?? []).includes(name) &&
        track.lastStartSeq < validation.seq;
      const waitingOn = nearestBlockers(columns.slice(0, columnIndex), agents);
      const status = statusOf(track, phase, sentBack, waitingOn.length > 0);
      agents[name] = {
        name,
        role: meta.get(name)?.role ?? "",
        goal: meta.get(name)?.goal ?? "",
        tools: meta.get(name)?.tools ?? [],
        column: columnIndex,
        status,
        waitingOn: status === "waiting" ? waitingOn : [],
        activity: activityOf(status, track, waitingOn),
        runs: track.runs,
        toolCalls: track.toolCalls,
        startedAt: track.startedAt,
        finishedAt: track.finishedAt,
        events: track.events,
        output: track.output,
        error: status === "failed" ? (track.error ?? error) : null,
        spans: openWaitingSpan(track, status, startedAt, lastRevisionAt),
      };
    }
  });

  return {
    phase,
    startedAt,
    finishedAt,
    columns,
    order,
    agents,
    plan,
    validation: validation?.value ?? null,
    report,
    revisions,
    maxRevisions: workflow.max_revisions,
    error,
  };
}

/** Total time the agent spent running, counting a span still going on up to `now`. */
export function runningTime(agent: AgentView, now: number): number {
  return agent.spans
    .filter((span) => span.kind === "running")
    .reduce((total, span) => total + ((span.end ?? now) - span.start), 0);
}

function statusOf(track: Track, phase: RunPhase, sentBack: boolean, blocked: boolean): AgentStatus {
  if (track.lastFailSeq > track.lastStartSeq) return "failed";
  const isRunning = track.lastStartSeq > Math.max(track.lastFinishSeq, track.lastFailSeq);
  if (isRunning) return phase === "running" ? "running" : "stopped";
  const hasFinished = track.lastFinishSeq > 0;
  if (phase !== "running") return hasFinished ? "done" : "not_started";
  if (sentBack) return "sent_back";
  // Every agent in an earlier column feeds this one, so while any of them
  // still has work to do, this agent will run (again) after them.
  if (!hasFinished || blocked) return "waiting";
  return "done";
}

/** The busy agents in the closest earlier column that has any. */
function nearestBlockers(earlierColumns: string[][], agents: Record<string, AgentView>): string[] {
  for (const column of [...earlierColumns].reverse()) {
    const busy = column.filter((name) => BUSY.has(agents[name].status));
    if (busy.length) return busy;
  }
  return [];
}

function activityOf(status: AgentStatus, track: Track, waitingOn: string[]): string | null {
  switch (status) {
    case "running":
      return runningActivity(track.events.at(-1));
    case "waiting":
      return waitingOn.length ? `Waiting for ${waitingOn.join(", ")}` : "Starting soon…";
    case "sent_back":
      return "Sent back by the reviewer";
    case "stopped":
      return "Stopped because the run failed";
    default:
      return null;
  }
}

function runningActivity(last: RunEvent | undefined): string {
  const detail = last?.detail ?? {};
  switch (last?.kind) {
    case "llm_called":
      return detail.purpose === "final_answer" ? "Writing the finding…" : "Thinking about what to look up…";
    case "tool_called": {
      const query = (detail.args as Record<string, unknown> | undefined)?.query;
      return query ? `${toolLabel(text(detail.tool))}: “${text(query)}”` : `${toolLabel(text(detail.tool))}…`;
    }
    case "tool_returned":
      return detail.ok ? "Reading the results…" : `${text(detail.tool)} failed, trying another way…`;
    default:
      return "Working…";
  }
}

/** Adds the wait that is still going on, so the timeline can draw it up to now. */
function openWaitingSpan(track: Track, status: AgentStatus, startedAt: number | null, lastRevisionAt: number | null): Span[] {
  if (status !== "waiting" || startedAt === null) return track.spans;
  const start = Math.max(startedAt, track.finishedAt ?? 0, lastRevisionAt ?? 0);
  return [...track.spans, { kind: "waiting", start, end: null }];
}

function closeSpan(track: Track, at: number): void {
  const open = track.spans.at(-1);
  if (open && open.end === null) open.end = at;
}

function emptyTrack(): Track {
  return {
    lastStartSeq: 0,
    lastFinishSeq: 0,
    lastFailSeq: 0,
    runs: 0,
    toolCalls: 0,
    startedAt: null,
    finishedAt: null,
    events: [],
    output: null,
    error: null,
    spans: [],
  };
}

const text = (value: unknown): string => (value === undefined || value === null ? "" : String(value));
