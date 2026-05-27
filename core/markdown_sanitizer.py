from __future__ import annotations

import re


COMMENT_PATTERN = re.compile(r"<!--\s*ANTHOLOGYSOURCEINDEX:\s*\d+\s*-->", re.IGNORECASE)
SECTION_OPEN_PATTERN = re.compile(r'<section\s+class=["\']chapterfold-title-page["\']\s*>', re.IGNORECASE)
SECTION_CLOSE_PATTERN = re.compile(r"</section>", re.IGNORECASE)
PAGE_BREAK_PATTERN = re.compile(r'<div\s+class=["\']chapterfold-page-break["\']\s*>\s*</div>', re.IGNORECASE)


def sanitize_chapterfold_markdown_for_render(markdown: str) -> str:
    """Remove or convert internal ChapterFOLD structural markup before rendering.

    Anthology generation may use lightweight HTML markers for internal structure.
    The renderer should not expose those markers as visible book text.
    """

    text = markdown

    text = COMMENT_PATTERN.sub("", text)
    text = SECTION_OPEN_PATTERN.sub("", text)
    text = SECTION_CLOSE_PATTERN.sub("", text)

    # Preserve the intended page break as semantic Markdown spacing.
    text = PAGE_BREAK_PATTERN.sub("\n\n<div style=\"page-break-after: always;\"></div>\n\n", text)

    # Avoid excessive blank pages caused by stacked page-break markers.
    text = re.sub(
        r'(?:\s*<div style="page-break-after: always;"></div>\s*){2,}',
        '\n\n<div style="page-break-after: always;"></div>\n\n',
        text,
    )

    # Normalize runaway blank lines while keeping readable separation.
    text = re.sub(r"\n{5,}", "\n\n\n", text)

    return text.strip() + "\n"
