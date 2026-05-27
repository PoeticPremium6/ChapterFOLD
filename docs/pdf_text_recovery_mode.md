# Experimental PDF Text Recovery Mode

This mode is separate from reliable PDF Binding Mode.

## Current status

Implemented backend support for text-based PDFs:

- Page-by-page text extraction.
- Extraction quality report.
- OCR-needed estimate.
- Confidence rating.
- Empty / likely scanned / garbled page detection.
- Repeated-line candidates for future header/footer cleanup.
- Editable Markdown export.
- Simple DOCX export.

## Current limitations

This mode does not yet support:

- OCR.
- scanned/image-only PDFs.
- layout-faithful reconstruction.
- multi-column reconstruction.
- tables.
- figures/captions.
- footnotes.
- polished paragraph reflow.
- robust chapter detection.

## Product framing

PDF Binding Mode is reliable and uses the PDF as final pages.

PDF Text Recovery Mode is experimental and attempts to recover editable text from text-based PDFs. It should be exposed as an optional recovery/analyze workflow, not as the default PDF workflow.

## Future GUI entry points

Suggested GUI actions:

- Analyze PDF text.
- Show extraction quality report.
- Export extracted Markdown.
- Export extracted DOCX.
