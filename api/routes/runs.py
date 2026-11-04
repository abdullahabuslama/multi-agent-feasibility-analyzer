"""`/api/runs`: start runs, list them, and stream their live events.

The live stream uses Server-Sent Events (SSE): one long HTTP response that
sends each event as a few lines of text the moment it is saved. Every event
carries its `seq` as the SSE `id`, so a browser that loses the connection
reconnects with `Last-Event-ID` and gets only what it missed.
"""

import asyncio
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse

from api.dependencies import get_run_service, get_run_store
from api.schemas import AnalysisResponse, RunCreated, RunDetail, RunSummary
from src.orchestrator.events import FINAL_EVENT_KINDS
from src.orchestrator.state import BusinessIdea
from src.runs.service import RunService
from src.runs.store import RunRecord, RunStatus, RunStore

POLL_SECONDS = 0.25
# Proxies close a silent connection after a while; a comment line keeps it open.
KEEP_ALIVE_SECONDS = 15

router = APIRouter(prefix="/api/runs", tags=["runs"])


@router.post("", status_code=202, response_model=RunCreated)
def start_run(idea: BusinessIdea, service: RunService = Depends(get_run_service)) -> RunCreated:
    """Start an analysis in the background. Follow it with the events endpoint."""
    return RunCreated(run_id=service.start(idea))


@router.get("", response_model=list[RunSummary])
def list_runs(store: RunStore = Depends(get_run_store)) -> list[RunSummary]:
    """Past and running analyses, the latest first."""
    return [_summary(run) for run in store.list_runs()]


@router.get("/{run_id}", response_model=RunDetail)
def get_run(run_id: str, store: RunStore = Depends(get_run_store)) -> RunDetail:
    """One run with all its events so far, and its result once it is done."""
    run = _require_run(store, run_id)
    result = AnalysisResponse(thread_id=run.id, **run.result) if run.result else None
    return RunDetail(**_summary(run).model_dump(), events=store.events(run_id), result=result)


@router.get("/{run_id}/events", response_class=StreamingResponse)
async def stream_events(
    run_id: str,
    after: int = 0,
    last_event_id: str | None = Header(default=None),
    store: RunStore = Depends(get_run_store),
) -> StreamingResponse:
    """Live events of a run as Server-Sent Events. Ends when the run ends."""
    _require_run(store, run_id)
    start_after = max(after, int(last_event_id or 0))
    return StreamingResponse(
        _event_stream(store, run_id, start_after),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _event_stream(store: RunStore, run_id: str, after: int) -> AsyncIterator[str]:
    quiet_seconds = 0.0
    while True:
        events = await asyncio.to_thread(store.events, run_id, after)
        for event in events:
            yield f"id: {event.seq}\ndata: {event.model_dump_json()}\n\n"
            after = event.seq
            if event.kind in FINAL_EVENT_KINDS:
                return
        if not events and await asyncio.to_thread(_has_ended, store, run_id):
            return  # ended without a final event, for example a server stop
        quiet_seconds = 0.0 if events else quiet_seconds + POLL_SECONDS
        if quiet_seconds >= KEEP_ALIVE_SECONDS:
            yield ": keep-alive\n\n"
            quiet_seconds = 0.0
        await asyncio.sleep(POLL_SECONDS)


def _has_ended(store: RunStore, run_id: str) -> bool:
    run = store.get_run(run_id)
    return run is None or run.status != RunStatus.RUNNING


def _require_run(store: RunStore, run_id: str) -> RunRecord:
    run = store.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"No run with id '{run_id}'.")
    return run


def _summary(run: RunRecord) -> RunSummary:
    return RunSummary(**run.model_dump(exclude={"result"}))
