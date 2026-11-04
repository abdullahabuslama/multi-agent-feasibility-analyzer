"""`POST /analyses`: run one analysis and wait for the result.

For scripts and `curl`. The dashboard uses `/api/runs` instead, which
returns at once and streams the progress. Both run through `RunService`,
so an analysis started here also shows up in the dashboard's history.
"""

from fastapi import APIRouter, Depends

from api.dependencies import get_run_service
from api.schemas import AnalysisResponse
from src.orchestrator.state import BusinessIdea
from src.runs.service import RunService

router = APIRouter(tags=["analyses"])


@router.post("/analyses", response_model=AnalysisResponse)
def create_analysis(idea: BusinessIdea, service: RunService = Depends(get_run_service)) -> AnalysisResponse:
    """Run the full workflow for one idea and return everything it produced."""
    run_id, state = service.run_and_wait(idea)
    return AnalysisResponse(thread_id=run_id, **state)
