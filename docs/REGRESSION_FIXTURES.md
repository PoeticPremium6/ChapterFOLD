# ChapterFOLD EPUB regression fixtures

Patch 004 adds a safer way to test ChapterFOLD against repeatable EPUB edge cases without storing copyrighted books in the repository.

## Why this matters

ChapterFOLD's hardest bugs are likely to come from real-world EPUB variation:

- strange paragraph boundaries
- dialogue split across visual lines
- scene breaks represented as symbols
- Unicode punctuation
- inconsistent metadata
- output differences between Linux and Windows

Before the web sprint, the engine needs repeatable tests that catch these issues early.

## Build the fixtures manually

```bash
python scripts/build_sample_epubs.py
```

By default, generated files go to:

```text
tests/fixtures/epubs/generated
```

## Run the tests

```bash
pytest tests/test_epub_regression_fixtures.py
python scripts/check_project.py
```

## Adding future fixtures

Add new synthetic examples to `scripts/build_sample_epubs.py` rather than committing copyrighted EPUBs. Each new bug should ideally become:

1. a small synthetic fixture;
2. a failing regression test;
3. a code fix;
4. a passing regression test.

That pattern is what will make the future API/web version much safer to build.
