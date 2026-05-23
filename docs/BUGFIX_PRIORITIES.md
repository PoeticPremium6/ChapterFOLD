# ChapterFOLD Bugfix Priorities Before Fullstack Sprint

Recommended order before investing heavily in the hosted web product.

## Priority 1: Confirm the patched foundation is stable

```bash
python scripts/preflight_check.py
python scripts/check_project.py
python chapterfold_app/app.py
```

## Priority 2: Fix Word / Google Docs to EPUB messiness

This is probably the most important product-quality issue.

Focus areas:

- excessive empty paragraphs
- broken dialogue lines
- scene break normalization
- smart quotes / punctuation
- chapter heading detection
- inline style noise
- Google Docs span/class clutter
- Word-generated HTML artifacts
- inconsistent paragraph indentation

Every fix should add or update a fixture test.

## Priority 3: Add conversion reports

Each conversion should eventually produce a small report with detected title/author, chapter count, selected settings, generated files, warnings, cleanup actions, and failed stage if any.

## Priority 4: Stabilize the canonical settings schema

The same settings object should serve desktop GUI, CLI, FastAPI backend, and future Next.js frontend.

## Priority 5: Add real-world private fixtures

Keep copyrighted/user EPUBs out of Git. Suggested local-only fixtures: Google Docs export, Word export, dialogue-heavy chapter, scene-break-heavy chapter, long novel, non-ASCII punctuation, malformed EPUB.

## Priority 6: Windows packaging reliability

Before promoting a desktop release, test on Windows, verify PyInstaller build, verify generated files open, verify fonts/WeasyPrint behavior, and verify paths with spaces/Unicode usernames.

## Priority 7: Web prototype only after engine confidence

Move heavily into fullstack once CLI is stable, API prototype validates jobs, fixture tests catch known bugs, conversion errors are diagnosable, and desktop workflow still works.
