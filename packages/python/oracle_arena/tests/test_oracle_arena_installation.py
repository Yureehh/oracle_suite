"""Verify the installed oracle-arena distribution and import boundary."""

from importlib.metadata import version

import oracle_arena


def test_installed_package() -> None:
    """The workspace installs the distribution and exposes the intended module."""
    assert version("oracle-arena") == "0.1.0"
    assert oracle_arena.__name__ == "oracle_arena"
