"""Verify the installed strixia-core distribution and import boundary."""

from importlib.metadata import version

import strixia_core


def test_installed_package() -> None:
    """The workspace installs the distribution and exposes the intended module."""
    assert version("strixia-core") == "0.3.0"
    assert strixia_core.__name__ == "strixia_core"
