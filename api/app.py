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
    return AnalysisResponse(
        thread_id=thread_id,
        plan=result.get("plan"),
        findings=result.get("findings", {}),
        validation=result.get("validation"),
        revision_count=result.get("revision_count", 0),
        report=result.get("report"),
    )
