from pathlib import Path

from core.job import run_chapterfold_job
from core.schemas import ChapterfoldJobInput


def test_run_chapterfold_job_reports_missing_file(tmp_path):
    job = ChapterfoldJobInput(input_epub=tmp_path / "missing.epub", output_dir=tmp_path / "out")
    result = run_chapterfold_job(job)
    assert result.success is False
    assert result.stage == "validate"
    assert "does not exist" in (result.error or "")


def test_run_chapterfold_job_rejects_non_epub(tmp_path):
    src = tmp_path / "book.txt"
    src.write_text("not epub")
    job = ChapterfoldJobInput(input_epub=src, output_dir=tmp_path / "out")
    result = run_chapterfold_job(job)
    assert result.success is False
    assert result.stage == "validate"
    assert ".epub" in (result.error or "")
