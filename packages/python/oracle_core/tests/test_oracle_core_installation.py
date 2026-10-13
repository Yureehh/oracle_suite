"""Verify the installed oracle-core distribution and import boundary."""

from importlib.metadata import version

import oracle_core


def test_installed_package() -> None:
    """The workspace installs the distribution and exposes the intended module."""
    assert version("oracle-core") == "0.1.0"
    assert oracle_core.__name__ == "oracle_core"
