from __future__ import annotations

from pathlib import Path
from typing import Callable

LogCallback = Callable[[str], None]


def run_processing(
    input_epub: Path,
    output_dir: Path,
    variant: str,
    log_callback: LogCallback | None = None,
) -> Path:
    if not input_epub.exists():
        raise FileNotFoundError(f"Input EPUB not found: {input_epub}")

    output_dir.mkdir(parents=True, exist_ok=True)

    def log(message: str) -> None:
        if log_callback:
            log_callback(message)

    log("Starting processing...")

    # ---- ADAPT THIS PART TO YOUR REAL CHAPTERFOLD CODE ----
    #
    # Example pattern:
    #
    # from core.epub_service import process_epub, CleanupSettings
    #
    # settings_map = {
    #     "standard": CleanupSettings(...),
    #     "aggressive-cleanup": CleanupSettings(...),
    #     "paragraph-dialogue-merge": CleanupSettings(...),
    # }
    #
    # settings = settings_map[variant]
    # output_path = output_dir / f"{input_epub.stem}_{variant}.epub"
    # process_epub(input_epub, output_path, settings=settings)
    #
    # return output_path
    #
    # -----------------------------------------------

    # Temporary placeholder so the UI can be tested first:
    output_path = output_dir / f"{input_epub.stem}_{variant}.epub"

    # Replace this block with the actual ChapterFOLD processing call.
    output_path.write_bytes(input_epub.read_bytes())

    log("Processing completed.")
    return output_path
