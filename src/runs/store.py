"""Saves runs and their events in a SQLite file, so history survives restarts.

SQLite is not a server: it is one file (`RUNS_DB_PATH`, by default
`.runs/runs.sqlite`), read and written with Python's built-in `sqlite3`.
Each method opens the file, does its work, and closes it again. That is
fast, and it lets the run thread write while the API reads, because a
SQLite connection must not be shared between threads.
"""

import json
import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import closing, contextmanager
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from src.orchestrator.events import RunEvent
from src.orchestrator.state import BusinessIdea

SERVER_STOPPED_ERROR = "The server stopped before the run finished."

_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    idea TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    finished_at TEXT,
    result TEXT,
    error TEXT
);
CREATE TABLE IF NOT EXISTS events (
    run_id TEXT NOT NULL REFERENCES runs(id),
    seq INTEGER NOT NULL,
    kind TEXT NOT NULL,
    agent TEXT,
    at TEXT NOT NULL,
    detail TEXT NOT NULL,
    PRIMARY KEY (run_id, seq)
);
"""


class RunStatus(StrEnum):
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class RunRecord(BaseModel):
    id: str
    idea: BusinessIdea
    status: RunStatus
    created_at: datetime
    finished_at: datetime | None = None
    # The final state as plain JSON. The API turns it into its response model.
    result: dict[str, Any] | None = None
    error: str | None = None


class RunStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.executescript(_SCHEMA)

    def create_run(self, idea: BusinessIdea) -> RunRecord:
        run = RunRecord(id=str(uuid.uuid4()), idea=idea, status=RunStatus.RUNNING, created_at=_now())
        with self._connect() as db:
            db.execute(
                "INSERT INTO runs (id, idea, status, created_at) VALUES (?, ?, ?, ?)",
                (run.id, idea.model_dump_json(), run.status, run.created_at.isoformat()),
            )
        return run

    def finish_run(
        self,
        run_id: str,
        status: RunStatus,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        with self._connect() as db:
            db.execute(
                "UPDATE runs SET status = ?, finished_at = ?, result = ?, error = ? WHERE id = ?",
                (status, _now().isoformat(), json.dumps(result) if result else None, error, run_id),
            )

    def fail_unfinished_runs(self) -> None:
        """Mark runs that were still running when the server stopped. Call once at start-up."""
        with self._connect() as db:
            db.execute(
                "UPDATE runs SET status = ?, finished_at = ?, error = ? WHERE status = ?",
                (RunStatus.FAILED, _now().isoformat(), SERVER_STOPPED_ERROR, RunStatus.RUNNING),
            )

    def add_event(self, run_id: str, event: RunEvent) -> RunEvent:
        """Save `event` as the next event of the run and return it with its `seq`."""
        with self._connect() as db:
            (last_seq,) = db.execute("SELECT COALESCE(MAX(seq), 0) FROM events WHERE run_id = ?", (run_id,)).fetchone()
            saved = event.model_copy(update={"seq": last_seq + 1})
            db.execute(
                "INSERT INTO events (run_id, seq, kind, agent, at, detail) VALUES (?, ?, ?, ?, ?, ?)",
                (run_id, saved.seq, saved.kind, saved.agent, saved.at.isoformat(), json.dumps(saved.detail)),
            )
        return saved

    def get_run(self, run_id: str) -> RunRecord | None:
        with self._connect() as db:
            row = db.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        return _to_run(row) if row else None

    def list_runs(self, limit: int = 100) -> list[RunRecord]:
        """The latest runs first."""
        with self._connect() as db:
            rows = db.execute("SELECT * FROM runs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [_to_run(row) for row in rows]

    def events(self, run_id: str, after: int = 0) -> list[RunEvent]:
        """The run's events with a `seq` above `after`, in order."""
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM events WHERE run_id = ? AND seq > ? ORDER BY seq", (run_id, after)
            ).fetchall()
        return [
            RunEvent(seq=row["seq"], kind=row["kind"], agent=row["agent"], at=row["at"], detail=json.loads(row["detail"]))
            for row in rows
        ]

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        # `closing` closes the file; the inner `with` commits, or rolls back on an error.
        with closing(sqlite3.connect(self.path)) as connection:
            connection.row_factory = sqlite3.Row
            with connection:
                yield connection


def _to_run(row: sqlite3.Row) -> RunRecord:
    return RunRecord(
        id=row["id"],
        idea=BusinessIdea.model_validate_json(row["idea"]),
        status=row["status"],
        created_at=row["created_at"],
        finished_at=row["finished_at"],
        result=json.loads(row["result"]) if row["result"] else None,
        error=row["error"],
    )


def _now() -> datetime:
    return datetime.now(UTC)
