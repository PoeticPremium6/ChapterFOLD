from __future__ import annotations

from core.diagnostics import _package_version


def test_package_version_prefers_importability():
    status = _package_version("json", "json")

    assert status.startswith("OK")


def test_package_version_reports_missing_import():
    status = _package_version("definitely_missing_chapterfold_module_12345")

    assert status.startswith("not importable")
