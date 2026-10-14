"""Probe artifact boundaries and explicit failure reporting, without benchmarking."""

import importlib.util
import multiprocessing as mp
import subprocess
from pathlib import Path

import pytest
from strixia_agon.pokemon.representation import (
    NUMERIC_FIELDS,
    SCALES,
    SCHEMA,
    Evidence,
    Features,
    Observation,
)

pytest.importorskip("torch")
spec = importlib.util.spec_from_file_location(
    "pokemon_models_probe",
    Path(__file__).resolve().parents[4] / "scripts/pokemon_models.py",
)
assert spec is not None and spec.loader is not None
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def test_output_is_exclusive_and_ignored(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        probe.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess([], 0)
    )
    destination = tmp_path / "new"
    probe.reserve_output(destination)
    sentinel = destination / "existing.json"
    sentinel.write_text("preserved")
    with pytest.raises(FileExistsError):
        probe.reserve_output(destination)
    assert sentinel.read_text() == "preserved"
    monkeypatch.setattr(
        probe.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess([], 1)
    )
    with pytest.raises(ValueError, match="ignored"):
        probe.reserve_output(tmp_path / "unignored")
    assert not (tmp_path / "unignored").exists()


def test_synthetic_history_and_explicit_case_failure() -> None:
    features = Features((1,), (0.0,) * len(NUMERIC_FIELDS), (3,) * len(NUMERIC_FIELDS))
    evidence = Evidence(1, 0, 1, "public", "synthetic", (), features, (features,))
    observation = Observation(
        SCHEMA, "synthetic", "p1", 1, 0, (features,) * 12, (), (evidence,), ()
    )
    repeated = probe.synthetic_history(observation, 256)
    assert len(repeated.history) == 256
    assert [e.sequence for e in repeated.history] == list(range(1, 257))
    assert all(e.context == evidence.context for e in repeated.history)
    assert (
        repeated.history[-1].features.values[NUMERIC_FIELDS.index("sequence")]
        == 256 / SCALES["sequence"]
    )
    reader, writer = mp.Pipe(duplex=False)
    probe._case(writer, observation, 3, "invalid", 1, "cpu", 17)
    result = reader.recv()
    reader.close()
    assert result["status"] == "failed"
    assert result["error_type"] == "ValueError"


def test_failed_matrix_is_saved_and_exits_nonzero_with_bounded_cleanup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exercise orchestration when a child returns failure but does not exit."""
    import json
    import sys
    from types import SimpleNamespace
    from typing import Any

    feature = Features((1,), (0.0,) * len(NUMERIC_FIELDS), (3,) * len(NUMERIC_FIELDS))
    evidence = Evidence(1, 0, 1, "public", "synthetic", (), feature, (feature,))
    observation = Observation(
        SCHEMA, "synthetic", "p1", 1, 0, (feature,) * 12, (), (evidence,), ()
    )

    class Pipe:
        def poll(self, timeout: float) -> bool:
            return True

        def recv(self) -> dict[str, str]:
            return {"status": "failed", "error": "controlled worker failure"}

        def close(self) -> None:
            pass

    class Process:
        exitcode = -9
        alive = True

        def __init__(self, **kwargs: Any) -> None:
            pass

        def start(self) -> None:
            pass

        def join(self, timeout: float | None = None) -> None:
            assert timeout is not None, "cleanup must not wait forever"

        def is_alive(self) -> bool:
            return self.alive

        def terminate(self) -> None:
            pass

        def kill(self) -> None:
            self.alive = False

    context = SimpleNamespace(Process=Process, Pipe=lambda **kwargs: (Pipe(), Pipe()))
    monkeypatch.setattr(probe.mp, "get_context", lambda _: context)
    monkeypatch.setattr(
        probe, "real_samples", lambda *a: (3, observation, observation, "synthetic")
    )
    monkeypatch.setattr(probe, "reserve_output", lambda path: path.mkdir())
    monkeypatch.setattr(sys, "argv", ["pokemon_models.py", str(tmp_path / "failed")])
    with pytest.raises(SystemExit) as exit:
        probe.main()
    assert exit.value.code == 1
    rows = json.loads((tmp_path / "failed/results.json").read_text())
    assert len(rows) == 36 and all(r["status"] == "failed" for r in rows)
    assert any(r["batch_size"] == 32 and r["history"] == 256 for r in rows)
