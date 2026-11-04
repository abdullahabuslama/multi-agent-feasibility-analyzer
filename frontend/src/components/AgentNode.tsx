/** One agent card in the workflow graph. */
import { Handle, type Node, type NodeProps, Position } from "@xyflow/react";

import { type AgentView, runningTime } from "../run/deriveRunView";
import { agentTitle, formatDuration } from "../run/format";
import { STATUS_STYLE } from "../run/statusStyle";
import { StatusBadge } from "./StatusBadge";

export type AgentNodeData = { agent: AgentView; selected: boolean; now: number };
export type AgentNodeType = Node<AgentNodeData, "agent">;

/** Handle ids for the review loop, which leaves and enters cards at the bottom. */
export const LOOP_OUT = "loop-out";
export const LOOP_IN = "loop-in";

export function AgentNode({ data }: NodeProps<AgentNodeType>) {
  const { agent, selected, now } = data;
  const style = STATUS_STYLE[agent.status];
  const time = runningTime(agent, now);
  return (
    <div
      className={`w-56 cursor-pointer rounded-lg border-2 bg-white p-3 shadow-sm transition dark:bg-slate-900 ${style.border} ${
        selected ? "outline outline-2 outline-offset-2 outline-slate-900 dark:outline-slate-100" : ""
      }`}
    >
      <Handle type="target" position={Position.Left} className="!bg-slate-400" />
      <Handle type="source" position={Position.Right} className="!bg-slate-400" />
      <Handle id={LOOP_IN} type="target" position={Position.Bottom} className="!opacity-0" />
      <Handle id={LOOP_OUT} type="source" position={Position.Bottom} className="!opacity-0" />

      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="font-semibold">{agentTitle(agent.name)}</p>
          <p className="truncate text-xs text-slate-500" title={agent.role}>
            {agent.role}
          </p>
        </div>
        <StatusBadge style={style} pulse={agent.status === "running"} />
      </div>

      <p className="mt-2 line-clamp-2 min-h-[2rem] text-xs text-slate-700 dark:text-slate-300" title={agent.activity ?? ""}>
        {agent.activity ?? (agent.status === "done" ? "Finished" : "")}
      </p>

      <div className="mt-2 flex gap-3 text-[11px] text-slate-500">
        {time > 0 && <span title="Time spent running">⏱ {formatDuration(time)}</span>}
        {agent.toolCalls > 0 && <span title="Tool calls">⚙ {agent.toolCalls}</span>}
        {agent.runs > 1 && <span title="Times this agent ran">↻ {agent.runs}</span>}
      </div>
    </div>
  );
}
