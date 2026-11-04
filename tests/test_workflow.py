"""Integration tests: the full graph, and the API on top of it."""

import pytest
from fastapi.testclient import TestClient

from api.app import app
from config.settings import load_tasks_config
from src.agents.technical import TechnicalAgent
from src.agents.validator import ValidatorAgent
from src.memory.short_term import get_checkpointer
from src.orchestrator.graph import build_graph
from src.orchestrator.router import route_after_review
from src.orchestrator.state import ValidationResult
from tests.conftest import SAMPLE_IDEA

RUN_CONFIG = {"configurable": {"thread_id": "test"}}


def test_full_run_collects_every_output() -> None:
    result = build_graph(get_checkpointer()).invoke({"idea": SAMPLE_IDEA}, RUN_CONFIG)

    assert set(result["findings"]) == {"technical", "financial", "competitor", "risk"}
    assert result["plan"].summary
    assert result["validation"].approved
    assert result["report"].markdown.startswith("# Feasibility report")
    assert result.get("revision_count", 0) == 0


def test_revision_loop_stops_at_max_revisions(monkeypatch: pytest.MonkeyPatch) -> None:
    max_revisions = load_tasks_config().workflow.review.max_revisions
    always_reject = ValidationResult(
        approved=False, summary="Missing evidence.", revision_requests=["technical"]
    )
    monkeypatch.setattr(ValidatorAgent, "analyze", lambda self, state: always_reject)
    technical_runs = []
    original_analyze = TechnicalAgent.analyze

    def counting_analyze(self, state):
        technical_runs.append(state)
        return original_analyze(self, state)

    monkeypatch.setattr(TechnicalAgent, "analyze", counting_analyze)

    result = build_graph(get_checkpointer()).invoke({"idea": SAMPLE_IDEA}, RUN_CONFIG)

    assert len(technical_runs) == 1 + max_revisions
    assert result["report"] is not None


def test_router_reruns_only_the_earliest_requested_stage() -> None:
    state = {
        "validation": ValidationResult(
            approved=False, summary="", revision_requests=["risk", "financial"]
        ),
        "revision_count": 1,
    }

    targets = route_after_review(
        state,
        stages_before_review=[["technical", "financial", "competitor"], ["risk"]],
        next_stage=["reporter"],
        max_revisions=2,
    )

    assert targets == ["financial"]


def test_api_runs_an_analysis() -> None:
    client = TestClient(app)

    response = client.post("/analyses", json=SAMPLE_IDEA.model_dump())

    assert response.status_code == 200
    body = response.json()
    assert body["thread_id"]
    assert set(body["findings"]) == {"technical", "financial", "competitor", "risk"}
    assert body["report"]["markdown"]


def test_api_rejects_too_short_idea() -> None:
    response = TestClient(app).post("/analyses", json={"idea": "short"})

    assert response.status_code == 422
