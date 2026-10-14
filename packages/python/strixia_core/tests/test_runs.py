import json
import sqlite3
from pathlib import Path

import pytest
from strixia_core.runs import RunError, RunStore


def test_run_progress_and_fencing(tmp_path: Path) -> None:
    path = tmp_path / "runs.db"
    with RunStore(path) as store:
        run = store.submit({"games": 3}, "batch")
        assert store.submit({"games": 3}, "batch") == run
        with pytest.raises(RunError):
            store.submit({"games": 4}, "batch")
        attempt = store.claim(run)
        with RunStore(path) as other, pytest.raises(RunError):
            other.claim(run)
        store.record_game(run, attempt, 2, {"sha256": "a"})
        store.record_game(run, attempt, 2, {"sha256": "a"})
        with pytest.raises(RunError):
            store.record_game(run, attempt, 2, {"sha256": "b"})
    with RunStore(path) as store:
        assert store.completed(run) == {2: {"sha256": "a"}}
        store.resume(run)
        second = store.claim(run)
        assert store.get(run)["attempts"][0]["status"] == "interrupted"
        assert store.get(run)["attempts"][0]["finished_at"]
        assert second == attempt + 1
        with pytest.raises(RunError):
            store.record_game(run, attempt, 0, {})
        with pytest.raises(RunError):
            store.finish(run, attempt, "succeeded")
        store.record_game(run, second, 0, {"sha256": "c"})
        store.finish(run, second, "succeeded")
        with pytest.raises(RunError):
            store.resume(run)
        assert store.get(run)["status"] == "succeeded"


def test_export_backup_and_version(tmp_path: Path) -> None:
    with RunStore(tmp_path / "runs.db") as store:
        run = store.submit({"seed": [1, 2]}, "key")
        store.export_json(tmp_path / "export.json")
        store.backup(tmp_path / "backup.db")
    exported = json.loads((tmp_path / "export.json").read_text())
    assert exported["schema_version"] == 1
    with RunStore(tmp_path / "backup.db") as backup:
        assert backup.get(run)["config"] == {"seed": [1, 2]}
    with sqlite3.connect(tmp_path / "future.db") as connection:
        connection.execute("PRAGMA user_version=2")
    with pytest.raises(RunError, match="version"):
        RunStore(tmp_path / "future.db")


def test_inputs_and_failure_resume(tmp_path: Path) -> None:
    with RunStore(tmp_path / "runs.db") as store:
        with pytest.raises(RunError):
            store.submit({"bad": float("nan")}, "bad")
        with pytest.raises(RunError):
            store.submit({1: "bad"}, "bad")  # type: ignore[dict-item]
        with pytest.raises(RunError):
            store.submit({}, "")
        run = store.submit({}, "okay")
        with pytest.raises(RunError):
            store.get("missing")
        attempt = store.claim(run)
        store.finish(run, attempt, "failed", "engine failure")
        store.resume(run)
        assert store.get(run)["error"] is None
        assert store.completed(run) == {}


def test_concurrent_claim_has_one_winner(tmp_path: Path) -> None:
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    path = tmp_path / "race.db"
    with RunStore(path) as store:
        run = store.submit({}, "race")
    barrier = Barrier(2)

    def claim() -> int | None:
        with RunStore(path) as store:
            barrier.wait(timeout=5)
            try:
                return store.claim(run)
            except RunError:
                return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: claim(), range(2)))
    assert outcomes.count(1) == 1
    assert outcomes.count(None) == 1


def test_corrupt_config_detected(tmp_path: Path) -> None:
    path = tmp_path / "runs.db"
    with RunStore(path) as store:
        run = store.submit({}, "key")
    with sqlite3.connect(path) as connection:
        connection.execute(
            "UPDATE runs SET config=? WHERE id=?", ('{"changed":true}', run)
        )
    with RunStore(path) as store, pytest.raises(RunError, match="hash"):
        store.get(run)


def test_cancelled_resume_and_invalid_publication(tmp_path: Path) -> None:
    with RunStore(tmp_path / "runs.db") as store:
        run = store.submit({}, "cancel")
        attempt = store.claim(run)
        with pytest.raises(RunError):
            store.record_game(run, attempt, -1, {})
        with pytest.raises(RunError):
            store.record_game(run, True, 0, {})
        with pytest.raises(RunError):
            store.finish(run, True, "succeeded")
        with pytest.raises(RunError):
            store.finish(run, attempt, "unknown")
        assert store.completed(run) == {}
        store.finish(run, attempt, "cancelled")
        store.resume(run)
        assert store.claim(run) == attempt + 1


def test_finish_idempotency_and_attempt_history(tmp_path: Path) -> None:
    path = tmp_path / "history.db"
    with RunStore(path) as store:
        run = store.submit({}, "history")
        first = store.claim(run)
        store.finish(run, first, "failed", "engine failed")
        store.finish(run, first, "failed", "engine failed")
        with pytest.raises(RunError):
            store.finish(run, first, "failed", "changed error")
        with pytest.raises(RunError):
            store.finish(run, first, "succeeded")
        store.resume(run)
        second = store.claim(run)
        with pytest.raises(RunError):
            store.finish(run, first, "failed", "engine failed")
        store.finish(run, second, "succeeded")
    with RunStore(path) as store:
        record = store.get(run)
        assert record["created_at"]
        assert record["finished_at"]
        history = record["attempts"]
        assert [attempt["status"] for attempt in history] == ["failed", "succeeded"]
        assert history[0]["error"] == "engine failed"
        assert all(
            attempt["started_at"] and attempt["finished_at"] for attempt in history
        )
        store.export_json(tmp_path / "history.json")
        store.backup(tmp_path / "history-backup.db")
        with pytest.raises(RunError):
            store.backup(path.parent / "." / path.name)
    assert len(json.loads((tmp_path / "history.json").read_text())["attempts"]) == 2
    with RunStore(tmp_path / "history-backup.db") as backup:
        assert backup.get(run)["attempts"] == history


def test_export_cannot_overwrite_database_or_file(tmp_path: Path) -> None:
    path = tmp_path / "runs.db"
    with RunStore(path) as store:
        run = store.submit({}, "keep")
        with pytest.raises(RunError, match="overwrite"):
            store.export_json(path)
        existing = tmp_path / "existing.json"
        existing.write_text("keep")
        with pytest.raises(RunError, match="exist"):
            store.export_json(existing)
        assert existing.read_text() == "keep"
        assert store.get(run)["status"] == "queued"


def test_backup_reserves_destination_exclusively(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    destination = tmp_path / "backup.db"
    with RunStore(destination) as competing:
        kept = competing.submit({"keep": True}, "competing")
    original = destination.read_bytes()
    exists = Path.exists
    # Reproduce another writer winning after a stale existence check.
    monkeypatch.setattr(
        Path, "exists", lambda p: False if p == destination else exists(p)
    )
    with RunStore(tmp_path / "source.db") as store:
        store.submit({}, "source")
        with pytest.raises(RunError, match="destination"):
            store.backup(destination)
    assert destination.read_bytes() == original
    with RunStore(destination) as competing:
        assert competing.get(kept)["config"] == {"keep": True}
