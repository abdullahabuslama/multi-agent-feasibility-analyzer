/**
 * How each event reads in the activity list and the live log. One entry per
 * event kind, so a new kind is one new entry (TypeScript requires it).
 */
import type { EventKind, RunEvent } from "../api/client";
import { toolLabel } from "./format";

const detail = (event: RunEvent) => event.detail ?? {};

function toolInput(event: RunEvent): string {
  const args = (detail(event).args ?? {}) as Record<string, unknown>;
  return typeof args.query === "string" ? `“${args.query}”` : JSON.stringify(args);
}

export const EVENT_ICON: Record<EventKind, string> = {
  run_started: "▶",
  agent_started: "▶",
  llm_called: "✦",
  tool_called: "⚙",
  tool_returned: "↳",
  agent_finished: "✓",
  agent_failed: "✕",
  run_finished: "■",
  run_failed: "✕",
};

const EVENT_TEXT: Record<EventKind, (event: RunEvent) => string> = {
  run_started: () => "Run started",
  run_finished: () => "Run finished",
  run_failed: (event) => `Run failed: ${String(detail(event).error ?? "")}`,
  agent_started: () => "Started",
  agent_finished: () => "Finished",
  agent_failed: (event) => `Failed: ${String(detail(event).error ?? "")}`,
  llm_called: (event) =>
    detail(event).purpose === "final_answer" ? "Asked the LLM to write the finding" : "Asked the LLM what to look up",
  tool_called: (event) => `${toolLabel(String(detail(event).tool))} ${toolInput(event)}`,
  tool_returned: (event) =>
    detail(event).ok
      ? `${String(detail(event).tool)} returned ${Number(detail(event).characters ?? 0).toLocaleString()} characters`
      : `${String(detail(event).tool)} failed`,
};

export const describeEvent = (event: RunEvent): string => EVENT_TEXT[event.kind](event);
