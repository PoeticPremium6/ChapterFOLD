# Full chapter TOC detection

Patch 021 improves Issue #20 by detecting chapter starts that exist as plain text lines, not only Markdown headings.

This helps books such as *Moby Dick*, where cleaned Markdown may contain headings for every source HTML chunk but plain-text chapter starts inside those chunks.

Implemented behavior:

- detect `CHAPTER 2. The Carpet-Bag.` style lines
- detect Roman numeral chapter headings
- detect `Epilogue`
- promote inline chapter starts to `##` headings during TOC render workflows
- rebuild `## Contents` from the full detected chapter list

This still does not create true PDF page-numbered TOCs. It creates an anchor-ready full chapter TOC. Page-synced TOC should remain a later two-pass PDF-rendering feature.
