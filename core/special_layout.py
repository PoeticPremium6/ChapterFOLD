from __future__ import annotations

import html


def preserve_special_short_line_blocks(text: str) -> str:
    """Preserve long runs of short lines as special verse/layout blocks.

    Designed for shaped verse, songs, letters, and display-poem passages
    without converting ordinary short dialogue into special blocks.
    """
    lines = text.splitlines()
    out: list[str] = []
    buffer: list[str] = []

    def flush_buffer() -> None:
        nonlocal buffer
        if not buffer:
            return

        meaningful = [line for line in buffer if line.strip()]
        lengths = [len(line.strip()) for line in meaningful]
        shortish = [n for n in lengths if n <= 42]
        very_short = [n for n in lengths if n <= 24]
        verse_punct = sum(
            1
            for line in meaningful
            if line.strip().endswith((",", ";", ":", "—", "-", "’", "'", "”", '"'))
        )

        average_len = sum(lengths) / max(len(lengths), 1)
        short_ratio = len(shortish) / max(len(meaningful), 1)
        very_short_ratio = len(very_short) / max(len(meaningful), 1)

        should_preserve = (
            len(meaningful) >= 10
            and short_ratio >= 0.85
            and (
                average_len <= 28
                or very_short_ratio >= 0.55
                or verse_punct >= 4
            )
        )

        if should_preserve:
            out.append('<div class="special-layout-block">')
            for line in buffer:
                out.append(html.escape(line.rstrip()))
            out.append("</div>")
        else:
            out.extend(buffer)

        buffer = []

    for line in lines:
        s = line.strip()

        if not s:
            flush_buffer()
            out.append(line)
            continue

        if len(s) <= 42 and not s.startswith("#"):
            buffer.append(line)
        else:
            flush_buffer()
            out.append(line)

    flush_buffer()
    return "\n".join(out)
