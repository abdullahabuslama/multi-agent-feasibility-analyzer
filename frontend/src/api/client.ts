/**
 * The one place that talks to the backend.
 *
 * Types come from `schema.d.ts`, which is generated from the FastAPI models
 * (`npm run gen:api` while the API runs), so they cannot drift from Python.
 */
import type { components } from "./schema";

type Schemas = components["schemas"];
export type Workflow = Schemas["WorkflowView"];
export type WorkflowAgent = Schemas["AgentView"];
export type RunSummary = Schemas["RunSummary"];
export type RunDetail = Schemas["RunDetail"];
export type RunEvent = Schemas["RunEvent"];
export type EventKind = Schemas["EventKind"];
export type RunStatus = Schemas["RunStatus"];
export type BusinessIdea = Schemas["BusinessIdea"];
export type AgentFinding = Schemas["AgentFinding"];
export type TaskPlan = Schemas["TaskPlan"];
export type ValidationResult = Schemas["ValidationResult"];
export type FinalReport = Schemas["FinalReport"];

/** After one of these, a run sends no more events. Mirrors FINAL_EVENT_KINDS in Python. */
export const FINAL_EVENT_KINDS: ReadonlySet<EventKind> = new Set(["run_finished", "run_failed"]);

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

export const getWorkflow = () => request<Workflow>("/api/workflow");
export const listRuns = () => request<RunSummary[]>("/api/runs");
export const getRun = (runId: string) => request<RunDetail>(`/api/runs/${runId}`);

export async function startRun(idea: BusinessIdea): Promise<string> {
  const created = await request<Schemas["RunCreated"]>("/api/runs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(idea),
  });
  return created.run_id;
}

export const eventsUrl = (runId: string, after: number) => `/api/runs/${runId}/events?after=${after}`;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  if (!response.ok) {
    throw new ApiError(await errorMessage(response), response.status);
  }
  return (await response.json()) as T;
}

/** FastAPI errors: `detail` is a string, or a list of field errors (422). */
async function errorMessage(response: Response): Promise<string> {
  try {
    const body = await response.json();
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) {
      return body.detail.map((item: { loc: string[]; msg: string }) => `${item.loc.at(-1)}: ${item.msg}`).join("\n");
    }
  } catch {
    // not JSON; fall through
  }
  return `Request failed (${response.status}).`;
}
