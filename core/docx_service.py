from __future__ import annotations

from pathlib import Path
from docx import Document


def export_clean_docx(
    *,
    title: str,
    author: str,
    sections: list[tuple[str, str]],
    output_path: str | Path,
) -> Path:
    output_path = Path(output_path)
    doc = Document()

    doc.add_heading(title, level=0)
    doc.add_paragraph(author)

    for heading, text in sections:
        if heading:
            doc.add_page_break()
            doc.add_heading(heading, level=1)

        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        for para in paragraphs:
            doc.add_paragraph(para)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))
    return output_path
