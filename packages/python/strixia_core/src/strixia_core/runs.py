"""Local run records; domain code owns execution and completion criteria."""

import hashlib
import json
import sqlite3
from pathlib import Path
from types import TracebackType
from typing import Any, Self
from uuid import uuid4


class RunError(ValueError):
    """A run operation conflicts with its persisted state or input."""


def _json(value: Any) -> str:
    def check(item: Any) -> None:
        if isinstance(item, dict):
            if any(not isinstance(key, str) for key in item):
                raise RunError("JSON object keys must be strings")
            for child in item.values():
                check(child)
        elif isinstance(item, list):
            for child in item:
                check(child)
        elif item is not None and not isinstance(item, (str, int, float, bool)):
            raise RunError("Only JSON values are supported")

    check(value)
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise RunError("Invalid finite JSON value") from exc


def _identifier(run_id: str) -> None:
    if not isinstance(run_id, str) or not run_id.strip():
        raise RunError("Nonempty run identifier is required")


class RunStore:
    """SQLite adapter. An exclusive execution lock is owned by the worker."""

    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self._path = path.resolve()
        self._db = sqlite3.connect(path, timeout=10)
        self._db.row_factory = sqlite3.Row
        try:
            version = self._db.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1):
                raise RunError(f"Unsupported schema version: {version}")
            self._db.execute("PRAGMA foreign_keys=ON")
            with self._db:
                self._db.execute("""CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY, submission_key TEXT UNIQUE NOT NULL,
                    config TEXT NOT NULL, config_hash TEXT NOT NULL,
                    status TEXT NOT NULL, attempt INTEGER NOT NULL DEFAULT 0,
                    error TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    started_at TEXT, finished_at TEXT)""")
                self._db.execute("""CREATE TABLE IF NOT EXISTS completed (
                    run_id TEXT NOT NULL REFERENCES runs(id), task_index INTEGER NOT NULL,
                    attempt INTEGER NOT NULL, manifest TEXT NOT NULL,
                    PRIMARY KEY(run_id, task_index))""")
                self._db.execute("""CREATE TABLE IF NOT EXISTS attempts (
                    run_id TEXT NOT NULL REFERENCES runs(id), attempt INTEGER NOT NULL,
                    status TEXT NOT NULL, error TEXT,
                    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    finished_at TEXT, PRIMARY KEY(run_id, attempt))""")
                self._db.execute("PRAGMA user_version=1")
        except Exception:
            self._db.close()
            raise

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._db.close()

    def submit(self, config: dict[str, Any], submission_key: str) -> str:
        if (
            not isinstance(config, dict)
            or not isinstance(submission_key, str)
            or not submission_key.strip()
        ):
            raise RunError(
                "A JSON config object and nonempty submission key are required"
            )
        encoded = _json(config)
        digest = hashlib.sha256(encoded.encode()).hexdigest()
        identifier = uuid4().hex
        with self._db:
            self._db.execute(
                """INSERT INTO runs
                (id, submission_key, config, config_hash, status)
                VALUES (?, ?, ?, ?, 'queued') ON CONFLICT(submission_key) DO NOTHING""",
                (identifier, submission_key, encoded, digest),
            )
            row = self._db.execute(
                "SELECT id, config FROM runs WHERE submission_key=?", (submission_key,)
            ).fetchone()
            if row["config"] != encoded:
                raise RunError("Submission key already has a different configuration")
            return str(row["id"])

    def get(self, run_id: str) -> dict[str, Any]:
        _identifier(run_id)
        row = self._db.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        if row is None:
            raise RunError("Unknown run")
        result = dict(row)
        if (
            hashlib.sha256(result["config"].encode()).hexdigest()
            != result["config_hash"]
        ):
            raise RunError("Stored configuration hash mismatch")
        result["config"] = json.loads(result["config"])
        result["attempts"] = [
            dict(row)
            for row in self._db.execute(
                "SELECT * FROM attempts WHERE run_id=? ORDER BY attempt", (run_id,)
            )
        ]
        return result

    def claim(self, run_id: str) -> int:
        _identifier(run_id)
        with self._db:
            cursor = self._db.execute(
                """UPDATE runs SET status='running',
                attempt=attempt+1, error=NULL, started_at=CURRENT_TIMESTAMP, finished_at=NULL
                WHERE id=? AND status='queued' """,
                (run_id,),
            )
            if cursor.rowcount != 1:
                raise RunError("Only queued runs can be claimed")
            attempt = int(self.get(run_id)["attempt"])
            self._db.execute(
                "INSERT INTO attempts (run_id, attempt, status) VALUES (?, ?, 'running')",
                (run_id, attempt),
            )
            return attempt

    def resume(self, run_id: str) -> None:
        _identifier(run_id)
        with self._db:
            self._db.execute("BEGIN IMMEDIATE")
            row = self.get(run_id)
            if row["status"] == "running":
                self._db.execute(
                    """UPDATE attempts SET status='interrupted',
                    finished_at=CURRENT_TIMESTAMP WHERE run_id=? AND attempt=?""",
                    (run_id, row["attempt"]),
                )
            cursor = self._db.execute(
                """UPDATE runs SET status='queued', error=NULL
                WHERE id=? AND status IN ('running','failed','cancelled','queued')""",
                (run_id,),
            )
            if cursor.rowcount != 1:
                raise RunError("Unknown or succeeded run cannot be resumed")

    def completed(self, run_id: str) -> dict[int, dict[str, Any]]:
        self.get(run_id)
        rows = self._db.execute(
            "SELECT task_index, manifest FROM completed WHERE run_id=? ORDER BY task_index",
            (run_id,),
        )
        return {row["task_index"]: json.loads(row["manifest"]) for row in rows}

    def record_game(
        self, run_id: str, attempt: int, index: int, manifest: dict[str, Any]
    ) -> None:
        if (
            type(index) is not int
            or index < 0
            or type(attempt) is not int
            or attempt < 1
        ):
            raise RunError("Nonnegative task index and positive attempt are required")
        if not isinstance(manifest, dict):
            raise RunError("Manifest must be a JSON object")
        encoded = _json(manifest)
        with self._db:
            self._db.execute("BEGIN IMMEDIATE")
            row = self.get(run_id)
            if row["attempt"] != attempt or row["status"] != "running":
                raise RunError("Stale or inactive attempt")
            previous = self._db.execute(
                "SELECT manifest FROM completed WHERE run_id=? AND task_index=?",
                (run_id, index),
            ).fetchone()
            if previous is not None:
                if previous["manifest"] != encoded:
                    raise RunError("Completed task publication conflicts")
                return
            self._db.execute(
                "INSERT INTO completed VALUES (?, ?, ?, ?)",
                (run_id, index, attempt, encoded),
            )

    def finish(
        self, run_id: str, attempt: int, status: str, error: str | None = None
    ) -> None:
        _identifier(run_id)
        if type(attempt) is not int or attempt < 1:
            raise RunError("Positive attempt is required")
        if error is not None and not isinstance(error, str):
            raise RunError("Error must be a string or None")
        if status not in ("succeeded", "failed", "cancelled"):
            raise RunError("Unsupported final status")
        with self._db:
            self._db.execute("BEGIN IMMEDIATE")
            row = self.get(run_id)
            if row["attempt"] != attempt:
                raise RunError("Stale attempt")
            if row["status"] != "running":
                if row["status"] == status and row["error"] == error:
                    return
                raise RunError("Inactive or conflicting attempt")
            self._db.execute(
                """UPDATE runs SET status=?, error=?,
                finished_at=CURRENT_TIMESTAMP WHERE id=?""",
                (status, error, run_id),
            )
            self._db.execute(
                """UPDATE attempts SET status=?, error=?,
                finished_at=CURRENT_TIMESTAMP WHERE run_id=? AND attempt=?""",
                (status, error, run_id, attempt),
            )

    def export_json(self, path: Path) -> None:
        with self._db:
            self._db.execute("BEGIN")
            payload = {
                "schema_version": 1,
                "runs": [
                    dict(row)
                    for row in self._db.execute("SELECT * FROM runs ORDER BY id")
                ],
                "attempts": [
                    dict(row)
                    for row in self._db.execute(
                        "SELECT * FROM attempts ORDER BY run_id, attempt"
                    )
                ],
                "completed": [
                    dict(row)
                    for row in self._db.execute(
                        "SELECT * FROM completed ORDER BY run_id, task_index"
                    )
                ],
            }
        if path.resolve() == self._path:
            raise RunError("Export must not overwrite the database")
        try:
            with path.open("x", encoding="utf-8") as stream:
                stream.write(_json(payload) + "\n")
        except FileExistsError as exc:
            raise RunError("Export destination must not exist") from exc

    def backup(self, path: Path) -> None:
        if path.resolve() == self._path or path.exists():
            raise RunError("Backup destination must be new and different from source")
        target = sqlite3.connect(path)
        try:
            self._db.backup(target)
        finally:
            target.close()
