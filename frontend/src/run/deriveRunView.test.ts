import { beforeEach, describe, expect, it } from "vitest";

import type { EventKind, RunEvent, Workflow } from "../api/client";
import { deriveRunView } from "./deriveRunView";

const STAGES = [["technical", "financial", "competitor"], ["risk"], ["validator"], ["reporter"]];
const WORKFLOW: Workflow = {
  entry: "supervisor",
  stages: STAGES,
  review_agent: "validator",
  max_revisions: 2,
  agents: ["supervisor", ...STAGES.flat()].map((name) => ({ name, role: name, goal: "", tools: [] })),
};
const START_MS = Date.parse("2026-11-04T12:00:00Z");

let seq = 0;
function event(kind: EventKind, agent: string | null = null, detail: Record<string, unknown> = {}): RunEvent {
  seq += 1;
  return { seq, kind, agent, at: new Date(START_MS + seq * 1000).toISOString(), detail };
}
const started = (agent: string) => event("agent_started", agent);
const finished = (agent: string, output: Record<string, unknown> = {}) => event("agent_finished", agent, { output });
const validation = (revision_requests: string[]) => ({
  validation: { approved: !revision_requests.length, summary: "", issues: ["No source."], revision_requests },
});

/** Supervisor done, then the three analysts started. */
const analystsRunning = () => [
  event("run_started"),
  started("supervisor"),
  finished("supervisor", { plan: { summary: "Plan.", briefs: [] } }),
  started("technical"),
  started("financial"),
  started("competitor"),
];

beforeEach(() => {
  seq = 0;
});

describe("deriveRunView", () => {
  it("shows parallel analysts running and risk waiting for them", () => {
    const view = deriveRunView(WORKFLOW, analystsRunning(), "running");

    expect(view.phase).toBe("running");
    expect(view.agents.supervisor.status).toBe("done");
    expect(["technical", "financial", "competitor"].map((name) => view.agents[name].status)).toEqual([
      "running",
      "running",
      "running",
    ]);
    expect(view.agents.risk.status).toBe("waiting");
    expect(view.agents.risk.waitingOn).toEqual(["technical", "financial", "competitor"]);
    expect(view.agents.validator.waitingOn).toEqual(["risk"]);
    expect(view.plan?.summary).toBe("Plan.");
  });

  it("narrows who an agent waits for as earlier agents finish", () => {
    const events = [...analystsRunning(), finished("technical"), finished("financial")];

    const view = deriveRunView(WORKFLOW, events, "running");

    expect(view.agents.risk.waitingOn).toEqual(["competitor"]);
    expect(view.agents.risk.activity).toBe("Waiting for competitor");
  });

  it("marks agents the reviewer sent back, and the agents after them as waiting again", () => {
    const events = [
      ...analystsRunning(),
      ...["technical", "financial", "competitor"].map((name) => finished(name)),
      started("risk"),
      finished("risk"),
      started("validator"),
      finished("validator", validation(["technical"])),
    ];

    const view = deriveRunView(WORKFLOW, events, "running");

    expect(view.revisions).toBe(1);
    expect(view.agents.technical.status).toBe("sent_back");
    expect(view.agents.financial.status).toBe("done");
    expect(view.agents.risk.status).toBe("waiting");
    expect(view.agents.risk.waitingOn).toEqual(["technical"]);

    const rerun = deriveRunView(WORKFLOW, [...events, started("technical")], "running");
    expect(rerun.agents.technical.status).toBe("running");
    expect(rerun.agents.technical.runs).toBe(2);
  });

  it("shows a failed agent with its error and ends the run as failed", () => {
    const events = [
      ...analystsRunning(),
      event("agent_failed", "technical", { error: "model is down" }),
      event("run_failed", null, { error: "model is down" }),
    ];

    const view = deriveRunView(WORKFLOW, events, "failed");

    expect(view.phase).toBe("failed");
    expect(view.agents.technical.status).toBe("failed");
    expect(view.agents.technical.error).toBe("model is down");
    expect(view.agents.financial.status).toBe("stopped");
    expect(view.agents.financial.error).toBeNull();
    expect(view.agents.risk.status).toBe("not_started");
  });

  it("describes what a running agent is doing from its latest event", () => {
    const events = [
      ...analystsRunning(),
      event("tool_called", "competitor", { tool: "web_search", args: { query: "Shahry BNPL Egypt" } }),
    ];

    const view = deriveRunView(WORKFLOW, events, "running");

    expect(view.agents.competitor.activity).toBe("Searching the web: “Shahry BNPL Egypt”");
    expect(view.agents.competitor.toolCalls).toBe(1);
  });

  it("ends a run the server stopped as failed, even without a final event", () => {
    const view = deriveRunView(WORKFLOW, analystsRunning(), "failed");

    expect(view.phase).toBe("failed");
    expect(view.agents.technical.status).toBe("stopped");
    expect(view.finishedAt).not.toBeNull();
  });

  it("records how long an agent waited before it ran", () => {
    const events = [...analystsRunning(), ...STAGES[0].map((name) => finished(name)), started("risk")];

    const view = deriveRunView(WORKFLOW, events, "running");

    const [waiting, running] = view.agents.risk.spans;
    expect(waiting).toMatchObject({ kind: "waiting", start: view.startedAt });
    expect(running).toMatchObject({ kind: "running", end: null });
    expect(waiting.end).toBe(running.start);
  });
});
