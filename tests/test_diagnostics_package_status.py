from __future__ import annotations

import sys
from importlib import metadata

import core.diagnostics as diagnostics


def _packages_from_environment_info(info):
    if isinstance(info, dict):
        return info["packages"]
    return info.packages


def test_diagnostics_prefers_importability_when_metadata_missing(monkeypatch) -> None:
    def missing_metadata(_name: str) -> str:
        raise metadata.PackageNotFoundError(_name)

    monkeypatch.setattr(metadata, "version", missing_metadata)
    monkeypatch.setattr(sys, "frozen", True, raising=False)

    info = diagnostics.get_environment_info()
    packages = _packages_from_environment_info(info)

    # Exact version strings are also valid. The regression we care about is
    # preventing bundled/importable packages from being reported as not installed.
    for label, status in packages.items():
        assert status != "not installed", f"{label} was incorrectly reported as not installed"
        assert status, f"{label} returned an empty package status"


def test_diagnostics_uses_correct_import_names_for_distribution_labels() -> None:
    assert diagnostics._chapterfold_package_status("docx", "python-docx") != "not installed"
    assert diagnostics._chapterfold_package_status("bs4", "beautifulsoup4") != "not installed"
    assert diagnostics._chapterfold_package_status("ebooklib", "EbookLib") != "not installed"
