from __future__ import annotations

from pathlib import Path

import pytest

from core.job_workspace import (
    create_job_workspace,
    ensure_child_path,
    safe_slug,
    validate_input_file,
)


def test_safe_slug_cleans_user_text():
    assert safe_slug("My Fancy Book!!!") == "my-fancy-book"
    assert safe_slug("...") == "chapterfold-job"


def test_validate_input_file_accepts_supported_file(tmp_path):
    source = tmp_path / "book.epub"
    source.write_bytes(b"fake epub bytes")

    result = validate_input_file(source, max_size_mb=1)

    assert result.path == source
    assert result.suffix == ".epub"
    assert result.size_bytes > 0


def test_validate_input_file_rejects_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        validate_input_file(tmp_path / "missing.epub")


def test_validate_input_file_rejects_unsupported_suffix(tmp_path):
    source = tmp_path / "book.exe"
    source.write_bytes(b"bad")

    with pytest.raises(ValueError, match="Unsupported input file type"):
        validate_input_file(source)


def test_validate_input_file_rejects_large_file(tmp_path):
    source = tmp_path / "book.pdf"
    source.write_bytes(b"x" * 2048)

    with pytest.raises(ValueError, match="too large"):
        validate_input_file(source, max_size_mb=0.001)


def test_create_job_workspace_creates_isolated_folders(tmp_path):
    workspace = create_job_workspace(
        tmp_path,
        job_id="ABC123",
        label="My Book",
    )

    assert workspace.job_id == "my-book-abc123"
    assert workspace.input_dir.exists()
    assert workspace.output_dir.exists()
    assert workspace.reports_dir.exists()


def test_ensure_child_path_accepts_child(tmp_path):
    parent = tmp_path / "root"
    child = parent / "nested" / "file.txt"
    child.parent.mkdir(parents=True)
    child.write_text("x", encoding="utf-8")

    assert ensure_child_path(parent, child) == child.resolve()


def test_ensure_child_path_rejects_escape(tmp_path):
    parent = tmp_path / "root"
    outside = tmp_path / "outside.txt"
    parent.mkdir()
    outside.write_text("x", encoding="utf-8")

    with pytest.raises(ValueError, match="escapes"):
        ensure_child_path(parent, outside)
