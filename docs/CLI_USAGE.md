# ChapterFOLD CLI Usage

Patch 003 adds a command-line runner so you can test ChapterFOLD without launching the PySide desktop GUI.

This is useful for:

- testing EPUB conversions quickly;
- reproducing user bugs;
- running batch/manual smoke tests before a release;
- preparing the future FastAPI/Render backend;
- proving the core engine works independently from the desktop UI.

## Basic dry run

```bash
cd ~/Desktop/BioStudio/Github/ChapterFOLD
source ChapterFOLD/bin/activate
python scripts/run_chapterfold_job.py path/to/book.epub outputs --dry-run
```

## Basic conversion

```bash
python scripts/run_chapterfold_job.py path/to/book.epub outputs
```

## Export DOCX and Markdown too

```bash
python scripts/run_chapterfold_job.py path/to/book.epub outputs --export-docx --export-markdown
```

## Create an imposed/signature PDF

```bash
python scripts/run_chapterfold_job.py path/to/book.epub outputs --impose --signature-pages 16
```

## Save a JSON report

```bash
python scripts/run_chapterfold_job.py path/to/book.epub outputs --report-json outputs/job-report.json
```

## Use a settings JSON file

Create `settings.json`:

```json
{
  "variant": "aggressive-cleanup",
  "export_docx": true,
  "export_markdown": false,
  "create_imposed_pdf": true,
  "imposed_pages_per_signature": 16,
  "binding_direction": "ltr"
}
```

Then run:

```bash
python scripts/run_chapterfold_job.py path/to/book.epub outputs --settings-json settings.json
```

CLI flags override values loaded from `--settings-json`.

## Why this matters for the web version

The web app should eventually call the same core workflow:

```text
EPUB + shared settings object -> generated files + JSON result
```

The CLI runner is a stepping stone between the desktop GUI and the future hosted API.
