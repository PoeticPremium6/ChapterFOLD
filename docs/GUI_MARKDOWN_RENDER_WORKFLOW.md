# Render Edited Markdown in the GUI

Issue #22 adds a safer pre-editing workflow for users who want to remove author notes, tidy frontmatter, or splice books together before printing.

## Recommended workflow

1. Convert an EPUB normally in ChapterFOLD.
2. Open the generated `Editable.md` file.
3. Edit it in a text editor or Markdown editor.
4. Re-render the edited Markdown into a fresh PDF.

This avoids the fragile route of editing in Word or Google Docs, exporting to EPUB, and asking ChapterFOLD to clean up the messy EPUB HTML.

## Standalone GUI launcher

Run:

```bash
python scripts/render_markdown_gui.py
```

The dialog lets you:

- choose an edited Markdown file,
- open it in your system editor,
- choose an output folder,
- render a PDF,
- optionally export DOCX.

## Terminal equivalent

```bash
python scripts/render_markdown_book.py Edited.md reports/edited_render
```

Optional DOCX:

```bash
python scripts/render_markdown_book.py Edited.md reports/edited_render --docx
```

## Client-facing explanation

Use ChapterFOLD's generated Markdown as the editable intermediate format. Do not use Word or Google Docs as the EPUB editing step unless there is no alternative.
