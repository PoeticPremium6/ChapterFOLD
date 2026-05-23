# GUI Markdown Render Integration

Issue #22 now has a visible desktop path for edited Markdown.

Workflow:

1. Run a normal EPUB conversion and open the generated `Editable.md` file.
2. Edit the Markdown in any editor.
3. In ChapterFOLD, use `Tools > Render Edited Markdown...`.
4. Choose the edited `.md` file and an output folder.
5. Render a fresh PDF, and optionally DOCX.

This keeps the fragile Word/Google Docs → EPUB loop out of the workflow.
Instead, users edit the clean ChapterFOLD Markdown and send it back into the
rendering loop.

If the menu item is not visible on a specific desktop build, the same dialog can
still be launched with:

```bash
python scripts/render_markdown_gui.py
```
