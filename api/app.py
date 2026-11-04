"""HTTP API of the feasibility analyzer, and the dashboard it serves.

Start it from the project root:

    uvicorn api.app:app --reload

Then open http://127.0.0.1:8000/docs to try the endpoints. After
`npm run build` in `frontend/`, the dashboard is at http://127.0.0.1:8000/.
"""

from fastapi import FastAPI

from api.routes import analyses, runs, workflow
from api.static import SinglePageApp
from config.settings import PROJECT_ROOT

FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"

app = FastAPI(
    title="Business Feasibility Analyzer",
    description="Multi-agent analysis of new e-commerce business ideas.",
    version="0.1.0",
)
app.include_router(analyses.router)
app.include_router(runs.router)
app.include_router(workflow.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# Mounted last, so the API routes above always win.
if FRONTEND_DIST.is_dir():
    app.mount("/", SinglePageApp(directory=FRONTEND_DIST, html=True), name="dashboard")
