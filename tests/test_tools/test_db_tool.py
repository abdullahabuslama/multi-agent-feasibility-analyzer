from pathlib import Path

import pytest

from config.settings import get_settings
from src.memory import ingest
from src.tools import TOOL_REGISTRY, resolve_tools
from src.tools.db_tool import search_company_docs

REFUND_TEXT = "Refunds above EGP 5,000 need a human approval."
DELIVERY_TEXT = "Express orders are delivered the next day in Cairo."


@pytest.fixture
def knowledge_base(tmp_path: Path) -> Path:
    (tmp_path / "refunds.md").write_text(REFUND_TEXT, encoding="utf-8")
    (tmp_path / "delivery.md").write_text(DELIVERY_TEXT, encoding="utf-8")
    (tmp_path / "notes.csv").write_text("not a supported type", encoding="utf-8")
    return tmp_path


def test_ingest_skips_unsupported_files(knowledge_base: Path) -> None:
    sources = [doc.metadata["source"] for doc in ingest.load_documents(knowledge_base)]

    assert sources == ["delivery.md", "refunds.md"]


def test_search_returns_matching_passage_with_source(memory_store, knowledge_base: Path) -> None:
    ingest.ingest(knowledge_base, rebuild=True)

    result = search_company_docs.invoke({"query": REFUND_TEXT})

    assert result.startswith("[source: refunds.md]")


def test_ingest_twice_does_not_duplicate_chunks(memory_store, knowledge_base: Path) -> None:
    first = ingest.ingest(knowledge_base)
    ingest.ingest(knowledge_base)

    collection = get_settings().qdrant_collection
    assert memory_store.count(collection).count == first


def test_search_tool_is_registered() -> None:
    assert "search_company_docs" in TOOL_REGISTRY


def test_unknown_tool_name_fails_early() -> None:
    with pytest.raises(KeyError):
        resolve_tools(["no_such_tool"])
