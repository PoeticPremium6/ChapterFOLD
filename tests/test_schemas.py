from pathlib import Path

import pytest

from core.schemas import ChapterfoldJobInput, ChapterfoldSettings


def test_default_settings_validate():
    settings = ChapterfoldSettings()
    settings.validate()
    assert settings.signature_size == 16
    assert settings.generate_clean_pdf is True


def test_signature_size_must_be_positive():
    settings = ChapterfoldSettings(signature_size=0)
    with pytest.raises(ValueError):
        settings.validate()


def test_signature_size_should_be_divisible_by_four():
    settings = ChapterfoldSettings(signature_size=10)
    with pytest.raises(ValueError):
        settings.validate()


def test_job_input_requires_existing_epub(tmp_path):
    missing = tmp_path / "missing.epub"
    job = ChapterfoldJobInput(input_epub=missing, output_dir=tmp_path / "out")
    with pytest.raises(FileNotFoundError):
        job.validate()


def test_job_input_creates_output_dir(tmp_path):
    epub = tmp_path / "book.epub"
    epub.write_bytes(b"dummy")
    out = tmp_path / "out"
    job = ChapterfoldJobInput(input_epub=epub, output_dir=out)
    job.validate()
    assert out.exists()
