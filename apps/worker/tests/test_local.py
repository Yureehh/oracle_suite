"""Coordinator contracts and a real pinned-engine batch."""

from __future__ import annotations

import importlib.util
import json
import threading
from pathlib import Path
from typing import Any

import pytest
from strixia_core.artifacts import ArtifactError, Artifacts
from strixia_core.runs import RunError, RunStore

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location(
    "local_worker", ROOT / "apps/worker/local.py"
)
assert spec is not None and spec.loader is not None
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)


def submit(storage: Path, games: int = 4) -> str:
    with RunStore(storage / "runs.sqlite3") as store:
        return store.submit(worker.configuration(None, games, [1, 2, 3, 4]), "batch")


def test_seed_schedule_and_bounds() -> None:
    assert worker.game_seed([1, 2, 3, 4], 0) == worker.game_seed([1, 2, 3, 4], 0)
    assert worker.game_seed([1, 2, 3, 4], 0) != worker.game_seed([1, 2, 3, 4], 1)
    with pytest.raises(ValueError):
        worker.game_seed([1, 2, 3, -1], 0)
    with pytest.raises(ValueError):
        worker.configuration(None, True, [1, 2, 3, 4])


def test_parallel_cancel_and_resume(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(worker, "validate_runtime", lambda *_: None)
    run_id = submit(tmp_path)
    barrier = threading.Barrier(2)
    stop = threading.Event()
    started: list[int] = []

    def first(config: dict[str, Any], index: int, checkout: Path) -> bytes:
        started.append(index)
        barrier.wait(timeout=5)
        stop.set()
        return json.dumps({"index": index}).encode()

    result = worker.execute(tmp_path, run_id, ROOT, 2, stop=stop, game=first)
    assert result["status"] == "cancelled"
    assert sorted(started) == [0, 1]
    with RunStore(tmp_path / "runs.sqlite3") as store:
        saved = store.completed(run_id)
        assert set(saved) == {0, 1}
    resumed: list[int] = []

    def remaining(config: dict[str, Any], index: int, checkout: Path) -> bytes:
        resumed.append(index)
        return json.dumps({"index": index}).encode()

    result = worker.execute(tmp_path, run_id, ROOT, 2, resume=True, game=remaining)
    assert result["status"] == "succeeded" and result["attempt"] == 2
    assert sorted(resumed) == [2, 3]
    with RunStore(tmp_path / "runs.sqlite3") as store:
        assert all(
            store.completed(run_id)[i] == manifest for i, manifest in saved.items()
        )


def test_out_of_order_crash_progress(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(worker, "validate_runtime", lambda *_: None)
    run_id = submit(tmp_path)
    with RunStore(tmp_path / "runs.sqlite3") as store:
        attempt = store.claim(run_id)
        manifest = Artifacts(tmp_path / "artifacts").write(
            run_id, attempt, 2, b"completed"
        )
        store.record_game(run_id, attempt, 2, manifest)
    resumed: list[int] = []

    def game(config: dict[str, Any], index: int, checkout: Path) -> bytes:
        resumed.append(index)
        return str(index).encode()

    assert (
        worker.execute(tmp_path, run_id, ROOT, 2, resume=True, game=game)["status"]
        == "succeeded"
    )
    assert sorted(resumed) == [0, 1, 3]


def test_lock_and_failure_integrity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(worker, "validate_runtime", lambda *_: None)
    run_id = submit(tmp_path, 2)
    with worker.run_lock(tmp_path, run_id), pytest.raises(RunError, match="Another"):
        worker.execute(tmp_path, run_id, ROOT)

    def broken(config: dict[str, Any], index: int, checkout: Path) -> bytes:
        raise RuntimeError("demonstration failure")

    result = worker.execute(tmp_path, run_id, ROOT, 1, game=broken)
    assert result["status"] == "failed" and "demonstration failure" in result["error"]
    with RunStore(tmp_path / "runs.sqlite3") as store:
        assert store.completed(run_id) == {}
        store.resume(run_id)
        attempt = store.claim(run_id)
        manifest = Artifacts(tmp_path / "artifacts").write(run_id, attempt, 0, b"good")
        store.record_game(run_id, attempt, 0, manifest)
    (tmp_path / "artifacts" / manifest["path"]).write_bytes(b"bad")
    with pytest.raises(ArtifactError):
        worker.execute(tmp_path, run_id, ROOT, resume=True)
    with RunStore(tmp_path / "runs.sqlite3") as store:
        assert store.get(run_id)["attempt"] == attempt


def test_real_engine_batch(tmp_path: Path) -> None:
    checkout = ROOT / "tmp/pokemon-foundation/showdown"
    if not (checkout / "dist/sim/index.js").exists():
        pytest.skip("Prepare pinned engine")
    run_id = submit(tmp_path, 3)
    result = worker.execute(tmp_path, run_id, checkout, 2)
    assert result["status"] == "succeeded"
    with RunStore(tmp_path / "runs.sqlite3") as store:
        manifests = store.completed(run_id)
        assert set(manifests) == {0, 1, 2}
    artifacts = Artifacts(tmp_path / "artifacts")
    for index, manifest in manifests.items():
        trace = json.loads(artifacts.read(manifest))
        assert trace["game"] == index
        assert trace["seed"] == result["config"]["seeds"][index]
        assert trace["winner"] in ("p1", "p2")
        assert trace["choices"][0] == ["team 1234", "team 1234"]


def test_process_death_preserves_completed_games(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import selectors
    import subprocess
    import sys

    monkeypatch.setattr(worker, "validate_runtime", lambda *_: None)
    run_id = submit(tmp_path, 2)
    script = tmp_path / "crash_worker.py"
    script.write_text(
        "import importlib.util, threading\n"
        f"spec=importlib.util.spec_from_file_location('worker', {str(ROOT / 'apps/worker/local.py')!r})\n"
        "module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)\n"
        "module.validate_runtime=lambda *_: None\n"
        "def game(config,index,checkout):\n"
        " if index==1: threading.Event().wait(60)\n"
        " return str(index).encode()\n"
        f"module.execute(module.Path({str(tmp_path)!r}), {run_id!r}, module.Path('.'), 1, game=game)\n"
    )
    process = subprocess.Popen(
        [sys.executable, str(script)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert process.stdout is not None
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            assert selector.select(timeout=10), "Worker did not publish first game"
            assert "saved game 1" in process.stdout.readline()
        process.kill()
        process.wait(timeout=5)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        process.stdout.close()
        assert process.stderr is not None
        process.stderr.close()
    with RunStore(tmp_path / "runs.sqlite3") as store:
        assert store.get(run_id)["status"] == "running"
        assert set(store.completed(run_id)) == {0}
    executed: list[int] = []

    def remainder(config: dict[str, Any], index: int, checkout: Path) -> bytes:
        executed.append(index)
        return str(index).encode()

    assert (
        worker.execute(tmp_path, run_id, ROOT, 1, resume=True, game=remainder)["status"]
        == "succeeded"
    )
    assert executed == [1]


def test_frozen_runtime_and_lock_provenance(tmp_path: Path) -> None:
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    lock = checkout / "package-lock.json"
    lock.write_bytes(
        (ROOT / "scripts/pokemon_foundation/showdown-package-lock.json").read_bytes()
    )
    config = worker.configuration(None, 2, [1, 2, 3, 4])
    worker.validate_runtime(config, checkout)
    for changed in (
        config | {"npm_lock_sha256": "0" * 64},
        config | {"npm_lock_sha256": None},
        config | {"python_version": "different"},
        config | {"node_version": "different"},
    ):
        with pytest.raises(RunError):
            worker.validate_runtime(changed, checkout)
    missing = dict(config)
    del missing["npm_lock_sha256"]
    with pytest.raises(RunError, match="submission"):
        worker.validate_runtime(missing, checkout)
    lock.write_text("changed")
    with pytest.raises(RunError, match="submission"):
        worker.validate_runtime(config, checkout)
