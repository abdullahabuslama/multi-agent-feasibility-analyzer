"""`GET /api/workflow`: the shape of the workflow, read from the YAML config.

The dashboard draws the graph from this, so a new agent or stage in
`config/tasks.yaml` appears in the dashboard without a frontend change.
"""

from fastapi import APIRouter

from api.schemas import AgentView, WorkflowView
from config.settings import load_agents_config, load_tasks_config

router = APIRouter(prefix="/api", tags=["workflow"])


@router.get("/workflow", response_model=WorkflowView)
def get_workflow() -> WorkflowView:
    workflow = load_tasks_config().workflow
    agents = load_agents_config()
    return WorkflowView(
        entry=workflow.entry,
        stages=workflow.stages,
        review_agent=workflow.review.agent,
        max_revisions=workflow.review.max_revisions,
        agents=[
            AgentView(name=name, role=agents[name].role, goal=agents[name].goal.strip(), tools=agents[name].tools)
            for name in [workflow.entry, *workflow.agents]
        ],
    )
