from pathlib import Path

import pytest
from strixia_core.artifacts import ArtifactError, Artifacts


def test_integrity_and_duplicate(tmp_path: Path) -> None:
    artifacts = Artifacts(tmp_path)
    manifest = artifacts.write("abc", 1, 0, b"events")
    assert artifacts.read(manifest) == b"events"
    assert artifacts.write("abc", 1, 0, b"events") == manifest
    with pytest.raises(ArtifactError):
        artifacts.write("abc", 1, 0, b"different")
    path = tmp_path / manifest["path"]
    path.write_bytes(b"changed")
    with pytest.raises(ArtifactError):
        artifacts.read(manifest)
    path.unlink()
    with pytest.raises(ArtifactError):
        artifacts.read(manifest)
    assert not list(tmp_path.rglob("*.tmp"))


def test_paths(tmp_path: Path) -> None:
    artifacts = Artifacts(tmp_path / "private")
    with pytest.raises(ArtifactError):
        artifacts.write("../outside", 1, 0, b"events")
    with pytest.raises(ArtifactError):
        artifacts.write("okay", 0, 0, b"events")
    with pytest.raises(ArtifactError):
        artifacts.read({"path": "../outside", "size": 0, "sha256": ""})
    outside = tmp_path / "outside"
    outside.mkdir()
    (tmp_path / "private" / "escape").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ArtifactError):
        artifacts.write("escape", 1, 0, b"events")


def test_failed_publication_cleans_temporary_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import os

    def fail_link(source: str, target: Path) -> None:
        raise OSError("injected disk failure")

    artifacts = Artifacts(tmp_path)
    monkeypatch.setattr(os, "link", fail_link)
    with pytest.raises(ArtifactError, match="write failed"):
        artifacts.write("run", 1, 0, b"events")
    assert not list(tmp_path.rglob("*.tmp"))
    assert not list(tmp_path.rglob("*.json"))
