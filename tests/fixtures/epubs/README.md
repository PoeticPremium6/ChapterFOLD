# EPUB regression fixtures

This folder is reserved for synthetic EPUB fixtures used by the test suite.

The generated `.epub` files are intentionally not committed by default. Build them with:

```bash
python scripts/build_sample_epubs.py
```

The fixture builder creates tiny, copyright-safe EPUBs covering:

- scene-break preservation
- dialogue continuation / soft wrapping
- Unicode punctuation and non-ASCII characters

These are regression fixtures, not user-facing sample books.
