# ChapterFOLD diagnostics

Patch 002 adds a lightweight diagnostic-report layer so user bug reports are easier to reproduce.

The report includes:

- app/runtime stage
- timestamp
- operating system
- Python version
- virtual environment path
- key package versions
- selected settings, when provided
- sanitized input/output filenames
- optional error traceback

It intentionally does **not** include EPUB/PDF/DOCX contents.

## Command-line usage

From the repository root with your environment active:

```bash
python scripts/diagnose_project.py
```

## Developer usage

```python
from core.diagnostics import build_diagnostic_report

report = build_diagnostic_report(
    app_version="0.2.0",
    stage="PDF export",
    input_path="/home/user/Book.epub",
    output_dir="/home/user/output",
    settings={"trim_size": "A5", "signature_size": 16},
)
print(report)
```

## GUI integration

The patch attempts to add a **Help > Copy diagnostic report** action to the PySide GUI. If the GUI structure changes and the patch cannot apply safely, see:

```text
patch_notes/diagnostics_gui_integration_notes.md
```
