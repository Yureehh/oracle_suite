"""Verify the installed strixia-agon distribution and import boundary."""

from importlib.metadata import version

import strixia_agon


def test_installed_package() -> None:
    """The workspace installs the distribution and exposes the intended module."""
    assert version("strixia-agon") == "0.5.0"
    assert strixia_agon.__name__ == "strixia_agon"
