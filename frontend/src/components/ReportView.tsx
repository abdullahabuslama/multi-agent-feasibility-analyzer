import Markdown from "react-markdown";

import type { FinalReport } from "../api/client";

export function ReportView({ report }: { report: FinalReport | null }) {
  if (!report) return <p className="p-6 text-sm text-slate-500">The report appears here when the reporter finishes.</p>;
  return (
    <article className="prose prose-slate mx-auto h-full max-w-3xl overflow-y-auto p-6 dark:prose-invert">
      <Markdown>{report.markdown}</Markdown>
    </article>
  );
}
