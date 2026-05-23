from __future__ import annotations

from dataclasses import dataclass

from core.diagnostics import build_diagnostic_report, sanitize_path


@dataclass
class DummySettings:
    trim_size: str = "A5"
    signature_size: int = 16


def test_sanitize_path_returns_filename_only():
    assert sanitize_path("/home/example/private/My Book.epub") == "My Book.epub"


def test_build_diagnostic_report_contains_environment_and_settings():
    report = build_diagnostic_report(
        app_version="test-version",
        stage="unit-test",
        input_path="/private/path/Test.epub",
        output_dir="/private/output",
        settings=DummySettings(),
    )

    assert "ChapterFOLD Diagnostic Report" in report
    assert "App version: test-version" in report
    assert "Stage: unit-test" in report
    assert "Input filename: Test.epub" in report
    assert "trim_size: A5" in report
    assert "signature_size: 16" in report
    assert "/private/path" not in report


def test_build_diagnostic_report_accepts_error_string():
    report = build_diagnostic_report(error="Something failed")
    assert "Error" in report
    assert "Something failed" in report
