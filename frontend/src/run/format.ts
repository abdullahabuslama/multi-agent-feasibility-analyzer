/** Small text helpers shared by the views. */

/** How each tool reads in the dashboard. A new tool without an entry shows its own name. */
const TOOL_LABELS: Record<string, string> = {
  web_search: "Searching the web",
  search_company_docs: "Searching company documents",
};

export const toolLabel = (tool: string): string => TOOL_LABELS[tool] ?? tool;

/** "technical" -> "Technical" */
export const agentTitle = (name: string): string => name.charAt(0).toUpperCase() + name.slice(1);

export function formatDuration(ms: number): string {
  const seconds = Math.max(0, Math.round(ms / 1000));
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  return `${minutes}m ${String(seconds % 60).padStart(2, "0")}s`;
}

export const formatClock = (ms: number): string =>
  new Date(ms).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });

export const formatDateTime = (iso: string): string =>
  new Date(iso).toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
