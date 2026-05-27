from __future__ import annotations

from core.schemas import ChapterfoldSettings


def test_settings_accept_page_ornament():
    settings = ChapterfoldSettings(page_ornament="floral-corner")
    settings.validate()

    assert settings.page_ornament == "floral-corner"


def test_settings_reject_unknown_page_ornament():
    settings = ChapterfoldSettings(page_ornament="bad")

    try:
        settings.validate()
    except ValueError as exc:
        assert "page_ornament" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_run_chapterfold_job_exposes_page_ornament_flag():
    text = open("scripts/run_chapterfold_job.py", encoding="utf-8").read()

    assert "--page-ornament" in text
    assert "botanical-leaf" in text
    assert "floral-corner" in text
    assert "gothic-flourish" in text
    assert "storybook" in text


def test_run_chapterfold_input_job_exposes_page_ornament_flag():
    text = open("scripts/run_chapterfold_input_job.py", encoding="utf-8").read()

    assert "--page-ornament" in text
    assert "classic-rule" in text
    assert "botanical-leaf" in text
