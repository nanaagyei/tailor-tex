"""Verify that the package loads and version is set."""

from tailortex import __version__


def test_version_is_set() -> None:
    assert __version__ == "0.1.0"
