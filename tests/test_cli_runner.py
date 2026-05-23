from __future__ import annotations

import json
import subprocess
import sys
from argparse import Namespace
from pathlib import Path

import pytest

from core.schemas import ChapterfoldSettings
from scripts import run_chapterfold_job as cli


def _base_args(**overrides):
    data = dict(
        settings_json=None,
        variant=None,
        export_docx=False,
        export_markdown=False,
        paragraph_spacing_mode=None,
        margin_preset=None,
        page_size_preset=None,
        impose=False,
        signature_pages=None,
        binding_direction=None,
        max_end_padding=None,
        custom_trim_width_cm=None,
        custom_trim_height_cm=None,
        custom_margin_top_cm=None,
        custom_margin_bottom_cm=None,
        custom_margin_inside_cm=None,
        custom_margin_outside_cm=None,
    )
    data.update(overrides)
    return Namespace(**data)


def test_build_settings_uses_defaults():
    settings = cli.build_settings(_base_args())
    assert isinstance(settings, ChapterfoldSettings)
    assert settings.variant == "standard"


def test_build_settings_accepts_cli_overrides():
    settings = cli.build_settings(
        _base_args(
            variant="aggressive-cleanup",
            export_docx=True,
            impose=True,
            signature_pages=20,
            binding_direction="rtl",
        )
    )
    assert settings.variant == "aggressive-cleanup"
    assert settings.export_docx is True
    assert settings.create_imposed_pdf is True
    assert settings.imposed_pages_per_signature == 20
    assert settings.binding_direction == "rtl"


def test_build_settings_loads_json_then_overrides(tmp_path):
    settings_file = tmp_path / "settings.json"
    settings_file.write_text(json.dumps({"variant": "standard", "export_markdown": True}), encoding="utf-8")
    settings = cli.build_settings(_base_args(settings_json=settings_file, variant="paragraph-dialogue-merge"))
    assert settings.variant == "paragraph-dialogue-merge"
    assert settings.export_markdown is True


def test_build_settings_rejects_unknown_json_key(tmp_path):
    settings_file = tmp_path / "settings.json"
    settings_file.write_text(json.dumps({"not_real": True}), encoding="utf-8")
    with pytest.raises(ValueError, match="Unknown setting"):
        cli.build_settings(_base_args(settings_json=settings_file))


def test_cli_help_runs():
    completed = subprocess.run(
        [sys.executable, "scripts/run_chapterfold_job.py", "--help"],
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0
    assert "Run a ChapterFOLD EPUB conversion" in completed.stdout
