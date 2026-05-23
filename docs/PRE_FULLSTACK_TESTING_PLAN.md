# ChapterFOLD Pre-Fullstack Testing Plan

Use this plan before moving heavily into Next.js, Supabase, Render, or Vercel work.

## 1. Preflight after every patch

```bash
cd ~/Desktop/BioStudio/Github/ChapterFOLD
source ChapterFOLD/bin/activate
python scripts/preflight_check.py
python scripts/check_project.py
```

This confirms imports, core schema, diagnostics, CLI, Qt, fixtures, and optional API wiring.

## 2. Desktop smoke test

```bash
python chapterfold_app/app.py
```

Check that the app opens, diagnostics works if available, EPUB input/output selection works, conversion starts, and errors are readable.

## 3. CLI smoke test

```bash
python scripts/run_chapterfold_job.py tests/fixtures/epubs/scene_breaks.epub /tmp/chapterfold-test --dry-run
python scripts/run_chapterfold_job.py tests/fixtures/epubs/scene_breaks.epub /tmp/chapterfold-test --export-markdown
```

## 4. Fixture regression tests

```bash
python scripts/build_sample_epubs.py
pytest tests/test_epub_regression_fixtures.py
```

## 5. API prototype smoke test

After Patch 5:

```bash
python scripts/run_api.py
```

Open:

```text
http://127.0.0.1:8000/docs
```

Do not treat this as production-ready yet. It is a local prototype.

## 6. Windows release check

Before public releases, repeat key tests on Windows or GitHub Actions.
Linux should be your development environment, but Windows remains the desktop release target.
