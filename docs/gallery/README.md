# ChapterFOLD Sample Gallery

This folder documents before/after examples for ChapterFOLD V2.0 hardening.

Suggested examples:

| Sample | Purpose | Input | Output |
|---|---|---|---|
| Unicode multilingual | Unicode rendering and page numbering | `tests/fixtures/unicode/multilingual.epub` | Interior PDF |
| Pride and Prejudice | Gutenberg cleanup, contents, image retention | `tests/fixtures/gutenberg/raw/Pride and Prejudice.epub` | Interior PDF + Markdown |
| PDF binding smoke | PDF input binding-only flow | `tests/fixtures/pdf/simple-binding.pdf` | Interior PDF + Imposed PDF |
| Ornament smoke | Page/chapter ornaments | Unicode or Pride fixture | Ornamented Interior PDF |
| Anthology smoke | Batch drag/drop anthology | Pride + Alice/Grimms | Anthology Markdown |

Each gallery sample should include:

- input file
- selected settings
- generated outputs
- conversion report
- manual QA log
- before/after screenshots when available
