"""Runs: saved events, history that survives a restart, and the runs API."""

import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

from api.app import app
from api.static import SinglePageApp
from config.settings import load_tasks_config
from src.agents.technical import TechnicalAgent
from src.memory.short_term import get_checkpointer
from src.orchestrator.events import EventKind
from src.orchestrator.graph import build_graph
from src.runs.service import RunService
from src.runs.store import SERVER_STOPPED_ERROR, RunStatus, RunStore
from tests.conftest import SAMPLE_IDEA

ANALYSTS = {"technical", "financial", "competitor", "risk"}


def run_service(store: RunStore) -> RunService:
    return RunService(build_graph(get_checkpointer()), store)


def read_sse(client: TestClient, url: str, headers: dict[str, str] | None = None) -> tuple[list[int], list[dict]]:
    """The `id:` values and the parsed `data:` events of an SSE response."""
    with client.stream("GET", url, headers=headers or {}) as response:
        assert response.headers["content-type"].startswith("text/event-stream")
        lines = list(response.iter_lines())
    ids = [int(line.removeprefix("id: ")) for line in lines if line.startswith("id: ")]
    events = [json.loads(line.removeprefix("data: ")) for line in lines if line.startswith("data: ")]
    return ids, events


def test_run_saves_every_agent_start_and_finish_in_order(run_store: RunStore) -> None:
    run_id, _ = run_service(run_store).run_and_wait(SAMPLE_IDEA)

    events = run_store.events(run_id)
    started = [e.agent for e in events if e.kind == EventKind.AGENT_STARTED]
    finished = [e.agent for e in events if e.kind == EventKind.AGENT_FINISHED]
    assert (events[0].kind, events[-1].kind) == (EventKind.RUN_STARTED, EventKind.RUN_FINISHED)
    assert [e.seq for e in events] == list(range(1, len(events) + 1))
    assert (started[0], started[-1]) == ("supervisor", "reporter")
    assert set(started) == set(finished) == {"supervisor", "validator", "reporter", *ANALYSTS}
    assert run_store.get_run(run_id).status == RunStatus.DONE


def test_finished_event_carries_the_agent_output(run_store: RunStore) -> None:
    run_id, _ = run_service(run_store).run_and_wait(SAMPLE_IDEA)

    finished = next(
        e for e in run_store.events(run_id) if e.kind == EventKind.AGENT_FINISHED and e.agent == "technical"
    )
    assert finished.detail["output"]["findings"]["technical"]["status"] == "done"


def test_tool_calls_are_saved_under_the_calling_agent(run_store: RunStore, fake_llm, memory_store) -> None:
    fake_llm.tool_replies = [
        AIMessage("", tool_calls=[{"name": "search_company_docs", "args": {"query": "refunds"}, "id": "c1"}])
    ]

    run_id, _ = run_service(run_store).run_and_wait(SAMPLE_IDEA)

    events = run_store.events(run_id)
    called = [e for e in events if e.kind == EventKind.TOOL_CALLED]
    returned = [e for e in events if e.kind == EventKind.TOOL_RETURNED]
    assert {e.agent for e in called} == {e.agent for e in returned} == ANALYSTS
    assert called[0].detail == {"tool": "search_company_docs", "args": {"query": "refunds"}}
    # The in-memory knowledge base is empty, so the tool fails and says why.
    assert returned[0].detail["ok"] is False
    assert "knowledge base is empty" in returned[0].detail["preview"]


def test_failed_agent_ends_the_run_as_failed(run_store: RunStore, monkeypatch: pytest.MonkeyPatch) -> None:
    def broken_analyze(self, state):
        raise RuntimeError("model is down")

    monkeypatch.setattr(TechnicalAgent, "analyze", broken_analyze)

    with pytest.raises(RuntimeError):
        run_service(run_store).run_and_wait(SAMPLE_IDEA)

    run = run_store.list_runs()[0]
    events = run_store.events(run.id)
    failure = next(e for e in events if e.kind == EventKind.AGENT_FAILED)
    assert (failure.agent, failure.detail["error"]) == ("technical", "model is down")
    assert events[-1].kind == EventKind.RUN_FAILED
    assert run.status == RunStatus.FAILED


def test_history_survives_a_restart(run_store: RunStore) -> None:
    run_id, _ = run_service(run_store).run_and_wait(SAMPLE_IDEA)

    reopened = RunStore(run_store.path)

    assert reopened.get_run(run_id).status == RunStatus.DONE
    assert reopened.events(run_id) == run_store.events(run_id)


def test_runs_left_running_by_a_stopped_server_are_marked_failed(run_store: RunStore) -> None:
    run = run_store.create_run(SAMPLE_IDEA)

    run_store.fail_unfinished_runs()

    saved = run_store.get_run(run.id)
    assert (saved.status, saved.error) == (RunStatus.FAILED, SERVER_STOPPED_ERROR)


def test_started_run_streams_its_events_then_closes(run_store: RunStore) -> None:
    client = TestClient(app)

    response = client.post("/api/runs", json=SAMPLE_IDEA.model_dump())
    assert response.status_code == 202
    run_id = response.json()["run_id"]
    ids, events = read_sse(client, f"/api/runs/{run_id}/events")

    assert ids == list(range(1, len(ids) + 1))
    assert events[-1]["kind"] == "run_finished"
    detail = client.get(f"/api/runs/{run_id}").json()
    assert detail["status"] == "done"
    assert len(detail["events"]) == len(events)
    assert detail["result"]["report"]["markdown"]


def test_reconnect_with_last_event_id_gets_only_missed_events(run_store: RunStore) -> None:
    run_id, _ = run_service(run_store).run_and_wait(SAMPLE_IDEA)

    ids, _ = read_sse(TestClient(app), f"/api/runs/{run_id}/events", headers={"Last-Event-ID": "3"})

    assert ids[0] == 4


def test_runs_list_shows_the_latest_first(run_store: RunStore) -> None:
    service = run_service(run_store)
    first, _ = service.run_and_wait(SAMPLE_IDEA)
    second, _ = service.run_and_wait(SAMPLE_IDEA)

    runs = TestClient(app).get("/api/runs").json()

    assert [run["id"] for run in runs] == [second, first]


def test_unknown_run_is_404() -> None:
    assert TestClient(app).get("/api/runs/no-such-run").status_code == 404


def test_workflow_endpoint_describes_stages_and_agents() -> None:
    body = TestClient(app).get("/api/workflow").json()

    workflow = load_tasks_config().workflow
    assert body["stages"] == workflow.stages
    assert body["review_agent"] == workflow.review.agent
    assert [agent["name"] for agent in body["agents"]] == [workflow.entry, *workflow.agents]
    assert "web_search" in next(a for a in body["agents"] if a["name"] == "competitor")["tools"]


def test_dashboard_paths_fall_back_to_the_app_but_api_paths_do_not(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("<html>dashboard</html>", encoding="utf-8")
    site = FastAPI()
    site.mount("/", SinglePageApp(directory=tmp_path, html=True))
    client = TestClient(site)

    assert client.get("/runs/some-id").text == "<html>dashboard</html>"
    assert client.get("/api/no-such-endpoint").status_code == 404
