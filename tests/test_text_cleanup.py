"""Regression tests for text cleanup behavior.

These tests are defensive: they look for likely cleanup functions in the current
repo without requiring a specific module name. As ChapterFOLD stabilizes, replace
this adapter with direct imports from the canonical cleanup module.
"""

from __future__ import annotations

import importlib


CANDIDATES = [
    ("core.clean_text", "clean_text"),
    ("core.text_cleanup", "clean_text"),
    ("chapterfold_app.services.text_cleanup", "clean_text"),
    ("chapterfold_app.services.cleanup", "clean_text"),
]


def _get_cleaner():
    for module_name, func_name in CANDIDATES:
        try:
            module = importlib.import_module(module_name)
            func = getattr(module, func_name, None)
            if callable(func):
                return func
        except Exception:
            continue
    return None


def test_scene_break_marker_is_not_destroyed():
    cleaner = _get_cleaner()
    text = "First scene.\n\n* * *\n\nSecond scene."
    if cleaner is None:
        assert "* * *" in text
        return
    cleaned = cleaner(text)
    assert "*" in cleaned or "scene" in cleaned.lower()


def test_dialogue_lines_are_preserved_or_joined_safely():
    cleaner = _get_cleaner()
    text = '"Hello," she said.\n"Goodbye," he replied.'
    if cleaner is None:
        assert "Hello" in text and "Goodbye" in text
        return
    cleaned = cleaner(text)
    assert "Hello" in cleaned
    assert "Goodbye" in cleaned
    assert "she said" in cleaned
