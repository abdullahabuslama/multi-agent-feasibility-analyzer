/**
 * Shows what an agent posted. Each kind of output has its own card, picked by
 * which key the output has (`findings`, `validation`, `plan`, `report`).
 * A new kind of output is one new entry in OUTPUT_CARDS.
 */
import type { ReactNode } from "react";

import type { AgentFinding, FinalReport, TaskPlan, ValidationResult } from "../api/client";
import type { AgentOutput } from "../run/deriveRunView";
import { agentTitle } from "../run/format";

/** Fields every AgentFinding has. Anything else came from an agent's own subclass. */
const STANDARD_FINDING_FIELDS = new Set(["agent", "status", "summary", "score", "assumptions", "evidence"]);

const OUTPUT_CARDS: [keyof AgentOutput, (output: AgentOutput, agent: string) => ReactNode][] = [
  ["findings", (output, agent) => <FindingCard finding={output.findings![agent]} />],
  ["validation", (output) => <ValidationCard validation={output.validation!} />],
  ["plan", (output) => <PlanCard plan={output.plan!} />],
  ["report", (output) => <ReportNote report={output.report!} />],
];

export function OutputView({ output, agent }: { output: AgentOutput | null; agent: string }) {
  const card = output && OUTPUT_CARDS.find(([key]) => output[key] !== undefined);
  if (!card) return <Empty>Nothing yet. The output appears when the agent finishes.</Empty>;
  return <>{card[1](output, agent)}</>;
}

function FindingCard({ finding }: { finding: (AgentFinding & Record<string, unknown>) | undefined }) {
  if (!finding) return <Empty>No finding.</Empty>;
  const extra = Object.entries(finding).filter(([key]) => !STANDARD_FINDING_FIELDS.has(key));
  return (
    <div className="space-y-4 text-sm">
      <p className="leading-relaxed">{finding.summary}</p>
      {finding.score != null && <ScoreBar score={finding.score} />}
      <Section title={`Assumptions (${finding.assumptions?.length ?? 0})`}>
        <ul className="list-disc space-y-1 pl-5">
          {finding.assumptions?.map((assumption) => <li key={assumption}>{assumption}</li>)}
        </ul>
      </Section>
      <Section title={`Evidence (${finding.evidence?.length ?? 0})`}>
        <ul className="space-y-2">
          {finding.evidence?.map((item) => (
            <li key={`${item.source}:${item.snippet}`} className="rounded border border-slate-200 p-2 dark:border-slate-700">
              <SourceLink source={item.source} />
              <p className="mt-1 text-slate-600 dark:text-slate-300">{item.snippet}</p>
            </li>
          ))}
        </ul>
      </Section>
      {extra.length > 0 && (
        <Section title="More fields">
          <pre className="overflow-x-auto rounded bg-slate-100 p-2 text-xs dark:bg-slate-800">
            {JSON.stringify(Object.fromEntries(extra), null, 2)}
          </pre>
        </Section>
      )}
    </div>
  );
}

function ValidationCard({ validation }: { validation: ValidationResult }) {
  return (
    <div className="space-y-4 text-sm">
      <p className="font-medium">{validation.approved ? "✓ Approved" : "↩ Changes requested"}</p>
      <p>{validation.summary}</p>
      {!!validation.revision_requests?.length && (
        <Section title="Sent back to">
          <p>{validation.revision_requests.map(agentTitle).join(", ")}</p>
        </Section>
      )}
      {!!validation.issues?.length && (
        <Section title="Issues">
          <ul className="list-disc space-y-1 pl-5">
            {validation.issues.map((issue) => <li key={issue}>{issue}</li>)}
          </ul>
        </Section>
      )}
    </div>
  );
}

export function PlanCard({ plan }: { plan: TaskPlan }) {
  return (
    <div className="space-y-4 text-sm">
      <p className="leading-relaxed">{plan.summary}</p>
      {plan.briefs.map((brief) => (
        <Section key={brief.agent} title={agentTitle(brief.agent)}>
          <p className="leading-relaxed">{brief.instructions}</p>
        </Section>
      ))}
    </div>
  );
}

function ReportNote({ report }: { report: FinalReport }) {
  return (
    <p className="text-sm">
      The report is ready ({report.markdown.length.toLocaleString()} characters). Open the <b>Report</b> tab to read it.
    </p>
  );
}

function ScoreBar({ score }: { score: number }) {
  return (
    <div>
      <div className="mb-1 flex justify-between text-xs text-slate-500">
        <span>Feasibility score</span>
        <span className="font-semibold text-slate-900 dark:text-slate-100">{score.toFixed(1)} / 10</span>
      </div>
      <div className="h-2 rounded bg-slate-200 dark:bg-slate-700">
        <div className="h-2 rounded bg-emerald-500" style={{ width: `${score * 10}%` }} />
      </div>
    </div>
  );
}

function SourceLink({ source }: { source: string }) {
  if (!/^https?:\/\//.test(source)) return <span className="font-mono text-xs">{source}</span>;
  return (
    <a href={source} target="_blank" rel="noreferrer" className="break-all text-xs text-sky-700 underline dark:text-sky-400">
      {source}
    </a>
  );
}

export function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section>
      <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">{title}</h4>
      {children}
    </section>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return <p className="text-sm text-slate-500">{children}</p>;
}
