from __future__ import annotations

VALID_CONTENTS_MODES = {
    "keep",
    "remove",
    "rebuild",
    "rebuild-paged",
}

DEFAULT_CONTENTS_MODE = "rebuild"


def normalize_contents_mode(value: str | None) -> str:
    mode = (value or DEFAULT_CONTENTS_MODE).strip().lower()
    if mode not in VALID_CONTENTS_MODES:
        raise ValueError(
            f"Unknown contents mode: {value!r}. "
            f"Expected one of: {', '.join(sorted(VALID_CONTENTS_MODES))}"
        )
    return mode


def should_strip_source_contents(value: str | None) -> bool:
    return normalize_contents_mode(value) in {"remove", "rebuild", "rebuild-paged"}


def should_generate_contents(value: str | None) -> bool:
    return normalize_contents_mode(value) in {"rebuild", "rebuild-paged"}
