/**
 * The live workflow graph. Columns come from the workflow stages, the same
 * way `src/orchestrator/graph.py` connects them: every agent in a column
 * feeds every agent in the next one. The dashed edges at the bottom are the
 * review loop, from the reviewer back to the agents it can send work to.
 */
import "@xyflow/react/dist/style.css";

import { Background, Controls, type Edge, MarkerType, ReactFlow } from "@xyflow/react";
import { useMemo } from "react";

import type { RunView } from "../run/deriveRunView";
import { AgentNode, type AgentNodeType, LOOP_IN, LOOP_OUT } from "./AgentNode";

const COLUMN_WIDTH = 290;
const ROW_HEIGHT = 160;
const NODE_TYPES = { agent: AgentNode };

const EDGE_COLOR = { idle: "#94a3b8", flowing: "#0ea5e9", blocking: "#f59e0b", loop: "#8b5cf6" };

interface Props {
  view: RunView;
  reviewAgent: string;
  selected: string | null;
  now: number;
  onSelect: (agent: string) => void;
}

export function WorkflowGraph({ view, reviewAgent, selected, now, onSelect }: Props) {
  const nodes = useMemo<AgentNodeType[]>(
    () =>
      view.columns.flatMap((column, columnIndex) =>
        column.map((name, row) => ({
          id: name,
          type: "agent",
          position: { x: columnIndex * COLUMN_WIDTH, y: (row - (column.length - 1) / 2) * ROW_HEIGHT },
          data: { agent: view.agents[name], selected: selected === name, now },
          draggable: false,
        })),
      ),
    [view, selected, now],
  );

  const edges = useMemo(() => [...stageEdges(view), ...reviewEdges(view, reviewAgent)], [view, reviewAgent]);

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      nodeTypes={NODE_TYPES}
      onNodeClick={(_, node) => onSelect(node.id)}
      fitView
      fitViewOptions={{ padding: 0.2 }}
      nodesConnectable={false}
      proOptions={{ hideAttribution: true }}
      colorMode="system"
      minZoom={0.3}
    >
      <Background gap={24} />
      <Controls showInteractive={false} />
    </ReactFlow>
  );
}

/** Edges between consecutive columns. Coloured by what flows along them right now. */
function stageEdges(view: RunView): Edge[] {
  return view.columns.slice(1).flatMap((targets, index) =>
    view.columns[index].flatMap((source) =>
      targets.map((target) => {
        const flowing = view.agents[target].status === "running" && view.agents[source].status === "done";
        const blocking = view.agents[target].waitingOn.includes(source);
        const color = flowing ? EDGE_COLOR.flowing : blocking ? EDGE_COLOR.blocking : EDGE_COLOR.idle;
        return {
          id: `${source}->${target}`,
          source,
          target,
          animated: flowing,
          style: { stroke: color, strokeWidth: flowing || blocking ? 2 : 1 },
          markerEnd: { type: MarkerType.ArrowClosed, color },
        };
      }),
    ),
  );
}

/** Dashed edges from the reviewer back to the agents it can send work to. */
function reviewEdges(view: RunView, reviewAgent: string): Edge[] {
  const reviewColumn = view.agents[reviewAgent]?.column ?? 0;
  const targets = view.columns.slice(1, reviewColumn).flat();
  return targets.map((target, index) => {
    const active = view.agents[target].status === "sent_back";
    return {
      id: `${reviewAgent}~>${target}`,
      source: reviewAgent,
      target,
      sourceHandle: LOOP_OUT,
      targetHandle: LOOP_IN,
      type: "smoothstep",
      animated: active,
      label: index === 0 ? "revision" : undefined,
      labelStyle: { fill: EDGE_COLOR.loop, fontSize: 11 },
      style: { stroke: EDGE_COLOR.loop, strokeDasharray: "6 4", strokeWidth: active ? 2 : 1, opacity: active ? 1 : 0.45 },
      markerEnd: { type: MarkerType.ArrowClosed, color: EDGE_COLOR.loop },
    };
  });
}
