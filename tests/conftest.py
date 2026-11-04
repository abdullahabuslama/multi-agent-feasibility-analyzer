"""Shared test fixtures. Tests use no network and no API key.

- `fake_llm`: every agent gets a fake chat model with canned answers. Set
  `fake_llm.tool_replies` to make it ask for tools first.
- `memory_store`: Qdrant runs in memory with fake embeddings, so no model
  is downloaded and nothing is written to disk.
- `run_store`: every test saves runs in its own temporary SQLite file,
  never in the real run history.
"""

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel
from qdrant_client import QdrantClient

from api.app import app
from api.dependencies import get_run_store
from src.agents import base as agents_base
from src.memory import long_term
from src.orchestrator.state import AgentBrief, AgentFinding, BusinessIdea, FindingStatus, TaskPlan
from src.runs.store import RunStore

SAMPLE_IDEA = BusinessIdea(
    idea="Add an AI chat assistant that answers 'Where is my order?' questions.",
    context="Pilot budget around EGP 1.5 million.",
)

FAKE_PLAN = TaskPlan(
    summary="Decide whether an AI order-tracking assistant is worth a pilot.",
    briefs=[
        AgentBrief(agent="technical", instructions="Check the Orders API and help desk."),
        AgentBrief(agent="financial", instructions="Compare cost to support savings."),
        AgentBrief(agent="not_an_agent", instructions="Should be dropped."),
    ],
)

# Signed with a wrong name and status on purpose: the agent must overwrite both.
FAKE_FINDING = AgentFinding(agent="written-by-llm", status=FindingStatus.PENDING, summary="Canned finding.")


class FakeChatModel:
    """Stands in for a real chat model.

    `with_structured_output` returns a canned answer per output model and
    keeps the messages it was given in `seen`. `bind_tools` replays
    `tool_replies` in order, then answers without asking for a tool.
    """

    def __init__(self, answers: dict[type[BaseModel], BaseModel]) -> None:
        self.answers = answers
        self.tool_replies: list[AIMessage] = []
        self.seen: list[list[BaseMessage]] = []

    def with_structured_output(self, schema: type[BaseModel], **_: Any) -> RunnableLambda:
        def answer(messages: list[BaseMessage]) -> BaseModel:
            self.seen.append(messages)
            return self.answers[schema]

        return RunnableLambda(answer)

    def bind_tools(self, _tools: list[Any], **_: Any) -> RunnableLambda:
        replies = iter(self.tool_replies)
        return RunnableLambda(lambda _messages: next(replies, AIMessage("Research done.")))


@pytest.fixture(autouse=True)
def fake_llm(monkeypatch: pytest.MonkeyPatch) -> FakeChatModel:
    model = FakeChatModel({TaskPlan: FAKE_PLAN, AgentFinding: FAKE_FINDING})
    monkeypatch.setattr(agents_base, "get_chat_model", lambda _params=None: model)
    return model


@pytest.fixture
def memory_store(monkeypatch: pytest.MonkeyPatch) -> QdrantClient:
    client = QdrantClient(":memory:")
    embeddings = DeterministicFakeEmbedding(size=64)
    monkeypatch.setattr(long_term, "get_client", lambda: client)
    monkeypatch.setattr(long_term, "get_embeddings", lambda: embeddings)
    return client


@pytest.fixture(autouse=True)
def run_store(tmp_path: Path) -> Iterator[RunStore]:
    store = RunStore(tmp_path / "runs.sqlite")
    app.dependency_overrides[get_run_store] = lambda: store
    yield store
    app.dependency_overrides.pop(get_run_store, None)
