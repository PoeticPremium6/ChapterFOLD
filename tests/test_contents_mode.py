from __future__ import annotations

import pytest

from core.contents_mode import (
    normalize_contents_mode,
    should_generate_contents,
    should_strip_source_contents,
)
from core.schemas import ChapterfoldSettings


def test_contents_mode_helpers():
    assert normalize_contents_mode(None) == "rebuild"
    assert should_strip_source_contents("keep") is False
    assert should_strip_source_contents("remove") is True
    assert should_generate_contents("remove") is False
    assert should_generate_contents("rebuild") is True
    assert should_generate_contents("rebuild-paged") is True


def test_settings_validate_contents_mode():
    settings = ChapterfoldSettings(contents_mode="rebuild-paged")
    settings.validate()

    bad = ChapterfoldSettings(contents_mode="bad")
    with pytest.raises(ValueError):
        bad.validate()
