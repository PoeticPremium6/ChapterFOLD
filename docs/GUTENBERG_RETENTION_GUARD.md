# Gutenberg retention guard and multi-root fragment fix

Patch 011 fixes the failure where Moby Dick was correctly selected by the
Gutenberg spine selector, but the final PDF/Markdown still collapsed to a tiny
fragment.

## Root cause

The selected Gutenberg HTML body was stored as a fragment containing many
sibling top-level tags, for example:

```html
<p>...</p>
<h2>CHAPTER 17. The Ramadan.</h2>
<p>...</p>
<p>...</p>
```

The cleanup path parsed these fragments using BeautifulSoup's XML parser.
For multi-root fragments, that can silently keep only the first top-level tag.
This explains outputs that retained the selector report's 96% body text but
rendered only one paragraph in the final files.

## Changes

- Parse cleanup fragments with `html.parser` instead of XML.
- Add cleanup retention measurement.
- Add a Gutenberg-specific retention guard.
- Add a conservative fallback pass if cleanup removes too much text.
- Add local regression coverage for Moby Dick when the local fixture exists.

## Next manual test

Run Moby Dick again through the GUI with the same settings:

- Standard Cleanup
- Indented compact
- Markdown export enabled

Expected result: output should contain the full body from Chapter 1 onwards,
not just the Chapter 17 fragment.
