"""HTTP API of the feasibility analyzer.

Start it from the project root:

    uvicorn api.app:app --reload

Then open http://127.0.0.1:8000/docs to try the endpoints.
"""

from uuid import uuid4

from fastapi import Depends, FastAPI
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel, SerializeAsAny

from api.dependencies import get_graph
from src.orchestrator.state import (
    AgentFinding,
    BusinessIdea,
    FinalReport,
    TaskPlan,
    ValidationResult,
)

app = FastAPI(
    title="Business Feasibility Analyzer",
    description="Multi-agent analysis of new e-commerce business ideas.",
    version="0.1.0",
)


class AnalysisResponse(BaseModel):
    """What the API returns: the run's id plus the final state.

    The fields have the same names as the keys of `FeasibilityState`, so the
    state is passed in as it is. This model stays separate from the state on
    purpose: it is the public API contract, and the state may grow internal
    keys that clients should not see. Unknown keys are ignored.
    """

    thread_id: str
    plan: TaskPlan | None = None
    # SerializeAsAny keeps extra fields of agent-specific finding subclasses.
    findings: dict[str, SerializeAsAny[AgentFinding]] = {}
    validation: ValidationResult | None = None
    revision_count: int = 0
    report: FinalReport | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyses", response_model=AnalysisResponse)
def create_analysis(
    idea: BusinessIdea, graph: CompiledStateGraph = Depends(get_graph)
) -> AnalysisResponse:
    """Run the full workflow for one idea and return everything it produced."""
    thread_id = str(uuid4())
    result = graph.invoke({"idea": idea}, config={"configurable": {"thread_id": thread_id}})
    return AnalysisResponse(thread_id=thread_id, **result)
