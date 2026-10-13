"""Immutable private local artifacts with content integrity checks."""

import hashlib
import os
import re
import tempfile
from pathlib import Path
from typing import Any


class ArtifactError(ValueError):
    """An artifact is invalid, missing, conflicting or corrupt."""


class Artifacts:
    def __init__(self, root: Path):
        root.mkdir(parents=True, exist_ok=True)
        self.root = root.resolve()

    def _path(self, name: str) -> Path:
        path = (self.root / name).resolve()
        if not path.is_relative_to(self.root) or path == self.root:
            raise ArtifactError("Artifact path escapes its root")
        return path

    def write(
        self, run_id: str, attempt: int, index: int, data: bytes
    ) -> dict[str, Any]:
        if (
            not isinstance(run_id, str)
            or re.fullmatch(r"[A-Za-z0-9_-]+", run_id) is None
        ):
            raise ArtifactError("Invalid run identifier")
        if (
            type(attempt) is not int
            or attempt < 1
            or type(index) is not int
            or index < 0
        ):
            raise ArtifactError("Positive attempt and nonnegative index are required")
        if not isinstance(data, bytes):
            raise ArtifactError("Artifact content must be bytes")
        name = f"{run_id}/attempt-{attempt}/game-{index}.json"
        path = self._path(name)
        manifest = {
            "path": name,
            "sha256": hashlib.sha256(data).hexdigest(),
            "size": len(data),
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(suffix=".tmp", dir=path.parent)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                os.link(
                    temporary, path
                )  # Atomic publication without replacing a winner.
            except FileExistsError:
                if self.read(manifest) != data:
                    raise ArtifactError("Artifact publication conflicts") from None
            parent = path.parent
            while True:
                directory = os.open(parent, os.O_RDONLY)
                try:
                    os.fsync(directory)
                finally:
                    os.close(directory)
                if parent == self.root:
                    break
                parent = parent.parent
        except OSError as exc:
            raise ArtifactError(f"Artifact write failed: {exc}") from exc
        finally:
            Path(temporary).unlink(missing_ok=True)
        return manifest

    def read(self, manifest: dict[str, Any]) -> bytes:
        if not isinstance(manifest, dict):
            raise ArtifactError("Invalid manifest")
        name, size, digest = (manifest.get(key) for key in ("path", "size", "sha256"))
        if (
            not isinstance(name, str)
            or Path(name).is_absolute()
            or type(size) is not int
            or size < 0
            or not isinstance(digest, str)
            or re.fullmatch(r"[a-f0-9]{64}", digest) is None
        ):
            raise ArtifactError("Invalid manifest fields")
        path = self._path(name)
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise ArtifactError(f"Artifact cannot be read: {exc}") from exc
        if len(data) != size or hashlib.sha256(data).hexdigest() != digest:
            raise ArtifactError("Artifact size or hash mismatch")
        return data
