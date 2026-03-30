from __future__ import annotations

import re
from dataclasses import dataclass


SCENE_BREAK_RE = re.compile(
    r"^\s*(\*\s*){3,}$|^\s*#{3,}\s*$|^\s*-\s*-\s*-\s*$|^\s*~\s*~\s*~\s*$"
)


@dataclass
class CleanupSettings:
    join_soft_wrapped_lines: bool = True
    join_dialogue_continuations: bool = True
    collapse_extra_blank_lines: bool = True
    preserve_scene_breaks: bool = True


def normalize_line_endings(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def normalize_spaces(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return text


def is_scene_break(line: str) -> bool:
    return bool(SCENE_BREAK_RE.match(line.strip()))


def join_dialogue_line_pair(current: str, nxt: str) -> str | None:
    """
    Join likely dialogue continuations, for example:

    "I don't know,"
    he said.

    -> "I don't know," he said.
    """
    current = current.rstrip()
    nxt = nxt.lstrip()

    if not current or not nxt:
        return None

    # Common cases: line ends with comma / quote / dash and next line starts lowercase
    if re.search(r'[,"\u201d\u2019—-]$', current) and re.match(r"^[a-z(]", nxt):
        return f"{current} {nxt}"

    # Dialogue tag continuation
    if re.search(r'["\u201d\u2019]$', current) and re.match(
        r"^(he|she|they|i|we|it|harry|draco|ron|hermione)\b",
        nxt,
        flags=re.IGNORECASE,
    ):
        return f"{current} {nxt}"

    return None


def clean_block_lines(lines: list[str], settings: CleanupSettings) -> list[str]:
    """
    Clean a sequence of non-blank lines belonging to one paragraph-ish block.
    """
    if not lines:
        return []

    result: list[str] = []
    i = 0

    while i < len(lines):
        current = lines[i].strip()

        if settings.join_dialogue_continuations and i + 1 < len(lines):
            joined = join_dialogue_line_pair(current, lines[i + 1])
            if joined is not None:
                result.append(joined)
                i += 2
                continue

        result.append(current)
        i += 1

    if settings.join_soft_wrapped_lines:
        merged = " ".join(x for x in result if x.strip())
        merged = re.sub(r" {2,}", " ", merged).strip()
        return [merged] if merged else []

    return result


def clean_text_block(text: str, settings: CleanupSettings | None = None) -> str:
    settings = settings or CleanupSettings()

    text = normalize_line_endings(text)
    text = normalize_spaces(text)

    lines = text.split("\n")
    output_blocks: list[str] = []
    current_block: list[str] = []

    def flush_current_block() -> None:
        nonlocal current_block
        if not current_block:
            return
        cleaned_lines = clean_block_lines(current_block, settings)
        if cleaned_lines:
            output_blocks.append("\n".join(cleaned_lines))
        current_block = []

    blank_run = 0

    for raw_line in lines:
        line = raw_line.strip()

        if not line:
            blank_run += 1
            flush_current_block()
            if not settings.collapse_extra_blank_lines or blank_run == 1:
                output_blocks.append("")
            continue

        blank_run = 0

        if settings.preserve_scene_breaks and is_scene_break(line):
            flush_current_block()
            output_blocks.append(line)
            continue

        current_block.append(line)

    flush_current_block()

    cleaned = "\n".join(output_blocks)

    if settings.collapse_extra_blank_lines:
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned.strip()
