# Gutenberg debugging workflow

ChapterFOLD currently handles many fanfic EPUBs well, but Project Gutenberg EPUBs vary widely. They can include front/back license text, repeated title headers, multiple generated contents pages, unusual chapter markup, footnotes, and START/END Gutenberg markers.

Patch 008 adds inspection tools only. It does not alter conversion behavior.

## Local fixture location

Store real Gutenberg EPUBs locally here:

```text
tests/fixtures/gutenberg/raw/
```

These full book files should stay out of Git. The repo hygiene patch should ignore this directory.

## Batch inspect all Gutenberg samples

```bash
cd ~/Desktop/BioStudio/Github/ChapterFOLD
source ChapterFOLD/bin/activate
python scripts/inspect_gutenberg_batch.py tests/fixtures/gutenberg/raw reports/gutenberg
```

Open:

```text
reports/gutenberg/summary.md
```

## Inspect one EPUB

```bash
python scripts/inspect_epub_structure.py \
  "tests/fixtures/gutenberg/raw/Little Women.epub" \
  reports/gutenberg/little_women.json \
  --markdown reports/gutenberg/little_women.md
```

## What to look for

- Does the EPUB have clear `START OF THE PROJECT GUTENBERG EBOOK` and `END OF THE PROJECT GUTENBERG EBOOK` markers?
- Which HTML files contain the actual prose?
- Are contents pages being confused with chapter bodies?
- Are chapters represented as headings, anchors, or only plain paragraphs?
- Is estimated body text suspiciously tiny?
- Do failures correlate with many TOC hints, footnotes, or no chapter heading candidates?

## Next patches

After generating reports for Dracula, Little Women, Moby Dick, and Dorian Gray, the next cleanup patches should be evidence-based:

1. Gutenberg-safe body extraction.
2. Retained-text sanity checks.
3. Conversion warning report when output text is suspiciously short.
